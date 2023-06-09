import smtplib
import time
from secrets import randbelow
from email.message import EmailMessage

from flask import Blueprint, Response, render_template, request, session, current_app
from mysql.connector import Error as MySQLError

from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.database import connect_db
from src.blueprints.auth import login_required
from src.blueprints.bp_auth import generateHash
from src.blueprints.exceptions import UserRoleError, UserNotFoundError, ExistingEmailError, DatabaseConnectionError, EmailNotFoundError, InvalidEmailError, IncorrectPasswordError, IncorrectCodeError, ExpiredCodeError

# create SMTP session for sending the mail
# TODO: Find other SMTP server
def start_email_session ():
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    return session

# send email based on request type
# TODO: Fix email content (too bland)
def send_email (session, type, recipient, **kwargs):
    # construct message
    msg = EmailMessage()
    msg['From'] = "sIMS <" + sender_address + ">"
    msg['To'] = recipient

    if(type == "add"):
        msg["Subject"] = "Account credentials"
        msg.set_content(f"Good day! You have been added into sIMS. Please use the following credentials to log in.\nUsername: {kwargs['username']}\nPassword: {kwargs['password']}")
    elif(type == "delete"):
        msg["Subject"] = "Account removal"
        msg.set_content("Your account was deleted.")
    elif(type == "promote"):
        msg["Subject"] = "Account promoted"
        msg.set_content("Your account was promoted to Custodian. This means that:\n(a) You can now add, delete, and update items in the inventory.\n(b) You can now approve or deny item requests.")
    elif(type == "demote"):
        msg["Subject"] = "Account demoted"
        msg.set_content("Your account was demoted to Personnel. This means that:\n(a) You can no longer add, delete, and update items in the inventory.\n(b) You can no longer approve or deny item requests.")
    elif(type == "password"):
        msg["Subject"] = "Password changed"
        msg.set_content("Your account password was changed.")
    elif(type == "email"):
        msg["Subject"] = "Email updated"
        msg.set_content("Your account email was updated.") 
    elif(type == "code"):
        msg["Subject"] = "Reset password"
        msg.set_content(f"Your 4-digit code is {kwargs['code']}.")
    
    text = msg.as_string()
    session.sendmail(sender_address, recipient, text)

# generate username for new users
def generate_userID (first, last, cxn):
    userID = first.replace(" ", "")[0].lower() + last.replace(" ", "").lower()
    userID_length = len(userID)

    items = 1
    counter = 0

    db = cxn.cursor()
    while items:
        db.execute(f"SELECT * FROM user WHERE Username LIKE '{userID}'")
        items = len(db.fetchall())

        if items:
            counter += 1
            userID = userID[:userID_length] + str(counter)

    return userID

### ROUTES ###

bp_user = Blueprint("bp_user", __name__, url_prefix = "/users")

# route for users
@bp_user.route('/')
@login_required
def show_users ():
    if session['user']['RoleID'] != 0: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to see the users in the database."), 403
    else: 
        return render_template("user/users.html", active="users")

# TODO: Change this to other email address
sender_address = 'iamjhin01@gmail.com'
sender_pass = 'qenmyutlantkdgap'

# route for adding users
# password for new users is 'ilovesims'
@bp_user.route('/add', methods = ["GET", "POST"])
@login_required
def add_users ():
    if request.method == 'GET':
        if session['user']['RoleID'] != 0: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add users to the database."), 403
        else: 
            return render_template("user/add.html")

    if request.method == 'POST':
        try:
            cxn = None
            mail_session = None
            try:
                values = request.get_json()["values"]

                cxn = connect_db()
                db = cxn.cursor()
                mail_session = start_email_session()
                default = generateHash('ilovesims')

                users = {}

                for v in values:
                    db.execute(f"SELECT * FROM user WHERE Email = '{v['email']}'")
                    if db.fetchone() is not None: raise ExistingEmailError(email = v['email'])

                    userID = generate_userID(v['firstName'], v['lastName'], cxn)
                    db.execute(f"INSERT INTO user VALUES ('{userID}', '{default}', '{v['firstName']}', '{v['lastName']}', '{v['email']}', {v['role']}, 0, 0)")
                    users[v['email']] = userID
                cxn.commit()

                for u in users: send_email(mail_session, "add", u, username = users[u], password = 'ilovesims')
            except MySQLError as e:
                if e.args[0] == 3819: raise InvalidEmailError
                if e.args[0] == 2003: raise DatabaseConnectionError

                current_app.logger.error(e.args[1])
                return { "error": e.args[1] }, 500
            finally:
                if cxn is not None: cxn.close()
                if mail_session is not None: mail_session.quit()
        except ExistingEmailError as e:
            current_app.logger.error(e)
            return { "error": str(e), "email": e.args[0] }, 500
        except Exception as e:
            current_app.logger.error(e)
            return { "error": str(e) }, 500
        
        return Response(status = 200)

# route for removing users
@bp_user.route('/remove', methods = ["GET", "POST"])
@login_required
def remove_users ():
    if request.method == "GET":
        if session['user']['RoleID'] != 0: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove users from the database."), 403
        else: 
            return render_template("user/remove.html")

    if request.method == "POST":
        try:
            cxn = None
            mail_session = None
            try:
                users = request.get_json()["users"]

                cxn = connect_db()
                db = cxn.cursor()
                mail_session = start_email_session()

                emails = []

                for user in users:
                    db.execute(f"SELECT Email FROM user WHERE Username = '{user}'")
                    f = db.fetchone()
                    if f is None: raise UserNotFoundError(username = user)

                    emails.append(f[0])
                    
                    db.execute(f"DELETE FROM user WHERE Username = '{user}'")
                cxn.commit()

                for p in emails: send_email(mail_session, "delete", p)
            except MySQLError as e:
                if e.args[0] == 2003: raise DatabaseConnectionError

                current_app.logger.error(e.args[1])
                return { "error": e.args[1] }, 500
            finally:
                if cxn is not None: cxn.close()
                if mail_session is not None: mail_session.quit()
        except Exception as e:
            current_app.logger.error(e)
            return { "error": str(e) }, 500

        return Response(status = 200)

# route for promoting user
@bp_user.route('/promote', methods = ["POST"])
@login_required
def promote_user ():
    try:
        cxn = None
        mail_session = None
        try:
            username = request.get_json()["username"]

            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{username}'")
            f = db.fetchone()
            if f is None: raise UserNotFoundError(username = username)

            role = f[0]
            if role != 2: raise UserRoleError(username = username, role = role)

            db.execute(f"UPDATE user SET RoleID = 1 WHERE Username = '{username}'")
            db.execute(f"SELECT Email FROM user WHERE Username = '{username}'")
            email = db.fetchone()[0]
            cxn.commit()

            send_email(mail_session, "promote", email)
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500
    
    return Response(status = 200)

# route for demoting user
@bp_user.route('/demote', methods = ["POST"])
@login_required
def demote_user ():
    try:
        cxn = None
        mail_session = None
        try:
            username = request.get_json()["username"]
        
            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{username}'")
            f = db.fetchone()
            if f is None: raise UserNotFoundError(username = username)

            role = f[0]
            if role != 1: raise UserRoleError(username = username, role = role)

            db.execute(f"UPDATE user SET RoleID = 2 WHERE Username = '{username}'")
            db.execute(f"SELECT Email FROM user WHERE Username = '{username}'")
            email = db.fetchone()[0]
            cxn.commit()

            send_email(mail_session, "demote", email)
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500
    
    return Response(status = 200)

# route for searching users
@bp_user.route('/search')
@login_required
def search_users ():
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]

    conditions = []
    for x in keywords:
        conditions.append(f"(Username LIKE '%{x}%' OR FirstName LIKE '%{x}%' OR LastName LIKE '%{x}%')")

    query = f"SELECT Username, FirstName, LastName, Email, RoleName as Role FROM user LEFT JOIN role USING (RoleID) {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY Username"
    
    try:
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(query)
            users = db.fetchall()
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return { "users": [{
        "Username": x[0],
        "FirstName": x[1],
        "LastName": x[2],
        "Email": x[3],
        "Role": x[4]
    } for x in users] }, 200

### FORGOT PASSWORD & CHANGE PASSWORD ROUTES ###

# route for checking email
@bp_user.route('/check_email', methods = ["POST"])
def check_email ():
    try:
        cxn = None
        try:
            email = request.get_json()["email"]

            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT * FROM user WHERE Email = '{email}'")
            if db.fetchone() is None: raise EmailNotFoundError(email = email)

            generate_code(email)
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return Response(status = 200)

# route for generating code
@bp_user.route('/generate_code', methods = ["POST"])
def generate_code (email = ''):
    try:
        cxn = None
        mail_session = None
        try:
            if (email == ''): email = request.get_json()["email"]
            code_key = randbelow(9000) + 1000

            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT * FROM user WHERE Email = '{email}'")
            if db.fetchone() is None: raise EmailNotFoundError(email = email)

            db.execute(f"UPDATE user SET Code = {code_key}, CodeIssueDate = {time.time()} WHERE Email = '{email}'")
            cxn.commit()

            mail_session = start_email_session()
            send_email(mail_session, "code", email, code = code_key)
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[0] }, 500
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return Response(status = 200)

# route for checking code
@bp_user.route('/verify_code', methods = ["POST"])
def check_code ():
    try:
        cxn = None
        try:
            code = request.get_json()["code"]
            email = request.get_json()["email"]

            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT Code, CodeIssueDate FROM user WHERE Email = '{email}'")
            f = db.fetchone()
            if f is None: raise EmailNotFoundError(email = email)

            if (int(f[0]) != code): raise IncorrectCodeError
            if (int(f[0]) == code and time.time() - f[1] > 180): raise ExpiredCodeError
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500
    
    return Response(status = 200)

# route for changing password (forgot password)
@bp_user.route('/forgot_password', methods = ["POST"])
def forgot_password ():
    try:
        cxn = None
        mail_session = None
        try:
            r = request.get_json()
            email, password = r['email'], r['new-password']

            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            db.execute(f"SELECT * FROM user WHERE Email = '{email}'")
            if db.fetchone() is None: raise EmailNotFoundError(email = email)

            db.execute(f"UPDATE user SET Password = '{generateHash(password)}' WHERE Email = '{email}'")
            cxn.commit()

            send_email(mail_session, "password", email)
        except MySQLError as e:
            if e.args[0] == 2003: raise DatabaseConnectionError

            current_app.logger.error(e.args[1])
            return { "error": e.args[1] }, 500
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return Response(status = 200)

# route for changing password (update password)
@bp_user.route('/change_password', methods = ["POST"])
@login_required
def change_password ():
    try:
        cxn = None
        mail_session = None
        try:
            req = request.get_json()
            if generateHash(req['old-password']) != session['user']['Password']: raise IncorrectPasswordError(changing = True)

            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            db.execute(f"SELECT * FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise UserNotFoundError(username = session['user']['Username'])

            db.execute(f"UPDATE user SET Password = '{generateHash(req['new-password'])}' WHERE Username = '{session['user']['Username']}'")
            cxn.commit()
            send_email(mail_session, "password", session['user']['Email'])
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: raise DatabaseConnectionError
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return Response(status = 200)

# route for changing email address
@bp_user.route('/change_email', methods = ["POST"])
@login_required
def change_email ():
    try:
        cxn = None
        mail_session = None
        try:
            password = request.get_json()["password"]
            
            if session['user']['Password'] != generateHash(password):
                return { "error": -1, "msg": "The password you have entered is incorrect. Please make sure you have entered your password correctly." }, 500
            
            email = request.get_json()["email"]

            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            db.execute(f"SELECT * FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise UserNotFoundError(username = session['user']['Username'])

            db.execute(f"UPDATE user SET Email = '{email}' WHERE Username = '{session['user']['Username']}'")
            cxn.commit()
            send_email(mail_session, "email", email)
        finally:
            if cxn is not None: cxn.close()
            if mail_session is not None: mail_session.quit()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 3819: raise InvalidEmailError(email = email)
        if e.args[0] == 2003: raise DatabaseConnectionError
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": str(e) }, 500

    return Response(status = 200)
