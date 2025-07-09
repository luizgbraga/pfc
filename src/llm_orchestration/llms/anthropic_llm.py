from typing import Any, Dict

import anthropic
from loguru import logger

from src.llm_orchestration.llms.llm_base import LLM


class AnthropicLLM(LLM):
    def __init__(self, model_name: str = None, api_key: str = None):
        super().__init__(model_name)
        self.api_key = api_key or anthropic.api_key
        logger.info(f"AnthropicLLM configurado com modelo '{self.model_name}'")

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
            logger.debug(f"Enviando prompt para Anthropic ({len(prompt)} caracteres)")
            client = anthropic.Anthropic(api_key=self.api_key)
            response = client.messages.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = {
                "content": response.completion,
                "model": response.model,
                "usage": {},
            }
            logger.info("Resposta gerada pelo Anthropic.")
            return result
        except Exception as e:
            logger.error(f"Erro ao gerar resposta LLM com Anthropic: {str(e)}")
            return {"content": f"Erro: {str(e)}", "error": True}
