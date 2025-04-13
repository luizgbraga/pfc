# src/playbook_generator/html_exporter.py
import json
import os
import re
from datetime import datetime


class PlaybookHTMLExporter:
    """Exporta playbooks para HTML para visualização."""

    @staticmethod
    def export_to_html(playbook_data, output_path=None):
        """Exporta um playbook para um arquivo HTML.

        Args:
            playbook_data: Dicionário do playbook ou caminho para arquivo JSON
            output_path: Caminho para salvar o arquivo HTML

        Returns:
            Caminho para o arquivo HTML gerado
        """
        if isinstance(playbook_data, str) and os.path.exists(playbook_data):
            with open(playbook_data, "r") as f:
                playbook = json.load(f)
        else:
            playbook = playbook_data

        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"playbook_{timestamp}.html"

        html_content = f"""
        <!DOCTYPE html>
        <html lang="pt-br">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Playbook de Segurança - {playbook['metadata'].get('alert_name', 'Alerta')}</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    margin: 0;
                    padding: 20px;
                    color: #333;
                    background-color: #f8f9fa;
                }}
                .container {{
                    max-width: 1200px;
                    margin: 0 auto;
                    background-color: white;
                    box-shadow: 0 0 10px rgba(0,0,0,0.1);
                    border-radius: 8px;
                    overflow: hidden;
                }}
                header {{
                    background-color: #2c3e50;
                    color: white;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                h1, h2, h3 {{
                    margin-top: 0;
                }}
                .metadata {{
                    background-color: #f5f5f5;
                    padding: 15px;
                    border-radius: 5px;
                    margin-bottom: 20px;
                    border-left: 4px solid #3498db;
                }}
                .metadata-item {{
                    margin: 5px 0;
                }}
                .section {{
                    margin-bottom: 30px;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    overflow: hidden;
                }}
                .section-header {{
                    background-color: #34495e;
                    color: white;
                    padding: 10px 15px;
                }}
                .section-content {{
                    padding: 15px;
                }}
                .step {{
                    margin-bottom: 25px;
                    border-left: 3px solid #3498db;
                    padding-left: 15px;
                }}
                .step-header {{
                    font-weight: bold;
                    font-size: 1.1em;
                    margin-bottom: 10px;
                    color: #2980b9;
                }}
                .step-content {{
                    margin: 10px 0;
                }}
                .commands {{
                    background-color: #f9f9f9;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                    margin: 10px 0;
                }}
                .command {{
                    margin: 5px 0;
                    padding: 5px;
                    background-color: #eee;
                    border-radius: 3px;
                }}
                .subitems {{
                    margin: 10px 0 10px 20px;
                }}
                .subitem {{
                    margin: 5px 0;
                }}
                .severity-high {{
                    color: #e74c3c;
                    font-weight: bold;
                }}
                .severity-medium {{
                    color: #f39c12;
                    font-weight: bold;
                }}
                .severity-low {{
                    color: #2ecc71;
                    font-weight: bold;
                }}
                strong {{
                    color: #2c3e50;
                }}
                pre {{
                    white-space: pre-wrap;
                    background-color: #f8f9fa;
                    padding: 10px;
                    border-radius: 5px;
                    font-family: monospace;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <header>
                    <h1>Playbook de Resposta a Incidentes</h1>
                    <h2>{playbook['metadata'].get('alert_name', 'Alerta de Segurança')}</h2>
                </header>
                
                <div class="metadata">
                    <h3>Metadados do Incidente</h3>
                    <div class="metadata-item"><strong>Tipo de Incidente:</strong> {playbook['metadata'].get('incident_type', 'Não especificado')}</div>
                    <div class="metadata-item"><strong>Severidade:</strong> <span class="severity-{playbook['metadata'].get('severity', 'medium').lower()}">{playbook['metadata'].get('severity', 'Média')}</span></div>
                    <div class="metadata-item"><strong>IP de Origem:</strong> {playbook['metadata'].get('source_ip', 'N/A')}</div>
                    <div class="metadata-item"><strong>IP de Destino:</strong> {playbook['metadata'].get('destination_ip', 'N/A')}</div>
                    <div class="metadata-item"><strong>Hostname:</strong> {playbook['metadata'].get('hostname', 'N/A')}</div>
                    <div class="metadata-item"><strong>Usuário:</strong> {playbook['metadata'].get('user', 'N/A')}</div>
                    <div class="metadata-item"><strong>Gerado em:</strong> {playbook['metadata'].get('generated_at', 'N/A')}</div>
                </div>
        """

        section_titles = {
            "resumo": "Resumo do Incidente",
            "investigacao": "Passos de Investigação",
            "contencao": "Procedimentos de Contenção",
            "erradicacao": "Passos de Erradicação",
            "recuperacao": "Procedimentos de Recuperação",
            "prevencao": "Lições Aprendidas e Prevenção",
        }

        for section_key, section_steps in playbook["sections"].items():
            section_title = section_titles.get(section_key, section_key.capitalize())

            html_content += f"""
                <div class="section">
                    <div class="section-header">
                        <h3>{section_title}</h3>
                    </div>
                    <div class="section-content">
            """

            for step in section_steps:
                title = step.get("title", "")
                if title:
                    title = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", title)
                    title = title.replace("**", "")

                html_content += f"""
                        <div class="step">
                            <div class="step-header">{title}</div>
                """

                if step.get("content"):
                    content = step["content"]
                    content = re.sub(r"\*\*(.*?)\*\*", r"<strong>\1</strong>", content)
                    content = re.sub(r"^[\s]*-\s+", "", content)
                    content = re.sub(r"\n[\s]*-\s+", "\n", content)
                    content = re.sub(r"`([^`]+)`", r"<code>\1</code>", content)
                    content = content.replace("**", "")

                    html_content += f"""
                            <div class="step-content">{content}</div>
                    """

                if step.get("commands"):
                    html_content += """
                            <div class="commands">
                    """

                    for cmd in step["commands"]:
                        html_content += f"""
                                <div class="command">$ {cmd}</div>
                        """

                    html_content += """
                            </div>
                    """

                if step.get("subitems"):
                    html_content += """
                            <div class="subitems">
                    """

                    for subitem in step["subitems"]:
                        subitem = re.sub(
                            r"\*\*(.*?)\*\*", r"<strong>\1</strong>", subitem
                        )
                        subitem = subitem.replace("**", "")

                        html_content += f"""
                                <div class="subitem">• {subitem}</div>
                        """

                    html_content += """
                            </div>
                    """

                html_content += """
                        </div>
                """

            html_content += """
                    </div>
                </div>
            """

        if playbook.get("references"):
            html_content += """
                <div class="section">
                    <div class="section-header">
                        <h3>Referências</h3>
                    </div>
                    <div class="section-content">
                        <ul>
            """

            for ref in playbook["references"]:
                html_content += f"""
                            <li><strong>{ref.get('type', 'Referência')}:</strong> <a href="{ref.get('uri', '#')}" target="_blank">{ref.get('uri', 'Link')}</a></li>
                """

            html_content += """
                        </ul>
                    </div>
                </div>
            """

        html_content += """
                <div class="section">
                    <div class="section-header">
                        <h3>Resposta Original do LLM</h3>
                    </div>
                    <div class="section-content">
                        <details>
                            <summary>Expandir para ver a resposta completa</summary>
                            <pre>
        """

        html_content += (
            playbook["original_response"].replace("<", "&lt;").replace(">", "&gt;")
        )

        html_content += """
                            </pre>
                        </details>
                    </div>
                </div>
        """

        html_content += """
            </div>
        </body>
        </html>
        """

        with open(output_path, "w", encoding="utf-8") as f:
            f.write(html_content)

        return output_path
