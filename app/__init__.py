import os
from flask import Flask, g

from config import config
from flask_compress import Compress
from flask_login import LoginManager
from flask_mail import Mail
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from flaskext.markdown import Markdown
from flask_babel import Babel
from .ext_config import get_locale
from sqlalchemy import text
import warnings

basedir = os.path.abspath(os.path.dirname(__file__))

mail = Mail()
db = SQLAlchemy()
csrf = CSRFProtect()
compress = Compress()
babel = Babel()
# Set up Flask-Login
login_manager = LoginManager()
login_manager.session_protection = 'strong'
login_manager.login_view = 'account.login'


def create_app(config_name="dev"):
    """ Create the application """

    app = Flask(
        __name__,
        template_folder=config[config_name].template_folder,
        static_folder=config[config_name].static_folder,
        static_url_path="/statics"
    )
        
    if not isinstance(config_name, str):
        app.config.from_object(config)
    else:
        app.config.from_object(config[config_name])
        
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    config[config_name].init_app(app)

    # Set up extensions
    mail.init_app(app)
    db.init_app(app)
    login_manager.init_app(app)
    #csrf.init_app(app)
    compress.init_app(app)
    md = Markdown(app, safe_mode=True)
    babel.init_app(app, locale_selector=get_locale)
    if db.session.get_bind().dialect.name == "postgresql":
        lc_messages_query = db.session.execute(text("SHOW lc_messages;"))
        psql_locale = lc_messages_query.fetchone()[0]
        if psql_locale != "en_US.UTF-8":
            warnings.warn("Your postgresql instance language is not english. Switching to English.")
            db.session.execute(text("SET lc_messages TO 'en_US.UTF-8';"))
            db.session.commit()
    # Register Jinja template functions
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    from .account import account as account_blueprint
    app.register_blueprint(account_blueprint, url_prefix='/account')

    from .admin import admin as admin_blueprint
    app.register_blueprint(admin_blueprint, url_prefix='/admin')

    from .configurations import configuration as configurations_blueprint
    app.register_blueprint(configurations_blueprint)

    from .control_lists import control_lists_bp
    app.register_blueprint(control_lists_bp)

    return app

    
