import json
import os
import re
import sys
from typing import Optional

import typer
from loguru import logger

from config.settings import LOG_LEVEL
from src.graph_rag.context_builder import ContextBuilder
from src.graph_rag.retriever import GraphRetriever
from src.knowledge_graph.neo4j_manager import Neo4jManager
from src.llm_orchestration.llm_interface import LLMInterface
from src.llm_orchestration.prompt_manager import PromptManager
from src.playbook_generator.formatter import PlaybookFormatter

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
def generate_playbook(
    alert_file: str = typer.Option(..., help="Arquivo JSON contendo dados do alerta"),
    output_file: str = typer.Option(None, help="Arquivo para salvar o playbook gerado"),
    export: bool = typer.Option(False, help="Exportar para HTML após geração"),
    display: bool = typer.Option(False, help="Exibir no terminal após geração"),
):
    """Gera um playbook a partir de um alerta de segurança."""
    try:
        with open(alert_file, "r") as f:
            incident_data = json.load(f)

        logger.info(f"Alerta carregado: {alert_file}")

        neo4j = Neo4jManager()
        graph_retriever = GraphRetriever(neo4j)
        context_builder = ContextBuilder(graph_retriever)
        llm = LLMInterface()
        prompt_manager = PromptManager()
        formatter = PlaybookFormatter()

        logger.info("Recuperando conhecimento contextual do grafo UCO...")
        graph_context = context_builder.build_context_for_incident(incident_data)

        logger.info("Preparando prompt para LLM...")
        prompt_data = prompt_manager.format_playbook_prompt(
            incident_data, graph_context
        )

        logger.info("Gerando playbook com LLM...")
        llm_response = llm.generate(
            prompt=prompt_data["prompt"], system_message=prompt_data["system_message"]
        )

        logger.info("Formatando resposta em playbook estruturado...")
        playbook = formatter.format_playbook(llm_response["content"], incident_data)

        if not output_file:
            from datetime import datetime

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"playbook_{timestamp}.json"

        with open(output_file, "w") as f:
            json.dump(playbook, f, indent=2)
        logger.info(f"Playbook salvo em: {output_file}")

        neo4j.close()

        if export:
            html_output = output_file.replace(".json", ".html")
            export_playbook(playbook_file=output_file, output_file=html_output)

        if display:
            display_playbook(playbook_file=output_file)

    except Exception as e:
        logger.error(f"Erro ao gerar playbook: {str(e)}")


@app.command()
def export_playbook(
    playbook_file: str = typer.Option(..., help="Arquivo JSON do playbook"),
    output_file: Optional[str] = typer.Option(None, help="Arquivo HTML de saída"),
):
    """Exporta um playbook para HTML para visualização."""
    try:
        from src.playbook_generator.html_exporter import PlaybookHTMLExporter

        html_path = PlaybookHTMLExporter.export_to_html(playbook_file, output_file)

        print(f"Playbook exportado para HTML: {html_path}")
        print(
            "Abra este arquivo em seu navegador para visualizar o playbook formatado."
        )

        import webbrowser

        webbrowser.open("file://" + os.path.abspath(html_path))

    except Exception as e:
        logger.error(f"Erro ao exportar playbook: {str(e)}")


@app.command()
def display_playbook(
    playbook_file: str = typer.Option(..., help="Arquivo JSON do playbook"),
):
    """Exibe um playbook formatado no terminal."""
    try:
        with open(playbook_file, "r") as f:
            playbook = json.load(f)

        BOLD = "\033[1m"
        BLUE = "\033[94m"
        GREEN = "\033[92m"
        YELLOW = "\033[93m"
        RED = "\033[91m"
        CYAN = "\033[96m"
        RESET = "\033[0m"

        def clean_markdown(text):
            cleaned = re.sub(r"\*\*(.*?)\*\*", r"\1", text)
            cleaned = cleaned.replace("**", "")
            return cleaned

        print("\n" + "=" * 80)
        print(f"{BOLD}{BLUE}PLAYBOOK DE RESPOSTA A INCIDENTES{RESET}")
        print(
            f"{BOLD}Alerta:{RESET} {playbook['metadata'].get('alert_name', 'Alerta de Segurança')}"
        )
        print("=" * 80)

        print(f"\n{BOLD}{BLUE}METADADOS:{RESET}")
        print(
            f"{BOLD}Tipo de Incidente:{RESET} {playbook['metadata'].get('incident_type', 'Não especificado')}"
        )
        severity = playbook["metadata"].get("severity", "Medium")

        if severity.lower() == "high":
            print(f"{BOLD}Severidade:{RESET} {RED}{severity}{RESET}")
        elif severity.lower() == "medium":
            print(f"{BOLD}Severidade:{RESET} {YELLOW}{severity}{RESET}")
        else:
            print(f"{BOLD}Severidade:{RESET} {GREEN}{severity}{RESET}")

        print(
            f"{BOLD}IP de Origem:{RESET} {playbook['metadata'].get('source_ip', 'N/A')}"
        )
        print(
            f"{BOLD}IP de Destino:{RESET} {playbook['metadata'].get('destination_ip', 'N/A')}"
        )
        print(f"{BOLD}Hostname:{RESET} {playbook['metadata'].get('hostname', 'N/A')}")
        print(f"{BOLD}Usuário:{RESET} {playbook['metadata'].get('user', 'N/A')}")

        section_titles = {
            "resumo": "RESUMO DO INCIDENTE",
            "investigacao": "PASSOS DE INVESTIGAÇÃO",
            "contencao": "PROCEDIMENTOS DE CONTENÇÃO",
            "erradicacao": "PASSOS DE ERRADICAÇÃO",
            "recuperacao": "PROCEDIMENTOS DE RECUPERAÇÃO",
            "prevencao": "LIÇÕES APRENDIDAS E PREVENÇÃO",
        }

        for section_key, section_steps in playbook["sections"].items():
            if section_key.startswith("playbook_") or "_de_" in section_key:
                continue

            section_title = section_titles.get(section_key, section_key.upper())

            print(f"\n{BOLD}{BLUE}{section_title}{RESET}")
            print("-" * 80)

            for i, step in enumerate(section_steps, 1):
                title = step.get("title", step.get("description", ""))
                title = clean_markdown(title)

                print(f"{BOLD}{i}. {title}{RESET}")

                if "content" in step and step["content"] and step["content"] != title:
                    content = clean_markdown(step["content"])
                    if content.startswith(title):
                        content = content[len(title) :].strip()

                    content = re.sub(r"^[\s]*-\s+", "   ", content)
                    content = re.sub(r"\n[\s]*-\s+", "\n   ", content)

                    if content:
                        print(f"   {content}")

                if step.get("commands"):
                    print(f"   {YELLOW}Comandos:{RESET}")
                    for cmd in step.get("commands"):
                        print(f"   $ {cmd}")

                if step.get("subitems"):
                    if step.get("subitems") and not step.get("commands"):
                        print(f"   {CYAN}Detalhes:{RESET}")
                    for subitem in step.get("subitems"):
                        subitem = clean_markdown(subitem)
                        print(f"   • {subitem}")

                print()

        print("=" * 80)

    except Exception as e:
        logger.error(f"Erro ao exibir playbook: {str(e)}")


if __name__ == "__main__":
    app()
