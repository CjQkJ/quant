"""内部 API 依赖。"""

from __future__ import annotations

from fastapi import HTTPException, Request, status

from shared.config.settings import get_settings


def require_internal_access(request: Request) -> None:
    """限制高风险接口仅允许内部访问。"""

    settings = get_settings()
    if settings.allow_remote_internal_api:
        return
    client_host = request.client.host if request.client else ""
    if client_host in settings.internal_api_host_set():
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="当前接口仅允许本机或内网访问")
