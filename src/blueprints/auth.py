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