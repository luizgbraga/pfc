from typing import Any, Dict, List

from loguru import logger

from src.knowledge_graph.neo4j_manager import Neo4jManager


class GraphRetriever:
    """Recupera informações relevantes do grafo de conhecimento UCO."""

    def __init__(self, neo4j_manager: Neo4jManager):
        """Inicializa o recuperador de grafo.

        Args:
            neo4j_manager: Instância de Neo4jManager para operações no grafo
        """
        self.neo4j = neo4j_manager

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

        # Heurísticas para determinar o tipo baseado no conteúdo
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
        # Converter tipo de incidente para termos de busca
        search_terms = []

        # Mapear tipos de incidente para termos relevantes na UCO
        incident_term_map = {
            "Brute Force Attack": ["Brute", "Password", "Credential"],
            "Malware Infection": ["Malware", "Malicious", "Infection"],
            "Lateral Movement": ["Lateral", "Movement", "Access"],
            "Data Exfiltration": ["Exfiltration", "Data", "Theft"],
            "Phishing Attack": ["Phishing", "Social", "Engineering"],
            "Privilege Escalation": ["Privilege", "Escalation", "Permission"],
            "Malicious File Download": ["Download", "Payload", "Remote"],
        }

        # Obter termos para o tipo de incidente
        if incident_type in incident_term_map:
            search_terms = incident_term_map[incident_type]
        else:
            # Usar os termos do próprio tipo de incidente
            search_terms = incident_type.split()

        # Buscar padrões de ataque para cada termo
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

        # Remover duplicados (baseado no URI)
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
        # Mapear tipos de entidades para classes na UCO
        entity_type_map = {
            "ip_addresses": ["IPAddress", "NetworkAddress"],
            "hostnames": ["Hostname", "Device", "Computer"],
            "users": ["Account", "User", "Identity"],
            "processes": ["Process", "Application"],
            "files": ["File", "Content"],
            "commands": ["Action", "Command", "Process"],
        }

        # Buscar observáveis para cada tipo de entidade
        observables = []
        for entity_type, values in entities.items():
            if not values:
                continue

            # Obter classes de observáveis relacionadas
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

        # Remover duplicados (baseado no URI)
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

            # Buscar mitigações relacionadas
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

        # Remover duplicados
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

        # Remover duplicados
        unique_concepts = []
        uris = set()
        for concept in related_concepts:
            if concept["uri"] not in uris:
                unique_concepts.append(concept)
                uris.add(concept["uri"])

        return unique_concepts
