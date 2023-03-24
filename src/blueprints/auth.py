from hashlib import sha256
from functools import wraps

from flask import redirect, url_for, session

from src.blueprints.database import connect_db

# decorator for pages that require authentication
def login_required (view):
    @wraps(view)
    def wrapped_view(**kwargs):
        if 'user' not in session.keys():
            return redirect(url_for('bp_auth.login'))

        return view(**kwargs)

    return wrapped_view

# encrypt password using sha256
def generateHash (a):
    m = sha256()
    m.update(a.encode('utf-8'))
    return m.hexdigest()

# update values of session['user']
def update_session():
    cxn = connect_db()
    db = cxn.cursor()
    db.execute(f"SELECT Username, Password, FirstName, LastName, RoleID, RoleName, Email FROM user LEFT JOIN role USING (RoleID) WHERE Username = '{session['user']['Username']}'")
    user = {a: b for a, b in zip(["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName", "Email"], db.fetchone())}
    cxn.close()

    session.clear()
    session['user'] = user
    return
