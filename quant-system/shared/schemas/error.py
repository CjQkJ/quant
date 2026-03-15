"""错误模型。"""

from shared.schemas.base import BaseSchema


class ErrorDetail(BaseSchema):
    code: str
    message: str
    retryable: bool = False

