import os
import httpx

from fastapi import FastAPI, Request
from fastapi.responses import Response

OPENROUTER_BASE = os.getenv(
    "OPENROUTER_BASE",
    "https://openrouter.ai/api/v1"
).rstrip("/")

TIMEOUT = float(os.getenv("PROXY_TIMEOUT", "120"))

app = FastAPI(title="OpenRouter Proxy")


@app.get("/")
async def root():
    return {
        "status": "ok",
        "service": "openrouter-proxy"
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


def get_headers(request: Request):
    headers = {}

    if request.headers.get("authorization"):
        headers["Authorization"] = request.headers["authorization"]

    if request.headers.get("http-referer"):
        headers["HTTP-Referer"] = request.headers["http-referer"]

    if request.headers.get("x-title"):
        headers["X-Title"] = request.headers["x-title"]

    if request.headers.get("content-type"):
        headers["Content-Type"] = request.headers["content-type"]

    if request.headers.get("accept"):
        headers["Accept"] = request.headers["accept"]

    return headers


@app.get("/v1/models")
async def models(request: Request):

    headers = get_headers(request)

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT
        ) as client:

            r = await client.get(
                f"{OPENROUTER_BASE}/models",
                headers=headers
            )

        return Response(
            content=r.content,
            status_code=r.status_code,
            headers={
                "Content-Type":
                    r.headers.get(
                        "content-type",
                        "application/json"
                    )
            }
        )

    except httpx.HTTPError as e:

        return Response(
            content=f'{{"error":"{str(e)}"}}',
            status_code=502,
            media_type="application/json"
        )


@app.post("/v1/chat/completions")
async def chat_completions(request: Request):

    body = await request.body()

    headers = get_headers(request)

    try:
        async with httpx.AsyncClient(
            timeout=TIMEOUT
        ) as client:

            r = await client.post(
                f"{OPENROUTER_BASE}/chat/completions",
                content=body,
                headers=headers
            )

        return Response(
            content=r.content,
            status_code=r.status_code,
            headers={
                "Content-Type":
                    r.headers.get(
                        "content-type",
                        "application/json"
                    )
            }
        )

    except httpx.HTTPError as e:

        return Response(
            content=f'{{"error":"{str(e)}"}}',
            status_code=502,
            media_type="application/json"
        )
