from dataclasses import dataclass


@dataclass
class LLMRequest:
    system_prompt: str
    user_prompt: str
    temperature: float = 0.2
    max_tokens: int = 1024


@dataclass
class LLMResponse:
    content: str
    model: str = ""
    usage: dict | None = None
