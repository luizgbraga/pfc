import json
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

        # Testar consultas à UCO
        logger.info("Consultando observáveis da UCO...")
        observables = neo4j.get_cyber_observables()
        logger.info(f"Encontrados {len(observables)} observáveis")

        # Exibir alguns exemplos
        for i, obs in enumerate(observables[:5]):
            logger.info(
                f"Observable {i+1}: {obs['label']} - {obs['description'][:100]}..."
            )

        # Testar busca de padrões de ataque
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
async def generate_playbook(
    alert_file: str = typer.Option(..., help="Arquivo JSON contendo dados do alerta"),
    output_file: Optional[str] = typer.Option(
        None, help="Arquivo para salvar o playbook gerado"
    ),
):
    """Gera um playbook a partir de um alerta de segurança."""
    try:
        # Carregar dados do alerta
        with open(alert_file, "r") as f:
            incident_data = json.load(f)

        logger.info(f"Alerta carregado: {alert_file}")

        # Inicializar componentes
        neo4j = Neo4jManager()
        graph_retriever = GraphRetriever(neo4j)
        context_builder = ContextBuilder(graph_retriever)
        llm = LLMInterface()
        prompt_manager = PromptManager()
        formatter = PlaybookFormatter()

        # Construir contexto do grafo
        logger.info("Recuperando conhecimento contextual do grafo UCO...")
        graph_context = context_builder.build_context_for_incident(incident_data)

        # Formatar prompt para LLM
        logger.info("Preparando prompt para LLM...")
        prompt_data = prompt_manager.format_playbook_prompt(
            incident_data, graph_context
        )

        # Gerar playbook com LLM
        logger.info("Gerando playbook com LLM...")
        llm_response = await llm.generate(
            prompt=prompt_data["prompt"], system_message=prompt_data["system_message"]
        )

        # Formatar resultado em playbook estruturado
        logger.info("Formatando resposta em playbook estruturado...")
        playbook = formatter.format_playbook(llm_response["content"], incident_data)

        # Salvar ou exibir resultado
        if output_file:
            with open(output_file, "w") as f:
                json.dump(playbook, f, indent=2)
            logger.info(f"Playbook salvo em: {output_file}")
        else:
            # Exibir resumo
            print("\n" + "=" * 50)
            print(
                f"PLAYBOOK PARA: {incident_data.get('alert_name', 'Alerta de Segurança')}"
            )
            print("=" * 50)

            # Exibir cada seção
            for section_name, steps in playbook["sections"].items():
                print(f"\n## {section_name.upper()}")
                for step in steps:
                    print(f"- {step['description']}")
                    if step["commands"]:
                        print("  Comandos:")
                        for cmd in step["commands"]:
                            print(f"    $ {cmd}")

            print("\n" + "=" * 50)

        # Limpar
        neo4j.close()

    except Exception as e:
        logger.error(f"Erro ao gerar playbook: {str(e)}")


@app.command()
def explore_ontology(
    search_term: str = typer.Option(..., help="Termo para buscar na ontologia UCO"),
):
    """Explora a ontologia UCO buscando por um termo específico."""
    try:
        neo4j = Neo4jManager()

        # Consulta para encontrar classes relacionadas ao termo
        query = """
        MATCH (c:Resource:owl__Class)
        WHERE ANY(label IN c.rdfs__label WHERE toLower(label) CONTAINS toLower($term))
        RETURN c.uri AS uri, c.rdfs__label[0] AS label, 
               CASE WHEN c.rdfs__comment IS NULL THEN '' 
                    ELSE c.rdfs__comment[0] END AS description
        LIMIT 10
        """

        results = neo4j.execute_query(query, {"term": search_term})

        if not results:
            print(f"Nenhum resultado encontrado para '{search_term}'")
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


if __name__ == "__main__":
    app()
