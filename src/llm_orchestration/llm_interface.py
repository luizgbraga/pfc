from dataclasses import dataclass
from typing import List

from src.graph_rag.retriever import Subgraph
from src.llm_orchestration.llms.llm_base import LLM
from src.llm_orchestration.prompt_manager import (
    build_explorer_prompt,
    build_planner_prompt,
    build_playbook_prompt,
)
from src.utils.string import clean_json


@dataclass
class PlannerExplorationPlan:
    step: int
    description: str

    def to_dict(self):
        return {
            "step": self.step,
            "description": self.description,
        }


@dataclass
class PlannerResponse:
    query: str
    initial_nodes: List[str]
    exploration_plan: List[PlannerExplorationPlan]

    def to_dict(self):
        return {
            "query": self.query,
            "initial_nodes": self.initial_nodes,
            "exploration_plan": [step.to_dict() for step in self.exploration_plan],
        }


def invoke_planner(llm: LLM, incident_data: str) -> PlannerResponse:
    """
    Invokes the planner LLM to generate an exploration plan based on incident data.

    Args:
        llm (LLM): The LLM instance to use for generating the exploration plan.

    Returns:
        PlannerResponse: The response from the planner LLM containing the query, initial nodes, and exploration plan.
    """
    planner_response = llm.invoke(
        prompt=build_planner_prompt(incident_data=incident_data),
    )

    planner_response_dict = clean_json(planner_response)
    return PlannerResponse(
        query=planner_response_dict["query"],
        initial_nodes=planner_response_dict["initial_nodes"],
        exploration_plan=[
            PlannerExplorationPlan(
                step=step["step"],
                description=step["description"],
            )
            for step in planner_response_dict["exploration_plan"]
        ],
    )


@dataclass
class ExplorerExpandNode:
    node_uri: str
    reason: str

    def to_dict(self):
        return {
            "node_uri": self.node_uri,
            "reason": self.reason,
        }


@dataclass
class ExplorerResponse:
    nodes_to_expand: List[ExplorerExpandNode]

    def to_dict(self):
        return {
            "nodes_to_expand": [node.to_dict() for node in self.nodes_to_expand],
        }


def invoke_explorer(
    llm: LLM, incident_data: str, subgraph: Subgraph
) -> ExplorerResponse:
    """
    Invokes the explorer LLM to determine which nodes to expand based on incident data and subgraph.

    Args:
        llm (LLM): The LLM instance to use for determining node expansions.
        incident_data (str): The incident data to provide context for the exploration.
        subgraph (Subgraph): The subgraph containing the current state of the graph.

    Returns:
        ExplorerResponse: The response from the explorer LLM containing nodes to expand and reasons.
    """
    explorer_response = llm.invoke(
        prompt=build_explorer_prompt(incident_data=incident_data, subgraph=subgraph),
    )

    explorer_response_dict = clean_json(explorer_response)
    return ExplorerResponse(
        nodes_to_expand=[
            ExplorerExpandNode(
                node_uri=node["node_uri"],
                reason=node["reason"],
            )
            for node in explorer_response_dict["nodes_to_expand"]
        ]
    )


@dataclass
class IncidentSummary:
    overview: str
    technical_classification: str
    severity_assessment: str
    potential_impact: str

    def to_dict(self):
        return {
            "overview": self.overview,
            "technical_classification": self.technical_classification,
            "severity_assessment": self.severity_assessment,
            "potential_impact": self.potential_impact,
        }


@dataclass
class EvidenceCommand:
    description: str
    command: str

    def to_dict(self):
        return {
            "description": self.description,
            "command": self.command,
        }


@dataclass
class ToolCommand:
    tool: str
    usage: str
    example: str

    def to_dict(self):
        return {
            "tool": self.tool,
            "usage": self.usage,
            "example": self.example,
        }


@dataclass
class InvestigationSteps:
    triage_steps: str
    evidence_collection: List[EvidenceCommand]
    technical_analysis: str
    tools_and_commands: List[ToolCommand]
    indicators_of_compromise: List[str]

    def to_dict(self):
        return {
            "triage_steps": self.triage_steps,
            "evidence_collection": [cmd.to_dict() for cmd in self.evidence_collection],
            "technical_analysis": self.technical_analysis,
            "tools_and_commands": [tool.to_dict() for tool in self.tools_and_commands],
            "indicators_of_compromise": self.indicators_of_compromise,
        }


@dataclass
class ContainmentProcedures:
    immediate_actions: str
    system_isolation: str
    malicious_activity_blocking: str
    evidence_preservation: str

    def to_dict(self):
        return {
            "immediate_actions": self.immediate_actions,
            "system_isolation": self.system_isolation,
            "malicious_activity_blocking": self.malicious_activity_blocking,
            "evidence_preservation": self.evidence_preservation,
        }


@dataclass
class EradicationSteps:
    threat_removal: str
    vulnerability_fix: str
    lateral_movement_check: str

    def to_dict(self):
        return {
            "threat_removal": self.threat_removal,
            "vulnerability_fix": self.vulnerability_fix,
            "lateral_movement_check": self.lateral_movement_check,
        }


@dataclass
class RecoveryProcedures:
    system_restoration: str
    integrity_validation: str
    return_to_operations: str

    def to_dict(self):
        return {
            "system_restoration": self.system_restoration,
            "integrity_validation": self.integrity_validation,
            "return_to_operations": self.return_to_operations,
        }


@dataclass
class LessonsLearnedAndPrevention:
    preventive_recommendations: str
    security_improvements: str
    policy_updates: str

    def to_dict(self):
        return {
            "preventive_recommendations": self.preventive_recommendations,
            "security_improvements": self.security_improvements,
            "policy_updates": self.policy_updates,
        }


@dataclass
class IncidentResponsePlaybook:
    incident_summary: IncidentSummary
    investigation_steps: InvestigationSteps
    containment_procedures: ContainmentProcedures
    eradication_steps: EradicationSteps
    recovery_procedures: RecoveryProcedures
    lessons_learned_and_prevention: LessonsLearnedAndPrevention

    def to_dict(self):
        return {
            "incident_summary": self.incident_summary.to_dict(),
            "investigation_steps": self.investigation_steps.to_dict(),
            "containment_procedures": self.containment_procedures.to_dict(),
            "eradication_steps": self.eradication_steps.to_dict(),
            "recovery_procedures": self.recovery_procedures.to_dict(),
            "lessons_learned_and_prevention": self.lessons_learned_and_prevention.to_dict(),
        }


def invoke_playbook(
    llm: LLM, incident_data: str, subgraph: Subgraph
) -> IncidentResponsePlaybook:
    """
    Invokes the LLM to generate a structured incident response playbook.

    Returns:
        IncidentResponsePlaybook: The structured playbook generated by the LLM.
    """
    playbook_response = llm.invoke(
        prompt=build_playbook_prompt(incident_data=incident_data, subgraph=subgraph),
    )
    playbook_response_dict = clean_json(playbook_response)

    return IncidentResponsePlaybook(
        incident_summary=IncidentSummary(
            overview=playbook_response_dict["incident_summary"]["overview"],
            technical_classification=playbook_response_dict["incident_summary"][
                "technical_classification"
            ],
            severity_assessment=playbook_response_dict["incident_summary"][
                "severity_assessment"
            ],
            potential_impact=playbook_response_dict["incident_summary"][
                "potential_impact"
            ],
        ),
        investigation_steps=InvestigationSteps(
            triage_steps=playbook_response_dict["investigation_steps"]["triage_steps"],
            evidence_collection=[
                EvidenceCommand(
                    description=step["description"],
                    command=step["command"],
                )
                for step in playbook_response_dict["investigation_steps"][
                    "evidence_collection"
                ]
            ],
            technical_analysis=playbook_response_dict["investigation_steps"][
                "technical_analysis"
            ],
            tools_and_commands=[
                ToolCommand(
                    tool=tool["tool"],
                    usage=tool["usage"],
                    example=tool["example"],
                )
                for tool in playbook_response_dict["investigation_steps"][
                    "tools_and_commands"
                ]
            ],
            indicators_of_compromise=playbook_response_dict["investigation_steps"][
                "indicators_of_compromise"
            ],
        ),
        containment_procedures=ContainmentProcedures(
            immediate_actions=playbook_response_dict["containment_procedures"][
                "immediate_actions"
            ],
            system_isolation=playbook_response_dict["containment_procedures"][
                "system_isolation"
            ],
            malicious_activity_blocking=playbook_response_dict[
                "containment_procedures"
            ]["malicious_activity_blocking"],
            evidence_preservation=playbook_response_dict["containment_procedures"][
                "evidence_preservation"
            ],
        ),
        eradication_steps=EradicationSteps(
            threat_removal=playbook_response_dict["eradication_steps"][
                "threat_removal"
            ],
            vulnerability_fix=playbook_response_dict["eradication_steps"][
                "vulnerability_fix"
            ],
            lateral_movement_check=playbook_response_dict["eradication_steps"][
                "lateral_movement_check"
            ],
        ),
        recovery_procedures=RecoveryProcedures(
            system_restoration=playbook_response_dict["recovery_procedures"][
                "system_restoration"
            ],
            integrity_validation=playbook_response_dict["recovery_procedures"][
                "integrity_validation"
            ],
            return_to_operations=playbook_response_dict["recovery_procedures"][
                "return_to_operations"
            ],
        ),
        lessons_learned_and_prevention=LessonsLearnedAndPrevention(
            preventive_recommendations=playbook_response_dict[
                "lessons_learned_and_prevention"
            ]["preventive_recommendations"],
            security_improvements=playbook_response_dict[
                "lessons_learned_and_prevention"
            ]["security_improvements"],
            policy_updates=playbook_response_dict["lessons_learned_and_prevention"][
                "policy_updates"
            ],
        ),
    )
