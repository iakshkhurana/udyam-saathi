import base64
import logging
from collections.abc import Callable
from typing import Protocol

from ..config import get_settings

log = logging.getLogger(__name__)
MAX_TOOL_ROUNDS = 8


class LLMClient(Protocol):
    def run_tools(self, system: str, messages: list[dict], tools: list[dict],
                  execute: Callable[[str, dict], str]) -> tuple[str, list[dict]]:
        """Run a tool loop; returns final text and the appended message history."""

    def read_image(self, image: bytes, prompt: str) -> str: ...


class AnthropicClient:
    def __init__(self, api_key: str, model: str):
        import anthropic

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = model

    def _create(self, **kwargs):
        return self.client.beta.messages.create(
            model=self.model, max_tokens=4000, output_config={"effort": "low"},
            betas=["server-side-fallback-2026-07-01"], fallbacks="default", **kwargs)

    def run_tools(self, system, messages, tools, execute):
        messages = list(messages)
        for _ in range(MAX_TOOL_ROUNDS):
            response = self._create(system=system, tools=tools, tool_choice={"type": "auto"}, messages=messages)
            messages.append({"role": "assistant",
                             "content": [b.model_dump(mode="json", exclude_none=True) for b in response.content]})
            if response.stop_reason == "refusal":
                return "", messages
            calls = [b for b in response.content if b.type == "tool_use"]
            if response.stop_reason != "tool_use" or not calls:
                return "".join(b.text for b in response.content if b.type == "text"), messages
            results = []
            for call in calls:
                try:
                    content, is_error = execute(call.name, call.input), False
                except Exception as exc:
                    log.warning("Tool %s failed: %s", call.name, exc)
                    content, is_error = f"Error: {exc}", True
                results.append({"type": "tool_result", "tool_use_id": call.id, "content": content,
                                "is_error": is_error})
            messages.append({"role": "user", "content": results})
        return "", messages

    def read_image(self, image, prompt):
        data = base64.standard_b64encode(image).decode()
        response = self._create(messages=[{"role": "user", "content": [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": data}},
            {"type": "text", "text": prompt}]}])
        return "".join(b.text for b in response.content if b.type == "text")


def get_llm_client() -> LLMClient | None:
    s = get_settings()
    if not s.ai_mode or s.llm_provider != "anthropic":
        return None
    return AnthropicClient(s.anthropic_api_key, s.llm_model)
