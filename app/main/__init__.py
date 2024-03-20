from flask import Blueprint

# Create the current blueprint
main = Blueprint('main', __name__)

from . import errors, filters
from .views import tokens, corpus, index, dashboard
