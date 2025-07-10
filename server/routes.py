import os

from flask import Blueprint, abort, jsonify, request, send_from_directory

from server.controllers import (
    generate_playbook_controller,
)

routes = Blueprint("routes", __name__)


@routes.route("/")
def index():
    """Serve the HTML frontend"""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "static"), "index.html"
    )


@routes.route("/generate-playbook", methods=["POST"])
def generate_playbook():
    data = request.get_json()
    alert = data.get("alert")
    if not alert:
        return abort(400, "Missing 'alert' field in request data")
    if not isinstance(alert, dict):
        return abort(400, "'alert' must be a dictionary")
    output_file = data.get("output_file")
    export = data.get("export", False)
    display = data.get("display", False)
    return jsonify(generate_playbook_controller(alert, output_file, export, display))
