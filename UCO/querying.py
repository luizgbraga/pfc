from rdflib import Graph

g = Graph()

ontology_files = [
    "core/core.ttl",
    "identity/identity.ttl",
    "observable/observable.ttl",
    "action/action.ttl",
    "analysis/analysis.ttl",
]

for file in ontology_files:
    g.parse(f"ontology/uco/{file}", format="turtle")

query = """
SELECT ?s ?p ?o WHERE {
    ?s ?p ?o .
} LIMIT 10
"""
for row in g.query(query):
    print(row)
