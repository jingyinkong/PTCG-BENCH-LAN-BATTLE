"""Shared OpenAI client factory for all LLM agents."""

from __future__ import annotations

import logging
import os
from typing import Any

import openai
from openai import OpenAI
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"

OPENROUTER_BACKBONE_MODELS = (
    "openai/gpt-5.5",
    "openai/gpt-5.4",
    "openai/gpt-5.4-mini",
    "openai/gpt-5.4-nano",
    "openai/gpt-5-mini",
    "openai/gpt-5-nano",
    "anthropic/claude-opus-4.7",
    "anthropic/claude-sonnet-4.6",
    "anthropic/claude-haiku-4.5",
    "google/gemini-3.1-pro-preview",
    "google/gemini-3-flash-preview",
    "google/gemini-2.5-pro",
    "google/gemini-2.5-flash",
    "qwen/qwen3.6-plus",
    "qwen/qwen3.5-flash-02-23",
    "qwen/qwen3-coder",
    "qwen/qwen3-coder-plus",
    "qwen/qwen3.5-flash-02-23",
    "deepseek/deepseek-v4-flash",
    "deepseek/deepseek-v3.2",
    "deepseek/deepseek-v4-pro",
    "mistralai/mistral-large-2512",
    "mistralai/mistral-medium-3.1",
    "mistralai/mistral-small-2603",
    "x-ai/grok-4.1-fast",
    "meta-llama/llama-4-scout",
    "meta-llama/llama-3.3-70b-instruct",
    "z-ai/glm-4.7-flash",
    "minimax/minimax-m2.5",
)

_RETRYABLE_ERRORS = (
    openai.RateLimitError,
    openai.APITimeoutError,
    openai.APIConnectionError,
    openai.InternalServerError,
)

def _resolve_api_key(env_var: str) -> str:
    """Get API key at call time: env var first, DB fallback (searches upward)."""
    value = os.getenv(env_var, "")
    if value:
        return value
    try:
        import sqlite3
        from pathlib import Path
        current = Path(__file__).resolve().parent
        for _ in range(8):
            for tail in ("backend/data/ptcg.db", "data/ptcg.db"):
                db_path = current / tail
                if db_path.exists():
                    db = sqlite3.connect(str(db_path))
                    row = db.execute(
                        "SELECT value FROM settings WHERE key = ?", (env_var,)
                    ).fetchone()
                    db.close()
                    if row:
                        return row[0]
            current = current.parent
    except Exception:
        pass
    return ""


# Base URLs only — API keys resolved lazily in build_client()
_MODEL_BASE_URLS: dict[str, str] = {
    "deepseek-chat": "https://api.deepseek.com",
    "deepseek-v4-flash": "https://api.deepseek.com",
    "deepseek-v4-pro": "https://api.deepseek.com",
    "glm-4.7": "https://api.z.ai/api/paas/v4",
    "qwen3.5-flash": "https://dashscope.aliyuncs.com/compatible-mode/v1",
    "MiniMax-M2.5": "https://api.minimax.io/v1",
}

_API_KEY_ENV_MAP: dict[str, str] = {
    "deepseek-chat": "DEEPSEEK_API_KEY",
    "deepseek-v4-flash": "DEEPSEEK_API_KEY",
    "deepseek-v4-pro": "DEEPSEEK_API_KEY",
    "glm-4.7": "ZAI_API_KEY",
    "qwen3.5-flash": "DASHSCOPE_API_KEY",
    "MiniMax-M2.5": "MINIMAX_API_KEY",
}


@retry(
    retry=retry_if_exception_type(_RETRYABLE_ERRORS),
    wait=wait_exponential(multiplier=1, min=2, max=60),
    stop=stop_after_attempt(5),
    reraise=True,
    before_sleep=before_sleep_log(logger, logging.WARNING),
)
def chat_completion_with_retry(client: OpenAI, **kwargs: Any) -> Any:
    """Call client.chat.completions.create with exponential-backoff retry."""
    return client.chat.completions.create(**kwargs)


def assistant_message_to_history(message: Any) -> dict[str, Any]:
    """Convert an SDK assistant message into a history item for the next request."""
    if hasattr(message, "model_dump"):
        raw = message.model_dump(exclude_unset=True)
    elif isinstance(message, dict):
        raw = dict(message)
    else:
        raw = {}

    history: dict[str, Any] = {"role": "assistant"}
    allowed_fields = (
        "content",
        "tool_calls",
        "function_call",
        "name",
        "refusal",
        "audio",
        # DeepSeek thinking-mode models require this field to be passed back.
        "reasoning_content",
    )

    for field in allowed_fields:
        value = raw.get(field, getattr(message, field, None))
        if value is not None:
            history[field] = value

    return history


def build_client(model: str) -> OpenAI:
    # Resolve base URL
    base_url = _MODEL_BASE_URLS.get(model)
    if base_url is None:
        base_url = OPENROUTER_BASE_URL

    # Resolve API key lazily — reads DB at call time, not import time
    env_var = _API_KEY_ENV_MAP.get(model, "OPENROUTER_API_KEY")
    api_key = _resolve_api_key(env_var)

    import httpx
    return OpenAI(
        base_url=base_url,
        api_key=api_key,
        timeout=httpx.Timeout(120.0, connect=10.0),
        max_retries=1,
    )
