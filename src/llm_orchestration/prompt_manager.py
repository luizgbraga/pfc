import json
from dataclasses import dataclass
from typing import List

from config.settings import (
    EXPLORER_EXAMPLES,
    EXPLORER_PROMPT,
    PLANNER_EXAMPLES,
    PLANNER_PROMPT,
    PLAYBOOK_EXAMPLES,
    PLAYBOOK_PROMPT,
)
from src.graph_rag.retriever import Subgraph
from src.llm_orchestration.prompt_techniques import QA, few_shot_prompt


@dataclass
class PlannerExplorationPlan:
    step: int
    description: str


@dataclass
class PlannerResponse:
    query: str
    initial_nodes: List[str]
    exploration_plan: List[PlannerExplorationPlan]


def build_planner_prompt(incident_data: str) -> str:
    """
    Constructs the planner prompt using the few-shot technique with provided examples.

    Returns:
        str: The formatted planner prompt ready for use.
    """
    planner_examples_json = PLANNER_EXAMPLES.read_text(encoding="utf-8")
    planner_examples_data = json.loads(planner_examples_json)

    planner_examples: List[QA] = [
        QA(
            question=json.dumps(example["question"], ensure_ascii=False, indent=2),
            answer=json.dumps(example["answer"], ensure_ascii=False, indent=2),
        )
        for example in planner_examples_data
    ]

    planner_prompt = few_shot_prompt(
        PLANNER_PROMPT.read_text(encoding="utf-8"),
        examples=planner_examples,
    )
    planner_prompt += "\n\n- Dados do incidente:\n" + incident_data

    return planner_prompt


@dataclass
class ExplorerExpandNode:
    node_uri: str
    reason: str


@dataclass
class ExplorerResponse:
    nodes_to_expand: List[ExplorerExpandNode]


def build_explorer_prompt(incident_data: str, subgraph: Subgraph) -> str:
    """
    Constructs the explorer prompt using the few-shot technique with provided examples.

    Returns:
        str: The formatted explorer prompt ready for use.
    """
    explorer_examples_json = EXPLORER_EXAMPLES.read_text(encoding="utf-8")
    explorer_examples_data = json.loads(explorer_examples_json)

    explorer_examples: List[QA] = [
        QA(
            question=json.dumps(example["question"], ensure_ascii=False, indent=2),
            answer=json.dumps(example["answer"], ensure_ascii=False, indent=2),
        )
        for example in explorer_examples_data
    ]

    explorer_prompt = few_shot_prompt(
        EXPLORER_PROMPT.read_text(encoding="utf-8"),
        examples=explorer_examples,
    )

    explorer_prompt += "\n\n- Subgrafo atual:\n"
    explorer_prompt += json.dumps(
        {
            "nodes": subgraph.nodes,
            "relationships": subgraph.relationships,
            "leaf_nodes": subgraph.leaf_nodes,
        },
        ensure_ascii=False,
        indent=2,
    )
    explorer_prompt += "Os nós escolhidos para a expansão DEVEM SER os LEAF_NODES do subgrafo atual.\n"
    explorer_prompt += f"Logo, escolha somente entre os nós da lista: {', '.join(subgraph.leaf_nodes)}\n"
    explorer_prompt += "\n\n- Dados do incidente:\n" + incident_data

    return explorer_prompt


@dataclass
class IncidentSummary:
    overview: str
    technical_classification: str
    severity_assessment: str
    potential_impact: str


@dataclass
class EvidenceCommand:
    description: str
    command: str


@dataclass
class ToolCommand:
    tool: str
    usage: str
    example: str


@dataclass
class InvestigationSteps:
    triage_steps: str
    evidence_collection: List[EvidenceCommand]
    technical_analysis: str
    tools_and_commands: List[ToolCommand]
    indicators_of_compromise: List[str]


@dataclass
class ContainmentProcedures:
    immediate_actions: str
    system_isolation: str
    malicious_activity_blocking: str
    evidence_preservation: str


@dataclass
class EradicationSteps:
    threat_removal: str
    vulnerability_fix: str
    lateral_movement_check: str


@dataclass
class RecoveryProcedures:
    system_restoration: str
    integrity_validation: str
    return_to_operations: str


@dataclass
class LessonsLearnedAndPrevention:
    preventive_recommendations: str
    security_improvements: str
    policy_updates: str


@dataclass
class IncidentResponsePlaybook:
    incident_summary: IncidentSummary
    investigation_steps: InvestigationSteps
    containment_procedures: ContainmentProcedures
    eradication_steps: EradicationSteps
    recovery_procedures: RecoveryProcedures
    lessons_learned_and_prevention: LessonsLearnedAndPrevention


def build_playbook_prompt(incident_data: str, subgraph: Subgraph) -> str:
    """
    Constructs the playbook prompt using the few-shot technique with provided examples.

    Returns:
        str: The formatted playbook prompt ready for use.
    """
    playbook_examples_json = PLAYBOOK_EXAMPLES.read_text(encoding="utf-8")
    playbook_examples_data = json.loads(playbook_examples_json)

    playbook_examples: List[QA] = [
        QA(
            question=json.dumps(example["question"], ensure_ascii=False, indent=2),
            answer=json.dumps(example["answer"], ensure_ascii=False, indent=2),
        )
        for example in playbook_examples_data
    ]

    playbook_prompt = few_shot_prompt(
        PLAYBOOK_PROMPT.read_text(encoding="utf-8"),
        examples=playbook_examples,
    )

    playbook_prompt += "\n\n- Subgrafo atual:\n"
    playbook_prompt += json.dumps(
        {
            "nodes": subgraph.nodes,
            "relationships": subgraph.relationships,
            "leaf_nodes": subgraph.leaf_nodes,
        },
        ensure_ascii=False,
        indent=2,
    )
    playbook_prompt += "\n\n- Dados do incidente:\n" + incident_data

    return playbook_prompt
