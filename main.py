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

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE"])
async def proxy(request: Request, path: str):
    # 1. Нормализуем путь: если Hermes шлет /chat/completions, 
    # а база у нас .../api/v1, нам нужно добавить v1
    if not path.startswith("v1/"):
        path = f"v1/{path}"
    
    target_url = f"{OPENROUTER_BASE}/{path}"
    
    # 2. Собираем заголовки
    headers = dict(request.headers)
    headers.pop("host", None)
    headers.pop("content-length", None)
    
    # 3. Если Hermes не прислал ключ, берем его из переменной окружения Render
    if "authorization" not in [k.lower() for k in headers.keys()]:
        api_key = os.getenv("OPENROUTER_API_KEY")
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
    
    # 4. Читаем тело запроса
    body = await request.body()
    
    # 5. Отправляем запрос в OpenRouter со стримингом
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
            
            # 6. Возвращаем потоковый ответ
            return StreamingResponse(
                response.aiter_raw(),
                status_code=response.status_code,
                headers=dict(response.headers),
            )
        except httpx.HTTPError as e:
            raise HTTPException(status_code=502, detail=f"Proxy error: {str(e)}")
