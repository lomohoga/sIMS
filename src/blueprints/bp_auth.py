from flask import Blueprint, render_template, redirect, url_for, request, session

from src.blueprints.auth import generateHash
from src.blueprints.database import connect_db

bp_auth = Blueprint('bp_auth', __name__)

# route for login page
@bp_auth.route('/login', methods=('GET', 'POST'))
def login ():
    error = ""

    if request.method == 'POST':
        username = request.form['uname']
        password = request.form['pword']

        cxn = connect_db()
        db = cxn.cursor()
        db.execute(f"SELECT Username, Password, FirstName, LastName, RoleID, RoleName, Email FROM user LEFT JOIN role USING (RoleID) WHERE Username = '{username}' OR Email = '{username}'")
        record = db.fetchone()
        cxn.close()

        if record is None:
            error = "Invalid login, please try again."
        else:
            user = {a: b for a, b in zip(["Username", "Password", "FirstName", "LastName", "RoleID", "RoleName", "Email"], record)}

            if generateHash(password) != user["Password"]:
                error = "Invalid login, please try again."

        if error == "":
            session.clear()
            session['user'] = user
            return redirect(url_for('bp_inventory.inventory'))

    return render_template("login.html", msg = error)

# route for logging out
@bp_auth.route('/logout')
def logout ():
    session.clear()
    return redirect(url_for('bp_auth.login'))
