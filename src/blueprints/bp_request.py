import locale

from flask import Blueprint, Response, render_template, request, session, current_app
from mysql.connector import Error as MySQLError

from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.format_data import format_requests
from src.blueprints.auth import login_required
from src.blueprints.exceptions import NoRowsError, RequestStatusError, ItemIssuedError

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

    conditions = []
    for x in keywords:
        conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%' OR RequestedBy LIKE '%{x}%'")
    if len(filter) > 0: conditions.append(f'LOWER(StatusName) in {str(filter).replace("[", "(").replace("]", ")")}')

    w = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT RequestID, RequestedBy, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status, ItemID, ItemName, ItemDescription, RequestQuantity, QuantityIssued, AvailableStock, Unit FROM request INNER JOIN request_status USING (StatusID) INNER JOIN request_item USING (RequestID) INNER JOIN stock USING (ItemID){' WHERE RequestID IN (SELECT DISTINCT RequestID FROM request INNER JOIN request_item USING (RequestID) INNER JOIN item USING (ItemID) WHERE ' + w + ')' if w != '' else ''} ORDER BY RequestID, ItemID")
            requests = db.fetchall()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500

    return { "requests": format_requests(requests, session['user']['RoleID'] == 1) }

# route for request approval
@bp_request.route('/approve', methods = ["POST"])
def approve_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {id}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{id} not found.")
            if f[0] != 1: raise RequestStatusError("Cannot approve a request that is not pending.")
            
            db.execute(f"UPDATE request SET StatusID = 2, ActingAdmin = '{session['user']['Username']}' WHERE RequestID = {id}")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500
        
    return Response(status = 200)

# route for request denial
@bp_request.route('/deny', methods = ["POST"])
def deny_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {id}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{id} not found.")
            if f[0] != 1: raise RequestStatusError("Cannot deny a request that is not pending.")
            
            db.execute(f"UPDATE request SET StatusID = 5, ActingAdmin = '{session['user']['Username']}' WHERE RequestID = {id}")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500
    
    return Response(status = 200)

# route for request cancellation
@bp_request.route('/cancel', methods = ["POST"])
@login_required
def cancel_request ():
    body = request.get_json()

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {id}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{id} not found.")
            if f[0] == 4: raise RequestStatusError("Cannot cancel a request that is already completed.")
            if f[0] == 5: raise RequestStatusError("Cannot cancel a request that has been denied.")
            if f[0] == 6: raise RequestStatusError("Cannot cancel a request that is already cancelled.")
            
            db.execute(f"UPDATE request SET StatusID = 6 WHERE RequestID = {body['RequestID']}")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500
    
    return Response(status = 200)

# route for request receipt
@bp_request.route('/receive', methods = ["POST"])
@login_required
def receive_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()
        
        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {id}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{id} not found.")
            if f[0] == 5: raise RequestStatusError("Cannot receive a request that has been denied.")
            if f[0] == 6: raise RequestStatusError("Cannot receive a request that is already cancelled.")
            if f[0] != 4: raise RequestStatusError("Cannot receive a request that has not yet been issued.")
            
            db.execute(f"UPDATE request SET StatusID = 4, ReceivedBy = '{session['user']['Username']}', DateReceived = CURDATE() WHERE RequestID = {id}")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e.args[1])
        return {"error": e.args[0], "msg": e.args[1]}, 500

    return Response(status = 200)

# route for individual issue of request item
@bp_request.route('/issue/item', methods = ["POST"])
@login_required
def issue_item ():
    body = request.get_json()

    try:
        cxn = connect_db()
        db = cxn.cursor()
        
        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {body['RequestID']}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{body['RequestID']} not found.")
            if f[0] == 5: raise RequestStatusError("Cannot issue items in a request that has been denied.")
            if f[0] == 6: raise RequestStatusError("Cannot issue items in a request that is already cancelled.")
            if f[0] != 2: raise RequestStatusError("Cannot issue items in a request that has not yet been approved.")
            
            db.execute(f"SELECT QuantityIssued FROM request_item WHERE RequestID = {body['RequestID']} AND ItemID = {body['ItemID']}")
            g = db.fetchone()
            if g is None: raise NoRowsError(f"Item {body['ItemID']} not found in request #{body['RequestID']}.")
            if g[0] is not None: raise ItemIssuedError(f"Item {body['ItemID']} has already been issued.")
            
            db.execute(f"UPDATE request_item SET QuantityIssued = {body['QuantityIssued']} WHERE RequestID = {body['RequestID']} AND ItemID = '{body['ItemID']}';")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500
    
    return Response(status = 200)

# route for request issue
@bp_request.route('/issue', methods = ["POST"])
@login_required
def issue_request ():
    id = request.get_json()['RequestID']

    try:
        cxn = connect_db()
        db = cxn.cursor()

        try:
            db.execute(f"SELECT StatusID FROM request WHERE RequestID = {id}")
            f = db.fetchone()
            if f is None: raise NoRowsError(f"Request #{id} not found.")
            if f[0] == 5: raise RequestStatusError("Cannot issue a request that has been denied.")
            if f[0] == 6: raise RequestStatusError("Cannot issue a request that is already cancelled.")
            if f[0] != 2: raise RequestStatusError("Cannot issue a request that is not yet approved.")

            db.execute(f"SELECT QuantityIssued FROM request_item WHERE RequestID = {id}")
            g = all([x[0] is not None for x in db.fetchall()])
            if not g: raise RequestStatusError("Cannot issue a request with unissued items.")
            
            db.execute(f"UPDATE request SET StatusID = 3, IssuedBy = '{session['user']['Username']}', DateIssued = CURDATE() WHERE RequestID = {id}")
            cxn.commit()
        finally:
            cxn.close()
    except MySQLError as e:
        current_app.logger.error(e.args[1])
        if e.args[0] == 2003: return { "error": "Could not connect to database. Please try reloading the page. "}, 500
        return { "error": e.args[1] }, 500
    except Exception as e:
        current_app.logger.error(e)
        return { "error": e }, 500

    return Response(status = 200)