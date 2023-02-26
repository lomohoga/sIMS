import os
import hashlib
import functools
import locale
import re

import mysql.connector
from flask import Flask, render_template, request, redirect, url_for, session, Response

locale.setlocale(locale.LC_ALL, 'en_PH')

# session['user'] = (role_id, username, password, firstName, lastName, role_name) of the CURRENT user
# role_id: 1(Custodian), 2(Personnel)

def format_values (values):
    formatted = [];

    for item in values:
        formatted.append((item[0], item[1], item[2], locale.format("%s", item[3], grouping = True) if item[3] > 0 else "\u2014", locale.currency(item[4], grouping = True), locale.format("%s", item[5], grouping = True), item[6]))

    return formatted;

def decode_keyword (k):
    return re.sub(r'%[0-9A-F]{2}', lambda x: chr(int(x.group(0)[1:3], base = 16)), k).replace("'", "\\'")

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

    # convert password to hash using sha256
    def generateHash (a):
        m = hashlib.sha256()
        m.update(a.encode('utf-8'))
        return m.hexdigest()

    # route for login page
    @app.route('/login', methods=('GET', 'POST'))
    def login ():
        error = ""

        if request.method == 'POST':
            username = request.form['uname']
            password = request.form['pword']

            cxn = connect_db()
            db = cxn.cursor()
            db.execute("SELECT * FROM user LEFT JOIN role USING (RoleID) WHERE Username = %s;", [username])
            user = db.fetchone()
            cxn.close()

            if user is None:
                error = 'User not found.'
            elif (username != "" and password != "" and generateHash(password) != user[2]):
                error = 'Incorrect password.'

            if error == "":
                session.clear()
                session['user'] = user
                return redirect(url_for('inventory'))

        return render_template("login.html", msg = error)
    
    # decorator for pages that require authentication
    def login_required (view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user' not in session.keys():
                return redirect(url_for('login'))

            return view(**kwargs)

        return wrapped_view

    # route for inventory (main page)
    @app.route('/')
    @login_required
    def inventory ():
        return render_template("inventory.html", active = "inventory")
    
    # route for requests
    @app.route('/requests')
    @login_required
    def requests ():
        return render_template("requests.html", active = "requests")

    # route for item addition
    @app.route('/add', methods = ["GET", "POST"])
    @login_required
    def add_items ():
        if request.method == 'GET':
            if (session['user'])[0] == 2: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
            else: return render_template("add.html")

        if request.method == 'POST':
            values = request.get_json()

            cxn = connect_db()
            db = cxn.cursor()
            try:
                for v in values["values"]:
                    db.execute("INSERT INTO item VALUES (%s, %s, %s, %s, %s, %s, %s);", [re.sub(r'[\u2018\u2019\u201c\u201d]', lambda x: "\'" if x.group(0) in ['\u201c', '\u201d'] else "\"", z) if type(z) == str else z for z in v])
                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()
            
            return Response(status = 200)
    
    def generate_userID(first, last):
        userID = first[0].lower() + last.lower()
        userID_length = len(userID)
        items = 1
        counter = 0

        cxn = connect_db()
        db = cxn.cursor()
        while(items):
            query = "SELECT * FROM user WHERE Username LIKE '" + userID + "';"
            db.execute(query)
            items = len(db.fetchall())

            if(items):
                counter = counter + 1;
                userID = userID[:userID_length] + str(counter);

        cxn.close()
        return userID
    
    # route for item addition
    @app.route('/add-users', methods = ["GET", "POST"])
    @login_required
    def add_users ():
        if request.method == 'GET':
            if (session['user'])[0] == 2: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
            else: return render_template("add_user.html")

        if request.method == 'POST':
            values = request.get_json()["values"]

            #TODO: Insert to user table
            cxn = connect_db()
            db = cxn.cursor()
            default = generateHash('ilovesims')
            try:
                for v in values:
                    userID = generate_userID(v[0], v[1])
                    db.execute("INSERT INTO user VALUES (%s, %s, %s, %s, %s);", [userID, default, v[0], v[1], v[2]])

                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()
            
            return Response(status = 200)

    # route for item removal
    @app.route('/remove', methods = ["GET", "POST"])
    @login_required
    def remove_items ():
        if request.method == "GET":
            if (session['user'])[0] == 2: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403
            else: return render_template("delete.html")

        if request.method == "POST":
            items = request.get_json()["items"]
            choices = [(x,) for x in items]

            try:
                cxn = connect_db()
                db = cxn.cursor()
                db.executemany("DELETE FROM item WHERE ItemCode = %s;", choices)
                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()

            return Response(status = 200)
    
    # route for item removal
    @app.route('/remove-users', methods = ["GET", "POST"])
    @login_required
    def remove_users ():
        if request.method == "GET":
            if (session['user'])[0] == 2: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403
            else: return render_template("delete_user.html")

        if request.method == "POST":
            users = request.get_json()["users"]
            choices = [(x,) for x in users]

            try:
                cxn = connect_db()
                db = cxn.cursor()
                db.executemany("DELETE FROM user WHERE Username = %s;", choices)
                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()

            return Response(status = 200)

    # route for item update
    @app.route('/update', methods = ["GET", "POST"])
    @login_required
    def update_items ():
        if request.method == "GET":
            if (session['user'])[0] == 2: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update items in the database."), 403
            else: return render_template("update.html")

        if request.method == "POST":
            values = request.get_json()["values"]

            try:
                cxn = connect_db()
                db = cxn.cursor()

                for v in values:
                    db.execute("UPDATE item SET ItemCode = %s, ItemName = %s, ItemDescription = %s, ShelfLife = %s, Price = %s, QuantityAvailable = %s, Unit = %s WHERE ItemCode = '" + v + "';", [re.sub(r'[\u2018\u2019\u201c\u201d]', lambda x: "\'" if x.group(0) in ['\u201c', '\u201d'] else "\"", z) if type(z) == str else z for z in values[v]])

                cxn.commit()
            except Exception as e:
                return Response(status = 500)
            finally:
                cxn.close()

            return Response(status = 200)

    # route for promoting user
    @app.route('/promote-user', methods = ["POST"])
    @login_required
    def promote_user():
        values = request.get_json()["values"]
        
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute("UPDATE user SET RoleID = 1 WHERE Username = '" + values + "';")

            cxn.commit()
        except Exception as e:
            return Response(status = 500)
        finally:
            cxn.close()
        
        return Response(status = 200)

    # route for demoting user
    @app.route('/demote-user', methods = ["POST"])
    @login_required
    def demote_user():
        values = request.get_json()["values"]
        
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute("UPDATE user SET RoleID = 2 WHERE Username = '" + values + "';")

            cxn.commit()
        except Exception as e:
            return Response(status = 500)
        finally:
            cxn.close()
        
        return Response(status = 200)

    # route for item request
    @app.route('/request', methods = ["GET", "POST"])
    @login_required
    def request_items ():
        if (request.method == "GET"):
            if (session['user'])[0] == 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to request items from the database."), 403
            else: return render_template("request.html")

        if (request.method == "POST"):
            req = request.get_json()["items"]

            try:
                cxn = connect_db()
                db = cxn.cursor()

                for x in req:
                    db.execute("INSERT INTO request (ItemCode, RequestQuantity, RequestedBy) VALUES (%s, %s, %s);", [x[0], x[1], session['user'][1]])
                cxn.commit()
            except Exception as e:
                return { "error": e.args[1] }, 500
            finally:
                cxn.close()

            return Response(status = 200)

    # route for item search
    @app.route('/search')
    @login_required
    def search_items ():
        keyword = [decode_keyword(x) for x in request.args.get('keyword').lower().split()]

        cond = ""
        for a in keyword:
            cond = cond + "((LOWER(ItemCode) LIKE '%" + a + "%') OR "
            cond = cond + "(LOWER(ItemName) LIKE '%" + a + "%') OR "
            cond = cond + "(LOWER(ItemDescription) LIKE '%" + a + "%')) AND "
        cond = cond[:-5]
        
        cxn = connect_db()
        db = cxn.cursor()
        query = "SELECT * FROM item" + (" WHERE " + cond if cond != "" else "") + ";"
        db.execute(query)
        items = db.fetchall()
        cxn.close()

        return { "items": format_values(items) }

    # route for user search
    @app.route('/search-users')
    @login_required
    def search_users ():
        keyword = [decode_keyword(x) for x in request.args.get('keyword').lower().split()]

        cond = ""
        for a in keyword:
            cond = cond + "((LOWER(Username) LIKE '%" + a + "%') OR "
            cond = cond + "(LOWER(FirstName) LIKE '%" + a + "%') OR "
            cond = cond + "(LOWER(LastName) LIKE '%" + a + "%')) AND "
        cond = cond[:-5]
        
        cxn = connect_db()
        db = cxn.cursor()
        query = "SELECT Username, LastName, FirstName, RoleName FROM user LEFT JOIN role USING (RoleID)" + (" WHERE " + cond if cond != "" else "") + ";"
        db.execute(query)
        users = db.fetchall()
        cxn.close()
        return { "users": users }

    # route for request search
    @app.route('/search-requests')
    @login_required
    def search_requests ():
        keyword = [decode_keyword(x) for x in request.args.get('keyword').lower().split()]

        cond = ""
        for a in keyword:
            cond += "((LOWER(ItemCode) LIKE '%" + a + "%') OR "
            cond += "(LOWER(Itemname) LIKE '%" + a + "%') OR "
            cond += "(LOWER(ItemDescription) LIKE '%" + a + "%')"
            if (session['user'][0] == 1): cond += " OR (LOWER(RequestedBy) LIKE '%" + a + "%')) "
            cond += ") AND "
        if (session['user'][0] == 1): cond = cond[:-5]
        else: cond += "RequestedBy = '" + session["user"][1] + "'"

        cxn = connect_db()
        db = cxn.cursor()
        query = "SELECT ID, ItemCode, ItemName, ItemDescription, RequestQuantity, Unit, RequestedBy, DATE_FORMAT(RequestDate, '%e %b %Y') FROM request LEFT JOIN item USING (ItemCode)" + (" WHERE " + cond if cond != "" else "") + ";"
        db.execute(query)
        requests = db.fetchall()
        cxn.close()

        return { "requests": requests }

    #route for users
    @app.route('/users')
    @login_required
    def show_users():
        return render_template("user.html")
    
    # route for logging out
    @app.route('/logout')
    def logout ():
        session.clear()
        return redirect(url_for('login'))

    # 404 - page not found
    @app.errorhandler(404)
    def error_404 (e):
        return render_template("error.html", errcode = 404, errmsg = "Page not found. Please check if the URL you have typed is correct."), 404

    # 500 - server error
    @app.errorhandler(500)
    def error_500 (e):
        return render_template("error.html", errcode = 500, errmsg = "Internal server error. Please try again later."), 500

    return app
