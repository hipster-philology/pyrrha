from . import babel
from flask import request, session
from flask_login import current_user


@babel.localeselector
def get_locale():
    # if a user is logged in, use the locale from the user settings
    fb_lg = session.get("locale")
    if current_user.is_authenticated and not current_user.is_anonymous:
        return current_user.locale
    elif fb_lg:
        return fb_lg
    # otherwise try to guess the language from the user accept
    # header the browser transmits.  We support de/fr/en in this
    # example.  The best match wins.
    return request.accept_languages.best_match(['bo_CN', 'en'])