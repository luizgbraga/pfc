import time

from loguru import logger
from neo4j import GraphDatabase

TTL_FILES = [
    "uco.ttl",
    "core.ttl",
    "types.ttl",
    "vocabulary.ttl",
    "observable.ttl",
    "action.ttl",
    "identity.ttl",
    "location.ttl",
    "marking.ttl",
    "pattern.ttl",
    "role.ttl",
    "time.ttl",
    "tool.ttl",
    "victim.ttl",
]


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
    """Create constraint and configure n10s"""

    logger.info("Creating unique constraint for Resource.uri...")
    constraint_query = """
    CREATE CONSTRAINT n10s_unique_uri IF NOT EXISTS FOR (r:Resource) REQUIRE r.uri IS UNIQUE
    """
    session.run(constraint_query)
    logger.info("Constraint created")

    logger.info("Initializing n10s configuration...")
    config_query = """
    CALL n10s.graphconfig.init({
      handleVocabUris: "SHORTEN",
      handleMultival: "ARRAY",
      applyNeo4jNaming: true,
      keepLangTag: false,
      keepCustomDataTypes: false,
      prefixMappings: "uco:https://unifiedcyberontology.org/,owl:http://www.w3.org/2002/07/owl#,rdfs:http://www.w3.org/2000/01/rdf-schema#,core:https://unifiedcyberontology.org/core#,observable:https://unifiedcyberontology.org/observable#,action:https://unifiedcyberontology.org/action#"
    })
    """
    session.run(config_query)
    logger.info("n10s configuration initialized")


def import_ttl_file(session, ttl_file):
    """Import a single TTL file"""
    logger.info(f"Importing {ttl_file}...")

    import_query = """
    CALL n10s.rdf.import.fetch(
      $file_path,
      "Turtle"
    )
    """

    file_path = f"file:///uco-ttl/{ttl_file}"

    try:
        result = session.run(import_query, {"file_path": file_path})
        result.consume()
        logger.info(f"✓ {ttl_file} imported successfully")
        return True
    except Exception as e:
        logger.error(f"✗ Error importing {ttl_file}: {e}")
        return False


def verify_import(session):
    """Verify the import was successful"""
    logger.info("Verifying import...")

    result = session.run("MATCH (n) RETURN count(n) as total")
    total_nodes = result.single()["total"]
    logger.info(f"Total nodes: {total_nodes}")

    result = session.run("MATCH (c:Resource:owl__Class) RETURN count(c) AS count")
    uco_classes = result.single()["count"]
    logger.info(f"DEF3ND classes: {uco_classes}")

    result = session.run("CALL db.labels() YIELD label RETURN label LIMIT 10")
    labels = [record["label"] for record in result]
    logger.info(f"Sample labels: {labels}")

    return total_nodes > 0 and uco_classes > 0


def main():
    """Main import process"""
    logger.info("Starting DEF3ND ontology import to Docker Neo4j...")

    driver = wait_for_neo4j()

    try:
        with driver.session() as session:
            setup_n10s_constraint_and_config(session)

            successful_imports = 0
            for ttl_file in TTL_FILES:
                if import_ttl_file(session, ttl_file):
                    successful_imports += 1
                time.sleep(1)

            logger.info(
                f"Import completed: {successful_imports}/{len(TTL_FILES)} files imported successfully"
            )

            if verify_import(session):
                logger.info("DEF3ND ontology import verification successful!")
            else:
                logger.error("DEF3ND ontology import verification failed!")

    except Exception as e:
        logger.error(f"Import failed: {e}")
        raise
    finally:
        driver.close()


if __name__ == "__main__":
    main()
