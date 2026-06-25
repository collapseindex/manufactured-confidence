"""Shared harness: chat clients (OpenRouter + Anthropic), answer extraction, and the cross-provider
model registry. Self-contained so the probes don't depend on any other repo.
"""
from __future__ import annotations

import os
import re
import time
from dataclasses import dataclass
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cross-provider spread for the failure-mode / cascade generalization study.
MODELS = {
    "sonnet": "claude-sonnet-4-6",
    "haiku": "claude-haiku-4-5-20251001",
    "llama70": "meta-llama/llama-3.1-70b-instruct",
    "gpt4o-mini": "openai/gpt-4o-mini",
    "gpt4o": "openai/gpt-4o",
    "qwen72": "qwen/qwen-2.5-72b-instruct",
    "gemini-flash": "google/gemini-flash-1.5",
}


def load_env():
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, v = line.split("=", 1)
                os.environ.setdefault(k.strip(), v.strip())


def extract_answer(text: str):
    """The token (or short phrase) after the last 'ANSWER:'."""
    if not text:
        return None
    m = re.findall(r"ANSWER:\s*([^\n]+)", text, flags=re.I)
    return m[-1].strip() if m else None


@dataclass
class OpenRouterLLM:
    model: str
    temperature: float = 0.0
    max_tokens: int = 400
    timeout: int = 60

    def __post_init__(self):
        self.key = os.environ.get("OPENROUTER_API_KEY")
        if not self.key:
            raise RuntimeError("OPENROUTER_API_KEY not set (.env)")
        self.calls = 0

    def chat(self, messages):
        body = {"model": self.model, "messages": messages,
                "temperature": self.temperature, "max_tokens": self.max_tokens}
        for attempt in range(6):
            try:
                r = requests.post(OPENROUTER_URL, json=body, timeout=self.timeout,
                                  headers={"Authorization": f"Bearer {self.key}"})
                if r.status_code == 200:
                    ch = (r.json().get("choices") or [])
                    c = (ch[0].get("message") or {}).get("content") if ch else None
                    if c:
                        self.calls += 1
                        return c
                elif r.status_code not in (429, 500, 502, 503):
                    raise RuntimeError(f"OpenRouter {r.status_code}: {r.text[:200]}")
            except requests.RequestException:
                pass
            time.sleep(2 * (attempt + 1))
        raise RuntimeError("OpenRouter failed after retries")


@dataclass
class AnthropicLLM:
    model: str
    temperature: float = 0.0
    max_tokens: int = 400

    def __post_init__(self):
        self.key = os.environ.get("ANTHROPIC_API_KEY")
        if not self.key:
            raise RuntimeError("ANTHROPIC_API_KEY not set (.env)")
        import anthropic
        self._client = anthropic.Anthropic(api_key=self.key)
        self.calls = 0

    def chat(self, messages):
        import anthropic
        system = "\n".join(m["content"] for m in messages if m["role"] == "system")
        conv = []
        for m in messages:
            if m["role"] == "system":
                continue
            if conv and conv[-1]["role"] == m["role"]:
                conv[-1]["content"] += "\n" + m["content"]
            else:
                conv.append({"role": m["role"], "content": m["content"]})
        for attempt in range(6):
            try:
                resp = self._client.messages.create(
                    model=self.model, max_tokens=self.max_tokens, temperature=self.temperature,
                    system=system or anthropic.NOT_GIVEN, messages=conv)
                self.calls += 1
                return "".join(b.text for b in resp.content if getattr(b, "type", None) == "text")
            except (anthropic.APIStatusError, anthropic.APIConnectionError) as e:
                if getattr(e, "status_code", None) not in (None, 429, 500, 502, 503, 529):
                    raise
                time.sleep(2 * (attempt + 1))
        raise RuntimeError("Anthropic failed after retries")


def make_client(key_or_id):
    """Accept a registry key ('sonnet') or a raw model id."""
    model_id = MODELS.get(key_or_id, key_or_id)
    if model_id.startswith("claude"):
        return AnthropicLLM(model=model_id)
    return OpenRouterLLM(model=model_id)
