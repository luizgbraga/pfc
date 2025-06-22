from flask import Blueprint, jsonify, request

from server.controllers import (
    analyze_ontology_controller,
    display_playbook_controller,
    explore_ontology_controller,
    export_playbook_controller,
    generate_playbook_controller,
    list_key_concepts_controller,
    list_observables_controller,
    list_relationship_types_controller,
    test_neo4j_connection_controller,
)

routes = Blueprint("routes", __name__)


@routes.route("/test-neo4j-connection", methods=["GET"])
def test_neo4j_connection():
    return jsonify(test_neo4j_connection_controller())


@routes.route("/explore-ontology", methods=["GET"])
def explore_ontology():
    search_term = request.args.get("search_term")
    return jsonify(explore_ontology_controller(search_term))


@routes.route("/list-key-concepts", methods=["GET"])
def list_key_concepts():
    limit = request.args.get("limit", default=20, type=int)
    return jsonify(list_key_concepts_controller(limit))


@routes.route("/list-relationship-types", methods=["GET"])
def list_relationship_types():
    return jsonify(list_relationship_types_controller())


@routes.route("/analyze-ontology", methods=["GET"])
def analyze_ontology():
    return jsonify(analyze_ontology_controller())


@routes.route("/list-observables", methods=["GET"])
def list_observables():
    return jsonify(list_observables_controller())


@routes.route("/generate-playbook", methods=["POST"])
def generate_playbook():
    data = request.get_json()
    alert = data.get("alert")
    output_file = data.get("output_file")
    export = data.get("export", False)
    display = data.get("display", False)
    return jsonify(generate_playbook_controller(alert, output_file, export, display))


@routes.route("/export-playbook", methods=["POST"])
def export_playbook():
    data = request.get_json()
    playbook_file = data.get("playbook_file")
    output_file = data.get("output_file")
    return jsonify(export_playbook_controller(playbook_file, output_file))


@routes.route("/display-playbook", methods=["POST"])
def display_playbook():
    data = request.get_json()
    playbook_file = data.get("playbook_file")
    return jsonify(display_playbook_controller(playbook_file))
