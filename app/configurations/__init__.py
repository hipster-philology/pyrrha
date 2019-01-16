"""
Temporary hack before shared configurations.

Allows to stock configuration here.

"""
from os import path
from flask import Blueprint

#  Find the static folder
static_folder = path.join(path.abspath(path.dirname(__file__)), "langs")
#  Create the current blueprint
configuration = Blueprint('configurations', __name__, static_folder=static_folder)
