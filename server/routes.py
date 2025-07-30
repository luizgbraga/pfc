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


@routes.route("/playbook")
def playbook():
    """Serve the generated playbook HTML if it exists, otherwise show a message."""
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    playbook_path = os.path.join(static_dir, "playbook.html")
    if os.path.exists(playbook_path):
        return send_from_directory(static_dir, "playbook.html")
    else:
        return (
            "<h2>No playbook generated yet.</h2><p>Generate a playbook to view it here.</p>",
            200,
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
