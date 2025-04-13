# src/playbook_generator/formatter.py
import re
from datetime import datetime
from typing import Any, Dict, List

from loguru import logger


class PlaybookFormatter:
    """Formata e estrutura playbooks gerados pelo LLM."""

    def __init__(self):
        """Inicializa o formatador de playbooks."""
        pass

    def format_playbook(
        self, llm_response: str, incident_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Formata a resposta do LLM em um playbook estruturado.

        Args:
            llm_response: Resposta de texto gerada pelo LLM
            incident_data: Dados originais do incidente

        Returns:
            Playbook estruturado como dicionário
        """
        sections = self._extract_sections(llm_response)

        processed_sections = {}
        for section_name, section_content in sections.items():
            processed_sections[section_name] = self._process_section(
                section_name, section_content
            )

        metadata = self._create_metadata(incident_data)

        playbook = {
            "metadata": metadata,
            "sections": processed_sections,
            "references": self._extract_references(llm_response),
            "original_response": llm_response,
        }

        logger.info(f"Playbook formatado com {len(processed_sections)} seções")
        return playbook

    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extrai seções principais do texto do playbook.

        Args:
            text: Texto do playbook gerado pelo LLM

        Returns:
            Dicionário de nome da seção para conteúdo
        """
        sections = {}

        section_pattern = r"###\s*(?:\d+\.)?\s*([^#\n]+)(?:\n|\r\n?)(.*?)(?=###|\Z)"

        matches = re.finditer(section_pattern, text, re.DOTALL)

        section_mapping = {
            "RESUMO DO INCIDENTE": "resumo",
            "PASSOS DE INVESTIGAÇÃO": "investigacao",
            "PROCEDIMENTOS DE CONTENÇÃO": "contencao",
            "PASSOS DE ERRADICAÇÃO": "erradicacao",
            "PROCEDIMENTOS DE RECUPERAÇÃO": "recuperacao",
            "LIÇÕES APRENDIDAS": "prevencao",
        }

        for match in matches:
            section_title = match.group(1).strip().upper()
            section_content = match.group(2).strip()

            section_key = None
            for pattern, key in section_mapping.items():
                if pattern in section_title:
                    section_key = key
                    break

            if not section_key:
                section_key = section_title.lower().replace(" ", "_")

            sections[section_key] = section_content

        return sections

    def _process_section(
        self, section_name: str, section_content: str
    ) -> List[Dict[str, Any]]:
        """Processa o conteúdo de uma seção para extrair passos estruturados.

        Args:
            section_name: Nome da seção (ex: "investigacao")
            section_content: Texto do conteúdo da seção

        Returns:
            Lista de passos estruturados
        """
        steps = []

        # Isso captura linhas como: "- **Título do Passo:**"
        main_item_pattern = r"- \*\*([^:]+):\*\*(.*?)(?=- \*\*|$)"

        main_items = re.findall(main_item_pattern, section_content, re.DOTALL)

        for i, (title, content) in enumerate(main_items, 1):
            title = title.strip()
            content = content.strip()

            commands = self._extract_code_blocks(content)

            # Extrair subitens (linhas que começam com - e têm indentação)
            subitems = []
            subitem_pattern = r"(?:^|\n)\s+- ([^\n]+)"
            subitem_matches = re.finditer(subitem_pattern, content)
            for match in subitem_matches:
                subitems.append(match.group(1).strip())

            step = {
                "id": f"{section_name}_{i}",
                "title": title,
                "description": title,
                "content": content,
                "commands": commands,
                "subitems": subitems,
            }

            steps.append(step)

        # Se não encontrou passos com o padrão principal, tentar outro padrão mais simples
        if not steps:
            simple_item_pattern = r"- ([^\n]+)(?:\n((?:\s+[^\n]+\n?)*))?"
            simple_items = re.finditer(simple_item_pattern, section_content)

            for i, match in enumerate(simple_items, 1):
                description = match.group(1).strip()
                content = match.group(2).strip() if match.group(2) else ""

                steps.append(
                    {
                        "id": f"{section_name}_{i}",
                        "title": description,
                        "description": description,
                        "content": content,
                        "commands": self._extract_code_blocks(content),
                        "subitems": [],
                    }
                )

        # Se ainda não encontrou passos, usar o conteúdo completo
        if not steps:
            steps.append(
                {
                    "id": f"{section_name}_1",
                    "title": section_name.capitalize(),
                    "description": section_name.capitalize(),
                    "content": section_content,
                    "commands": self._extract_code_blocks(section_content),
                    "subitems": [],
                }
            )

        return steps

    def _extract_code_blocks(self, text: str) -> List[str]:
        """Extrai blocos de código/comandos do texto.

        Args:
            text: Texto para extrair blocos de código

        Returns:
            Lista de blocos de código encontrados
        """
        if not text:
            return []

        # Procurar por blocos de código em markdown
        code_pattern = r"```(?:\w+)?\s*(.*?)```"
        matches = re.finditer(code_pattern, text, re.DOTALL)

        code_blocks = [match.group(1).strip() for match in matches]

        # Procurar por comandos em linha precedidos por $ ou #
        command_pattern = r"(?:^|\n)\s*[`$#]\s+([^\n]+)"
        command_matches = re.finditer(command_pattern, text)

        for match in command_matches:
            code_blocks.append(match.group(1).strip())

        return code_blocks

    def _create_metadata(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria metadados para o playbook.

        Args:
            incident_data: Dados do incidente

        Returns:
            Dicionário de metadados
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "incident_type": incident_data.get("incident_type", "Security Incident"),
            "alert_name": incident_data.get("alert_name", ""),
            "severity": incident_data.get("severity", "Medium"),
            "source_ip": incident_data.get("source_ip", ""),
            "destination_ip": incident_data.get("destination_ip", ""),
            "hostname": incident_data.get("hostname", ""),
            "user": incident_data.get("user", ""),
        }

    def _extract_references(self, text: str) -> List[Dict[str, str]]:
        """Extrai referências do texto do playbook.

        Args:
            text: Texto do playbook

        Returns:
            Lista de referências encontradas
        """
        references = []

        # Procurar por referências em formato de URI
        uri_pattern = r"(?:https?://[^\s]+)"
        uri_matches = re.finditer(uri_pattern, text)

        for match in uri_matches:
            uri = match.group(0)
            # Verificar se é uma URI da UCO
            if "unifiedcyberontology" in uri:
                ref_type = "UCO Reference"
            elif "mitre" in uri:
                ref_type = "MITRE Reference"
            else:
                ref_type = "External Reference"

            references.append({"type": ref_type, "uri": uri})

        return references
