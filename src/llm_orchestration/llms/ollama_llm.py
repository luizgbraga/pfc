from typing import Any, Dict

import ollama
from loguru import logger

from config.settings import DEFAULT_OLLAMA_LLM_MODEL
from src.llm_orchestration.llms.llm_base import LLM


class OllamaLLM(LLM):
    """Implementação do LLM para Ollama local."""

    def __init__(self, model_name: str = None):
        """Inicializa a interface Ollama.

        Args:
            model_name: Nome do modelo a ser usado
        """
        used_model = model_name or DEFAULT_OLLAMA_LLM_MODEL
        super().__init__(used_model)

        logger.info(
            f"Interface LLM (Ollama) configurada com modelo '{self.model_name}'"
        )

    def invoke(
        self,
        prompt: str,
        system_message: str = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
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
