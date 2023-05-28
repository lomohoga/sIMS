import smtplib
import time
from secrets import randbelow
from email.message import EmailMessage

from flask import Blueprint, Response, render_template, request, session

from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.database import connect_db
from src.blueprints.auth import login_required, update_session
from src.blueprints.bp_auth import generateHash

# create SMTP session for sending the mail
# TODO: Find other SMTP server
def start_email_session ():
    session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
    session.starttls() #enable security
    session.login(sender_address, sender_pass) #login with mail_id and password
    return session

# send email based on request type
# TODO: Fix email content (too bland)
def send_email (session, type, recipient, username = "", password = ""):
    # construct message
    msg = EmailMessage()
    msg['From'] = "sIMS <" + sender_address + ">"
    msg['To'] = recipient

    if(type == "add"):
        msg["Subject"] = "Account credentials"
        msg.set_content(f'Good day! You have been added into sIMS. Please use the following credentials to log in.\nUsername: {username}\nPassword: {password}')
    elif(type == "delete"):
        msg["Subject"] = "Account removal"
        msg.set_content("Your account was deleted.")
    elif(type == "promote"):
        msg["Subject"] = "Account promoted"
        msg.set_content("Your account was promoted to Custodian. This means that\n(a) You can now add, delete, and update items in the inventory.\n(b) You can now approve or deny item requests.")
    elif(type == "demote"):
        msg["Subject"] = "Account demoted"
        msg.set_content("Your account was demoted to Personnel. This means that\n(a) You can no longer add, delete, and update items in the inventory.\n(b) You can no longer approve or deny item requests.")
    elif(type == "password"):
        msg["Subject"] = "Password changed"
        msg.set_content("Your account password was changed.")
    elif(type == "email"):
        msg["Subject"] = "Email updated"
        msg.set_content("Your account email was updated.") 
    elif(type == "code"):
        msg["Subject"] = "Reset password"
        msg.set_content(f'Your 4-digit code is {username}.')         
    
    text = msg.as_string()
    session.sendmail(sender_address, recipient, text)

# generate username for new users
def generate_userID (first, last, cxn):
    userID = first[0].lower() + last.lower()
    userID_length = len(userID)
    items = 1
    counter = 0

    db = cxn.cursor()
    while(items):
        db.execute(f"SELECT * FROM user WHERE Username LIKE '{userID}';")
        items = len(db.fetchall())

        if(items):
            counter = counter + 1
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
        values = request.get_json()["values"]

        try:
            cxn = connect_db()

            mail_session = start_email_session()

            #Add users in database
            default = generateHash('ilovesims')
            i = 0
            try:
                for v in values:
                    userID = generate_userID(v[0], v[1], cxn)
                    db = cxn.cursor()
                    db.execute(f"INSERT INTO user VALUES ('{userID}', '{default}', '{v[0]}', '{v[1]}', '{v[2]}', {v[3]}, 0, 0);")
                    i = i + 1
                cxn.commit()

                #Email here
                for v in values:
                    send_email(mail_session, "add", v[2], userID, 'ilovesims')
            except Exception as e:
                if(e.args[0] == 1062):
                    return {"error": e.args[0], "msg": values[i][2]}, 500
                else:
                    return { "error": e.args[0] }, 500
            finally:
                cxn.close()
                mail_session.quit()
        except Exception as e:
            return { "error": e.args[0] }, 500
        
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
        users = request.get_json()["users"]
        emails = request.get_json()["emails"]
        choices = [(x,) for x in users]

        try:
            cxn = connect_db()
            db = cxn.cursor()

            try:
                db.executemany("DELETE FROM user WHERE Username = %s;", choices)
                cxn.commit()

                mail_session = start_email_session()
                for p in emails:
                    send_email(mail_session, "delete", p)   
            except Exception as e:
                return { "error": e.args[0] }, 500
            finally:
                cxn.close()
                mail_session.quit()

        except Exception as e:
            return { "error": e.args[0] }, 500

        return Response(status = 200)

# route for promoting user
@bp_user.route('/promote', methods = ["POST"])
@login_required
def promote_user ():
    username = request.get_json()["Username"]
    
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"UPDATE user SET RoleID = 1 WHERE Username = '{username}';")
        db.execute(f"SELECT Email FROM user WHERE Username = '{username}';")
        email = db.fetchone()[0]
        cxn.commit()

        mail_session = start_email_session()
        send_email(mail_session, "promote", email)
        mail_session.quit()
    except Exception as e:
        return Response(status = 500)
    finally:
        cxn.close()
    
    return Response(status = 200)

# route for demoting user
@bp_user.route('/demote', methods = ["POST"])
@login_required
def demote_user ():
    username = request.get_json()["Username"]
    
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"UPDATE user SET RoleID = 2 WHERE Username = '{username}';")
        db.execute(f"SELECT Email FROM user WHERE Username = '{username}';")
        email = db.fetchone()[0]
        cxn.commit()

        mail_session = start_email_session()
        send_email(mail_session, "demote", email)
        mail_session.quit()
    except Exception as e:
        return Response(status = 500)
    finally:
        cxn.close()
    
    return Response(status = 200)

# route for searching users
@bp_user.route('/search')
@login_required
def search_users ():
    if session['user']['RoleID'] != 0: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to search for users in the database."), 403
    
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]

    conditions = []
    for x in keywords:
        conditions.append(f"(Username LIKE '%{x}%' OR FirstName LIKE '%{x}%' OR LastName LIKE '%{x}%')")

    query = f"SELECT Username, FirstName, LastName, Email, RoleName as Role FROM user LEFT JOIN role USING (RoleID) {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY Username;"
    cxn = 0
    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        users = db.fetchall()
    except Exception as e:
        return Response(status = 500)
    finally:
        if(cxn != 0):
            cxn.close()

    return { "users": [{
        "Username": x[0],
        "FirstName": x[1],
        "LastName": x[2],
        "Email": x[3],
        "Role": x[4]
    } for x in users] }, 200

# route for checking password
@bp_user.route('/check_password', methods = ["POST"])
def check_password ():
    password = request.get_json()["values"]
    if(session['user']['Password'] == generateHash(password)):
        return Response(status = 200)
    else:
        return Response(status = 304)

# route for checking email
@bp_user.route('/check_email', methods = ["POST"])
def check_email ():
    email = request.get_json()["email"]

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT COUNT(*) FROM user WHERE Email = '{email}';")
            count = db.fetchone()
            if (count[0] == 0): 
                return { "error": -1, "msg": "There are no accounts associated with this email address in the database." }, 500
        
            generate_code(email)
        except:
            return { "error": e.args[0] }, 500
        finally:
            cxn.close()
    except Exception as e:
        return { "error": e.args[0] }, 500

    return Response(status = 200)

# route for generating code
@bp_user.route('/generate_code', methods = ["POST"])
def generate_code (email = ''):
    # Set up email
    if (email == ''): email = request.get_json()["email"]
    
    # Generate code
    code_key = randbelow(9000) + 1000
    print(code_key)

    # Update code in database
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"UPDATE user SET Code = {code_key}, CodeIssueDate = {time.time()} WHERE Email = '{email}';")
        cxn.commit()

        # Email code
        mail_session = start_email_session()
        send_email(mail_session, "code", email, code_key)
        mail_session.quit()
    except Exception as e:
        return { "error": e.args[0] }, 500
    finally:
        cxn.close()

    return Response(status = 200)

# route for checking code
@bp_user.route('/verify_code', methods = ["POST"])
def check_code ():
    code = request.get_json()["code"]
    email = request.get_json()["email"]

    # Get code in database
    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT Code, CodeIssueDate FROM user WHERE Email = '{email}';")
            count = db.fetchone()

            if (int(count[0]) != code):
                return { "error": -1, "msg": "The code you entered is incorrect. Please try again. "}, 500
            elif (int(count[0]) == code and time.time() - count[1] <= 180):
                return Response(status = 200)
            else:
                return { "error": -1, "msg": "Your code has expired. Please generate a new code by clicking the \"Resend code\" button above." }, 500
        except Exception as e:
            return { "error": e.args[0] }, 500
        finally:
            cxn.close()
    except Exception as e:
        return { "error": e.args[0] }, 500

# route for changing password (forgot password)
@bp_user.route('/forgot_password', methods = ["POST"])
def forgot_password ():
    [email, password] = request.get_json()

    try:
        cxn = connect_db()
        db = cxn.cursor()
        mail_session = start_email_session()

        try:
            db.execute(f"UPDATE user SET Password = '{generateHash(password)}' WHERE Email = '{email}';")
            cxn.commit()

            send_email(mail_session, "password", email)
        except Exception as e:
            return { "error": e.args[0] }, 500
        finally:
            mail_session.quit()
            cxn.close()
    except Exception as e:
        return { "error": e.args[0] }, 500

    return Response(status = 200)

# route for changing password (update password)
@bp_user.route('/change_password', methods = ["POST"])
@login_required
def change_password ():
    req = request.get_json()

    if generateHash(req['old-password']) != session['user']['Password']: 
        return { "error": -1, "msg": "The old password you entered does not match your current password. Please try again." }, 500

    try:
        cxn = connect_db()
        db = cxn.cursor()
        mail_session = start_email_session()

        try:
            db.execute(f"UPDATE user SET Password = '{generateHash(req['new-password'])}' WHERE Username = '{session['user']['Username']}';")
            cxn.commit()

            send_email(mail_session, "password", session['user']['Email'])
        except Exception as e:
            return { "error": e.args[0] }, 500
        finally:
            cxn.close()
            mail_session.quit()
    except Exception as e:
        return { "error": e.args[0] }, 500

    return Response(status = 200)

# route for changing email address
@bp_user.route('/change_email', methods = ["POST"])
@login_required
def change_email ():
    password = request.get_json()["password"]
    
    if session['user']['Password'] != generateHash(password):
        return { "error": -1, "msg": "The password you have entered is incorrect. Please make sure you have entered your password correctly." }, 500
    else:
        email = request.get_json()["email"]

        try:
            cxn = connect_db()
            db = cxn.cursor()
            mail_session = start_email_session()

            try:
                db.execute(f"UPDATE user SET Email = '{email}' WHERE Username = '{session['user']['Username']}';")
                cxn.commit()

                send_email(mail_session, "email", email)
            except Exception as e:
                return { "error": e.args[0], "msg": email }, 500
            finally:
                cxn.close()
                mail_session.quit()
        except Exception as e:
            return { "error": e.args[0] }, 500

        return Response(status = 200)
