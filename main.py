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

logger.remove()
logger.add(sys.stderr, level=LOG_LEVEL)

app = typer.Typer()


@app.command()
def test_neo4j_connection():
    """Testa a conexão com o Neo4j e exibe informações sobre a ontologia UCO."""
    try:
        neo4j = Neo4jManager()

        logger.info("Consultando observáveis da UCO...")
        observables = neo4j.get_cyber_observables()
        logger.info(f"Encontrados {len(observables)} observáveis")

        for i, obs in enumerate(observables[:5]):
            logger.info(
                f"Observable {i+1}: {obs['label']} - {obs['description'][:100]}..."
            )

        logger.info("Consultando padrões de ataque...")
        attacks = neo4j.find_attack_patterns()
        logger.info(f"Encontrados {len(attacks)} padrões de ataque")

        for i, attack in enumerate(attacks[:3]):
            logger.info(
                f"Attack {i+1}: {attack['label']} - {attack['description'][:100]}..."
            )

        neo4j.close()
        logger.info("Conexão Neo4j testada com sucesso!")

    except Exception as e:
        logger.error(f"Erro ao testar Neo4j: {str(e)}")


@app.command()
def explore_ontology(
    search_term: str = typer.Option(..., help="Termo para buscar na ontologia UCO"),
):
    """Explora a ontologia UCO buscando por um termo específico."""
    try:
        neo4j = Neo4jManager()

        # Busca mais abrangente (labels, comentários e URIs)
        query = """
        MATCH (c:Resource:owl__Class)
        WHERE 
          ANY(label IN c.rdfs__label WHERE toLower(label) CONTAINS toLower($term))
          OR c.uri CONTAINS toLower($term)
          OR ANY(comment IN c.rdfs__comment WHERE 
                comment IS NOT NULL AND toLower(comment) CONTAINS toLower($term))
        RETURN c.uri AS uri, c.rdfs__label[0] AS label, 
              CASE WHEN c.rdfs__comment IS NULL THEN '' 
                   ELSE c.rdfs__comment[0] END AS description
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
                "\nDica: Experimente o comando analyze_ontology para explorar a estrutura da ontologia UCO."
            )
        else:
            print(f"\nResultados para '{search_term}' na ontologia UCO:\n")

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
    """Lista os principais conceitos na ontologia UCO."""
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

        print("\nPrincipais conceitos na ontologia UCO (com mais relacionamentos):\n")

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

        print("\nTipos de relacionamentos na ontologia UCO:\n")

        for result in results:
            print(f"- {result['relType']}: {result['count']} ocorrências")

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao listar tipos de relacionamentos: {str(e)}")


@app.command()
def analyze_ontology():
    """Fornece uma análise da estrutura da ontologia UCO no Neo4j."""
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

        print("\n=== MÓDULOS DA ONTOLOGIA UCO ===\n")
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
    """Lista observáveis disponíveis na ontologia UCO."""
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

        print("\nObserváveis na ontologia UCO (importantes para segurança):\n")

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
    """Lista todos os nós do grafo UCO."""
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

        print("\nTodos os nós no grafo UCO:\n")

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
def generate_playbook(
    alert: str = typer.Option(None, help="Dados crus do alerta"),
    output_file: str = typer.Option(None, help="Arquivo para salvar o playbook gerado"),
    export: bool = typer.Option(False, help="Exportar para HTML após geração"),
    display: bool = typer.Option(False, help="Exibir no terminal após geração"),
):
    """Gera um playbook a partir de um alerta de segurança."""
    try:
        incident_data = alert

        neo4j = Neo4jManager()
        graph_retriever = GraphRetriever(neo4j)
        # llm = OllamaLLM()
        llm = OpenAILLM()

        planner = invoke_planner(
            llm=llm,
            incident_data=str(incident_data),
        )

        subgraph = graph_retriever.build_initial_subgraph(planner.initial_nodes)

        explorer = invoke_explorer(
            llm=llm,
            incident_data=str(incident_data),
            subgraph=subgraph,
        )

        nodes_to_expand = [node.node_uri for node in explorer.nodes_to_expand]

        i = 1
        while len(nodes_to_expand) > 0:
            if i > 10:
                break
            print(f"{i}) Expanding... ", nodes_to_expand)
            subgraph = graph_retriever.expand_subgraph_from_leaves(
                subgraph=subgraph,
                leaf_node_uris=nodes_to_expand,
            )

            explorer = invoke_explorer(
                llm=llm,
                incident_data=str(incident_data),
                subgraph=subgraph,
            )

            next_nodes_to_expand = [node.node_uri for node in explorer.nodes_to_expand]
            if set(next_nodes_to_expand) == set(nodes_to_expand):
                print("No new nodes to expand, stopping.")
                break
            nodes_to_expand = next_nodes_to_expand
            i += 1

        playbook = invoke_playbook(
            llm=llm,
            incident_data=str(incident_data),
            subgraph=subgraph,
        )

        if not output_file:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"playbook_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(playbook.to_dict(), f, indent=2)
        logger.info(f"Playbook salvo em: {output_file}")

        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao gerar playbook: {str(e)}")


if __name__ == "__main__":
    app()
