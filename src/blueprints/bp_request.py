from flask import Blueprint, Response, render_template, request, session

from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.auth import login_required

bp_request = Blueprint("bp_request", __name__, url_prefix = "/requests")

# route for requests
@bp_request.route('/')
@login_required
def requests ():
    return render_template("requests/requests.html", active = "requests")


# route for request search
@bp_request.route('/search')
@login_required
def search_requests ():
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
    requestStatus = request.args.get("requestStatus")
    custodian = session['user']['RoleID'] == 1

    cxn = connect_db()
    db = cxn.cursor()

    db.execute("SELECT RequestID, RequestedBy, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName AS RequestStatus FROM request LEFT JOIN request_status USING (StatusID)")
    reqs = db.fetchall()

    requests = []
    for req in reqs:
        db.execute(f"SELECT ItemName, ItemDescription, Quantity FROM request_items INNER JOIN item USING (ItemID) WHERE RequestID = {req[0]}")
        reqItems = db.fetchall()
        req = list(req)
        req.append(reqItems)
        requests.append(req)

    # conditions = []
    # for x in keywords:
    #     a = f" OR RequestedBy LIKE '%{x}%'"
    #     conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%'{a if custodian else ''}")

    # cxn = connect_db()
    # db = cxn.cursor()

    # u = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""
    # v = f"RequestedBy LIKE '%{session['user']['Username']}%'" if not custodian else ""
    # w = ' AND '.join(filter(None, [u, v]))

    # db.execute(f"SELECT RequestID, ItemID, ItemName, ItemDescription, RequestedBy, RequestQuantity, Unit, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status FROM request INNER JOIN item USING (ItemID) INNER JOIN request_status ON (Status = StatusID){'WHERE ' + w if w != '' else ''} ORDER BY RequestID")
    # requests = db.fetchall()
    # cxn.close()    

    return { "requests": requests }

# route for item request
@bp_request.route('/request', methods = ["GET", "POST"])
@login_required
def make_requests ():
    if (request.method == "GET"):
        if session['user']['RoleID'] == 1: 
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to request items from the database."), 403
        else: 
            return render_template("requests/request.html")

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
                db.execute(f"INSERT INTO request_items (RequestID, ItemID, Quantity) VALUES ({requestID}, '{x['ItemID']}', {x['RequestQuantity']})")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()

        return Response(status = 200)