from flask import Blueprint, Response, render_template, request, session

from src.blueprints.auth import login_required
from src.blueprints.decode_keyword import decode_keyword

from src.formgen import form_58, form_69

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

    item = request.args["item"]

    return form_58(item)

# route for generating appendix 69
@bp_form.route('/69')
@login_required
def generate_69 ():
    if session['user']['RoleID'] != 1: 
        return render_template("error.html", errcode = 403, errmsg = "You do not have permission to generate forms."), 403

    item = request.args["item"]

    return form_69(item)
