import locale

from flask import Blueprint, Response, render_template, request, session

from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.format_data import format_requests
from src.blueprints.auth import login_required

locale.setlocale(locale.LC_ALL, 'en_PH.utf8')
bp_request = Blueprint("bp_request", __name__, url_prefix = "/requests")

# route for requests
@bp_request.route('/', methods=["GET"])
@login_required
def requests ():
    return render_template("requests/requests.html", active = "requests")

# route for request search
@bp_request.route('/search', methods = ["GET"])
@login_required
def search_requests ():
    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
    filter = [] if "filter" not in request.args else request.args.get("filter").split(",")
    custodian = session['user']['RoleID'] == 1

    conditions = []
    for x in keywords:
        conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%' OR RequestedBy LIKE '%{x}%'")
    if len(filter) > 0: conditions.append(f'LOWER(StatusName) in {str(filter).replace("[", "(").replace("]", ")")}')

    w = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""

    cxn = connect_db()
    db = cxn.cursor()

    db.execute(f"SELECT RequestID, RequestedBy, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status, ItemID, ItemName, ItemDescription, RequestQuantity, QuantityIssued, AvailableStock, Unit FROM request INNER JOIN request_status USING (StatusID) INNER JOIN request_item USING (RequestID) INNER JOIN stock USING (ItemID){' WHERE RequestID IN (SELECT DISTINCT RequestID FROM request INNER JOIN request_item USING (RequestID) INNER JOIN item USING (ItemID) WHERE ' + w + ')' if w != '' else ''} ORDER BY RequestID, ItemID")
    requests = db.fetchall()
    cxn.close()

    return { "requests": format_requests(requests, session['user']['RoleID'] == 1) }

# route for request approval
@bp_request.route('/approve', methods = ["POST"])
def approve_request ():
    if (request.method == "POST"):
        id = request.get_json()['RequestID']

        try:
            cxn = connect_db()
            db = cxn.cursor()
            db.execute(f"UPDATE request SET StatusID = 2, ActingAdmin = '{session['user']['Username']}' WHERE RequestID = {id}")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()
    
    return Response(status = 200)

# route for request denial
@bp_request.route('/deny', methods = ["POST"])
def deny_request ():
    if (request.method == "POST"):
        id = request.get_json()['RequestID']

        try:
            cxn = connect_db()
            db = cxn.cursor()
            db.execute(f"UPDATE request SET StatusID = 5, ActingAdmin = '{session['user']['Username']}' WHERE RequestID = {id}")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()
    
    return Response(status = 200)

# route for request cancellation
@bp_request.route('/cancel', methods = ["POST"])
@login_required
def cancel_request ():
    if (request.method == "POST"):
        body = request.get_json()

        try:
            cxn = connect_db()
            db = cxn.cursor()
            db.execute(f"UPDATE request SET StatusID = 6 WHERE RequestID = {body['RequestID']}")
            cxn.commit()
        except Exception as e:
            return { "error": e.args[1] }, 500
        finally:
            cxn.close()
    
    return Response(status = 200)

# route for request receipt
@bp_request.route('/receive', methods = ["POST"])
@login_required
def receive_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(f"UPDATE request SET StatusID = 4, ReceivedBy = '{session['user']['Username']}' WHERE RequestID = {id}")
        cxn.commit()
    except Exception as e:
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()

    return Response(status = 200)

# route for individual issue of request item
@bp_request.route('/issue/item', methods = ["POST"])
@login_required
def issue_item ():
    body = request.get_json()

    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(f"UPDATE request_item SET QuantityIssued = {body['QuantityIssued']} WHERE RequestID = {body['RequestID']} AND ItemID = '{body['ItemID']}';")
        cxn.commit()
    except Exception as e:
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()
    
    return Response(status = 200)

# route for request issue
@bp_request.route('/issue', methods = ["POST"])
@login_required
def issue_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(f"UPDATE request SET StatusID = 3, IssuedBy = '{session['user']['Username']}' WHERE RequestID = {id}")
        cxn.commit()
    except Exception as e:
        return { "error": e.args[1] }, 500
    finally:
        cxn.close()

    return Response(status = 200)