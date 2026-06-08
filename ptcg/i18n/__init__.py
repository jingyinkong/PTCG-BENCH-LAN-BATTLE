"""Simple i18n module for backend tips/prompt text.

Provides t(key, lang) to translate UI-facing text to the current language.
Supported languages: zh-CN, en-US. Default: zh-CN.
"""

import json
from pathlib import Path
from typing import Optional

_DIR = Path(__file__).parent
_CACHED: dict[str, dict[str, str]] = {}


def _load(lang: str) -> dict[str, str]:
    if lang not in _CACHED:
        path = _DIR / f"{lang}.json"
        if path.exists():
            with open(path, "r", encoding="utf-8") as f:
                _CACHED[lang] = json.load(f)
        else:
            _CACHED[lang] = {}
    return _CACHED[lang]


def t(key: str, lang: Optional[str] = None) -> str:
    """Translate a key into the target language.

    Args:
        key: The translation key (matches JSON keys).
        lang: Target language code (zh-CN, en-US). Defaults to zh-CN.

    Returns:
        Translated string if key is found, otherwise the key itself (fallback).
    """
    if lang is None:
        lang = "zh-CN"
    data = _load(lang)
    return data.get(key, key)
