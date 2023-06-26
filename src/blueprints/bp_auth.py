from flask import Blueprint, Response, render_template, redirect, url_for, request, session, current_app

from src.blueprints.auth import generateHash
from src.blueprints.database import connect_db

bp_auth = Blueprint('bp_auth', __name__)

# route for login page
@bp_auth.route('/login', methods=('GET', 'POST'))
def login ():
    if request.method == 'GET': return render_template('login.html')
    
    if request.method == 'POST':
        req = request.get_json()
        username, password = req['username'], req['password']
        cxn = None
        try:
            cxn = connect_db()
            db = cxn.cursor()

            db.execute(f"SELECT Username, Password, FirstName, LastName, RoleID, RoleName, Email FROM user LEFT JOIN role USING (RoleID) WHERE Username = '{username}' OR Email = '{username}'")
            record = db.fetchone()
        except Exception as e:
            current_app.logger.error(str(e))
            return { "error": str(e) }, 500
        finally:
            if cxn is not None: cxn.close()

        if record is None: return { "error": "Invalid login. Please try again." }, 500
        user = {a: b for a, b in zip(["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName", "Email"], record)}
        if generateHash(password) != user["Password"]: return { "error": "Invalid login. Please try again." }, 500
            
        session.clear()
        session['user'] = user
        return Response(status = 200)

# route for logging out
@bp_auth.route('/logout')
def logout ():
    session.clear()
    return redirect(url_for('bp_auth.login'))
