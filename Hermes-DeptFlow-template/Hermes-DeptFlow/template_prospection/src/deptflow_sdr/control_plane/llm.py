from __future__ import annotations

import json
import urllib.request
from typing import Any, Protocol


class LLMProvider(Protocol):
    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        ...


class HeuristicProvider:
    name = "heuristic"

    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"provider": self.name, "instruction": instruction, "input": payload}


class OpenAIProvider:
    name = "openai"

    def __init__(self, api_key: str, model: str = "gpt-4.1-mini", base_url: str = "https://api.openai.com/v1"):
        self.api_key = api_key
        self.model = model
        self.base_url = base_url.rstrip("/")

    def __repr__(self) -> str:
        return f"OpenAIProvider(model={self.model!r}, base_url={self.base_url!r})"

    def generate_json(self, instruction: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": "Return only valid JSON."},
                        {"role": "user", "content": instruction + "\n\n" + json.dumps(payload, ensure_ascii=False)},
                    ],
                    "response_format": {"type": "json_object"},
                }
            ).encode("utf-8"),
            method="POST",
            headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(request, timeout=60) as response:
            data = json.loads(response.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)


def make_llm_provider(env: dict[str, str]) -> LLMProvider:
    provider = env.get("LLM_PROVIDER", "openai").strip().lower()
    if provider == "openai" and env.get("OPENAI_API_KEY"):
        return OpenAIProvider(
            api_key=env["OPENAI_API_KEY"],
            model=env.get("OPENAI_MODEL", "gpt-4.1-mini"),
            base_url=env.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        )
    return HeuristicProvider()
