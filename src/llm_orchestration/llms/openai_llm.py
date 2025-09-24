from typing import Any, Dict

from loguru import logger
from openai import OpenAI

from config.settings import DEFAULT_OPENAI_LLM_MODEL, OPENAI_API_KEY
from src.llm_orchestration.llms.llm_base import LLM


class OpenAILLM(LLM):
    def __init__(self, model_name: str = None):
        """Inicializa a interface OpenAI.

        Args:
            model_name: Nome do modelo a ser usado
        """
        used_model = model_name or DEFAULT_OPENAI_LLM_MODEL
        super().__init__(used_model)

        self.client = OpenAI(api_key=OPENAI_API_KEY)

        logger.info(
            f"Interface LLM (OpenAI) configurada com modelo '{self.model_name}'"
        )

    def invoke(
        self,
        prompt: str,
        system_message: str = None,
        temperature: float = 0.1,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        try:
            messages = []
            if system_message:
                messages.append({"role": "system", "content": system_message})
            messages.append({"role": "user", "content": prompt})
            logger.debug(f"Enviando prompt para OpenAI ({len(prompt)} caracteres)")

            response = self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": dict(response.usage) if response.usage else {},
            }
            logger.info("Resposta gerada pelo OpenAI.")
            return result["content"]
        except Exception as e:
            logger.error(f"Erro ao gerar resposta LLM com OpenAI: {str(e)}")
            return {"content": f"Erro: {str(e)}", "error": True}
