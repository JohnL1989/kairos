"""
Aion Memory — 统一响应格式
所有 API 端点统一返回 {"code": int, "message": str, "data": any}
"""
import decimal
import json
from datetime import datetime, date, time

from fastapi.responses import Response


def _json_default(o):
    """让 JSON 序列化能处理 Decimal / 日期等非原生类型。"""
    if isinstance(o, decimal.Decimal):
        return float(o)
    if isinstance(o, (datetime, date, time)):
        return o.isoformat()
    raise TypeError(f"Object of type {o.__class__.__name__} is not JSON serializable")


def _render(code: int, message: str, data, status_code: int = None) -> Response:
    body = json.dumps(
        {"code": code, "message": message, "data": data},
        default=_json_default,
        ensure_ascii=False,
    )
    return Response(content=body, media_type="application/json", status_code=status_code or code)


def success(data: dict = None, message: str = "success", code: int = 200) -> Response:
    """成功响应"""
    return _render(code, message, data)


def error(message: str = "error", code: int = 400, status_code: int = 400, data: dict = None) -> Response:
    """错误响应（可选 data 透传额外结构化信息，如乐观锁当前版本）"""
    return _render(code, message, data, status_code)


def ok(data: dict = None) -> Response:
    """快捷方式：200 成功"""
    return success(data=data)
