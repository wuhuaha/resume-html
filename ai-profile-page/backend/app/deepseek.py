from __future__ import annotations

from typing import Literal

import httpx

from .config import settings

ChatPurpose = Literal["chat", "export"]


class LlmClient:
    def __init__(self) -> None:
        self.deepseek_base_url = settings.deepseek_base_url.rstrip("/")
        self.deepseek_api_key = settings.deepseek_api_key
        self.codex_base_url = settings.codex_base_url.rstrip("/")
        self.codex_api_key = settings.codex_api_key or settings.openai_api_key
        self.provider_mode = settings.llm_provider.lower().strip() or "auto"
        self.last_provider = ""
        self.last_model = ""

    @property
    def active_provider(self) -> str:
        if self.provider_mode in {"codex", "openai"}:
            return "codex" if self.codex_configured else "local"
        if self.provider_mode == "deepseek":
            return "deepseek" if self.deepseek_configured else "local"
        if self.provider_mode == "local":
            return "local"
        if self.codex_configured:
            return "codex"
        if self.deepseek_configured:
            return "deepseek"
        return "local"

    @property
    def configured(self) -> bool:
        return self.active_provider != "local"

    @property
    def provider_label(self) -> str:
        return self._provider_label(self.active_provider)

    @property
    def last_provider_label(self) -> str:
        return self._provider_label(self.last_provider or self.active_provider)

    def _provider_label(self, provider: str) -> str:
        if provider == "codex":
            return "Codex"
        if provider == "deepseek":
            return "DeepSeek"
        return "本地"

    @property
    def chat_model(self) -> str:
        return self.model_for("chat")

    @property
    def export_model(self) -> str:
        return self.model_for("export")

    @property
    def codex_configured(self) -> bool:
        return bool(self.codex_api_key)

    @property
    def deepseek_configured(self) -> bool:
        return bool(self.deepseek_api_key)

    def model_for(self, purpose: ChatPurpose = "chat") -> str:
        provider = self.active_provider
        if provider == "codex":
            return settings.codex_export_model if purpose == "export" else settings.codex_chat_model
        if provider == "deepseek":
            return settings.deepseek_export_model if purpose == "export" else settings.deepseek_chat_model
        return "local"

    async def chat(self, messages: list[dict[str, str]], model: str = "", purpose: ChatPurpose = "chat") -> str:
        provider = self.active_provider
        if provider == "codex":
            active_model = model or self.model_for(purpose)
            try:
                result = await self._codex_chat(messages, active_model)
                self.last_provider = "codex"
                self.last_model = active_model
                return result
            except Exception:
                if self.provider_mode == "auto" and self.deepseek_configured:
                    fallback_model = settings.deepseek_export_model if purpose == "export" else settings.deepseek_chat_model
                    result = await self._deepseek_chat(messages, fallback_model)
                    self.last_provider = "deepseek"
                    self.last_model = fallback_model
                    return result
                raise
        if provider == "deepseek":
            active_model = model or self.model_for(purpose)
            result = await self._deepseek_chat(messages, active_model)
            self.last_provider = "deepseek"
            self.last_model = active_model
            return result
        raise RuntimeError("LLM provider is not configured.")

    async def _deepseek_chat(self, messages: list[dict[str, str]], model: str) -> str:
        async with httpx.AsyncClient(timeout=60) as client:
            response = await client.post(
                f"{self.deepseek_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.deepseek_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload["choices"][0]["message"]["content"]

    async def _codex_chat(self, messages: list[dict[str, str]], model: str) -> str:
        if settings.codex_endpoint.strip().lower() == "chat_completions":
            return await self._codex_chat_completions(messages, model)
        return await self._codex_responses(messages, model)

    async def _codex_chat_completions(self, messages: list[dict[str, str]], model: str) -> str:
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.codex_base_url}/chat/completions",
                headers={
                    "Authorization": f"Bearer {self.codex_api_key}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": messages,
                    "temperature": 0.2,
                },
            )
            response.raise_for_status()
            payload = response.json()
            return payload["choices"][0]["message"]["content"]

    async def _codex_responses(self, messages: list[dict[str, str]], model: str) -> str:
        body = {
            "model": model,
            "input": self._responses_input(messages),
        }
        effort = settings.codex_reasoning_effort.strip()
        if effort:
            body["reasoning"] = {"effort": effort}

        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                f"{self.codex_base_url}/responses",
                headers={
                    "Authorization": f"Bearer {self.codex_api_key}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            response.raise_for_status()
            payload = response.json()
            return self._responses_text(payload)

    def _responses_input(self, messages: list[dict[str, str]]) -> list[dict[str, str]]:
        normalized = []
        for message in messages:
            role = message.get("role", "user")
            if role == "system":
                role = "developer"
            normalized.append(
                {
                    "role": role,
                    "content": message.get("content", ""),
                }
            )
        return normalized

    def _responses_text(self, payload: dict) -> str:
        direct = payload.get("output_text")
        if isinstance(direct, str) and direct.strip():
            return direct

        chunks: list[str] = []
        for item in payload.get("output", []):
            for content in item.get("content", []):
                if content.get("type") in {"output_text", "text"}:
                    text = content.get("text")
                    if isinstance(text, str):
                        chunks.append(text)
        return "\n".join(chunks).strip()


deepseek_client = LlmClient()
