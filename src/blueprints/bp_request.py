import locale

from flask import Blueprint, Response, render_template, request, session, current_app

from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword
from src.blueprints.format_data import format_requests
from src.blueprints.auth import login_required
from src.blueprints.exceptions import RequestNotFoundError, RequestStatusError, ItemIssuedError, ItemNotInRequestError, IllegalIssueError, IncompleteIssueError, SelfRoleError, SelfNotFoundError

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
    filters = [] if "filter" not in request.args else request.args.get("filter").split(",")

    conditions = []
    for x in keywords:
        conditions.append(f"ItemID LIKE '%{x}%' OR ItemName LIKE '%{x}%' OR ItemDescription LIKE '%{x}%' OR RequestedBy LIKE '%{x}%'")
    if len(filters) > 0: conditions.append(f'LOWER(StatusName) in {str(filters).replace("[", "(").replace("]", ")")}')

    w = f"({' AND '.join(conditions)})" if len(conditions) > 0 else ""
    cxn = None

    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT RequestID, RequestedBy, DATE_FORMAT(RequestDate, '%d %b %Y') AS RequestDate, StatusName as Status, Purpose, Remarks, ItemID, ItemName, Category, ItemDescription, RequestQuantity, QuantityIssued, AvailableStock, Unit FROM request INNER JOIN request_status USING (StatusID) INNER JOIN request_item USING (RequestID) INNER JOIN stock USING (ItemID){' WHERE RequestID IN (SELECT DISTINCT RequestID FROM request INNER JOIN request_item USING (RequestID) INNER JOIN item USING (ItemID) WHERE ' + w + ')' if w != '' else ''} ORDER BY RequestID, ItemID")
        requests = db.fetchall()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return { "requests": format_requests(requests, session['user']['RoleID'] == 1) }

# route for request approval
@bp_request.route('/approve', methods = ["POST"])
def approve_request ():
    req = request.get_json()['RequestID']
    cxn = None
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {req}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = req)
        if f[0] != 1: raise RequestStatusError(from_status = f[0], to_status = 2)
        
        db.execute(f"UPDATE request SET StatusID = 2, ActingAdmin = '{session['user']['Username']}', DateApproved = CURDATE() WHERE RequestID = {req}")
        cxn.commit()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()
        
    return Response(status = 200)

# route for request denial
@bp_request.route('/deny', methods = ["POST"])
def deny_request ():
    req = request.get_json()['RequestID']
    remarks = request.get_json()['Remarks']
    cxn = None
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {req}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = req)
        if f[0] != 1: raise RequestStatusError(from_status = f[0], to_status = 5)
        
        db.execute(f"UPDATE request SET StatusID = 5, ActingAdmin = '{session['user']['Username']}', DateCancelled = CURDATE(), Remarks = '{remarks}' WHERE RequestID = {req}")
        cxn.commit()
    except Exception  as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()
    
    return Response(status = 200)

# route for request cancellation
@bp_request.route('/cancel', methods = ["POST"])
@login_required
def cancel_request ():
    req = request.get_json()['RequestID']
    remarks = request.get_json()['Remarks']
    cxn = None
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {req}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = req)
        if f[0] in [4, 5, 6]: raise RequestStatusError(from_status = f[0], to_status = 6)
        
        db.execute(f"UPDATE request SET StatusID = 6, CancelledBy = '{session['user']['Username']}', DateCancelled = CURDATE(), Remarks = '{remarks}' WHERE RequestID = {req}")
        cxn.commit()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()
    
    return Response(status = 200)

# route for request receipt
@bp_request.route('/receive', methods = ["POST"])
@login_required
def receive_request ():
    req = request.get_json()['RequestID']
    cxn = None

    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 1 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])
    
        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {req}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = req)
        if f[0] != 3: raise RequestStatusError(from_status = f[0], to_status = 4)
        
        db.execute(f"UPDATE request SET StatusID = 4, ReceivedBy = '{session['user']['Username']}', DateReceived = CURDATE() WHERE RequestID = {req}")
        db.execute(f"SELECT COUNT(*) FROM request_item LEFT JOIN item USING (ItemID) WHERE RequestID = {req} && Price >= 50000 && QuantityIssued > 0;")
        g = db.fetchone()
        if(f[0] > 0):
            db.execute(f"UPDATE request SET hasPropertyApproved = 1 WHERE RequestID = {req};")
            
        cxn.commit()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return Response(status = 200)

# route for individual issue of request item
@bp_request.route('/issue/item', methods = ["POST"])
@login_required
def issue_item ():
    body = request.get_json()
    cxn = None

    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])
    
        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {body['RequestID']}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = body['RequestID'])
        if f[0] != 2: raise IllegalIssueError(request = body['RequestID'])
        
        db.execute(f"SELECT QuantityIssued FROM request_item WHERE RequestID = {body['RequestID']} AND ItemID = '{body['ItemID']}'")
        g = db.fetchone()
        if g is None: raise ItemNotInRequestError(item = body['ItemID'], request = body['RequestID'])
        if g[0] is not None: raise ItemIssuedError(item = body['ItemID'], request = body['RequestID'])
        
        db.execute(f"UPDATE request_item SET QuantityIssued = {body['QuantityIssued']} WHERE RequestID = {body['RequestID']} AND ItemID = '{body['ItemID']}'")
        cxn.commit()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()
    
    return Response(status = 200)

# route for request issue
@bp_request.route('/issue', methods = ["POST"])
@login_required
def issue_request ():
    req = request.get_json()['RequestID']
    remarks = request.get_json()['Remarks']
    cxn = None
    
    try:
        cxn = connect_db()
        db = cxn.cursor()

        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

        db.execute(f"SELECT StatusID FROM request WHERE RequestID = {req}")
        f = db.fetchone()
        if f is None: raise RequestNotFoundError(request = req)
        if f[0] != 2: raise RequestStatusError(from_status = f[0], to_status = 3)

        db.execute(f"SELECT QuantityIssued FROM request_item WHERE RequestID = {req}")
        g = all([x[0] is not None for x in db.fetchall()])
        if not g: raise IncompleteIssueError(request = req)
        
        db.execute(f"UPDATE request SET StatusID = 3, IssuedBy = '{session['user']['Username']}', DateIssued = CURDATE(), Remarks = '{remarks}' WHERE RequestID = {req}")
        cxn.commit()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return Response(status = 200)
