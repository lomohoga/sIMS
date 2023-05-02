import locale

from flask import Blueprint, Response, render_template, request, session

from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.auth import login_required

locale.setlocale(locale.LC_ALL, 'en_PH.utf8')
bp_request = Blueprint("bp_request", __name__, url_prefix = "/requests")

# route for requests
@bp_request.route('/')
@login_required
def requests ():
    return render_template("requests/requests.html", active = "requests")

# route for pending requests
@bp_request.route('/pendingRequests')
@login_required
def pendingRequests ():
    return render_template("requests/pendingRequests.html", active = "pendingRequests")

# route for request search
@bp_request.route('/search')
@login_required
def search_requests ():
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
    requestType = request.args.get("type")

    conditions = []
    for x in keywords:
        a = f" OR RequestedBy LIKE '%{x}%'"
        conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%'{a if requestType == 'user' else ''}")

    cxn = connect_db()
    db = cxn.cursor()

    u = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""
    v = f"RequestedBy LIKE '%{session['user']['Username']}%'" if requestType == 'user' else ""
    x = f"StatusName LIKE '%{requestType}%'" if requestType not in ['all', 'user'] else ""
    w = ' AND '.join(filter(None, [u, v, x]))

    print(w, request.args)

    db.execute(f"SELECT RequestID, RequestedBy, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status, ItemID, ItemName, ItemDescription, RequestQuantity, AvailableStock, Unit FROM request INNER JOIN request_status USING (StatusID) INNER JOIN request_item USING (RequestID) INNER JOIN stock USING (ItemID){' WHERE RequestID IN (SELECT DISTINCT RequestID FROM request INNER JOIN request_item USING (RequestID) INNER JOIN item USING (ItemID) WHERE ' + w + ')' if w != '' else ''} ORDER BY RequestID, ItemID")
    requests = db.fetchall()
    cxn.close()

    grouped = []
    for req in requests:
        d = next((g for g in grouped if g["RequestID"] == req[0]), None)
        if d == None:
            d = {
                "RequestID": req[0],
                "RequestedBy": req[1],
                "RequestDate": req[2],
                "Status": req[3],
                "Items": []
            } if requestType != 'user' else {
                "RequestID": req[0],
                "RequestDate": req[2],
                "Status": req[3],
                "Items": []
            }
            grouped.append(d)

        d["Items"].append({
            "ItemID": req[4],
            "ItemName": req[5],
            "ItemDescription": req[6],
            "RequestQuantity": locale.format("%s", req[7], grouping = True),
            "AvailableStock": locale.format("%s", req[8], grouping = True),
            "Unit": req[9]
        })

    return { "requests": grouped }

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
                db.execute(f"INSERT INTO request_item (RequestID, ItemID, RequestQuantity) VALUES ({requestID}, '{x['ItemID']}', {x['RequestQuantity']})")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()

        return Response(status = 200)

@bp_request.route('/pendingRequests/decide', methods = ["POST"])
@login_required
def decide_pendingRequest():
    if (request.method == "POST"):
        if (session['user']['RoleID'] != 0):
            return render_template("error.html", errcode = 403, errmsg = "You do not have permission to view this page."), 403
        else:
            body = request.get_json()

            try:
                cxn = connect_db()
                db = cxn.cursor()
                db.execute(f"UPDATE request SET StatusID = {'2' if body['decision'] else '5'} WHERE RequestID = {body['requestID']}")
                cxn.commit()
            except Exception as e:
                return { "error": e.args[1] }, 500
            finally:
                cxn.close()
        
        return Response(status = 200)