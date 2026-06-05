"""Lightweight translation utility for backend messages.

Language is detected from:
1. Explicit ``lang`` parameter passed to ``t()``
2. ``Accept-Language`` HTTP header (parsed from the request)
3. WebSocket query parameter ``?lang=zh-CN``
4. Default fallback: zh-CN
"""

from __future__ import annotations

from . import zh_CN, en_US

LOCALE_MAP: dict[str, dict[str, str]] = {
    "zh-CN": zh_CN.MESSAGES,
    "zh": zh_CN.MESSAGES,
    "en-US": en_US.MESSAGES,
    "en": en_US.MESSAGES,
}
_DEFAULT = zh_CN.MESSAGES


def get_locale(lang: str | None = None) -> dict[str, str]:
    """Return the translation dict for *lang*, falling back to zh-CN."""
    if lang and lang in LOCALE_MAP:
        return LOCALE_MAP[lang]
    return _DEFAULT


def t(key: str, lang: str | None = None, **kwargs) -> str:
    """Translate *key* to the target language.

    Any extra keyword arguments are used for ``str.format()`` interpolation.
    """
    msg = get_locale(lang).get(key, key)
    if kwargs:
        msg = msg.format(**kwargs)
    return msg


def parse_accept_language(header: str | None) -> str | None:
    """Extract the preferred locale from an Accept-Language header.

    Returns ``"zh-CN"``, ``"en-US"``, or ``None`` if unrecognized.
    """
    if not header:
        return None
    # Simple parser: take the first tag, map to our supported set
    first = header.split(",")[0].split(";")[0].strip()
    if first.startswith("zh"):
        return "zh-CN"
    if first.startswith("en"):
        return "en-US"
    return None
