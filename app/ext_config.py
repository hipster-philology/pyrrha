from flask import current_app
from . import babel, db
from .models.user import User

@babel.localeselector
def get_locale():
    return 'bo_CN'
