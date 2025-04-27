from typing import Any, Dict

import ollama
from loguru import logger

from config.settings import DEFAULT_LLM_MODEL


class LLMInterface:
    """Interface para comunicação com Modelos de Linguagem Grandes usando Ollama localmente."""

    def __init__(self, model_name: str = None):
        """Inicializa a interface LLM.

        Args:
            model_name: Nome do modelo a ser usado
        """
        self.model_name = model_name or DEFAULT_LLM_MODEL

        logger.info(
            f"Interface LLM (Ollama) configurada com modelo '{self.model_name}'"
        )

    def generate(
        self,
        prompt: str,
        system_message: str = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Gera uma resposta do LLM (versão síncrona).

        Args:
            prompt: O prompt a ser enviado ao modelo
            system_message: Mensagem de sistema opcional para contexto
            temperature: Configuração de temperatura (aleatoriedade)
            max_tokens: Tokens máximos na resposta

        Returns:
            Dicionário com a resposta do modelo e metadados
        """
        try:
            messages = []

            if system_message:
                messages.append({"role": "system", "content": system_message})

            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Enviando prompt para Ollama ({len(prompt)} caracteres)")

            response = ollama.chat(
                model=self.model_name,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                },
            )

            result = {
                "content": response["message"]["content"],
                "model": response["model"],
                "usage": {},
            }

            logger.info("Resposta gerada pelo Ollama.")
            return result

        except Exception as e:
            logger.error(f"Erro ao gerar resposta LLM com Ollama: {str(e)}")
            return {"content": f"Erro: {str(e)}", "error": True}
