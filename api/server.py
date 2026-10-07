"""Mirage scoring API.

Powers the browser extension and any other client. One endpoint scores
a posting with the rules engine. The translator and second opinion stay
out of this path on purpose: ambient scoring must be fast and cheap.

Deploy: root directory = repo root, build `pip install -r api/requirements.txt`,
start `PYTHONPATH=/app uvicorn api.server:app --host 0.0.0.0 --port $PORT`.
Set GOOGLE_API_KEY on the service to also enable the LLM passes later.
"""
from __future__ import annotations

import os
import time
from collections import defaultdict, deque

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from mirage.detector import analyze

app = FastAPI(title="Mirage scoring API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)

MIN_TEXT = 50
RATE_LIMIT = 30  # requests
RATE_WINDOW = 60  # seconds

_hits: dict[str, deque[float]] = defaultdict(deque)


def _rate_ok(ip: str) -> bool:
    now = time.monotonic()
    window = _hits[ip]
    while window and now - window[0] > RATE_WINDOW:
        window.popleft()
    if len(window) >= RATE_LIMIT:
        return False
    window.append(now)
    return True


class ScoreRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    url: str = Field(default="", max_length=2000)


class SignalOut(BaseModel):
    id: str
    title: str
    severity: str
    detail: str


class ScoreResponse(BaseModel):
    score: int
    verdict: str
    signals: list[SignalOut]


@app.middleware("http")
async def rate_limit_middleware(request: Request, call_next):
    if request.url.path == "/score":
        ip = request.headers.get("x-forwarded-for", "").split(",")[0].strip()
        ip = ip or (request.client.host if request.client else "unknown")
        if not _rate_ok(ip):
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit hit. Slow down a little."},
            )
    return await call_next(request)


@app.get("/health")
def health() -> dict:
    return {"ok": True}


@app.post("/score", response_model=ScoreResponse)
def score(req: ScoreRequest) -> ScoreResponse:
    text = req.text.strip()
    if len(text) < MIN_TEXT:
        raise HTTPException(
            status_code=422,
            detail="Text too short to score. Send the full posting.",
        )
    result = analyze(text)
    return ScoreResponse(
        score=result.score,
        verdict=result.verdict,
        signals=[
            SignalOut(
                id=s.id, title=s.title, severity=s.severity, detail=s.detail
            )
            for s in result.signals[:6]
        ],
    )


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        app, host="0.0.0.0", port=int(os.environ.get("PORT", 8000))
    )
