from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class ResolverContext:
    """未来用于将 Action/Card 解析为 GameOp 列表的上下文。"""

    state: Any
    action: Any | None = None
    acting_player: Any | None = None
    opponent_player: Any | None = None
    source_card: Any | None = None
    target_card: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ExecutionContext:
    """未来用于执行 GameOp 的上下文。"""

    state: Any
    acting_player: Any | None = None
    opponent_player: Any | None = None
    source_card: Any | None = None
    action: Any | None = None
    rng: Any | None = None
    emitter: Any | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
