import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

basedir = os.path.abspath(os.path.dirname(__file__))
db = SQLAlchemy()


def create_app(config_name="dev"):
    """ Create the application """
    app = Flask(
        __name__,
        template_folder=config[config_name].template_folder,
        static_folder=config[config_name].static_folder,
        static_path="/statics"
    )
    app.config.from_object(config[config_name])
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    config[config_name].init_app(app)

    # Set up extensions
    db.init_app(app)
    #assets_env = Environment(app)

    # Register Jinja template functions
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app