import os
from app.lemmatizers import LemmatizerService
from typing import List
from sqlalchemy.pool import NullPool

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
    LEMMATIZERS: List[LemmatizerService] = []

    # Change automatically the Postgresql instance language if not english
    FORCE_PSQL_EN_LOCALE = True

    @staticmethod
    def init_app(app):
        pass


class DevelopmentConfig(Config):
    DEBUG = True
    ASSETS_DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        "postgresql+psycopg://user:pwd@localhost:5432/data-dev"
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

    LEMMATIZERS = [        LemmatizerService(
            title="Latin",
            uri="https://tal.chartes.psl.eu/deucalion/api/lasla/",
            provider="PSL-École Nationale des Chartes & Huma-Num",
            ui="https://tal.chartes.psl.eu/deucalion/latin",
            apa="Thibault Clérice. (2020). Deucalion Latin Lemmatizer (0.1.1). "
            "Zenodo. https://doi.org/10.5281/zenodo.3660914",
            bibtex="""@software{thibault_clerice_2020_3660914,
  author       = {Thibault Clérice},
  title        = {Deucalion Latin Lemmatizer},
  month        = feb,
  year         = 2020,
  publisher    = {Zenodo},
  version      = {0.1.1},
  doi          = {10.5281/zenodo.3660914},
  url          = {https://doi.org/10.5281/zenodo.3660914}
}"""
        ),
        LemmatizerService(
            title="Old French",
            uri="https://tal.chartes.psl.eu/deucalion/api/fro-1/",
            provider="PSL-École Nationale des Chartes & Huma-Num",
            ui="https://dh.chartes.psl.eu/deucalion/fro",
            apa="Camps, J. B., Clérice, T., Duval, F., Kanaoka, N., & Pinche, A. (2021). Corpus and Models "
            "for Lemmatisation and POS-tagging of Old French. arXiv preprint arXiv:2109.11442.",
            bibtex="""@article{camps2021corpus,
  title={Corpus and Models for Lemmatisation and POS-tagging of Old French},
  author={Camps, Jean-Baptiste and Cl{\'e}rice, Thibault and Duval, Fr{\'e}d{\'e}ric and Kanaoka, Naomi and Pinche, Ariane and others},
  journal={arXiv preprint arXiv:2109.11442},
  year={2021}
}"""
        ),

    ]

    BABEL_TRANSLATION_DIRECTORIES = os.path.join(os.path.dirname(__file__), "translations")


class BaseTestConfig(Config):
    """Test configuration base class."""
    DEBUG = True
    ASSETS_DEBUG = True
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

    LEMMATIZERS = [
        LemmatizerService(
            "Dummy lemmatizer",
            "http://localhost:4567/lemma",
            provider="ProviderInstitution",
            ui="someui.com",
            apa="Clérice et al. 2019",
            bibtex="""@article{camps2021corpus,
	title        = {Corpus and Models for Lemmatisation and POS-tagging of Old French},
	author       = {Camps, Jean-Baptiste and Cl{\'e}rice, Thibault and Duval, Fr{\'e}d{\'e}ric and Kanaoka, Naomi and Pinche, Ariane and others},
	year         = 2021,
	journal      = {arXiv preprint arXiv:2109.11442},
	keywords     = {Old French}
}"""
        )
    ]


class SQLiteTestConfig(BaseTestConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'data-test.sqlite')
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}


class PostgreSQLTestConfig(BaseTestConfig):
    SQLALCHEMY_DATABASE_URI = os.environ.get('TEST_DATABASE_URL') or \
        'postgresql+psycopg:///data-test'
    SQLALCHEMY_ENGINE_OPTIONS = {"poolclass": NullPool}


config = {
    "dev": DevelopmentConfig,
    "prod": Config,
    "test": PostgreSQLTestConfig if os.environ.get("TEST_DBMS", "sqlite").lower() == "postgresql" else SQLiteTestConfig
}
