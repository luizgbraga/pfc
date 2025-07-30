import os

from src.llm_orchestration.llm_interface import IncidentResponsePlaybook


def playbook_to_html(playbook: IncidentResponsePlaybook):
    """
    Generates a well-formatted HTML file with CSS for the given IncidentResponsePlaybook.
    The file is saved as 'server/static/playbook.html' so it can be served by the Flask server.
    """
    html = f"""<!DOCTYPE html>
<html lang="pt">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Playbook de Resposta a Incidentes</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            max-width: 900px;
            margin: 0 auto;
            padding: 30px;
            background-color: #f5f5f5;
            color: #333;
        }}
        .container {{
            background-color: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1, h2, h3 {{
            color: #2c3e50;
        }}
        section {{
            margin-bottom: 32px;
        }}
        .section-title {{
            border-left: 5px solid #3498db;
            padding-left: 12px;
            margin-bottom: 12px;
            font-size: 1.4em;
        }}
        ul, ol {{
            margin-left: 24px;
        }}
        .subsection-title {{
            color: #2980b9;
            margin-top: 18px;
            font-size: 1.1em;
        }}
        .code-block {{
            background: #f8f8f8;
            border-radius: 5px;
            padding: 10px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            margin: 6px 0 12px 0;
            white-space: pre-wrap;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 16px;
        }}
        th, td {{
            border: 1px solid #ddd;
            padding: 8px;
        }}
        th {{
            background-color: #f0f4f8;
        }}
    </style>
</head>
<body>
    <div class="container">
        <h1>Playbook de Resposta a Incidentes</h1>

        <section>
            <div class="section-title">Contexto do Subgrafo</div>
            <div>{playbook.context_from_subgraph}</div>
        </section>

        <section>
            <div class="section-title">Resumo do Incidente</div>
            <ul>
                <li><b>Visão Geral:</b> {playbook.incident_summary.overview}</li>
                <li><b>Classificação Técnica:</b> {playbook.incident_summary.technical_classification}</li>
                <li><b>Avaliação de Severidade:</b> {playbook.incident_summary.severity_assessment}</li>
                <li><b>Impacto Potencial:</b> {playbook.incident_summary.potential_impact}</li>
            </ul>
        </section>

        <section>
            <div class="section-title">Etapas de Investigação</div>
            <div class="subsection-title">Etapas de Triagem</div>
            <div>{playbook.investigation_steps.triage_steps}</div>

            <div class="subsection-title">Coleta de Evidências</div>
            <table>
                <tr><th>Descrição</th><th>Comando</th></tr>
                {''.join(f'<tr><td>{ec.description}</td><td><span class="code-block">{ec.command}</span></td></tr>' for ec in playbook.investigation_steps.evidence_collection)}
            </table>

            <div class="subsection-title">Análise Técnica</div>
            <div>{playbook.investigation_steps.technical_analysis}</div>

            <div class="subsection-title">Ferramentas e Comandos</div>
            <table>
                <tr><th>Ferramenta</th><th>Uso</th><th>Exemplo</th></tr>
                {''.join(f'<tr><td>{tool.tool}</td><td>{tool.usage}</td><td><span class="code-block">{tool.example}</span></td></tr>' for tool in playbook.investigation_steps.tools_and_commands)}
            </table>

            <div class="subsection-title">Indicadores de Comprometimento</div>
            <ul>
                {''.join(f'<li>{ioc}</li>' for ioc in playbook.investigation_steps.indicators_of_compromise)}
            </ul>
        </section>

        <section>
            <div class="section-title">Procedimentos de Contenção</div>
            <ul>
                <li><b>Ações Imediatas:</b> {playbook.containment_procedures.immediate_actions}</li>
                <li><b>Isolamento do Sistema:</b> {playbook.containment_procedures.system_isolation}</li>
                <li><b>Bloqueio de Atividades Maliciosas:</b> {playbook.containment_procedures.malicious_activity_blocking}</li>
                <li><b>Preservação de Evidências:</b> {playbook.containment_procedures.evidence_preservation}</li>
            </ul>
        </section>

        <section>
            <div class="section-title">Etapas de Erradicação</div>
            <ul>
                <li><b>Remoção da Ameaça:</b> {playbook.eradication_steps.threat_removal}</li>
                <li><b>Correção de Vulnerabilidades:</b> {playbook.eradication_steps.vulnerability_fix}</li>
                <li><b>Verificação de Movimento Lateral:</b> {playbook.eradication_steps.lateral_movement_check}</li>
            </ul>
        </section>

        <section>
            <div class="section-title">Procedimentos de Recuperação</div>
            <ul>
                <li><b>Restauração do Sistema:</b> {playbook.recovery_procedures.system_restoration}</li>
                <li><b>Validação de Integridade:</b> {playbook.recovery_procedures.integrity_validation}</li>
                <li><b>Retorno às Operações:</b> {playbook.recovery_procedures.return_to_operations}</li>
            </ul>
        </section>

        <section>
            <div class="section-title">Lições Aprendidas & Prevenção</div>
            <ul>
                <li><b>Recomendações Preventivas:</b> {playbook.lessons_learned_and_prevention.preventive_recommendations}</li>
                <li><b>Melhorias de Segurança:</b> {playbook.lessons_learned_and_prevention.security_improvements}</li>
                <li><b>Atualizações de Políticas:</b> {playbook.lessons_learned_and_prevention.policy_updates}</li>
            </ul>
        </section>
    </div>
</body>
</html>
"""

    static_dir = os.path.join(os.path.dirname(__file__), "../../server/static")
    os.makedirs(static_dir, exist_ok=True)
    output_path = os.path.join(static_dir, "playbook.html")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
