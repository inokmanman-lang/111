"""Мини-прокси для OpenRouter на Render.

Зачем: сервер ADS-ENGINE стоит в РФ (это нужно для Ads-API), а OpenRouter
блокирует запросы с российских IP (HTTP 403 "Access denied by security policy").
Render разворачивает сервис на не-российском IP (США), поэтому OpenRouter его пускает.

Схема:  ADS-ENGINE (РФ)  ->  этот прокси на Render (США)  ->  OpenRouter  ->  ответ обратно.

Безопасность: ключ OpenRouter здесь НЕ хранится. Он приходит в заголовке Authorization
от твоего сервера и просто пересылается дальше. Без валидного ключа прокси бесполезен.
"""
import os

import httpx
from fastapi import FastAPI, Request, Response

OPENROUTER_BASE = os.environ.get("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
TIMEOUT = float(os.environ.get("PROXY_TIMEOUT", "90"))

app = FastAPI(title="openrouter-proxy")

# Заголовки, которые пробрасываем в OpenRouter (в правильном регистре).
_FORWARD = {
    "authorization": "Authorization",
    "http-referer": "HTTP-Referer",
    "x-title": "X-Title",
    "content-type": "Content-Type",
}


@app.get("/")
async def health():
    return {"status": "ok", "service": "openrouter-proxy"}


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):
    body = await request.body()
    headers = {"Content-Type": "application/json"}
    for raw, norm in _FORWARD.items():
        val = request.headers.get(raw)
        if val:
            headers[norm] = val
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as cx:
            r = await cx.post(f"{OPENROUTER_BASE}/chat/completions",
                              content=body, headers=headers)
    except httpx.HTTPError as e:
        return Response(content=f'{{"error":"proxy error: {e}"}}',
                        status_code=502, media_type="application/json")
    return Response(content=r.content, status_code=r.status_code,
                    media_type="application/json")
