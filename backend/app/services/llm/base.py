from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass(frozen=True)
class GenerationInput:
    task: str
    module: str = ""
    analysis_type: str = ""
    level: str = "Simples"
    facts: str = ""
    details: str = ""
    topic: str = ""
    length: str = "Curto"
    creativity: str = "Baixa"


class LLMProvider(ABC):
    @abstractmethod
    def generate(self, request: GenerationInput) -> str: ...

    @abstractmethod
    def is_available(self) -> bool: ...

    @abstractmethod
    def get_provider_name(self) -> str: ...
