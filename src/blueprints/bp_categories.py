from flask import Blueprint, Response, render_template, request, session, current_app

from src.blueprints.format_data import format_categories
from src.blueprints.auth import login_required
from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword, escape
from src.blueprints.exceptions import CategoryNotFoundError, ExistingCategoryError, OngoingRequestItemError, SelfNotFoundError, SelfRoleError

bp_categories = Blueprint('bp_categories', __name__, url_prefix = "/categories")

# route for inventory
@bp_categories.route('/')
@login_required
def categories ():
    return render_template("categories/categories.html", active = "inventory")

# route for item search
@bp_categories.route('/search')
@login_required
def search_categories ():
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
    conditions = []
    for x in keywords:
        conditions.append(f"(CategoryName LIKE '%{x}%' OR CategoryDescription LIKE '%{x}%')")
    query = f"SELECT * from categories {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'};"

    cxn = None

    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(query)
        categories = db.fetchall()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return { "categories": format_categories(categories) }

# route for item addition
@bp_categories.route('/add', methods = ["GET", "POST"])
@login_required
def add_categories ():
    if request.method == 'GET':
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
        else:
            return render_template("categories/add.html")

    if request.method == 'POST':        
        cxn = None
        values = request.get_json()
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise SelfNotFoundError(username = session['user']['Username'])
            if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

            for v in values['values']:
                db.execute(f"SELECT * FROM categories WHERE CategoryName = '{v['CategoryName']}'")
                if db.fetchone() is not None: raise ExistingCategoryError(category = v['CategoryName'])

                db.execute(f"INSERT INTO categories VALUES ('{escape(v['CategoryName'])}', '{escape(v['CategoryDescription'])}')")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()
        
        return Response(status = 200)

# route for item removal
@bp_categories.route('/remove', methods = ["GET", "POST"])
@login_required
def remove_categories ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403
        else: 
            return render_template("categories/remove.html")

    if request.method == "POST":
        categories = request.get_json()["categories"]
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise SelfNotFoundError(username = session['user']['Username'])
            if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

            for x in categories:
                db.execute(f"SELECT * FROM categories WHERE CategoryName = '{x}'")
                if db.fetchone() is None: raise CategoryNotFoundError(category = x)

                db.execute(f"DELETE FROM categories WHERE CategoryName = '{x}'")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()

        return Response(status = 200)

# route for item update
@bp_categories.route('/update', methods = ["GET", "POST"])
@login_required
def update_categories ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update items in the database."), 403
        else: 
            return render_template("categories/update.html")

    if request.method == "POST":
        values = request.get_json()["values"]
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise SelfNotFoundError(username = session['user']['Username'])
            if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

            for v in values:
                db.execute(f"SELECT * FROM categories WHERE CategoryName = '{v}'")
                if db.fetchone() is None: raise CategoryNotFoundError(category = v)

                db.execute(f"SELECT * FROM categories WHERE CategoryName = '{values[v]['CategoryName']}'")
                if db.fetchone() is not None and v != values[v]['CategoryName']: raise ExistingCategoryError(category= values[v]['CategoryName'])

                db.execute(f"UPDATE categories SET CategoryName = '{escape(values[v]['CategoryName'])}', CategoryDescription = '{escape(values[v]['CategoryDescription'])}' WHERE CategoryName = '{v}'")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()
        
        return Response(status = 200)