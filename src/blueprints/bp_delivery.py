from flask import Blueprint, Response, render_template, request, session

from src.blueprints.auth import login_required
from src.blueprints.database import connect_db
from src.blueprints.format_data import format_deliveries
from src.blueprints.decode_keyword import decode_keyword

bp_delivery = Blueprint("bp_delivery", __name__, url_prefix = "/deliveries")

@bp_delivery.route('/')
@login_required
def deliveries ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to view deliveries."), 403
    else:
        return render_template("deliveries/deliveries.html", active = "deliveries")

@bp_delivery.route('/search')
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

@bp_delivery.route('/add', methods = ["GET", "POST"])
@login_required
def add_deliveries ():
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
