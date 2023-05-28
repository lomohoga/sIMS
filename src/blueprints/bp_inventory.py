from flask import Blueprint, Response, render_template, request, session

from src.blueprints.format_data import format_items
from src.blueprints.auth import login_required
from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword, escape

bp_inventory = Blueprint('bp_inventory', __name__, url_prefix = "/inventory")

# route for inventory
@bp_inventory.route('/')
@login_required
def inventory ():
    return render_template("inventory/inventory.html", active = "inventory")

# route for item search
@bp_inventory.route('/search')
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
@bp_inventory.route('/add', methods = ["GET", "POST"])
@login_required
def add_items ():
    if request.method == 'GET':
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add items to the database."), 403
        else:
            return render_template("inventory/add.html")

    if request.method == 'POST':        
        values = request.get_json()

        try:
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
                return {"error": e.args[0], "msg": msg}, 500
            finally:
                cxn.close()
        except Exception as e:
            return {"error": e.args[0]}, 500
        
        return Response(status = 200)

# route for item removal
@bp_inventory.route('/remove', methods = ["GET", "POST"])
@login_required
def remove_items ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove items from the database."), 403
        else: 
            return render_template("inventory/remove.html")

    if request.method == "POST":
        items = request.get_json()["items"]

        try:
            cxn = connect_db()
            db = cxn.cursor()

            try:
                for x in items:
                    db.execute(f"DELETE FROM item WHERE ItemID = '{x}'")
                cxn.commit()
            except Exception as e:
                return { "error": e.args[0] }, 500
            finally:
                cxn.close()
        except Exception as e:
            return { "error": e.args[0] }, 500

        return Response(status = 200)

# route for item update
@bp_inventory.route('/update', methods = ["GET", "POST"])
@login_required
def update_items ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update items in the database."), 403
        else: 
            return render_template("inventory/update.html")

    if request.method == "POST":
        values = request.get_json()["values"]

        try:
            cxn = connect_db()
            db = cxn.cursor()

            try:
                for v in values:
                    db.execute(f"UPDATE item SET ItemID = '{values[v]['ItemID']}', ItemName = '{escape(values[v]['ItemName'])}', ItemDescription = '{escape(values[v]['ItemDescription'])}', ShelfLife = {'NULL' if values[v]['ShelfLife'] is None else values[v]['ShelfLife']}, Price = {values[v]['Price']}, Unit = '{values[v]['Unit']}' WHERE ItemID = '{v}'")

                cxn.commit()
            except Exception as e:
                # original error message as fallback
                msg = e.args[1]
                # MYSQL Error 1062: duplicate value for primary key
                if e.args[0] == 1062: 
                    msg = f'Item ID {values[v]["ItemID"]} has already been taken.'
                return {"error": e.args[0], "msg": msg}, 500
            finally:
                cxn.close()
        except Exception as e:
            return {"error": e.args[0]}, 500
        
        return Response(status = 200)

# route for item request
@bp_inventory.route('/request', methods = ["GET", "POST"])
@login_required
def request_items ():
    if (request.method == "GET"):
        return render_template("inventory/request.html")

    if (request.method == "POST"):
        if session['user']['RoleID'] == 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to request items from the database."), 403
        
        req = request.get_json()["items"]

        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"INSERT INTO request (RequestedBy) VALUES ('{session['user']['Username']}')")
            db.execute("SELECT LAST_INSERT_ID()")
            requestID = int(db.fetchone()[0])

            for x in req:
                db.execute(f"INSERT INTO request_item (RequestID, ItemID, RequestQuantity) VALUES ({requestID}, '{x['ItemID']}', {x['RequestQuantity']})")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()

        return Response(status = 200)
