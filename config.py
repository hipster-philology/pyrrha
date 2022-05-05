import os


basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    APP_NAME = 'Pyrrha'
    if os.environ.get('SECRET_KEY'):
        SECRET_KEY = os.environ.get('SECRET_KEY')
    else:
        SECRET_KEY = 'SECRET_KEY_ENV_VAR_NOT_SET'
        print('SECRET KEY ENV VAR NOT SET! SHOULD NOT SEE IN PRODUCTION')
    # SQLALCHEMY_COMMIT_ON_TEARDOWN = True
    # Deprecated
    SQLALCHEMY_COMMIT_ON_TEARDOWN = False
    template_folder = os.path.join(basedir, "app", "templates")
    static_folder = os.path.join(basedir, "app", "statics")
    # SQLALCHEMY_ECHO = True

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER')
    MAIL_PORT = 587
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or True
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') or False
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    SEND_MAIL_STATUS = os.environ.get('SEND_MAIL_STATUS', True)

    # Admin account
    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'ppa-admin@ppa.fr'
    EMAIL_SUBJECT_PREFIX = '[{}]'.format(APP_NAME)
    EMAIL_SENDER = '{app_name} Admin <{email}>'.format(app_name=APP_NAME, email=MAIL_USERNAME)

    # Defaults
    PAGINATION_DEFAULT_TOKENS = 100

    # Lemmatizer (until Deucalion client)
    LEMMATIZERS = []

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-dev.sqlite')
    #SQLALCHEMY_DATABASE_URI = "postgres://postgres:mysecretpassword@172.17.0.2:5432/postgres"
    print('THIS APP IS IN DEBUG MODE. YOU SHOULD NOT SEE THIS IN PRODUCTION.')

    # Email
    MAIL_SERVER = 'smtp.mailgun.org'
    MAIL_PORT = 465
    MAIL_USE_TLS = False
    MAIL_USE_SSL = True
    MAIL_USERNAME = 'postmaster@sandboxfa7a873303c1425f8fda7947aa195696.mailgun.org'
    MAIL_PASSWORD = 'c3c7cc3c785815a8728a6266745a70db-b6183ad4-c78d7487'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'ppa-admin@ppa.fr'
    EMAIL_SUBJECT_PREFIX = '[{}]'.format(Config.APP_NAME)
    SEND_MAIL_STATUS = os.environ.get('SEND_MAIL_STATUS', False)
    EMAIL_SENDER = '{app_name} Admin <{email}>'.format(app_name=Config.APP_NAME, email=MAIL_USERNAME)

    LEMMATIZERS = [
        ("Ancien Français", "http://localhost:5001/")
    ]

    BABEL_TRANSLATION_DIRECTORIES = os.path.join(os.path.dirname(__file__), "translations")


class TestConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    print('THIS APP IS IN DEBUG MODE. YOU SHOULD NOT SEE THIS IN PRODUCTION.')

    # Disable CSRF for login purpose
    WTF_CSRF_ENABLED = False

    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'smtp.mailgun.org'
    MAIL_PORT = 465
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS') or False
    MAIL_USE_SSL = os.environ.get('MAIL_USE_SSL') or True
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME') or 'postmaster@sandboxfa7a873303c1425f8fda7947aa195696.mailgun.org'
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD') or 'c3c7cc3c785815a8728a6266745a70db-b6183ad4-c78d7487'
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')
    SEND_MAIL_STATUS = os.environ.get('SEND_MAIL_STATUS', False)

    ADMIN_PASSWORD = os.environ.get('ADMIN_PASSWORD') or 'admin'
    ADMIN_EMAIL = os.environ.get('ADMIN_EMAIL') or 'ppa-admin@ppa.fr'
    EMAIL_SUBJECT_PREFIX = '[{}]'.format(Config.APP_NAME)
    EMAIL_SENDER = '{app_name} Admin <{email}>'.format(app_name=Config.APP_NAME, email=MAIL_USERNAME)



config = {
    "dev": DevelopmentConfig,
    "prod": Config,
    "test": TestConfig
}
