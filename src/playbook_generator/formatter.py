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
        # Extrair seções principais do playbook
        sections = self._extract_sections(llm_response)

        # Processar cada seção para extrair passos
        processed_sections = {}
        for section_name, section_content in sections.items():
            processed_sections[section_name] = self._process_section(
                section_name, section_content
            )

        # Criar metadados do playbook
        metadata = self._create_metadata(incident_data)

        # Montar playbook estruturado final
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

        # Padrões de seções padrão em playbooks
        section_patterns = [
            r"(?:1\.?|RESUMO DO INCIDENTE)\s+(.*?)(?=2\.?|PASSOS DE INVESTIGAÇÃO|$)",
            r"(?:2\.?|PASSOS DE INVESTIGAÇÃO)\s+(.*?)(?=3\.?|PROCEDIMENTOS DE CONTENÇÃO|$)",
            r"(?:3\.?|PROCEDIMENTOS DE CONTENÇÃO)\s+(.*?)(?=4\.?|PASSOS DE ERRADICAÇÃO|$)",
            r"(?:4\.?|PASSOS DE ERRADICAÇÃO)\s+(.*?)(?=5\.?|PROCEDIMENTOS DE RECUPERAÇÃO|$)",
            r"(?:5\.?|PROCEDIMENTOS DE RECUPERAÇÃO)\s+(.*?)(?=6\.?|LIÇÕES APRENDIDAS|$)",
            r"(?:6\.?|LIÇÕES APRENDIDAS|PREVENÇÃO)\s+(.*?)(?=$)",
        ]

        section_names = [
            "resumo",
            "investigacao",
            "contencao",
            "erradicacao",
            "recuperacao",
            "prevencao",
        ]

        # Usar DOTALL para fazer o ponto corresponder a qualquer caractere inclusive quebras de linha
        for i, pattern in enumerate(section_patterns):
            matches = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if matches:
                section_content = matches.group(1).strip()
                sections[section_names[i]] = section_content

        # Verificar se todas as seções foram encontradas
        if len(sections) != len(section_names):
            logger.warning(
                f"Algumas seções não foram encontradas. Encontradas: {len(sections)}/{len(section_names)}"
            )

            # Tentar abordagem mais simples para seções não encontradas
            remaining_text = text
            for name in section_names:
                if name not in sections:
                    # Procurar cabeçalho que contenha o nome da seção
                    header_pattern = rf"\b{name.upper()}\b|\b{name.title()}\b"
                    header_match = re.search(
                        header_pattern, remaining_text, re.IGNORECASE
                    )

                    if header_match:
                        start_pos = header_match.start()
                        # Encontrar o próximo cabeçalho ou fim do texto
                        next_header = re.search(
                            r"\n\s*\d+\.\s+|\n\s*[A-Z\s]{5,}",
                            remaining_text[start_pos + 1 :],
                        )

                        if next_header:
                            end_pos = start_pos + 1 + next_header.start()
                            sections[name] = remaining_text[start_pos:end_pos].strip()
                        else:
                            sections[name] = remaining_text[start_pos:].strip()

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

        # Identificar passos numerados
        step_pattern = r"(?:^|\n)(?:(?:\d+\.|\-|\*)\s+)([^.\n]+(?:\.[^.\n]+)*)(?:\n|$)"
        step_matches = re.finditer(step_pattern, section_content)

        for i, match in enumerate(step_matches):
            step_text = match.group(1).strip()

            # Verificar se há comandos ou código
            code_blocks = self._extract_code_blocks(section_content)

            # Verificar se há subitens
            subitems = self._extract_subitems(section_content)

            step = {
                "id": f"{section_name}_{i+1}",
                "description": step_text,
                "commands": code_blocks,
                "subitems": subitems,
            }

            steps.append(step)

        # Se não encontrou passos com o padrão, trate o conteúdo como um único passo
        if not steps:
            steps.append(
                {
                    "id": f"{section_name}_1",
                    "description": section_content,
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
        # Procurar por blocos de código em markdown
        code_pattern = r"```(?:\w+)?\s*(.*?)```"
        matches = re.finditer(code_pattern, text, re.DOTALL)

        code_blocks = [match.group(1).strip() for match in matches]

        # Procurar por comandos em linha precedidos por $
        command_pattern = r"\$\s+(.+)(?:\n|$)"
        command_matches = re.finditer(command_pattern, text)

        for match in command_matches:
            code_blocks.append(match.group(1).strip())

        return code_blocks

    def _extract_subitems(self, text: str) -> List[str]:
        """Extrai subitens de texto.

        Args:
            text: Texto para extrair subitens

        Returns:
            Lista de subitens encontrados
        """
        # Procurar por listas com letras ou pontos
        subitem_pattern = r"(?:^|\n)(?:[a-z]\.|\-|\+|\*)\s+([^\n]+)"
        matches = re.finditer(subitem_pattern, text)

        return [match.group(1).strip() for match in matches]

    def _create_metadata(self, incident_data: Dict[str, Any]) -> Dict[str, Any]:
        """Cria metadados para o playbook.

        Args:
            incident_data: Dados do incidente

        Returns:
            Dicionário de metadados
        """
        return {
            "generated_at": datetime.now().isoformat(),
            "incident_type": incident_data.get(
                "incident_type", "Unknown Security Incident"
            ),
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
