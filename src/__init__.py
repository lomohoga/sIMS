import os

from flask import Flask, Response, redirect, render_template, url_for, request, session
from logging.config import dictConfig

from src.blueprints.auth import login_required
from src.blueprints.bp_auth import bp_auth
from src.blueprints.bp_inventory import bp_inventory
from src.blueprints.bp_categories import bp_categories
from src.blueprints.bp_request import bp_request
from src.blueprints.bp_user import bp_user
from src.blueprints.bp_delivery import bp_delivery
from src.blueprints.bp_form import bp_form
from src.blueprints.bp_sources import bp_sources

#configure logger
dictConfig({
    "version": 1,
    "formatters": {
        "default": {
            "format": "[%(asctime)s] %(levelname)s in %(module)s, %(funcName)s: %(message)s",
        }
    },

    "handlers": {
        "file": {
            'level': 'ERROR',
            "class": "logging.handlers.RotatingFileHandler",
            "filename": "flask.log", #Change this for Windows
            "maxBytes": 3000000,
            "backupCount": 2,
            "formatter": "default",
        },
    },

    "root": {"handlers": ["file"]},
})

def create_app (test_config = None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config = True)
    app.config.from_mapping(SECRET_KEY = 'dev')

    # register blueprints here
    app.register_blueprint(bp_inventory)
    app.register_blueprint(bp_auth)
    app.register_blueprint(bp_request)
    app.register_blueprint(bp_user)
    app.register_blueprint(bp_delivery)
    app.register_blueprint(bp_form)
    app.register_blueprint(bp_categories)
    app.register_blueprint(bp_sources)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # route for inventory (main page)
    @app.route('/')
    def index ():
        return redirect(url_for('bp_inventory.inventory')), 303

    ### ERROR HANDLERS ###

    # 404 - page not found
    @app.errorhandler(404)
    def error_404 (e):
        return render_template("error.html", errcode = 404, errmsg = "Page not found. Please check if the URL you have typed is correct."), 404
    

    # 500 - server error
    @app.errorhandler(500)
    def error_500 (e):
        return render_template("error.html", errcode = 500, errmsg = "Internal server error. Please try again later."), 500

    return app
