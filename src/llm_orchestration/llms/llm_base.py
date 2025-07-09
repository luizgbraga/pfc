from abc import ABC, abstractmethod
from typing import Any, Dict


class LLM(ABC):
    def __init__(self, model_name: str):
        self.model_name = model_name

    @abstractmethod
    def invoke(
        self,
        prompt: str,
        system_message: str = None,
        temperature: float = 0.2,
        max_tokens: int = 2000,
    ) -> Dict[str, Any]:
        pass
