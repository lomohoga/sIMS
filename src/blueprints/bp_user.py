import smtplib
import random
import time
from email.message import EmailMessage

from flask import Blueprint, Response, redirect, render_template, url_for, request, session

from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.database import connect_db
from src.blueprints.auth import login_required
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
    #Contruct message
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
        msg.set_content("Your account was promoted to custodian. This means that\n(a) You can now add, delete, and update items in the inventory.\n(b) You can now approve or deny item requests.")
    elif(type == "demote"):
        msg["Subject"] = "Account demoted"
        msg.set_content("Your account was demoted to personnel. This means that\n(a) You can no longer add, delete, and update items in the inventory.\n(b) You can no longer approve or deny item requests.")
    elif(type == "password"):
        msg["Subject"] = "Password changed"
        msg.set_content("Your account password was changed.")
    elif(type == "email"):
        msg["Subject"] = "Email updated"
        msg.set_content("Your account email was updated.")         
    
    text = msg.as_string()
    session.sendmail(sender_address, recipient, text)

# generate username for new users
def generate_userID (first, last):
    userID = first[0].lower() + last.lower()
    userID_length = len(userID)
    items = 1
    counter = 0

    cxn = connect_db()
    db = cxn.cursor()
    while(items):
        db.execute(f"SELECT * FROM user WHERE Username LIKE '{userID}';")
        items = len(db.fetchall())

        if(items):
            counter = counter + 1;
            userID = userID[:userID_length] + str(counter);

    cxn.close()
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
        return render_template("user/user.html", active="users")

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
            db = cxn.cursor()

            mail_session = start_email_session()

            default = generateHash('ilovesims')
            index = 0
            for v in values:
                userID = generate_userID(v[0], v[1])
                index = index + 1
                
                db.execute(f"INSERT INTO user VALUES ('{userID}', '{default}', '{v[0]}', '{v[1]}', '{v[2]}', {v[3]});")
                send_email(mail_session, "add", v[2], userID, 'ilovesims')

            cxn.commit()
        except Exception as e:
            print(index)
            return Response(status = 500, response = [str(index)])
        finally:
            cxn.close()
            mail_session.quit()
        
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

            db.executemany("DELETE FROM user WHERE Username = %s;", choices)
            cxn.commit()

            mail_session = start_email_session()
            for p in emails:
                if p != '-':
                    send_email(mail_session, "delete", p)

        except Exception as e:
            return Response(status = 500)
        finally:
            cxn.close()
            mail_session.quit()

        return Response(status = 200)

# route for promoting user
@bp_user.route('/promote', methods = ["POST"])
@login_required
def promote_user ():
    values = request.get_json()["values"]
    
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"UPDATE user SET RoleID = 1 WHERE Username = '{values[0]}';")
        cxn.commit()

        mail_session = start_email_session()
        if(values[1] and values[1] != "NULL"):
            send_email(mail_session, "promote", values[1])
        
    except Exception as e:
        return Response(status = 500)
    finally:
        cxn.close()
        mail_session.quit()
    
    return Response(status = 200)

# route for demoting user
@bp_user.route('/demote', methods = ["POST"])
@login_required
def demote_user ():
    values = request.get_json()["values"]
    
    try:
        cxn = connect_db()
        db = cxn.cursor()
    

        db.execute(f"UPDATE user SET RoleID = 2 WHERE Username = '{values[0]}';")
        cxn.commit()

        mail_session = start_email_session()
        if(values[1] and values[1] != "NULL"):
            send_email(mail_session, "demote", values[1])
    except Exception as e:
        return Response(status = 500)
    finally:
        cxn.close()
        mail_session.quit()
    
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

    query = f"SELECT Username, LastName, FirstName, Email, RoleName FROM user LEFT JOIN role USING (RoleID) {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY Username;"
    cxn = 0
    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        users = db.fetchall()
    except Exception as e:
        return { "users": [] }, 500
    finally:
        if(cxn != 0):
            cxn.close()

    return { "users": users }, 200

# route for updating user settings
@bp_user.route('/settings')
def change_account_settings ():
    return render_template("user/settings.html", active = 'settings')

# route for checking password
@bp_user.route('/check_password', methods = ["POST"])
def check_password():
    password = request.get_json()["values"]
    if(session['user']['Password'] == generateHash(password)):
        return Response(status = 200)
    else:
        return Response(status = 304)

code_key = 0
time_start = 0

# route for checking email
@bp_user.route('/check_email', methods = ["POST"])
def check_email():
    email = request.get_json()["email"]

    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT COUNT(*) FROM user WHERE Email = '{email}';")
        count = db.fetchone()

        if(count[0] == 0):
            return Response(status = 304)
        
        generate_code()
        
        #mail_session = start_email_session()
        #send_email(mail_session, "password", email)
        #mail_session.quit()

    except Exception as e:
        # TODO: Fix this
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()

    return Response(status = 200)

# route for checking code
@bp_user.route('/generate_code', methods = ["POST"])
def generate_code():
    global code_key
    global time_start
    
    code_key = random.randint(1000, 9999)
    print(code_key)
    time_start = time.time()
    return Response(status = 200)

# route for checking code
@bp_user.route('/verify_code', methods = ["POST"])
def check_code():
    code = request.get_json()["code"]
    print(code_key)

    if(int(code) == code_key and time.time() - time_start <= 180):
        return Response(status = 200)
    else:
        return Response(status = 304)

# route for updating password
@bp_user.route('/settings/reset_password', methods = ["POST"])
def change_password2():
    password = request.get_json()['password']
    email = request.get_json()['email']

    try:
        cxn = connect_db()
        db = cxn.cursor()

        new_password = generateHash(password)
        db.execute(f"UPDATE user SET Password = '{new_password}' WHERE Email = '{email}';")
        cxn.commit()

        #mail_session = start_email_session()
        #send_email(mail_session, "password", email)
        #mail_session.quit()

    except Exception as e:
        # TODO: Fix this
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()

    return Response(status = 200)

# route for updating password
@bp_user.route('/settings/changepassword', methods = ["POST"])
@login_required
def change_password ():
    req = request.form['new-password']

    try:
        cxn = connect_db()
        db = cxn.cursor()

        new_password = generateHash(req)
        db.execute(f"UPDATE user SET Password = '{new_password}' WHERE Username = '{session['user']['Username']}';")
        cxn.commit()

        if (session['user']['Email'] is not None) and (session['user']['Email'] != "NULL"):
            mail_session = start_email_session()
            send_email(mail_session, "password", session['user']['Email'])
            mail_session.quit()

    except Exception as e:
        # TODO: Fix this
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()

    return redirect(url_for('bp_auth.logout'))

# route for changing email address
@bp_user.route('/settings/emailchange', methods = ["POST"])
@login_required
def change_email ():
    password = request.get_json()["password"]
    
    if(session['user']['Password'] != generateHash(password)):
        return Response(status = 304)
    else:
        email = request.get_json()["email"]

        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"UPDATE user SET Email = '{email}' WHERE Username = '{session['user']['Username']}';")
            cxn.commit()

            mail_session = start_email_session()
            send_email(mail_session, "email", email)
            mail_session.quit()

        except Exception as e:
            # TODO: Fix this
            return Response(status = 500)
        finally:
            cxn.close()

        return Response(status = 200)
