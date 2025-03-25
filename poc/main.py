from uco_kg import UCOKnowledgeGraph

if __name__ == "__main__":
    # Initialize the UCO knowledge graph
    uco_kg = UCOKnowledgeGraph()

    # Load the UCO ontology
    try:
        uco_kg.load_graph("../UCO")

        # Example: Find cybersecurity-related concepts
        cyber_concepts = uco_kg.get_cybersecurity_concepts()
        print(f"Found {len(cyber_concepts)} cybersecurity-related concepts")

        # Print a few of them as examples
        for concept in cyber_concepts[:5]:
            print(f"- {concept['label']}: {concept['comment'][:100]}...")

        # Example: Find entities related to 'attack'
        attack_entities = uco_kg.find_entities_by_label("attack")
        print(f"\nFound {len(attack_entities)} entities related to 'attack'")

        # Print a few of them as examples
        for entity in attack_entities[:5]:
            print(f"- {entity['label']}: {entity['comment'][:100]}...")

    except Exception as e:
        print(f"Error: {e}")
        import traceback

        traceback.print_exc()
