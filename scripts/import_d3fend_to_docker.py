import time

from loguru import logger
from neo4j import GraphDatabase

D3FEND_OWL_URL = "https://d3fend.mitre.org/ontologies/d3fend.owl"


def wait_for_neo4j(max_retries=30):
    """Wait for Neo4j to be ready"""
    driver = None
    for i in range(max_retries):
        try:
            driver = GraphDatabase.driver(
                "bolt://neo4j:7687", auth=("neo4j", "pfcime2025")
            )
            with driver.session() as session:
                session.run("RETURN 1")
            logger.info("Neo4j is ready!")
            return driver
        except Exception as e:
            logger.info(f"Waiting for Neo4j... ({i + 1}/{max_retries}): {e}")
            time.sleep(5)
    raise Exception("Neo4j not ready after maximum retries")


def setup_n10s_constraint_and_config(session):
    """Create constraint and configure n10s for D3FEND"""

    logger.info("Creating unique constraint for Resource.uri...")
    constraint_query = """
    CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE
    """
    session.run(constraint_query)
    logger.info("Constraint created")

    logger.info("Initializing n10s configuration for D3FEND...")
    config_query = """
    CALL n10s.graphconfig.init({
      handleVocabUris: "SHORTEN",
      handleMultival: "ARRAY",
      applyNeo4jNaming: true,
      keepLangTag: false,
      keepCustomDataTypes: false,
      prefixMappings: "d3f:https://d3fend.mitre.org/ontologies/d3fend.owl#,owl:http://www.w3.org/2002/07/owl#,rdfs:http://www.w3.org/2000/01/rdf-schema#"
    })
    """
    session.run(config_query)
    logger.info("n10s configuration initialized for D3FEND")


def import_d3fend_owl(session):
    """Import the D3FEND OWL file from the official URL"""
    logger.info(f"Importing D3FEND ontology from {D3FEND_OWL_URL} ...")

    import_query = """
    CALL n10s.rdf.import.fetch(
      $owl_url,
      "RDF/XML"
    )
    """

    try:
        result = session.run(import_query, {"owl_url": D3FEND_OWL_URL})
        result.consume()
        logger.info("✓ D3FEND ontology imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Error importing D3FEND ontology: {e}")
        return False


def verify_import(session):
    """Verify the import was successful"""
    logger.info("Verifying D3FEND import...")

    result = session.run("MATCH (n) RETURN count(n) as total")
    total_nodes = result.single()["total"]
    logger.info(f"Total nodes: {total_nodes}")

    result = session.run(
        "MATCH (c:Resource) WHERE c.uri CONTAINS 'd3fend' RETURN count(c) AS count"
    )
    d3fend_nodes = result.single()["count"]
    logger.info(f"D3FEND nodes: {d3fend_nodes}")

    result = session.run("CALL db.labels() YIELD label RETURN label LIMIT 10")
    labels = [record["label"] for record in result]
    logger.info(f"Sample labels: {labels}")

    return total_nodes > 0 and d3fend_nodes > 0


def main():
    """Main import process for D3FEND"""
    logger.info("Starting D3FEND ontology import to Docker Neo4j...")

    driver = wait_for_neo4j()

    try:
        with driver.session() as session:
            setup_n10s_constraint_and_config(session)

            if import_d3fend_owl(session):
                logger.info("Import completed: D3FEND ontology imported successfully")
            else:
                logger.error("D3FEND ontology import failed!")

            if verify_import(session):
                logger.info("D3FEND ontology import verification successful!")
            else:
                logger.error("D3FEND ontology import verification failed!")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
