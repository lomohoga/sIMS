from flask import Blueprint, Response, render_template, request, session, current_app

from src.blueprints.auth import login_required
from src.blueprints.database import connect_db
from src.blueprints.exceptions import SelfNotFoundError, SelfRoleError

from src.formgen import form_58, form_59, form_63, form_69, form_71

bp_form = Blueprint("bp_form", __name__, url_prefix = "/forms")

# route for form landing page
@bp_form.route('/')
@login_required
def forms ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403
    else:
        return render_template("forms/forms.html", active = "forms")

# route for generating appendix 58
@bp_form.route('/58')
@login_required
def generate_58 ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403

    cxn = None
    item = request.args["item"]
    try:
        cxn = connect_db()
        db = cxn.cursor(buffered=True)

        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2: raise SelfRoleError(username = session['user']['Username'], role = f[0])

        return form_58(db, item)
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

# route for generating appendix 59
@bp_form.route('/5971')
@login_required
def generate_5971 ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403

    cxn = None
    form = None
    item = request.args["item"]
    try:
        cxn = connect_db()
        db = cxn.cursor(buffered=True)

        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2: raise SelfRoleError(username = session['user']['Username'], role = f[0])

        db.execute(f"SELECT hasPropertyApproved FROM request WHERE RequestID = {item};")
        g = db.fetchone()
        if(g[0] == 0):
            form = form_59(db, item)
        else:
            form = form_71(db, item)
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

    return form

# route for generating appendix 63
@bp_form.route('/63')
@login_required
def generate_63 ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403

    cxn = None
    item = request.args["item"]
    try:
        cxn = connect_db()
        db = cxn.cursor(buffered=True)
        
        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2: raise SelfRoleError(username = session['user']['Username'], role = f[0])

        return form_63(db, item)
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()

# route for generating appendix 69
@bp_form.route('/69')
@login_required
def generate_69 ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403

    cxn = None
    item = request.args["item"]
    try:
        cxn = connect_db()
        db = cxn.cursor(buffered=True)
        
        db.execute(f"SELECT RoleID FROM user WHERE Username = '{session['user']['Username']}'")
        f = db.fetchone()
        if f is None: raise SelfNotFoundError(username = session['user']['Username'])
        if f[0] == 2: raise SelfRoleError(username = session['user']['Username'], role = f[0])

        return form_69(db, item)
    except Exception as e:
        current_app.logger.error(str(e))
        return { "error": str(e) }, 500
    finally:
        if cxn is not None: cxn.close()
