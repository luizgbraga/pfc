import argparse
import json
import os
import random
import sys
from typing import Any, Dict, List

from src.llm_orchestration.llm_interface import (
    ContainmentProcedures,
    EradicationSteps,
    EvidenceCommand,
    IncidentResponsePlaybook,
    IncidentSummary,
    InvestigationSteps,
    LessonsLearnedAndPrevention,
    RecoveryProcedures,
    ToolCommand,
)
from src.utils.html import playbook_to_html


def build_playbook_from_dict(d: Dict[str, Any]) -> IncidentResponsePlaybook:
    """Validate and build IncidentResponsePlaybook from a raw dict.

    Raises ValueError on missing or invalid fields.
    """
    try:
        ctx = d["context_from_subgraph"]

        isd = d["incident_summary"]
        incident_summary = IncidentSummary(
            overview=isd["overview"],
            technical_classification=isd["technical_classification"],
            severity_assessment=isd["severity_assessment"],
            potential_impact=isd["potential_impact"],
        )

        inv = d["investigation_steps"]
        evidence_collection = [
            EvidenceCommand(description=e["description"], command=e["command"])
            for e in inv["evidence_collection"]
        ]
        tools_and_commands = [
            ToolCommand(tool=t["tool"], usage=t["usage"], example=t["example"])
            for t in inv["tools_and_commands"]
        ]
        investigation_steps = InvestigationSteps(
            triage_steps=inv["triage_steps"],
            evidence_collection=evidence_collection,
            technical_analysis=inv["technical_analysis"],
            tools_and_commands=tools_and_commands,
            indicators_of_compromise=inv["indicators_of_compromise"],
        )

        cont = d["containment_procedures"]
        containment_procedures = ContainmentProcedures(
            immediate_actions=cont["immediate_actions"],
            system_isolation=cont["system_isolation"],
            malicious_activity_blocking=cont["malicious_activity_blocking"],
            evidence_preservation=cont["evidence_preservation"],
        )

        erad = d["eradication_steps"]
        eradication_steps = EradicationSteps(
            threat_removal=erad["threat_removal"],
            vulnerability_fix=erad["vulnerability_fix"],
            lateral_movement_check=erad["lateral_movement_check"],
        )

        rec = d["recovery_procedures"]
        recovery_procedures = RecoveryProcedures(
            system_restoration=rec["system_restoration"],
            integrity_validation=rec["integrity_validation"],
            return_to_operations=rec["return_to_operations"],
        )

        llp = d["lessons_learned_and_prevention"]
        lessons = LessonsLearnedAndPrevention(
            preventive_recommendations=llp["preventive_recommendations"],
            security_improvements=llp["security_improvements"],
            policy_updates=llp["policy_updates"],
        )

        return IncidentResponsePlaybook(
            context_from_subgraph=ctx,
            incident_summary=incident_summary,
            investigation_steps=investigation_steps,
            containment_procedures=containment_procedures,
            eradication_steps=eradication_steps,
            recovery_procedures=recovery_procedures,
            lessons_learned_and_prevention=lessons,
        )

    except KeyError as e:
        raise ValueError(f"Missing required field in playbook JSON: {e}") from e
    except TypeError as e:
        raise ValueError(f"Invalid type in playbook JSON: {e}") from e


def generate_random_playbook_dict() -> Dict[str, Any]:
    """Generate a random but valid playbook dict matching the dataclass structure."""
    n = random.randint(1, 9999)
    sample = {
        "context_from_subgraph": f"Context sample #{n}",
        "incident_summary": {
            "overview": "Example incident overview",
            "technical_classification": "Malware - Example",
            "severity_assessment": "High",
            "potential_impact": "Data exfiltration possible",
        },
        "investigation_steps": {
            "triage_steps": "Collect basic facts and isolate affected hosts",
            "evidence_collection": [
                {"description": "List running processes", "command": "ps aux"},
                {"description": "Network connections", "command": "netstat -an"},
            ],
            "technical_analysis": "Analyze artifacts and indicators",
            "tools_and_commands": [
                {"tool": "grep", "usage": "Search logs", "example": "grep -i attack /var/log/syslog"},
            ],
            "indicators_of_compromise": ["8.8.8.8", "malicious.exe"],
        },
        "containment_procedures": {
            "immediate_actions": "Isolate host from network",
            "system_isolation": "Disconnect from VPN and power down network ports",
            "malicious_activity_blocking": "Block IPs and domains at perimeter",
            "evidence_preservation": "Create disk images and collect logs",
        },
        "eradication_steps": {
            "threat_removal": "Remove malicious binaries and cron jobs",
            "vulnerability_fix": "Apply vendor patch",
            "lateral_movement_check": "Scan internal network for signs of spread",
        },
        "recovery_procedures": {
            "system_restoration": "Rebuild from known-good images",
            "integrity_validation": "Run file integrity checks",
            "return_to_operations": "Gradual reintroduction to network",
        },
        "lessons_learned_and_prevention": {
            "preventive_recommendations": "Improve patch cadence",
            "security_improvements": "Enable EDR on all endpoints",
            "policy_updates": "Update incident response runbooks",
        },
    }
    return sample


def main(argv: List[str]):
    parser = argparse.ArgumentParser(
        description="Convert a playbook JSON to HTML (validates dataclass construction)."
    )
    parser.add_argument("--input", "-i", help="Path to playbook JSON file (optional)")
    args = parser.parse_args(argv)

    if args.input:
        input_path = args.input
        if not os.path.exists(input_path):
            print(f"Input file does not exist: {input_path}")
            sys.exit(2)
        with open(input_path, "r", encoding="utf-8") as f:
            try:
                payload = json.load(f)
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON: {e}")
                sys.exit(2)
    else:
        # generate a random sample and write it to a temp file for inspection
        payload = generate_random_playbook_dict()
        input_path = os.path.abspath("temp_playbook_random.json")
        with open(input_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2, ensure_ascii=False)
        print(f"No input provided — generated sample JSON at: {input_path}")

    # validate and build dataclass
    try:
        playbook = build_playbook_from_dict(payload)
    except ValueError as e:
        print(f"Validation error when building IncidentResponsePlaybook: {e}")
        sys.exit(3)

    # render to HTML
    try:
        playbook_to_html(playbook)
    except Exception as e:
        print(f"Failed to render HTML: {e}")
        sys.exit(4)

    # report where the HTML was written (matches html.py behavior)
    script_dir = os.path.dirname(__file__)
    output_path = os.path.abspath(os.path.join(script_dir, "../../server/static/playbook.html"))
    print(f"Playbook HTML written to: {output_path}")


if __name__ == "__main__":
    main(sys.argv[1:])
