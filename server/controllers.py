from main import (
    analyze_ontology,
    display_playbook,
    explore_ontology,
    export_playbook,
    generate_playbook,
    list_key_concepts,
    list_observables,
    list_relationship_types,
    test_neo4j_connection,
)


def test_neo4j_connection_controller():
    return test_neo4j_connection()


def explore_ontology_controller(search_term):
    return explore_ontology(search_term=search_term)


def list_key_concepts_controller(limit):
    return list_key_concepts(limit=limit)


def list_relationship_types_controller():
    return list_relationship_types()


def analyze_ontology_controller():
    return analyze_ontology()


def list_observables_controller():
    return list_observables()


def generate_playbook_controller(alert, output_file, export, display):
    return generate_playbook(
        alert=alert, output_file=output_file, export=export, display=display
    )


def export_playbook_controller(playbook_file, output_file):
    return export_playbook(playbook_file=playbook_file, output_file=output_file)


def display_playbook_controller(playbook_file):
    return display_playbook(playbook_file=playbook_file)
