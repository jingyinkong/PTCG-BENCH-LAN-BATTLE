"""统一错误处理中间件 + API 响应格式。

所有 API: {"success": bool, "data": ..., "error": str|None}
"""
from fastapi import HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
import traceback


class UnifiedResponseMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        try:
            response = await call_next(request)
            if response.headers.get("content-type", "").startswith("application/json"):
                import json
                body = b""
                async for chunk in response.body_iterator:
                    body += chunk
                data = json.loads(body) if body else None
                return JSONResponse(
                    content={"success": response.status_code < 400, "data": data, "error": None},
                    status_code=response.status_code)
            return response
        except HTTPException as e:
            return JSONResponse(content={"success": False, "data": None, "error": e.detail}, status_code=e.status_code)
        except Exception as e:
            traceback.print_exc()
            return JSONResponse(content={"success": False, "data": None, "error": str(e)}, status_code=500)


def success(data=None, status=200):
    return JSONResponse(content={"success": True, "data": data, "error": None}, status_code=status)

def error(msg: str, status=400):
    return JSONResponse(content={"success": False, "data": None, "error": msg}, status_code=status)
