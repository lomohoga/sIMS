import os
import hashlib
import functools
import math

from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL

#session['user'] = (role_id, username, password, firstName, lastName, role_name) of the CURRENT user
#role_id: 1(Custodian), 2(Personnel)


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
            elif (generateHash(password) != user[2]):
                error = 'Incorrect password.'

            if len(error) == 0:
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

        return render_template("inventory.html", items=items)

    #route for adding an item
    @app.route('/add-item', methods=('GET', 'POST'))
    @login_required
    def add_item():
        if request.method == 'GET':
            if (session['user'])[0] == 2:
                return render_template('error_1.html', msg="This page is for custodian only.")

        if request.method == 'POST':
            name = request.form['name']
            code = request.form['code']
            desc = request.form['desc']
            life = float(request.form['life'])
            quantifier = float(request.form['quantifier'])

            if(quantifier == -1):
                life = -1
            else:
                life = math.ceil(life * quantifier)
            
            unit = request.form['unit']
            price = request.form['price']
            available = request.form['available']

            try:
                db = mysql.connection.cursor()
                result = db.execute("INSERT INTO item VALUES (%s, %s, %s, %s, %s, %s, %s);", (code, name, desc, life, unit, price, available))
                mysql.connection.commit()
                return redirect(url_for('inventory'))
            except Exception as e:
                return render_template("error_1.html", msg="Item code already exists.")
            finally:
                db.close()  

        return render_template("add_item.html")

    #route for showing the delete form (which item to delete)
    @app.route('/delete-form')
    @login_required
    def delete_form():
        if (session['user'])[0] == 2:
            return render_template('error_1.html', msg="This page is for custodian only.")
        else:
            db = mysql.connection.cursor()
            db.execute("SELECT * FROM item;")
            items = db.fetchall()
            db.close()
            return render_template("delete_form.html", items=items)
        
    #route for actually deleting the item
    @app.route('/delete-item')
    @login_required
    def delete_item():
        if (session['user'])[0] == 2:
            return render_template('error_1.html', msg="This page is for custodian only.")
        else:
            choice = request.args.get('choice')

            if(choice == None):
                return render_template("error_1.html", msg="No selected item.")

            try:
                db = mysql.connection.cursor()
                db.execute("DELETE FROM item WHERE code=%s;", [choice])
                mysql.connection.commit()
                db.close()
                return redirect(url_for('inventory'))
            except Exception as e:
                return render_template("error_1.html", msg="Cannot delete item.")
            finally:
                db.close()

    #route for request form (which item to request)
    @app.route('/request-form')
    @login_required
    def request_form():
        if (session['user'])[0] == 1:
            return render_template('error_1.html', msg="This page is for personnels only.")

        db = mysql.connection.cursor()
        db.execute("SELECT * FROM item WHERE available > 0;")
        items = db.fetchall()
        db.close()

        if(len(items) == 0):
            return render_template("error_1.html", msg="No available items")
        else:
            return render_template("req_form.html", items=items)

    #route for issuing request
    @app.route('/request-item')
    @login_required
    def request_item():
        if (session['user'])[0] == 1:
            return render_template('error_1.html', msg="This page is for personnels only.")

        choice = request.args.get('choice')
        req = int(request.args['req'])

        if(choice == None):
            return render_template("error_1.html", msg="No item selected.")

        if(req == 0):
            return render_template("error_1.html", msg="Requested quantity can't be 0.")

        try:
            db = mysql.connection.cursor()
            db.execute("SELECT available FROM item WHERE code=%s;", [choice])
            stock = int((db.fetchone())[0])
            if(req <= stock):
                #update db
                new = stock - req
                db.execute("UPDATE item SET available=%s WHERE code=%s;", (new, choice))
                username = (session['user'])[1]
                db.execute("INSERT INTO transaction (code, req, username, date) VALUES (%s, %s, %s, CURDATE());", (choice, req, username))
                mysql.connection.commit()
                db.close()
                return redirect(url_for('transactions'))
            else:
                db.close()
                return render_template("error_1.html", msg="Requested quantity exceeds available.")
        except Exception as e:
            return render_template("error_1.html", msg="Cannot request item.")
        finally:
            db.close()

    #route for searching an item
    @app.route('/search')
    @login_required
    def search():
        keyword = request.args.get('keyword')
        keyword = keyword.lower().split()
        if(len(keyword) == 0):
            return render_template("error_1.html", msg="No keyword indicated")

        cond = ""
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
        query = "SELECT * FROM item WHERE " + cond + ";"
        db.execute(query)
        items = db.fetchall()
        db.close()
        return render_template("inventory.html", items=items)
    
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
            db.execute("SELECT * FROM transaction WHERE username=%s;", [username])
        
        tran = db.fetchall()
        db.close()

        return render_template("transactions.html", tran=tran)
    
    #route for logging out
    @app.route('/logout')
    def logout():
        session.clear()
        return redirect(url_for('login'))

    return app