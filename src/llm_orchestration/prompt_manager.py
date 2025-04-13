import os
from typing import Any, Dict

from jinja2 import Template
from loguru import logger

from config.settings import PROMPT_TEMPLATES_DIR


class PromptManager:
    """Gerencia templates de prompt e construção para interação com LLM."""

    def __init__(self, templates_dir: str = None):
        """Inicializa o gerenciador de prompt.

        Args:
            templates_dir: Caminho para o diretório de templates de prompt
        """
        self.templates_dir = templates_dir or PROMPT_TEMPLATES_DIR
        self.ensure_templates_dir()
        self.templates = self._load_templates()

    def ensure_templates_dir(self) -> None:
        """Cria o diretório de templates se não existir e adiciona templates padrão."""
        if not os.path.exists(self.templates_dir):
            os.makedirs(self.templates_dir)
            logger.info(f"Diretório de templates criado: {self.templates_dir}")

            default_template = self._get_default_template()
            template_path = os.path.join(self.templates_dir, "playbook_default.j2")

            with open(template_path, "w") as f:
                f.write(default_template)

            logger.info(f"Template padrão criado: {template_path}")

    def _load_templates(self) -> Dict[str, Template]:
        """Carrega templates Jinja2 do diretório.

        Returns:
            Dicionário de templates Jinja2
        """
        templates = {}

        for filename in os.listdir(self.templates_dir):
            if filename.endswith(".j2"):
                template_name = os.path.splitext(filename)[0]
                template_path = os.path.join(self.templates_dir, filename)

                try:
                    with open(template_path, "r") as f:
                        template_content = f.read()

                    templates[template_name] = Template(template_content)
                    logger.debug(f"Template carregado: {template_name}")

                except Exception as e:
                    logger.error(f"Erro ao carregar template {filename}: {str(e)}")

        if not templates:
            default_content = self._get_default_template()
            templates["playbook_default"] = Template(default_content)
            logger.warning("Nenhum template em disco, usando padrão em memória")

        return templates

    def _get_default_template(self) -> str:
        """Retorna o template padrão para geração de playbook.

        Returns:
            Conteúdo do template padrão
        """
        return """
        {# Template para geração de playbook de segurança #}
        Você é um especialista em resposta a incidentes de segurança cibernética.
        Analise o seguinte alerta de segurança e crie um playbook detalhado de resposta com comandos técnicos específicos e passos concretos.

        ### ALERTA DE SEGURANÇA
        {% if alert_name %}Alerta: {{ alert_name }}{% endif %}
        {% if timestamp %}Timestamp: {{ timestamp }}{% endif %}
        {% if source_ip %}IP de Origem: {{ source_ip }}{% endif %}
        {% if destination_ip %}IP de Destino: {{ destination_ip }}{% endif %}
        {% if hostname %}Hostname: {{ hostname }}{% endif %}
        {% if user %}Usuário: {{ user }}{% endif %}
        {% if command %}Comando Executado: {{ command }}{% endif %}
        {% if severity %}Severidade: {{ severity }}{% endif %}
        {% if description %}Descrição: {{ description }}{% endif %}

        {% if raw_logs %}
        Logs Brutos:
        {{ raw_logs }}
        {% endif %}

        ### CONHECIMENTO CONTEXTUAL DA ONTOLOGIA DE SEGURANÇA
        {{ graph_context }}

        Crie um playbook técnico e detalhado de resposta a incidentes com as seguintes seções:

        1. RESUMO DO INCIDENTE
        - Visão geral do que ocorreu
        - Classificação técnica do incidente
        - Avaliação de severidade
        - Potencial impacto

        2. PASSOS DE INVESTIGAÇÃO
        - Passos iniciais para triagem
        - Coleta de evidências (com comandos específicos)
        - Análise técnica detalhada
        - Comandos e ferramentas específicos para usar
        - Indicadores a procurar

        3. PROCEDIMENTOS DE CONTENÇÃO
        - Ações imediatas para limitar o impacto
        - Isolamento de sistemas afetados
        - Bloqueio de atividade maliciosa
        - Preservação de evidências

        4. PASSOS DE ERRADICAÇÃO
        - Remoção da ameaça
        - Correção de vulnerabilidades exploradas
        - Verificação de comprometimento em outros sistemas

        5. PROCEDIMENTOS DE RECUPERAÇÃO
        - Restauração de sistemas afetados
        - Validação da integridade
        - Retorno às operações normais

        6. LIÇÕES APRENDIDAS E PREVENÇÃO
        - Recomendações para prevenir incidentes similares
        - Melhorias de segurança sugeridas
        - Atualizações de políticas ou procedimentos

        Para cada passo, forneça:
        - Instruções extremamente específicas e acionáveis
        - Comandos exatos quando aplicável (formatados como código)
        - Sintaxe precisa das ferramentas
        - Exemplos concretos
        - Critérios de decisão claros

        Baseie suas recomendações no conhecimento da ontologia de segurança fornecida.
        Seja técnico, detalhado e prático. Evite generalizações vagas.
        """

    def format_playbook_prompt(
        self,
        incident_data: Dict[str, Any],
        graph_context: str,
        template_name: str = "playbook_default",
    ) -> Dict[str, str]:
        """Formata um prompt para geração de playbook.

        Args:
            incident_data: Dicionário com informações do incidente
            graph_context: String de contexto do grafo de conhecimento
            template_name: Nome do template a usar

        Returns:
            Dicionário com mensagem do sistema e prompt
        """
        if template_name not in self.templates:
            logger.warning(f"Template '{template_name}' não encontrado, usando padrão")
            template_name = "playbook_default"

        template_data = {
            "graph_context": graph_context,
            "raw_logs": incident_data.get("logs", ""),
            **incident_data,
        }

        prompt = self.templates[template_name].render(template_data)

        system_message = (
            "Você é CyberPlaybookGPT, um assistente especializado em segurança cibernética "
            "para criar playbooks detalhados de resposta a incidentes baseados em ontologias "
            "de segurança e melhores práticas. Forneça orientações específicas e acionáveis."
        )

        return {"system_message": system_message, "prompt": prompt}
