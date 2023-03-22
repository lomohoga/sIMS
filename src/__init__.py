import os
import hashlib          #for hashing function
import functools        #for wrapper views
import locale
import re               #for regex
import mysql.connector  #for mysql
import smtplib          #for sending emails

from flask import Flask, render_template, request, redirect, url_for, session, Response, abort, make_response
from re import search
#from src.formgen import formgen
from email.message import EmailMessage

locale.setlocale(locale.LC_ALL, 'en_PH.utf8')

def format_items (items):
    return [
        {
            "ItemID": item[0],
            "ItemName": item[1],
            "ItemDescription": item[2],
            "ShelfLife": locale.format("%s", item[3], grouping = True) if item[3] != None else "\u2014",
            "Price": locale.currency(item[4], grouping = True),
            "AvailableStock": locale.format("%s", item[5], grouping = True),
            "Unit": item[6]
        } for item in items
    ]


def format_requests (requests, custodian = True):
    return [
        {
            "RequestID": req[0],
            "ItemID": req[1],
            "ItemName": req[2],
            "ItemDescription": req[3],
            "RequestedBy": req[4],
            "RequestQuantity": locale.format("%s", req[5], grouping = True),
            "Unit": req[6],
            "RequestDate": req[7],
            "Status": req[8]
        } if custodian
        else {
            "RequestID": req[0],
            "ItemID": req[1],
            "ItemName": req[2],
            "ItemDescription": req[3],
            "RequestQuantity": locale.format("%s", req[5], grouping = True),
            "Unit": req[6],
            "RequestDate": req[7],
            "Status": req[8]
        } for req in requests
    ]


def format_deliveries (deliveries):
    return [
        {
            "DeliveryID": d[0],
            "ItemID": d[1],
            "ItemName": d[2],
            "ItemDescription": d[3],
            "DeliveryQuantity": locale.format("%s", d[4], grouping = True),
            "Unit": d[5],
            "ShelfLife": locale.format("%s", d[6], grouping = True) if d[6] is not None else "\u2014",
            "DeliveryDate": d[7],
            "ReceivedBy": d[8],
            "IsExpired": bool(d[9])
        } for d in deliveries
    ]


def decode_keyword (k):
    return re.sub(r'%[0-9A-F]{2}', lambda x: chr(int(x.group(0)[1:3], base = 16)), k).replace("'", "\\'")


def escape (s):
    return re.sub(r'[\u2018\u2019\u201c\u201d]', lambda x: "\\'" if x.group(0) in ['\u201c', '\u201d'] else "\"", s)


def connect_db ():
    return mysql.connector.connect(host = "localhost", user = "root", password = "password", database = "sims")


def create_app (test_config = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config = True)
    app.config.from_mapping(SECRET_KEY = 'dev')

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # encrypt password using sha256
    def generateHash (a):
        m = hashlib.sha256()
        m.update(a.encode('utf-8'))
        return m.hexdigest()
    

    # route for login page
    # session['user'] is a dictionary with keys = ["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName"]
    @app.route('/login', methods=('GET', 'POST'))
    def login ():
        error = ""

        if request.method == 'POST':
            username = request.form['uname']
            password = request.form['pword']

            cxn = connect_db()
            db = cxn.cursor()
            db.execute(f"SELECT Username, Password, FirstName, LastName, RoleID, RoleName, Email FROM user LEFT JOIN role USING (RoleID) WHERE Username = '{username}'")
            user = {a: b for a, b in zip(["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName", "Email"], db.fetchone())}
            cxn.close()

            if user is None:
                error = 'User not found.'
            elif (username != "" and password != "" and generateHash(password) != user["Password"]):
                error = 'Incorrect password.'

            if error == "":
                session.clear()
                session['user'] = user
                return redirect(url_for('inventory'))

        return render_template("login.html", msg = error)
    
    
    # update values of session['user']
    def update_session():
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(f"SELECT Username, Password, FirstName, LastName, RoleID, RoleName, Email FROM user LEFT JOIN role USING (RoleID) WHERE Username = '{session['user']['Username']}'")
        user = {a: b for a, b in zip(["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName", "Email"], db.fetchone())}
        cxn.close()

        session.clear()
        session['user'] = user
        return
    
    
    # decorator for pages that require authentication
    def login_required (view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user' not in session.keys():
                return redirect(url_for('login'))

            return view(**kwargs)

        return wrapped_view
    

    # route for logging out
    @app.route('/logout')
    def logout ():
        session.clear()
        return redirect(url_for('login'))
    

    # route for inventory (main page)
    @app.route('/')
    @login_required
    def index ():
        return redirect(url_for('inventory')), 303
    



    ### INVENTORY - includes inventory display, item search, item addition, item removal & item update ###

    # route for inventory
    @app.route('/inventory')
    @login_required
    def inventory ():
        update_session()
        return render_template("inventory/inventory.html", active = "inventory")
    
    
    # route for item search
    @app.route('/inventory/search')
    @login_required
    def search_items ():
        keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]

        conditions = []
        for x in keywords:
            conditions.append(f"(ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%')")

        query = f"SELECT * from stock {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY ItemID"

        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        items = db.fetchall()
        cxn.close()

        return { "items": format_items(items) }
    
    
    # route for item addition
    @app.route('/inventory/add', methods = ["GET", "POST"])
    @login_required
    def add_items ():
        update_session()

        if request.method == 'GET':
            if session['user']['RoleID'] != 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
            else:
                return render_template("inventory/add.html")

        if request.method == 'POST':
            if session['user']['RoleID'] != 1:
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
            
            values = request.get_json()

            cxn = connect_db()
            db = cxn.cursor()
            try:
                for v in values['values']:
                    db.execute(f"INSERT INTO item VALUES ('{v['ItemID']}', '{escape(v['ItemName'])}', '{escape(v['ItemDescription'])}', {'NULL' if v['ShelfLife'] is None else v['ShelfLife']}, {v['Price']}, '{v['Unit']}')")
                cxn.commit()
            except Exception as e:
                # original error message as fallback
                msg = e.args[1]
                # MYSQL Error 1062: duplicate value for primary key
                if e.args[0] == 1062: 
                    msg = f'Item ID {v["ItemID"]} has already been taken.'
                return msg, 500
            finally:
                cxn.close()
            
            return Response(status = 200)
        
    
    # route for item removal
    @app.route('/inventory/remove', methods = ["GET", "POST"])
    @login_required
    def remove_items ():
        update_session()

        if request.method == "GET":
            if session['user']['RoleID'] != 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403
            else: 
                return render_template("inventory/remove.html")

        if request.method == "POST":
            if (session['user'])['RoleID'] != 1:
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403

            items = request.get_json()["items"]

            try:
                cxn = connect_db()
                db = cxn.cursor()
                for x in items:
                    db.execute(f"DELETE FROM item WHERE ItemID = {x}")
                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()

            return Response(status = 200)
        
    
    # route for item update
    @app.route('/inventory/update', methods = ["GET", "POST"])
    @login_required
    def update_items ():
        update_session()
        
        if request.method == "GET":
            if session['user']['RoleID'] != 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update items in the database."), 403
            else: 
                return render_template("inventory/update.html")

        if request.method == "POST":
            if session['user']['RoleID'] != 1:
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update items in the database."), 403
            
            values = request.get_json()["values"]

            try:
                cxn = connect_db()
                db = cxn.cursor()

                for v in values:
                    db.execute(f"UPDATE item SET ItemID = '{values[v]['ItemID']}', ItemName = '{escape(values[v]['ItemName'])}', ItemDescription = '{escape(values[v]['ItemDescription'])}', ShelfLife = {'NULL' if values[v]['ShelfLife'] is None else values[v]['ShelfLife']}, Price = {values[v]['Price']}, Unit = '{values[v]['Unit']}' WHERE ItemID = '{values[v]['ItemID']}'")

                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()

            return Response(status = 200)
        
    


    ### REQUESTS - includes request display, request search & item request ###

    # route for requests
    @app.route('/requests')
    @login_required
    def requests ():
        return render_template("requests/requests.html", active = "requests")
    
    
    # route for request search
    @app.route('/requests/search')
    @login_required
    def search_requests ():
        keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
        custodian = session['user']['RoleID'] == 1

        conditions = []
        for x in keywords:
            a = f" OR RequestedBy LIKE '%{x}%'"
            conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%'{a if custodian else ''}")

        cxn = connect_db()
        db = cxn.cursor()

        u = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""
        v = f"RequestedBy LIKE '%{session['user']['Username']}%'" if not custodian else ""
        w = ' AND '.join(filter(None, [u, v]))

        db.execute(f"SELECT RequestID, ItemID, ItemName, ItemDescription, RequestedBy, RequestQuantity, Unit, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status FROM request INNER JOIN item USING (ItemID) INNER JOIN request_status ON (Status = StatusID){'WHERE ' + w if w != '' else ''} ORDER BY RequestID")
        requests = db.fetchall()
        cxn.close()

        return { "requests": format_requests(requests, custodian) }
    
    
    # route for item request
    @app.route('/requests/request', methods = ["GET", "POST"])
    @login_required
    def make_requests ():
        update_session()

        if (request.method == "GET"):
            if session['user']['RoleID'] == 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to request items from the database."), 403
            else: 
                return render_template("requests/request.html")

        if (request.method == "POST"):
            if session['user']['RoleID'] == 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to request items from the database."), 403
            
            req = request.get_json()["items"]
            print(req)

            try:
                cxn = connect_db()
                db = cxn.cursor()

                for x in req:
                    db.execute(f"INSERT INTO request (ItemID, RequestQuantity, RequestedBy) VALUES ({x['ItemID']}, {x['RequestQuantity']}, '{session['user']['Username']}')")
                cxn.commit()
            except Exception as e:
                return { "error": e.args[1] }, 500
            finally:
                cxn.close()

            return Response(status = 200)
    



    ### USERS - all about managing users ###

    # route for users
    @app.route('/users')
    @login_required
    def show_users():
        if session['user']['RoleID'] != 0: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to see the users in the database."), 403
        else: 
            return render_template("user/user.html", active="users")
        
    
    # TODO: Change this to other email address
    sender_address = 'iamjhin01@gmail.com'
    sender_pass = 'qenmyutlantkdgap'
    
    # create SMTP session for sending the mail
    # TODO: Find other SMTP server
    def start_email_session():
        session = smtplib.SMTP('smtp.gmail.com', 587) #use gmail with port
        session.starttls() #enable security
        session.login(sender_address, sender_pass) #login with mail_id and password
        return session
    

    # send email based on request type
    # TODO: Fix email content (too bland)
    def send_email(session, type, recipient, username="", password=""):
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
    def generate_userID(first, last):
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
    
    
    # route for adding users
    # password for new users is 'ilovesims'
    @app.route('/users/add', methods = ["GET", "POST"])
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
                for v in values:
                    userID = generate_userID(v[0], v[1])
                    
                    if v[2] == '':
                        db.execute(f"INSERT INTO user(Username, Password, FirstName, LastName, RoleID) VALUES ({userID}, {default}, {v[0]}, {v[1]}, {v[3]});")
                    else:
                        db.execute(f"INSERT INTO user VALUES ({userID}, {default}, {v[0]}, {v[1]}, {v[2]}, {v[3]});")
                        send_email(mail_session, "add", v[2], userID, 'ilovesims')

                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()
                mail_session.quit()
            
            return Response(status = 200)
        
    
    # route for removing users
    @app.route('/users/remove', methods = ["GET", "POST"])
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
    @app.route('/users/promote', methods = ["POST"])
    @login_required
    def promote_user():
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
    @app.route('/users/demote', methods = ["POST"])
    @login_required
    def demote_user():
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
    @app.route('/users/search')
    @login_required
    def search_users ():
        if session['user']['RoleID'] != 0: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to search for users in the database."), 403
        
        keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]

        conditions = []
        for x in keywords:
            conditions.append(f"(Username LIKE '%{x}%' OR FirstName LIKE '%{x}%' OR LastName LIKE '%{x}%')")

        query = f"SELECT Username, LastName, FirstName, Email, RoleName FROM user LEFT JOIN role USING (RoleID) {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY Username;"

        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        users = db.fetchall()
        cxn.close()

        return { "users": users }
    
    
    # route for updating user settings
    @app.route('/settings')
    def change_account_settings ():
        update_session()
        return render_template("user/settings.html", active = 'settings')
    

    # route for updating password
    @app.route('/settings/changepassword', methods = ["POST"])
    @login_required
    def change_password():
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

        return redirect(url_for('logout'))
    
            
    # route for changing email address
    @app.route('/settings/emailchange', methods = ["POST"])
    @login_required
    def change_email():
        req = request.form['new-email']

        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"UPDATE user SET Email = '{req}' WHERE Username = '{session['user']['Username']}';")
            cxn.commit()

            mail_session = start_email_session()
            send_email(mail_session, "email", req)
            mail_session.quit()

        except Exception as e:
            # TODO: Fix this
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()

        return redirect(url_for('inventory'))
    



    ### DELIVERIES - includes delivery list, delivery search & delivery addition ###
    
    @app.route('/deliveries')
    @login_required
    def deliveries ():
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to view deliveries."), 403
        else:
            return render_template("deliveries/deliveries.html", active = "deliveries")
        
    
    @app.route('/deliveries/search')
    @login_required
    def search_deliveries ():
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to search for deliveries."), 403

        keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]

        conditions = []
        for x in keywords:
            conditions.append(f"(ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%')")

        query = f"SELECT DeliveryID, ItemID, ItemName, ItemDescription, DeliveryQuantity, Unit, ShelfLife, DATE_FORMAT(delivery.DeliveryDate, '%d %b %Y') as DeliveryDate, ReceivedBy, IsExpired FROM delivery INNER JOIN item USING (ItemID) INNER JOIN expiration USING (DeliveryID) {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'} ORDER BY DeliveryID"

        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        deliveries = db.fetchall()
        cxn.close()

        return { "deliveries": format_deliveries(deliveries) }

    
    @app.route('/deliveries/add', methods = ["GET", "POST"])
    @login_required
    def add_deliveries ():
        update_session()

        if request.method == 'GET':
            if session['user']['RoleID'] != 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add deliveries to the database."), 403
            else:
                return render_template("deliveries/add.html")

        if request.method == 'POST':
            if session['user']['RoleID'] != 1: 
                return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add deliveries to the database."), 403
            
            values = request.get_json()

            cxn = connect_db()
            db = cxn.cursor()
            try:
                for v in values['values']:
                    db.execute(f"INSERT INTO delivery (ItemID, DeliveryQuantity, DeliveryDate, ReceivedBy) VALUES ('{v['ItemID']}', {v['DeliveryQuantity']}, '{v['DeliveryDate']}', '{session['user']['Username']}')")
                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()
            
            return Response(status = 200)
        



    ### FORMS - includes form list & form generation ###
    
    @app.route('/forms')
    @login_required
    def forms ():
        return render_template("forms.html", active = "forms")
    
    
    @app.route('/generate')
    @login_required
    def generate ():
        try:
            return formgen("58", request.args.get("item"))
        except:
            return ""
        


    ### ERROR HANDLERS ###

    # 404 - page not found
    @app.errorhandler(404)
    def error_404 (e):
        return render_template("error.html", errcode = 404, errmsg = "Page not found. Please check if the URL you have typed is correct."), 404
    

    # 500 - server error
    @app.errorhandler(500)
    def error_500 (e):
        return render_template("error.html", errcode = 500, errmsg = "Internal server error. Please try again later."), 500

    return app