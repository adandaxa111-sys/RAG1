from openai import OpenAI

from app.core.config import LLM_BASE_URL, LLM_API_KEY, LLM_MODEL, LLM_TEMPERATURE, LLM_MAX_TOKENS
from app.core.logging import log
from app.llm.types import LLMRequest, LLMResponse


class LMStudioClient:
    """Client for LM Studio (or any OpenAI-compatible local server)."""

    def __init__(self):
        self.client = OpenAI(
            base_url=LLM_BASE_URL,
            api_key=LLM_API_KEY,
        )
        self.model = LLM_MODEL
        log.info(f"LLM client configured: {LLM_BASE_URL} (model={self.model})")

    def generate(self, request: LLMRequest) -> LLMResponse:
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": request.system_prompt},
                    {"role": "user", "content": request.user_prompt},
                ],
                temperature=request.temperature or LLM_TEMPERATURE,
                max_tokens=request.max_tokens or LLM_MAX_TOKENS,
            )
            return LLMResponse(
                content=response.choices[0].message.content,
                model=response.model or self.model,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens if response.usage else 0,
                    "completion_tokens": response.usage.completion_tokens if response.usage else 0,
                },
            )
        except Exception as e:
            log.error(f"LLM request failed: {e}")
            raise

    def is_available(self) -> bool:
        """Quick health check against the LLM server."""
        try:
            self.client.models.list()
            return True
        except Exception:
            return False
