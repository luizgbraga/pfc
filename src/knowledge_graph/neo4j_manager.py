import sys
from typing import Any, Dict, List

from loguru import logger
from neo4j import GraphDatabase

from config.settings import LOG_LEVEL, NEO4J_PASSWORD, NEO4J_URI, NEO4J_USER

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)


class Neo4jManager:
    """Gerencia conexões e consultas ao banco de dados Neo4j contendo a ontologia DEF3ND."""

    def __init__(self, uri: str = None, user: str = None, password: str = None):
        """Inicializa o gerenciador de Neo4j.

        Args:
            uri: URI de conexão Neo4j
            user: Nome de usuário
            password: Senha
        """
        self.uri = uri or NEO4J_URI
        self.user = user or NEO4J_USER
        self.password = password or NEO4J_PASSWORD
        self.driver = None
        self._connect()

    def _connect(self) -> None:
        """Estabelece conexão com o banco de dados Neo4j."""
        try:
            self.driver = GraphDatabase.driver(
                self.uri, auth=(self.user, self.password)
            )
            logger.info(f"Conectado ao Neo4j em {self.uri}")

            with self.driver.session() as session:
                result = session.run(
                    "MATCH (c:Resource:owl__Class) RETURN count(c) AS count"
                )
                count = result.single()["count"]
                logger.info(
                    f"Banco de dados contém {count} classes da ontologia DEF3ND"
                )
        except Exception as e:
            logger.error(f"Falha ao conectar ao Neo4j: {str(e)}")
            raise

    def close(self) -> None:
        """Fecha a conexão com o driver Neo4j."""
        if self.driver:
            self.driver.close()
            logger.info("Conexão Neo4j fechada")

    def execute_query(self, query: str, params: Dict = None) -> List[Dict[str, Any]]:
        """Executa uma consulta Cypher no Neo4j.

        Args:
            query: String de consulta Cypher
            params: Parâmetros da consulta

        Returns:
            Lista de resultados da consulta como dicionários
        """
        params = params or {}
        try:
            with self.driver.session() as session:
                result = session.run(query, params)
                return [dict(record) for record in result]
        except Exception as e:
            logger.error(f"Falha na execução da consulta: {str(e)}")
            logger.debug(f"Consulta: {query}")
            logger.debug(f"Parâmetros: {params}")
            raise

    def get_cyber_observables(self) -> List[Dict[str, Any]]:
        """Recupera tipos de observáveis de segurança cibernética da DEF3ND.

        Returns:
            Lista de observáveis com URI, rótulo e descrição
        """
        query = """
        MATCH (c:Resource:owl__Class)-[:rdfs__subClassOf*]->(parent:Resource:owl__Class)
        WHERE ANY(label IN parent.rdfs__label WHERE label = 'Observable')
        RETURN c.uri AS uri, 
               c.rdfs__label[0] AS label, 
               CASE WHEN c.rdfs__comment IS NULL THEN '' 
                    ELSE c.rdfs__comment[0] END AS description
        """
        return self.execute_query(query)

    def find_attack_patterns(self) -> List[Dict[str, Any]]:
        """Recupera padrões de ataque da DEF3ND.

        Returns:
            Lista de padrões de ataque com URI, rótulo e descrição
        """
        query = """
        MATCH (c:Resource:owl__Class)
        WHERE ANY(label IN c.rdfs__label WHERE 
                 label CONTAINS 'Attack' OR 
                 label CONTAINS 'Threat' OR
                 label CONTAINS 'Malicious')
        RETURN c.uri AS uri, 
               c.rdfs__label[0] AS label, 
               CASE WHEN c.rdfs__comment IS NULL THEN '' 
                    ELSE c.rdfs__comment[0] END AS description
        """
        return self.execute_query(query)

    def get_class_properties(self, class_name: str) -> List[Dict[str, Any]]:
        """Recupera propriedades associadas a uma classe específica.

        Args:
            class_name: Nome da classe (exato)

        Returns:
            Lista de propriedades com URI, rótulo e descrição
        """
        query = """
        MATCH (c:Resource:owl__Class)<-[:rdfs__domain]-(p:Resource)
        WHERE ANY(label IN c.rdfs__label WHERE label = $class_name)
        RETURN p.uri AS uri, 
               p.rdfs__label[0] AS label, 
               CASE WHEN p.rdfs__comment IS NULL THEN '' 
                    ELSE p.rdfs__comment[0] END AS description,
               CASE WHEN p.rdfs__range IS NULL THEN [] 
                    ELSE p.rdfs__range END AS range_type
        """
        return self.execute_query(query, {"class_name": class_name})

    def get_mitigations_for_attack(self, attack_pattern: str) -> List[Dict[str, Any]]:
        """Recupera mitigações recomendadas para um padrão de ataque.

        Args:
            attack_pattern: Nome ou parte do nome do padrão de ataque

        Returns:
            Lista de mitigações com URI, rótulo e descrição
        """
        query = """
        MATCH (attack:Resource:owl__Class)-[r]-(mitigation:Resource:owl__Class)
        WHERE ANY(label IN attack.rdfs__label WHERE label CONTAINS $attack_pattern)
        AND ANY(label IN mitigation.rdfs__label WHERE 
                label CONTAINS 'Mitigation' OR 
                label CONTAINS 'Control' OR
                label CONTAINS 'Prevention')
        RETURN mitigation.uri AS uri, 
               mitigation.rdfs__label[0] AS label, 
               CASE WHEN mitigation.rdfs__comment IS NULL THEN '' 
                    ELSE mitigation.rdfs__comment[0] END AS description,
               type(r) AS relationship_type
        """
        return self.execute_query(query, {"attack_pattern": attack_pattern})

    def get_related_concepts(
        self, concept_name: str, max_distance: int = 2
    ) -> List[Dict[str, Any]]:
        """Recupera conceitos relacionados a um conceito específico.

        Args:
            concept_name: Nome ou parte do nome do conceito
            max_distance: Distância máxima no grafo

        Returns:
            Lista de conceitos relacionados com URI, rótulo e descrição
        """
        query = """
        MATCH (c1:Resource:owl__Class)
        WHERE ANY(label IN c1.rdfs__label WHERE label CONTAINS $concept_name)
        MATCH (c1)-[r*1..$max_distance]-(c2:Resource:owl__Class)
        WHERE c1 <> c2
        RETURN DISTINCT c2.uri AS uri, 
               c2.rdfs__label[0] AS label, 
               CASE WHEN c2.rdfs__comment IS NULL THEN '' 
                    ELSE c2.rdfs__comment[0] END AS description
        LIMIT 10
        """
        return self.execute_query(
            query, {"concept_name": concept_name, "max_distance": max_distance}
        )
