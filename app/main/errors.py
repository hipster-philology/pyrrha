from flask import render_template, jsonify

from . import main
from .views.utils import request_wants_json


@main.app_errorhandler(403)
def forbidden(_):
    if request_wants_json():
        return jsonify({"error": "Forbidden"}), 403
    return render_template('errors/403.html'), 403


@main.app_errorhandler(404)
def page_not_found(_):
    if request_wants_json():
        return jsonify({"error": "Not found"}), 404
    return render_template('errors/404.html'), 404


@main.app_errorhandler(500)
def internal_server_error(_):
    if request_wants_json():
        return jsonify({"error": "Internal server error"}), 500
    return render_template('errors/500.html'), 500
