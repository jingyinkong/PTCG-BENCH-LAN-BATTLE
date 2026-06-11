"""Generator 安全执行包装器 — 区分预期 StopIteration 和真正的异常。

测试中用 SafeStepGenerator 替代裸 except StopIteration: pass。
"""
import logging
from dataclasses import dataclass, field
from typing import Any, Optional

logger = logging.getLogger(__name__)


@dataclass
class GeneratorResult:
    yields: int = 0
    results: list[Any] = field(default_factory=list)
    error: Optional[Exception] = None
    completed: bool = False


class SafeStepGenerator:
    """安全执行 Generator。"""

    def __init__(self, generator: Any):
        self._gen = generator

    def execute(self, max_yields: int = 20) -> GeneratorResult:
        """执行 generator，自动处理 StopIteration。"""
        result = GeneratorResult()
        try:
            for _ in range(max_yields):
                try:
                    result.results.append(next(self._gen))
                    result.yields += 1
                except StopIteration:
                    result.completed = True
                    break
        except Exception as e:
            result.error = e
        return result

    @staticmethod
    def assert_completes(gen: Any, msg: str = "") -> GeneratorResult:
        """断言 generator 正常完成，否则 raise AssertionError。"""
        result = SafeStepGenerator(gen).execute()
        if result.error:
            raise AssertionError(
                f"{msg}{type(result.error).__name__}: {result.error}"
            ) from result.error
        return result
