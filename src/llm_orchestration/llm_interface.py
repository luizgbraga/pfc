from typing import Any, Dict

import openai
from loguru import logger

from config.settings import DEFAULT_LLM_MODEL, OPENAI_API_KEY


class LLMInterface:
    """Interface para comunicação com Modelos de Linguagem Grandes."""

    def __init__(self, model_name: str = None, api_key: str = None):
        """Inicializa a interface LLM.

        Args:
            model_name: Nome do modelo a ser usado
            api_key: Chave de API para o serviço do modelo
        """
        self.model_name = model_name or DEFAULT_LLM_MODEL
        self.api_key = api_key or OPENAI_API_KEY

        if not self.api_key:
            logger.warning(
                "Nenhuma chave de API fornecida para LLM. Algumas funcionalidades podem ser limitadas."
            )
        else:
            openai.api_key = self.api_key
            logger.info(f"Interface LLM configurada com modelo {self.model_name}")

    async def generate(
        self,
        prompt: str,
        system_message: str = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        """Gera uma resposta do LLM.

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

            # Adicionar mensagem do sistema se fornecida
            if system_message:
                messages.append({"role": "system", "content": system_message})

            # Adicionar prompt do usuário
            messages.append({"role": "user", "content": prompt})

            logger.debug(f"Enviando prompt para LLM ({len(prompt)} caracteres)")

            # Chamar API OpenAI
            response = await openai.ChatCompletion.acreate(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )

            # Extrair e retornar a resposta
            result = {
                "content": response.choices[0].message.content,
                "model": response.model,
                "usage": {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
            }

            logger.info(
                f"Resposta gerada: {result['usage']['completion_tokens']} tokens"
            )
            return result

        except Exception as e:
            logger.error(f"Erro ao gerar resposta LLM: {str(e)}")
            return {"content": f"Erro: {str(e)}", "error": True}
