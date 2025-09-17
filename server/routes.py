import os
from typing import Any, Dict, Tuple, Union

from flask import Blueprint, Response, abort, jsonify, request, send_from_directory

from server.controllers import (
    generate_playbook_controller,
)

routes = Blueprint("routes", __name__)


@routes.route("/")
def index() -> Response:
    """Serve the HTML frontend"""
    return send_from_directory(
        os.path.join(os.path.dirname(__file__), "static"), "index.html"
    )


@routes.route("/playbook")
def playbook() -> Union[Response, Tuple[str, int]]:
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
def generate_playbook() -> Response:
    data: Dict[str, Any] = request.get_json()
    alert: Dict[str, Any] = data.get("alert")
    if not alert:
        return abort(400, "Missing 'alert' field in request data")
    if not isinstance(alert, dict):
        return abort(400, "'alert' must be a dictionary")
    output_file: str = data.get("output_file")
    export: bool = data.get("export", False)
    display: bool = data.get("display", False)
    graph_rag_enabled: bool = data.get("graph_rag_enabled", True)
    return jsonify(
        generate_playbook_controller(
            alert, output_file, export, display, graph_rag_enabled
        )
    )
