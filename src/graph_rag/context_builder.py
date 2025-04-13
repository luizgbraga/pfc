from typing import Any, Dict, List

from loguru import logger

from src.graph_rag.retriever import GraphRetriever


class ContextBuilder:
    """Constrói contexto rico para prompts de LLM a partir do conhecimento do grafo."""

    def __init__(self, graph_retriever: GraphRetriever):
        """Inicializa o construtor de contexto.

        Args:
            graph_retriever: Instância de GraphRetriever para consultar conhecimento
        """
        self.retriever = graph_retriever

    def build_context_for_incident(self, incident_data: Dict[str, Any]) -> str:
        """Constrói uma string de contexto abrangente para um incidente.

        Args:
            incident_data: Dicionário contendo informações do incidente

        Returns:
            String de contexto formatada para prompt do LLM
        """
        graph_context = self.retriever.retrieve_for_incident(incident_data)

        context_parts = []

        # 1. Seção de Tipo de Incidente
        context_parts.append(
            self._format_incident_type(
                graph_context.get("incident_type", "Unknown Security Incident")
            )
        )

        # 2. Seção de Padrões de Ataque
        if graph_context.get("related_attack_patterns"):
            context_parts.append(
                self._format_attack_patterns(graph_context["related_attack_patterns"])
            )

        # 3. Seção de Observáveis
        if graph_context.get("observables"):
            context_parts.append(self._format_observables(graph_context["observables"]))

        # 4. Seção de Mitigações
        if graph_context.get("mitigations"):
            context_parts.append(self._format_mitigations(graph_context["mitigations"]))

        # 5. Seção de Conceitos Relacionados
        if graph_context.get("related_concepts"):
            context_parts.append(
                self._format_related_concepts(graph_context["related_concepts"])
            )

        full_context = "\n\n".join(context_parts)

        logger.info(f"Contexto construído com {len(context_parts)} seções")
        return full_context

    def _format_incident_type(self, incident_type: str) -> str:
        """Formata a seção de tipo de incidente.

        Args:
            incident_type: Tipo identificado do incidente

        Returns:
            String formatada para a seção
        """
        return f"### TIPO DE INCIDENTE IDENTIFICADO\n{incident_type}"

    def _format_attack_patterns(self, attack_patterns: List[Dict[str, Any]]) -> str:
        """Formata a seção de padrões de ataque.

        Args:
            attack_patterns: Lista de padrões de ataque

        Returns:
            String formatada para a seção
        """
        if not attack_patterns:
            return ""

        lines = ["### PADRÕES DE ATAQUE RELACIONADOS"]

        for idx, pattern in enumerate(attack_patterns, 1):
            pattern_text = [f"{idx}. **{pattern['label']}**"]
            if pattern.get("description"):
                pattern_text.append(f"   Descrição: {pattern['description']}")
            pattern_text.append(f"   Referência: {pattern['uri']}")

            lines.append("\n".join(pattern_text))

        return "\n\n".join(lines)

    def _format_observables(self, observables: List[Dict[str, Any]]) -> str:
        """Formata a seção de observáveis.

        Args:
            observables: Lista de observáveis relevantes

        Returns:
            String formatada para a seção
        """
        if not observables:
            return ""

        lines = ["### OBSERVÁVEIS RELEVANTES"]

        grouped = {}
        for obs in observables:
            entity_type = obs.get("entity_type", "other")
            if entity_type not in grouped:
                grouped[entity_type] = []
            grouped[entity_type].append(obs)

        for entity_type, obs_list in grouped.items():
            formatted_type = entity_type.replace("_", " ").title()
            lines.append(f"\n#### {formatted_type}")

            for obs in obs_list:
                obs_text = [f"- **{obs['label']}**"]
                if obs.get("description"):
                    obs_text.append(f"  Descrição: {obs['description']}")

                if "entity_values" in obs and obs["entity_values"]:
                    values = obs["entity_values"]
                    if isinstance(values, list) and values:
                        values_str = ", ".join(values)
                        obs_text.append(f"  Valores identificados: {values_str}")

                lines.append("\n".join(obs_text))

        return "\n".join(lines)

    def _format_mitigations(self, mitigations: List[Dict[str, Any]]) -> str:
        """Formata a seção de mitigações.

        Args:
            mitigations: Lista de mitigações

        Returns:
            String formatada para a seção
        """
        if not mitigations:
            return ""

        lines = ["### MITIGAÇÕES RECOMENDADAS"]

        grouped = {}
        for mitigation in mitigations:
            related_to = mitigation.get("related_to", "Geral")
            if related_to not in grouped:
                grouped[related_to] = []
            grouped[related_to].append(mitigation)

        for related_to, mitig_list in grouped.items():
            lines.append(f"\n#### Para {related_to}")

            for idx, mitigation in enumerate(mitig_list, 1):
                mitig_text = [f"{idx}. **{mitigation['label']}**"]
                if mitigation.get("description"):
                    mitig_text.append(f"   Descrição: {mitigation['description']}")

                lines.append("\n".join(mitig_text))

        return "\n".join(lines)

    def _format_related_concepts(self, concepts: List[Dict[str, Any]]) -> str:
        """Formata a seção de conceitos relacionados.

        Args:
            concepts: Lista de conceitos relacionados

        Returns:
            String formatada para a seção
        """
        if not concepts:
            return ""

        lines = ["### CONCEITOS RELACIONADOS"]

        for idx, concept in enumerate(concepts, 1):
            concept_text = [f"{idx}. **{concept['label']}**"]
            if concept.get("description"):
                concept_text.append(f"   Descrição: {concept['description']}")

            lines.append("\n".join(concept_text))

        return "\n\n".join(lines)
