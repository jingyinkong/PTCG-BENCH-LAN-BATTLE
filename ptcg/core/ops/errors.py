class OperationError(Exception):
    """操作层基础异常。"""


class InvalidZoneError(OperationError):
    """区域引用非法或不可达。"""


class InvalidOperationError(OperationError):
    """操作定义不合法或不受支持。"""


class OperationPreconditionError(OperationError):
    """操作前置条件未满足。"""


class ChoiceRequiredError(OperationError):
    """操作需要显式选择结果。"""


class OperationInvariantError(OperationError):
    """操作执行破坏了预期不变量。"""
