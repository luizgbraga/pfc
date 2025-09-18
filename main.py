import json
import sys

import typer
from loguru import logger

from config.settings import LOG_LEVEL
from src.graph_rag.retriever import GraphRetriever
from src.knowledge_graph.neo4j_manager import Neo4jManager
from src.llm_orchestration.llm_interface import (
    invoke_explorer,
    invoke_planner,
    invoke_playbook,
)
from src.llm_orchestration.llms.openai_llm import OpenAILLM
from src.utils.html import playbook_to_html

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)

app = typer.Typer()


@app.command()
def test_neo4j_connection():
    """Testa a conexão com o Neo4j e exibe informações sobre a ontologia DEF3ND."""
    try:
        neo4j = Neo4jManager()

        logger.info("Consultando observáveis da DEF3ND...")
        observables = neo4j.get_cyber_observables()
        logger.info(f"Encontrados {len(observables)} observáveis")

        for i, obs in enumerate(observables[:5]):
            logger.info(
                f"Observable {i + 1}: {obs['label']} - {obs['description'][:100]}..."
            )

        logger.info("Consultando padrões de ataque...")
        attacks = neo4j.find_attack_patterns()
        logger.info(f"Encontrados {len(attacks)} padrões de ataque")

        for i, attack in enumerate(attacks[:3]):
            logger.info(
                f"Attack {i + 1}: {attack['label']} - {attack['description'][:100]}..."
            )

        neo4j.close()
        logger.info("Conexão Neo4j testada com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao testar Neo4j: {str(e)}")


@app.command()
def explore_ontology(
    search_term: str = typer.Option(..., help="Termo para buscar na ontologia DEF3ND"),
):
    """Explora a ontologia DEF3ND buscando por um termo específico."""
    try:
        neo4j = Neo4jManager()

        # Busca mais abrangente: procura em todos os nós, não só classes
        query = """
        MATCH (n)
        WHERE 
          (n.rdfs__label IS NOT NULL AND ANY(label IN n.rdfs__label WHERE toLower(label) CONTAINS toLower($term)))
          OR (n.uri IS NOT NULL AND toLower(n.uri) CONTAINS toLower($term))
          OR (n.rdfs__comment IS NOT NULL AND ANY(comment IN n.rdfs__comment WHERE comment IS NOT NULL AND toLower(comment) CONTAINS toLower($term)))
        RETURN n.uri AS uri, 
               CASE WHEN n.rdfs__label IS NULL THEN '' ELSE n.rdfs__label[0] END AS label, 
               CASE WHEN n.rdfs__comment IS NULL THEN '' ELSE n.rdfs__comment[0] END AS description
        """

        results = neo4j.execute_query(query, {"term": search_term})

        # Buscar também termos relacionados
        related_terms = {
            "malware": ["malicious", "threat", "virus", "trojan"],
            "attack": ["exploit", "compromise", "intrusion"],
            "breach": ["access", "unauthorized", "infiltration"],
            "software": ["application", "program", "tool"],
            "network": ["communication", "protocol", "infrastructure"],
            "observable": ["event", "activity", "signal"],
            "action": ["operation", "task", "procedure"],
            "pattern": ["behavior", "signature", "characteristic"],
        }

        if not results and search_term.lower() in related_terms:
            alt_terms = related_terms[search_term.lower()]
            print(
                f"Termo '{search_term}' não encontrado diretamente. Buscando termos relacionados: {', '.join(alt_terms)}\n"
            )

            for alt_term in alt_terms:
                alt_results = neo4j.execute_query(query, {"term": alt_term})
                if alt_results:
                    print(f"Resultados para termo relacionado '{alt_term}':")
                    for result in alt_results[:3]:  # Limitando a 3 resultados por termo
                        print(f"- {result['label']}: {result['description'][:100]}...")
                    print()

        if not results:
            print(f"\nNenhum resultado encontrado diretamente para '{search_term}'")
            print(
                "\nDica: Experimente o comando analyze_ontology para explorar a estrutura da ontologia DEF3ND."
            )
        else:
            print(f"\nResultados para '{search_term}' na ontologia DEF3ND:\n")

            for i, result in enumerate(results, 1):
                print(f"{i}. {result['label']}")
                print(f"   URI: {result['uri']}")
                if result["description"]:
                    print(f"   Descrição: {result['description']}")
                print()

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao explorar ontologia: {str(e)}")


@app.command()
def list_key_concepts(
    limit: int = typer.Option(20, help="Número máximo de conceitos a exibir"),
):
    """Lista os principais conceitos na ontologia DEF3ND."""
    try:
        neo4j = Neo4jManager()

        query = """
        MATCH (c:Resource:owl__Class)
        WHERE c.rdfs__label IS NOT NULL
        OPTIONAL MATCH (c)-[r]-()
        WITH c, COUNT(r) AS relation_count
        RETURN c.uri AS uri, c.rdfs__label[0] AS label, 
              CASE WHEN c.rdfs__comment IS NULL THEN '' 
                   ELSE c.rdfs__comment[0] END AS description,
              relation_count AS property_count
        ORDER BY relation_count DESC
        LIMIT $limit
        """

        results = neo4j.execute_query(query, {"limit": limit})

        print(
            "\nPrincipais conceitos na ontologia DEF3ND (com mais relacionamentos):\n"
        )

        for i, result in enumerate(results, 1):
            print(
                f"{i}. {result['label']} ({result['property_count']} relacionamentos)"
            )
            if result["description"]:
                desc = result["description"]
                print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
            print()

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao listar conceitos: {str(e)}")


@app.command()
def list_relationship_types():
    """Lista os tipos de relacionamentos disponíveis na ontologia."""
    try:
        neo4j = Neo4jManager()

        query = """
        MATCH ()-[r]-()
        WITH type(r) AS relType, count(*) AS count
        RETURN relType, count
        ORDER BY count DESC
        LIMIT 20
        """

        results = neo4j.execute_query(query)

        print("\nTipos de relacionamentos na ontologia DEF3ND:\n")

        for result in results:
            print(f"- {result['relType']}: {result['count']} ocorrências")

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao listar tipos de relacionamentos: {str(e)}")


@app.command()
def analyze_ontology():
    """Fornece uma análise da estrutura da ontologia DEF3ND no Neo4j."""
    try:
        neo4j = Neo4jManager()

        # 1. Contar conceitos por namespace/módulo
        namespace_query = """
        MATCH (c:Resource:owl__Class)
        WITH split(c.uri, "#")[0] AS namespace, count(*) AS count
        RETURN namespace, count
        ORDER BY count DESC
        """

        namespace_results = neo4j.execute_query(namespace_query)

        print("\n=== MÓDULOS DA ONTOLOGIA DEF3ND ===\n")
        for result in namespace_results:
            print(f"{result['namespace']}: {result['count']} classes")

        # 2. Examinar a hierarquia de classes
        hierarchy_query = """
        MATCH (c:Resource:owl__Class)-[r:rdfs__subClassOf]->(parent:Resource:owl__Class)
        WITH parent.rdfs__label[0] AS parent_class, count(*) AS child_count
        RETURN parent_class, child_count
        ORDER BY child_count DESC
        LIMIT 10
        """

        hierarchy_results = neo4j.execute_query(hierarchy_query)

        print("\n=== CLASSES PRINCIPAIS (COM MAIS SUBCLASSES) ===\n")
        for result in hierarchy_results:
            print(f"{result['parent_class']}: {result['child_count']} subclasses")

        # 3. Buscar conceitos de segurança
        security_query = """
        MATCH (c:Resource:owl__Class)
        WHERE 
          ANY(label IN c.rdfs__label WHERE 
              label CONTAINS 'Observable' OR
              label CONTAINS 'Action' OR
              label CONTAINS 'Pattern')
        RETURN c.rdfs__label[0] AS label
        LIMIT 20
        """

        security_results = neo4j.execute_query(security_query)

        print("\n=== ALGUNS CONCEITOS RELEVANTES PARA SEGURANÇA ===\n")
        for result in security_results:
            print(f"- {result['label']}")

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao analisar ontologia: {str(e)}")


@app.command()
def list_observables():
    """Lista observáveis disponíveis na ontologia DEF3ND."""
    try:
        neo4j = Neo4jManager()

        query = """
        MATCH (c:Resource:owl__Class)-[:rdfs__subClassOf*]->(parent:Resource:owl__Class)
        WHERE ANY(label IN parent.rdfs__label WHERE label = 'Observable')
        RETURN c.uri AS uri, c.rdfs__label[0] AS label, 
               CASE WHEN c.rdfs__comment IS NULL THEN '' 
                    ELSE c.rdfs__comment[0] END AS description
        """

        results = neo4j.execute_query(query)

        print("\nObserváveis na ontologia DEF3ND (importantes para segurança):\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['label']}")
            if result["description"]:
                desc = result["description"]
                print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
            print()

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao listar observáveis: {str(e)}")


@app.command()
def list_all_nodes():
    """Lista todos os nós do grafo DEF3ND."""
    try:
        neo4j = Neo4jManager()

        query = """
        MATCH (n)
        RETURN n.uri AS uri, n.rdfs__label[0] AS label, 
               CASE WHEN n.rdfs__comment IS NULL THEN '' 
                    ELSE n.rdfs__comment[0] END AS description
        ORDER BY label
        """

        results = neo4j.execute_query(query)

        print("\nTodos os nós no grafo DEF3ND:\n")

        for i, result in enumerate(results, 1):
            print(f"{i}. {result['label']}")
            if result["description"]:
                desc = result["description"]
                print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
            print()

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao listar nós do grafo: {str(e)}")


@app.command()
def list_top_k_nodes(
    k: int = typer.Option(5, help="Número mínimo de relacionamentos para exibir o nó"),
):
    """Lista todos os nós com pelo menos k relacionamentos."""
    try:
        neo4j = Neo4jManager()
        retriever = GraphRetriever(neo4j)
        nodes = retriever.get_top_k_nodes(min_rel_count=k)

        if not nodes:
            print(f"\nNenhum nó encontrado com pelo menos {k} relacionamentos.")
        else:
            print(f"\nNós com pelo menos {k} relacionamentos:\n")
            for i, node in enumerate(nodes, 1):
                print(
                    f"{i}. {node['label']} (URI: {node['uri']}) - {node['rel_count']} relacionamentos"
                )
                if node["description"]:
                    desc = node["description"]
                    print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
                print()

        neo4j.close()
    except Exception as e:
        logger.error(f"Erro ao listar nós com pelo menos {k} relacionamentos: {str(e)}")


@app.command()
def explore_node(
    node_uri: str = typer.Option(None, help="URI do nó a ser explorado"),
    node_label: str = typer.Option(
        None, help="Label do nó a ser explorado (opcional, busca exata)"
    ),
):
    """Exibe todos os nós conectados ao nó especificado pelo URI ou label."""
    try:
        neo4j = Neo4jManager()

        # If label is provided, find the node URI by label (exact match)
        if node_label:
            label_query = """
            MATCH (n)
            WHERE n.rdfs__label[0] = $label
            RETURN n.uri AS uri, n.rdfs__label[0] AS label
            LIMIT 1
            """
            label_result = neo4j.execute_query(label_query, {"label": node_label})
            if not label_result:
                print(f"\nNenhum nó encontrado com o label '{node_label}'.")
                neo4j.close()
                return
            node_uri = label_result[0]["uri"]

        if not node_uri:
            print("\nVocê deve fornecer um URI ou um label de nó.")
            neo4j.close()
            return

        # Only fetch connected nodes that are likely to be concepts (have a label or are owl:Class/Resource)
        query = """
        MATCH (n {uri: $uri})-[r]-(connected)
        WHERE (
            connected.rdfs__label IS NOT NULL AND connected.rdfs__label[0] <> ''
            OR connected:owl__Class
            OR connected:Resource
            OR (connected.rdfs__comment IS NOT NULL AND connected.rdfs__comment[0] <> '')
        )
        AND NOT connected.uri STARTS WITH 'bnode://'
        RETURN type(r) AS rel_type,
               connected.uri AS connected_uri,
               connected.rdfs__label[0] AS label,
               labels(connected) AS node_labels,
               CASE WHEN connected.rdfs__comment IS NULL THEN '' ELSE connected.rdfs__comment[0] END AS description
        ORDER BY rel_type, label
        """

        results = neo4j.execute_query(query, {"uri": node_uri})

        if not results:
            print(f"\nNenhum conceito relacionado encontrado para o nó '{node_uri}'.")
        else:
            print(f"\nConceitos relacionados ao nó '{node_uri}':\n")
            for i, result in enumerate(results, 1):
                label = (
                    result["label"]
                    if result["label"]
                    else ", ".join(result["node_labels"]) or "(sem label)"
                )
                print(
                    f"{i}. [{result['rel_type']}] {label} (URI: {result['connected_uri']})"
                )
                if result["description"]:
                    desc = result["description"]
                    print(f"   {desc[:100]}..." if len(desc) > 100 else f"   {desc}")
                print()

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao explorar conexões do nó: {str(e)}")


@app.command()
def generate_playbook(
    alert: str = typer.Option(None, help="Dados crus do alerta"),
    output_file: str = typer.Option(None, help="Arquivo para salvar o playbook gerado"),
    export: bool = typer.Option(False, help="Exportar para HTML após geração"),
    display: bool = typer.Option(False, help="Exibir no terminal após geração"),
    graph_rag_enabled: bool = typer.Option(
        True, help="Incluir informações do subgrafo no prompt do playbook"
    ),
):
    """Gera um playbook a partir de um alerta de segurança."""
    try:
        incident_data = alert

        neo4j = Neo4jManager()
        graph_retriever = GraphRetriever(neo4j)
        # llm = OllamaLLM()
        llm = OpenAILLM()

        all_nodes = graph_retriever.get_top_k_nodes()
        all_labels = [
            node["label"] for node in all_nodes if "label" in node and node["label"]
        ]

        planner = invoke_planner(
            llm=llm,
            incident_data=str(incident_data),
            all_labels=all_labels,
        )

        print("Nós iniciais escolhidos pelo planejador: ", planner.initial_nodes)

        subgraph = graph_retriever.build_initial_subgraph(planner.initial_nodes)

        if graph_rag_enabled:
            explorer = invoke_explorer(
                llm=llm,
                incident_summary=str(planner.query),
                subgraph=subgraph,
            )

            nodes_to_expand = [node.node_uri for node in explorer.nodes_to_expand]
            for node in explorer.nodes_to_expand:
                print("Expanding node:", node.node_uri)
                print("Reason:", node.reason)

            i = 2
            while len(nodes_to_expand) > 0:
                if i > 10:
                    break
                print(f"{i}) Expanding... ")
                subgraph = graph_retriever.expand_subgraph_from_leaves(
                    subgraph=subgraph,
                    leaf_node_uris=nodes_to_expand,
                )

                explorer = invoke_explorer(
                    llm=llm,
                    incident_summary=str(planner.query),
                    subgraph=subgraph,
                )

                for node in explorer.nodes_to_expand:
                    print("Expanding node:", node.node_uri)
                    print("Reason:", node.reason)

                next_nodes_to_expand = [
                    node.node_uri for node in explorer.nodes_to_expand
                ]
                if set(next_nodes_to_expand) == set(nodes_to_expand):
                    print("No new nodes to expand, stopping.")
                    break
                nodes_to_expand = next_nodes_to_expand
                i += 1

        playbook = invoke_playbook(
            llm=llm,
            incident_data=str(incident_data),
            subgraph=subgraph,
            graph_rag_enabled=graph_rag_enabled,
        )

        if not output_file:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"playbook_{timestamp}.json"

        with open(output_file, "w") as f:
            content = {**playbook.to_dict(), "subgraph": subgraph.to_dict()}
            json.dump(content, f, indent=2)
        logger.info(f"Playbook salvo em: {output_file}")

        if export:
            playbook_to_html(playbook)
            logger.info("Playbook exportado para HTML em: server/static/playbook.html")

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao gerar playbook: {str(e)}")


if __name__ == "__main__":
    app()
