import os
import httpx
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import StreamingResponse

app = FastAPI(title="openrouter-proxy")

OPENROUTER_BASE = os.environ.get("OPENROUTER_BASE", "https://openrouter.ai/api/v1")
TIMEOUT = float(os.environ.get("PROXY_TIMEOUT", "90"))


@app.get("/")
async def health():
    return {"status": "ok", "service": "openrouter-proxy"}


@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
async def proxy(request: Request, path: str):
    # Нормализация пути: убираем "v1/" если клиент его прислал,
    # потому что OPENROUTER_BASE уже содержит /v1
    if path.startswith("v1/"):
        path = path[3:]
    
    target_url = f"{OPENROUTER_BASE}/{path}"

    # Собираем заголовки
    headers = {}
    for key, value in request.headers.items():
        lower = key.lower()
        if lower in ("host", "content-length"):
            continue
        headers[key] = value

    # Если Hermes не прислал ключ, берём его из переменной окружения Render
    has_auth = any(k.lower() == "authorization" for k in headers.keys())
    if not has_auth:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"

    body = await request.body()

    async with httpx.AsyncClient(timeout=TIMEOUT) as client:
        try:
            req = client.build_request(
                method=request.method,
                url=target_url,
                headers=headers,
                content=body,
                params=request.query_params,
            )
            response = await client.send(req, stream=True)
            return StreamingResponse(
                response.aiter_raw(),
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")
