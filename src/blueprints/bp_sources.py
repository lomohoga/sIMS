from flask import Blueprint, Response, render_template, request, session, current_app

from src.blueprints.auth import login_required
from src.blueprints.database import connect_db
from src.blueprints.decode_keyword import decode_keyword, escape
from src.blueprints.exceptions import SourceNotFoundError, ExistingSourceError, SelfNotFoundError, SelfRoleError

bp_sources = Blueprint('bp_sources', __name__, url_prefix = "/sources")

# route for sources
@bp_sources.route('/')
@login_required
def sources ():
    if session['user']['RoleID'] != 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to view sources."), 403
    else: return render_template("sources/sources.html", active = "deliveries")

# route for source search
@bp_sources.route('/search')
@login_required
def search_sources ():
    if session['user']['RoleID'] != 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to search for sources."), 403

    keywords = [] if "keywords" not in request.args else [decode_keyword(x).lower() for x in request.args.get("keywords").split(" ")]
    conditions = []
    for x in keywords:
        conditions.append(f"(SourceName LIKE '%{x}%')")
    query = f"SELECT * from sources {'' if len(conditions) == 0 else 'WHERE (' + ' AND '.join(conditions) + ')'};"

    cxn = None
    try:
        cxn = connect_db()
        db = cxn.cursor()
        db.execute(query)
        sources = db.fetchall()
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return { "sources": [
        {"SourceName": d[0],} for d in sources
    ]}

# route for source addition
@bp_sources.route('/add', methods = ["GET", "POST"])
@login_required
def add_sources ():
    if request.method == 'GET':
        if session['user']['RoleID'] != 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to add sources to the database."), 403
        else: return render_template("sources/add.html")

    if request.method == 'POST':        
        values = request.get_json()
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise SelfNotFoundError(username = session['user']['Username'])
            if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

            for v in values['values']:
                db.execute(f"SELECT * FROM sources WHERE SourceName = '{v['SourceName']}'")
                if db.fetchone() is not None: raise ExistingSourceError(source = v['SourceName'])

                db.execute(f"INSERT INTO sources VALUES ('{escape(v['SourceName'])}')")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()
        
        return Response(status = 200)

# route for source removal
@bp_sources.route('/remove', methods = ["GET", "POST"])
@login_required
def remove_sources ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to remove sources from the database."), 403
        else: return render_template("sources/remove.html")

    if request.method == "POST":
        sources = request.get_json()["sources"]
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
            f = db.fetchone()
            if f is None: raise SelfNotFoundError(username = session['user']['Username'])
            if f[0] == 2 and f[0] != session['user']['RoleID']: raise SelfRoleError(username = session['user']['Username'], role = f[0])

            for x in sources:
                db.execute(f"SELECT * FROM sources WHERE SourceName = '{x}'")
                if db.fetchone() is None: raise SourceNotFoundError(source = x)

                db.execute(f"DELETE FROM sources WHERE SourceName = '{x}'")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()

        return Response(status = 200)

# route for source update
@bp_sources.route('/update', methods = ["GET", "POST"])
@login_required
def update_sources ():
    if request.method == "GET":
        if session['user']['RoleID'] != 1: return render_template("error.html", errcode = 403, errmsg = "You do not have permission to update sources in the database."), 403
        else: return render_template("sources/update.html")

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
                db.execute(f"SELECT * FROM sources WHERE SourceName = '{v}'")
                if db.fetchone() is None: raise SourceNotFoundError(bp_sources = v)

                db.execute(f"SELECT * FROM sources WHERE SourceName = '{values[v]['SourceName']}'")
                if db.fetchone() is not None and v != values[v]['SourceName']: raise ExistingSourceError(source= values[v]['SourceName'])

                db.execute(f"UPDATE sources SET SourceName = '{escape(values[v]['SourceName'])}' WHERE SourceName = '{v}'")
            cxn.commit()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()
        
        return Response(status = 200)