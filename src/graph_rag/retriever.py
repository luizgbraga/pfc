from dataclasses import dataclass
from typing import Any, Dict, List

from loguru import logger

from src.knowledge_graph.neo4j_manager import Neo4jManager

MAX_DEPTH = 0


@dataclass
class Subgraph:
    nodes: Dict[str, Dict[str, Any]]
    relationships: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        """Converte o subgrafo para um dicionário.

        Returns:
            Dicionário representando o subgrafo
        """
        return {
            "nodes": self.nodes,
            "relationships": self.relationships,
        }


class GraphRetriever:
    """Recupera informações relevantes do grafo de conhecimento DEF3ND."""

    def __init__(self, neo4j_manager: Neo4jManager):
        """Inicializa o recuperador de grafo.

        Args:
            neo4j_manager: Instância de Neo4jManager para operações no grafo
        """
        self.neo4j = neo4j_manager

    def get_all_nodes(self) -> List[Dict[str, Any]]:
        """Recupera todos os nós do grafo que possuem rdfs__label e não são blank nodes.

        Returns:
            Lista de dicionários representando os nós
        """
        query = """
        MATCH (n)
        WHERE n.rdfs__label IS NOT NULL 
        AND size(n.rdfs__label) > 0 
        AND NOT n.uri STARTS WITH 'bnode://'
        RETURN n.uri AS uri, n.rdfs__label[0] AS label, 
               CASE WHEN n.rdfs__comment IS NULL THEN '' 
                    ELSE n.rdfs__comment[0] END AS description
        ORDER BY label
        """
        return self.neo4j.execute_query(query)

    def get_top_k_nodes(self, min_rel_count: int = 5) -> List[Dict[str, Any]]:
        """Retorna os nós que possuem mais de min_rel_count relacionamentos (grau de saída).

        Args:
            min_rel_count: Número mínimo de relacionamentos para considerar o nó relevante

        Returns:
            Lista de dicionários representando os nós
        """
        query = """
        MATCH (n)
        WHERE n.rdfs__label IS NOT NULL 
        AND size(n.rdfs__label) > 0 
        AND NOT n.uri STARTS WITH 'bnode://'
        OPTIONAL MATCH (n)-[r]->()
        WITH n, count(r) AS rel_count
        WHERE rel_count > $min_rel_count
        RETURN n.uri AS uri, n.rdfs__label[0] AS label, 
            CASE WHEN n.rdfs__comment IS NULL THEN '' 
                    ELSE n.rdfs__comment[0] END AS description,
            rel_count
        ORDER BY rel_count DESC, label
        """
        return self.neo4j.execute_query(query, {"min_rel_count": min_rel_count})

    def build_initial_subgraph(self, node_labels: List[str]) -> Subgraph:
        """Constrói o subgrafo inicial do DEF3ND contendo todos os nós da lista expandidos com DFS até MAX_DEPTH.

        Args:
            node_labels: Lista de labels dos nós para incluir no subgrafo

        Returns:
            Subgraph contendo nós, relacionamentos e nós folha
        """
        try:
            # Buscar todos os nós que correspondem aos labels (filtrar blank nodes)
            initial_nodes = []
            for label in node_labels:
                query = """
                MATCH (n)
                WHERE ANY(rdfs_label IN n.rdfs__label WHERE rdfs_label = $label)
                AND NOT n.uri STARTS WITH 'bnode://'
                AND n.rdfs__label IS NOT NULL
                AND size(n.rdfs__label) > 0
                RETURN n.uri AS uri, n.rdfs__label AS labels, 
                       CASE WHEN n.rdfs__comment IS NULL THEN [] 
                            ELSE n.rdfs__comment END AS comments
                """
                results = self.neo4j.execute_query(query, {"label": label})
                if not results:
                    # Se não encontrar correspondência exata, tentar busca por contém
                    query = """
                    MATCH (n)
                    WHERE ANY(rdfs_label IN n.rdfs__label WHERE rdfs_label CONTAINS $label)
                    AND NOT n.uri STARTS WITH 'bnode://'
                    AND n.rdfs__label IS NOT NULL
                    AND size(n.rdfs__label) > 0
                    RETURN n.uri AS uri, n.rdfs__label AS labels, 
                           CASE WHEN n.rdfs__comment IS NULL THEN [] 
                                ELSE n.rdfs__comment END AS comments
                    LIMIT 1
                    """
                    results = self.neo4j.execute_query(query, {"label": label})
                initial_nodes.extend(results)

            if not initial_nodes:
                logger.warning(f"Nenhum nó encontrado para os labels: {node_labels}")
                return Subgraph(nodes={}, relationships=[])

            # URIs dos nós iniciais
            initial_uris = [node["uri"] for node in initial_nodes]

            # Expandir cada nó inicial com DFS até MAX_DEPTH
            subgraph = self._expand_nodes_dfs(initial_uris, MAX_DEPTH)

            logger.info(
                f"Subgrafo inicial construído com {len(subgraph.nodes)} nós e {len(subgraph.relationships)} relacionamentos"
            )
            return subgraph

        except Exception as e:
            logger.error(f"Erro ao construir subgrafo inicial: {str(e)}")
            return Subgraph(nodes={}, relationships=[])

    def expand_subgraph_from_leaves(
        self, subgraph: Subgraph, leaf_node_uris: List[str]
    ) -> Subgraph:
        """Expande o subgrafo existente a partir dos nós folha especificados.

        Args:
            subgraph: Subgrafo existente retornado por build_initial_subgraph ou chamadas anteriores
            leaf_node_uris: Lista de URIs dos nós folha para expandir

        Returns:
            Subgrafo expandido com os novos nós e relacionamentos
        """
        try:
            # Expandir os nós folha selecionados
            expansion = self._expand_nodes_dfs(
                leaf_node_uris, 1
            )  # Expandir apenas 1 nível por vez

            # Mesclar o subgrafo existente com a expansão
            merged_subgraph = self._merge_subgraphs(subgraph, expansion)

            logger.info(
                f"Subgrafo expandido: {len(merged_subgraph.nodes)} nós, {len(merged_subgraph.relationships)} relacionamentos"
            )
            return merged_subgraph

        except Exception as e:
            logger.error(f"Erro ao expandir subgrafo: {str(e)}")
            return subgraph

    def _expand_nodes_dfs(self, start_uris: List[str], max_depth: int) -> Subgraph:
        """Expande nós usando DFS até a profundidade máxima especificada.

        Args:
            start_uris: Lista de URIs dos nós iniciais
            max_depth: Profundidade máxima para expansão

        Returns:
            Subgraph com nós, relacionamentos e nós folha
        """
        nodes = {}
        relationships = []
        visited = set()

        # Inicializar com os nós iniciais na profundidade 0
        nodes_by_depth = {0: start_uris.copy()}

        # Adicionar nós iniciais
        for uri in start_uris:
            if uri not in visited:
                visited.add(uri)

                # Buscar informações do nó inicial
                node_query = """
                MATCH (n)
                WHERE n.uri = $uri 
                AND NOT n.uri STARTS WITH 'bnode://'
                AND n.rdfs__label IS NOT NULL 
                AND size(n.rdfs__label) > 0
                RETURN n.uri AS uri, n.rdfs__label AS labels,
                       CASE WHEN n.rdfs__comment IS NULL THEN []
                            ELSE n.rdfs__comment END AS comments
                """
                node_results = self.neo4j.execute_query(node_query, {"uri": uri})

                if node_results:
                    node_data = node_results[0]
                    nodes[uri] = {
                        "uri": node_data["uri"],
                        "labels": node_data["labels"] or [],
                        "comments": node_data["comments"] or [],
                        "depth": 0,
                    }

        # Expandir nível por nível
        for depth in range(max_depth):
            current_level_uris = nodes_by_depth.get(depth, [])
            if not current_level_uris:
                break

            next_level_uris = []

            for uri in current_level_uris:
                # Buscar todos os relacionamentos (entrada e saída, filtrar blank nodes dos targets)
                rel_query = """
                MATCH (start)-[r]-(target)
                WHERE start.uri = $uri
                AND NOT target.uri STARTS WITH 'bnode://'
                AND target.rdfs__label IS NOT NULL
                AND size(target.rdfs__label) > 0
                RETURN target.uri AS target_uri, type(r) AS relationship_type,
                       target.rdfs__label AS target_labels,
                       CASE WHEN target.rdfs__comment IS NULL THEN []
                            ELSE target.rdfs__comment END AS target_comments,
                       CASE WHEN start.uri = $uri THEN 'out' ELSE 'in' END AS direction
                LIMIT 40
                """
                rel_results = self.neo4j.execute_query(rel_query, {"uri": uri})

                for rel in rel_results:
                    target_uri = rel["target_uri"]
                    # Adicionar relacionamento (direção: source sempre o nó atual, target o outro)
                    if rel["direction"] == "out":
                        relationships.append(
                            {
                                "source": uri,
                                "target": target_uri,
                                "type": rel["relationship_type"],
                            }
                        )
                    else:
                        relationships.append(
                            {
                                "source": target_uri,
                                "target": uri,
                                "type": rel["relationship_type"],
                            }
                        )

                    # Adicionar nó target se ainda não visitado
                    if target_uri not in visited:
                        visited.add(target_uri)
                        next_level_uris.append(target_uri)

                        # Adicionar o nó target com a profundidade correta (depth + 1)
                        nodes[target_uri] = {
                            "uri": target_uri,
                            "labels": rel["target_labels"] or [],
                            "comments": rel["target_comments"] or [],
                            "depth": depth + 1,
                        }

            # Preparar para o próximo nível
            if next_level_uris:
                nodes_by_depth[depth + 1] = next_level_uris

        return Subgraph(nodes=nodes, relationships=relationships)

    def _merge_subgraphs(self, subgraph1: Subgraph, subgraph2: Subgraph) -> Subgraph:
        """Mescla dois subgrafos em um único subgrafo.

        Args:
            subgraph1: Primeiro subgrafo
            subgraph2: Segundo subgrafo

        Returns:
            Subgrafo mesclado
        """
        # Mesclar nós
        merged_nodes = subgraph1.nodes.copy()
        merged_nodes.update(subgraph2.nodes)

        # Mesclar relacionamentos (evitar duplicatas)
        merged_relationships = subgraph1.relationships.copy()
        existing_rels = {
            (rel["source"], rel["target"], rel["type"]) for rel in merged_relationships
        }

        for rel in subgraph2.relationships:
            rel_key = (rel["source"], rel["target"], rel["type"])
            if rel_key not in existing_rels:
                merged_relationships.append(rel)
                existing_rels.add(rel_key)

        return Subgraph(
            nodes=merged_nodes,
            relationships=merged_relationships,
        )

    def retrieve_for_incident(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Recupera contexto relevante do grafo de conhecimento para um incidente de segurança.

        Args:
            incident_data: Dicionário contendo informações do incidente

        Returns:
            Dicionário com informações de contexto recuperadas
        """
        try:
            incident_type = self._determine_incident_type(incident_data)
            entities = self._extract_entities(incident_data)

            context = {
                "incident_type": incident_type,
                "related_attack_patterns": self._get_attack_patterns(incident_type),
                "observables": self._get_related_observables(entities),
                "mitigations": self._get_mitigations(incident_type),
                "related_concepts": self._get_related_concepts(incident_type),
            }

            logger.info(f"Contexto recuperado para incidente: {incident_type}")
            return context

        except Exception as e:
            logger.error(f"Erro ao recuperar contexto do grafo: {str(e)}")
            return {}

    def _determine_incident_type(self, incident_data: Dict[str, Any]) -> str:
        """Determina o tipo de incidente baseado nos dados recebidos.

        Args:
            incident_data: Dados do incidente

        Returns:
            String representando o tipo de incidente
        """
        if "incident_type" in incident_data:
            return incident_data["incident_type"]

        if "alert_name" in incident_data:
            alert_name = incident_data["alert_name"].lower()

            if any(
                term in alert_name
                for term in [
                    "bruteforce",
                    "brute force",
                    "bruteforcing",
                    "credential stuffing",
                ]
            ):
                return "Brute Force Attack"

            if any(
                term in alert_name
                for term in ["malware", "virus", "ransomware", "trojan"]
            ):
                return "Malware Infection"

            if any(
                term in alert_name
                for term in ["lateral movement", "privilege escalation"]
            ):
                return "Lateral Movement"

            if any(
                term in alert_name
                for term in ["data exfiltration", "data leak", "data theft"]
            ):
                return "Data Exfiltration"

            if any(
                term in alert_name for term in ["phishing", "spear phishing", "whaling"]
            ):
                return "Phishing Attack"

        if "command" in incident_data:
            command = incident_data["command"].lower()

            if any(term in command for term in ["chmod 777", "chmod +s", "chmod a+x"]):
                return "Privilege Escalation"

            if any(term in command for term in ["wget", "curl", "nc ", "netcat"]):
                return "Malicious File Download"

        return "Unknown Security Incident"

    def _extract_entities(self, incident_data: Dict[str, Any]) -> Dict[str, List[str]]:
        """Extrai entidades relevantes do incidente.

        Args:
            incident_data: Dados do incidente

        Returns:
            Dicionário de tipos de entidades para seus valores
        """
        entities = {
            "ip_addresses": [],
            "hostnames": [],
            "users": [],
            "processes": [],
            "files": [],
            "commands": [],
        }

        # Extrair IPs
        for field in [
            "source_ip",
            "destination_ip",
            "src_ip",
            "dst_ip",
            "ipaddress",
            "ip",
        ]:
            if field in incident_data and incident_data[field]:
                entities["ip_addresses"].append(incident_data[field])

        # Extrair hostnames
        for field in [
            "hostname",
            "host",
            "source_host",
            "destination_host",
            "computer_name",
        ]:
            if field in incident_data and incident_data[field]:
                entities["hostnames"].append(incident_data[field])

        # Extrair usuários
        for field in ["user", "username", "account", "user_id"]:
            if field in incident_data and incident_data[field]:
                entities["users"].append(incident_data[field])

        # Extrair processos
        for field in ["process", "process_name", "image", "parent_process"]:
            if field in incident_data and incident_data[field]:
                entities["processes"].append(incident_data[field])

        # Extrair arquivos
        for field in ["file", "filename", "filepath", "file_path"]:
            if field in incident_data and incident_data[field]:
                entities["files"].append(incident_data[field])

        # Extrair comandos
        if "command" in incident_data and incident_data["command"]:
            entities["commands"].append(incident_data["command"])

        return entities

    def _get_attack_patterns(self, incident_type: str) -> List[Dict[str, Any]]:
        """Recupera padrões de ataque relacionados ao tipo de incidente.

        Args:
            incident_type: Tipo de incidente

        Returns:
            Lista de padrões de ataque
        """
        search_terms = []

        incident_term_map = {
            "Brute Force Attack": ["Brute", "Password", "Credential"],
            "Malware Infection": ["Malware", "Malicious", "Infection"],
            "Lateral Movement": ["Lateral", "Movement", "Access"],
            "Data Exfiltration": ["Exfiltration", "Data", "Theft"],
            "Phishing Attack": ["Phishing", "Social", "Engineering"],
            "Privilege Escalation": ["Privilege", "Escalation", "Permission"],
            "Malicious File Download": ["Download", "Payload", "Remote"],
        }

        if incident_type in incident_term_map:
            search_terms = incident_term_map[incident_type]
        else:
            search_terms = incident_type.split()

        attack_patterns = []
        for term in search_terms:
            query = """
            MATCH (c:Resource:owl__Class)
            WHERE ANY(label IN c.rdfs__label WHERE label CONTAINS $term)
            AND (
              ANY(label IN c.rdfs__label WHERE 
                  label CONTAINS 'Attack' OR 
                  label CONTAINS 'Threat' OR
                  label CONTAINS 'Malicious')
              OR c.uri CONTAINS 'action' OR c.uri CONTAINS 'pattern'
            )
            RETURN c.uri AS uri, 
                   c.rdfs__label[0] AS label, 
                   CASE WHEN c.rdfs__comment IS NULL THEN '' 
                        ELSE c.rdfs__comment[0] END AS description
            LIMIT 5
            """
            patterns = self.neo4j.execute_query(query, {"term": term})
            attack_patterns.extend(patterns)

        unique_patterns = []
        uris = set()
        for pattern in attack_patterns:
            if pattern["uri"] not in uris:
                unique_patterns.append(pattern)
                uris.add(pattern["uri"])

        return unique_patterns

    def _get_related_observables(
        self, entities: Dict[str, List[str]]
    ) -> List[Dict[str, Any]]:
        """Recupera observáveis relacionados às entidades do incidente.

        Args:
            entities: Dicionário de entidades extraídas

        Returns:
            Lista de observáveis relevantes
        """
        entity_type_map = {
            "ip_addresses": ["IPAddress", "NetworkAddress"],
            "hostnames": ["Hostname", "Device", "Computer"],
            "users": ["Account", "User", "Identity"],
            "processes": ["Process", "Application"],
            "files": ["File", "Content"],
            "commands": ["Action", "Command", "Process"],
        }

        observables = []
        for entity_type, values in entities.items():
            if not values:
                continue

            search_classes = entity_type_map.get(entity_type, [])
            for search_class in search_classes:
                query = """
                MATCH (o:Resource:owl__Class)
                WHERE ANY(label IN o.rdfs__label WHERE label CONTAINS $search_class)
                RETURN o.uri AS uri, 
                       o.rdfs__label[0] AS label, 
                       CASE WHEN o.rdfs__comment IS NULL THEN '' 
                            ELSE o.rdfs__comment[0] END AS description,
                       $entity_type AS entity_type,
                       $entity_values AS entity_values
                LIMIT 3
                """
                results = self.neo4j.execute_query(
                    query,
                    {
                        "search_class": search_class,
                        "entity_type": entity_type,
                        "entity_values": values,
                    },
                )
                observables.extend(results)

        unique_observables = []
        uris = set()
        for observable in observables:
            if observable["uri"] not in uris:
                unique_observables.append(observable)
                uris.add(observable["uri"])

        return unique_observables

    def _get_mitigations(self, incident_type: str) -> List[Dict[str, Any]]:
        """Recupera mitigações relacionadas ao tipo de incidente.

        Args:
            incident_type: Tipo de incidente

        Returns:
            Lista de mitigações
        """
        # Primeiro obtém padrões de ataque relacionados ao incidente
        attack_patterns = self._get_attack_patterns(incident_type)

        # Depois busca mitigações para esses padrões
        mitigations = []
        for pattern in attack_patterns:
            pattern_label = pattern["label"]

            query = """
            MATCH (attack:Resource:owl__Class)-[r]-(mitigation:Resource:owl__Class)
            WHERE ANY(label IN attack.rdfs__label WHERE label CONTAINS $pattern_label)
            AND (
              ANY(label IN mitigation.rdfs__label WHERE 
                  label CONTAINS 'Mitigation' OR 
                  label CONTAINS 'Control' OR
                  label CONTAINS 'Prevention')
              OR mitigation.uri CONTAINS 'action'
            )
            RETURN DISTINCT mitigation.uri AS uri, 
                   mitigation.rdfs__label[0] AS label, 
                   CASE WHEN mitigation.rdfs__comment IS NULL THEN '' 
                        ELSE mitigation.rdfs__comment[0] END AS description,
                   $related_to AS related_to
            LIMIT 3
            """
            results = self.neo4j.execute_query(
                query, {"pattern_label": pattern_label, "related_to": pattern_label}
            )

            # Se não encontrar, busca pelo termo de mitigação geral
            if not results:
                mitigation_terms = ["Prevent", "Block", "Detect", "Monitor", "Control"]
                for term in mitigation_terms:
                    query = """
                    MATCH (c:Resource:owl__Class)
                    WHERE ANY(label IN c.rdfs__label WHERE 
                             label CONTAINS $term OR 
                             label CONTAINS 'Mitigation' OR
                             label CONTAINS 'Response')
                    RETURN c.uri AS uri, 
                           c.rdfs__label[0] AS label, 
                           CASE WHEN c.rdfs__comment IS NULL THEN '' 
                                ELSE c.rdfs__comment[0] END AS description,
                           $related_to AS related_to
                    LIMIT 2
                    """
                    term_results = self.neo4j.execute_query(
                        query, {"term": term, "related_to": pattern_label}
                    )
                    if term_results:
                        results.extend(term_results)

            mitigations.extend(results)

        unique_mitigations = []
        uris = set()
        for mitigation in mitigations:
            if mitigation["uri"] not in uris:
                unique_mitigations.append(mitigation)
                uris.add(mitigation["uri"])

        return unique_mitigations

    def _get_related_concepts(self, incident_type: str) -> List[Dict[str, Any]]:
        """Recupera conceitos gerais relacionados ao incidente.

        Args:
            incident_type: Tipo de incidente

        Returns:
            Lista de conceitos relacionados
        """
        # Extrair termos do tipo de incidente
        terms = incident_type.split()

        related_concepts = []
        for term in terms:
            if len(term) <= 3:  # Ignorar termos muito curtos
                continue

            query = """
            MATCH (c:Resource:owl__Class)
            WHERE ANY(label IN c.rdfs__label WHERE label CONTAINS $term)
            RETURN c.uri AS uri, 
                   c.rdfs__label[0] AS label, 
                   CASE WHEN c.rdfs__comment IS NULL THEN '' 
                        ELSE c.rdfs__comment[0] END AS description
            LIMIT 5
            """
            results = self.neo4j.execute_query(query, {"term": term})
            related_concepts.extend(results)

        unique_concepts = []
        uris = set()
        for concept in related_concepts:
            if concept["uri"] not in uris:
                unique_concepts.append(concept)
                uris.add(concept["uri"])

        return unique_concepts
