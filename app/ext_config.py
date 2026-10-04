from flask import request, session, current_app
from flask_login import current_user


def get_locale():
    languages = list(current_app.config["LANGUAGES"])
    # if a user is logged in, use the locale from the user settings
    if current_user.is_authenticated and not current_user.is_anonymous:
        if current_user.locale in languages:
            return current_user.locale
    # otherwise use the locale chosen through the language menu
    elif session.get("locale") in languages:
        return session["locale"]
    # otherwise try to guess the language from the user accept
    # header the browser transmits. The best match wins.
    return request.accept_languages.best_match(languages) or "en"
