import os
import hashlib
import functools
import math
import locale

from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_mysqldb import MySQL

locale.setlocale(locale.LC_ALL, 'en_PH')

#session['user'] = (role_id, username, password, firstName, lastName, role_name) of the CURRENT user
#role_id: 1(Custodian), 2(Personnel)

def format_values (values):
    formatted = [];

    for item in values:
        formatted.append((item[0], item[1], item[2], locale.format("%d", item[3], grouping=True) if item[3] > 0 else "\u2014", item[4], locale.currency(item[5], grouping=True), locale.format("%d", item[6], grouping=True)))

    return formatted;

def create_app(test_config=None):
    #create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev'
    )

    #ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    #configure the database
    app.config['MYSQL_HOST'] = 'localhost'
    app.config['MYSQL_USER'] = 'root'
    app.config['MYSQL_PASSWORD'] = 'password'
    app.config['MYSQL_DB'] = 'sims'

    mysql = MySQL(app)

    #convert password to hash using sha256
    def generateHash(a):
        m = hashlib.sha256()
        m.update(a.encode('utf-8'))
        return m.hexdigest()

    #route for login page
    @app.route('/login', methods=('GET', 'POST'))
    def login():
        error = ""

        if request.method == 'POST':
            username = request.form['uname']
            password = request.form['pword']

            db = mysql.connection.cursor()
            db.execute("SELECT * FROM user LEFT JOIN roles USING (role_id) WHERE username = %s;", [username])
            user = db.fetchone()
            db.close()

            if user is None:
                error = 'Incorrect username.'
            elif (username != "" and password != "" and generateHash(password) != user[2]):
                error = 'Incorrect password.'

            if error == "":
                session.clear()
                session['user'] = user
                return redirect(url_for('inventory'))

        return render_template("login.html", msg=error)
    
    #decorator for pages that requires authentication
    def login_required(view):
        @functools.wraps(view)
        def wrapped_view(**kwargs):
            if 'user' not in session.keys():
                return redirect(url_for('login'))

            return view(**kwargs)

        return wrapped_view

    #route for inventory
    #inventory is our MAIN page
    @app.route('/')
    @login_required
    def inventory():
        #get items in db
        db = mysql.connection.cursor()
        db.execute("SELECT * FROM item;")
        items = db.fetchall()
        db.close()

        return render_template("inventory.html", items=format_values(items), active="inventory")

    #route for adding an item
    @app.route('/add-item', methods=('GET', 'POST'))
    @login_required
    def add_item():
        if request.method == 'GET':
            if (session['user'])[0] == 2:
                return jsonify({ "redirect": url_for("inventory") })

        if request.method == 'POST':
            values = request.get_json()

            db = mysql.connection.cursor()
            db.execute("SELECT code FROM item")
            codes = [x[0] for x in db.fetchall()]

            try:
                for v in values["values"]:
                    if v[0] in codes: return jsonify({ "redirect": url_for("add_item") })
                    db.execute("INSERT INTO item VALUES (%s, %s, %s, %s, %s, %s, %s);", v)
            except Exception as e:
                return jsonify({ "redirect": url_for("add_item") })
            finally:
                mysql.connection.commit()
                db.close()

            return jsonify({ "redirect": url_for("inventory") })

            # name = request.form['name']
            # code = request.form['code']
            # desc = request.form['desc']
            # life = float(request.form['life'])
            # quantifier = float(request.form['quantifier'])

            # if quantifier == -1:
            #     life = -1
            # else:
            #     life = math.ceil(life * quantifier)
            
            # unit = request.form['unit']
            # price = request.form['price']
            # available = request.form['available']

            # try:
            #     db = mysql.connection.cursor()
            #     result = db.execute("INSERT INTO item VALUES (%s, %s, %s, %s, %s, %s, %s);", (code, name, desc, life, unit, price, available))
            #     mysql.connection.commit()
            #     return redirect(url_for('inventory'))
            # except Exception as e:
            #     return render_template("error_1.html", msg="Item code already exists.")
            # finally:
            #     db.close()  

        return render_template("add_item.html")

    #route for showing the delete form (which item to delete)
    @app.route('/delete-form')
    @login_required
    def delete_form():
        if (session['user'])[0] == 2:
            return render_template('error_1.html', msg="This page is for Custodians only.")
        else:
            db = mysql.connection.cursor()
            db.execute("SELECT * FROM item;")
            items = db.fetchall()
            db.close()
            return render_template("delete_form.html", items=format_values(items))
        
    #route for actually deleting the item
    @app.route('/delete-item', methods=('POST',))
    @login_required
    def delete_item():
        if (session['user'])[0] == 2:
            return jsonify({ "redirect": url_for("inventory") })
        else:
            items = request.get_json()["items"]
            choices = [(x,) for x in items]

            try:
                db = mysql.connection.cursor()
                db.executemany("DELETE FROM item WHERE code=%s;", choices)
                mysql.connection.commit()
            except Exception as e:
                return jsonify({ "redirect": url_for("delete_form") })
            finally:
                db.close()

        return jsonify({ "redirect": url_for("inventory") })

    #route for request form (which item to request)
    @app.route('/request-form')
    @login_required
    def request_form():
        if (session['user'])[0] == 1:
            return render_template('error_1.html', msg="This page is for Personnel only.")

        db = mysql.connection.cursor()
        db.execute("SELECT * FROM item WHERE available > 0;")
        items = db.fetchall()
        db.close()

        if(len(items) == 0):
            return render_template("error_1.html", msg="No available items")
        else:
            return render_template("req_form.html", items=format_values(items), active="inventory")

    #route for issuing request
    @app.route('/request-item', methods=('POST',))
    @login_required
    def request_item():
        if (session['user'])[0] == 1:
            return jsonify({ "redirect": url_for('inventory') })

        req = request.get_json()["items"]

        try:
            username = session['user'][1]
            db = mysql.connection.cursor()

            for x in req:
                db.execute("UPDATE item SET available=%s WHERE code=%s;", [x[1], x[0]])
                db.execute("INSERT INTO transaction (code, req, username, date) VALUES (%s, %s, %s, CURDATE());", [x[0], x[1], username]);
            
            mysql.connection.commit()
            db.close()
        except Exception as e:
            print(e)
            return jsonify({ "redirect": url_for('request_form') })
        finally:
            db.close()

        return jsonify({ "redirect": url_for('inventory') })

        # try:
        #     db = mysql.connection.cursor()
        #     db.execute("SELECT available FROM item WHERE code=%s;", [choice])
        #     stock = int((db.fetchone())[0])
        #     if(req <= stock):
        #         #update db
        #         new = stock - req
        #         db.execute("UPDATE item SET available=%s WHERE code=%s;", (new, choice))
        #         username = (session['user'])[1]
        #         db.execute("INSERT INTO transaction (code, req, username, date) VALUES (%s, %s, %s, CURDATE());", (choice, req, username))
        #         mysql.connection.commit()
        #         db.close()
        #         return redirect(url_for('transactions'))
        #     else:
        #         db.close()
        #         return render_template("error_1.html", msg="Requested quantity exceeds available stock.")
        # except Exception as e:
        #     return render_template("error_1.html", msg="Cannot request item.")
        # finally:
        #     db.close()

    #route for searching an item
    @app.route('/search')
    @login_required
    def search():
        keyword = request.args.get('keyword')
        keyword = keyword.lower().split()

        print(f"keyword [{keyword}]")

        cond = ""
        if len(keyword) > 0:
            for a in keyword:
                cond = cond + "("
                cond = cond + "(LOWER(code) LIKE '%" + a + "%') OR "
                cond = cond + "(LOWER(name) LIKE '%" + a + "%') OR "
                cond = cond + "(LOWER(description) LIKE '%" + a + "%') OR "
                cond = cond[:-4]
                cond = cond + ") "
                cond = cond + "AND "
            cond = cond[:-5]
            
        db = mysql.connection.cursor()
        query = "SELECT * FROM item WHERE " + cond + ";" if cond != '' else "SELECT * FROM item"
        db.execute(query)
        items = db.fetchall()
        db.close()

        return jsonify(format_values(items))
    
    #route for transactions
    @app.route('/transactions')
    @login_required
    def transactions():
        #get transactions in db
        db = mysql.connection.cursor()

        if((session['user'])[0] == 1):
            db.execute("SELECT * FROM transaction;")
        else:
            username = (session['user'])[1]
            db.execute("SELECT transaction_id, code, req, date FROM transaction WHERE username=%s;", [username])
        
        tran = db.fetchall()
        db.close()

        return render_template("transactions.html", tran=tran, active="transactions")
    
    #route for logging out
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    # # 400 - bad request
    # @app.errorhandler(400)
    # def error_400 (e):
    #     print(e.get_response().data)
    #     return render_template("error_1.html", errcode = 400, errmsg="Bad request.")

    # # 403 - forbidden
    # @app.errorhandler(403)
    # def error_403 (e):
    #     return render_template("error_1.html", errcode = 403, errmsg="Forbidden.")

    # # 404 - page not found
    # @app.errorhandler(404)
    # def error_404 (e):
    #     return render_template("error_1.html", errcode = 404, errmsg="Not found.")

    return app