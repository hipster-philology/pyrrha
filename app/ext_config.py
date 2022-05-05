from . import babel, db, app
from .models.user import User

@babel.localeselector
def get_locale():
    return 'en'