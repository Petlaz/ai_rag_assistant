"""FastAPI-based landing page for Quest Analytics RAG Assistant."""

from __future__ import annotations

import asyncio
import csv
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates


APP_URL = os.getenv("APP_URL", "http://localhost:7860")
LANDING_PORT = int(os.getenv("LANDING_PORT", "3000"))
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "false").lower() in {"1", "true", "yes"}
ANALYTICS_PROVIDER = os.getenv("ANALYTICS_PROVIDER", "plausible").lower()
ANALYTICS_ID = os.getenv("ANALYTICS_ID", "")
ANALYTICS_CSV_PATH = Path(os.getenv("ANALYTICS_CSV_PATH", "/data/analytics.csv"))
ANALYTICS_MAX_BYTES = 5 * 1024 * 1024  # 5 MB rotation threshold

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

app = FastAPI(title="Quest Analytics RAG Assistant Landing Page")
_analytics_lock = asyncio.Lock()


def _ensure_analytics_file() -> None:
    """Ensure analytics CSV exists with header row."""

    if ENABLE_ANALYTICS:
        return
    ANALYTICS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ANALYTICS_CSV_PATH.exists():
        with ANALYTICS_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "user_ip", "action"])


def _rotate_if_needed() -> None:
    """Rotate analytics log when it grows beyond configured limit."""

    if not ANALYTICS_CSV_PATH.exists():
        return
    if ANALYTICS_CSV_PATH.stat().st_size < ANALYTICS_MAX_BYTES:
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rotated_name = ANALYTICS_CSV_PATH.with_name(f"analytics-{timestamp}.csv")
    ANALYTICS_CSV_PATH.rename(rotated_name)
    _ensure_analytics_file()


@app.on_event("startup")
async def on_startup() -> None:
    """Prepare analytics file and print helpful banner."""

    _ensure_analytics_file()
    print(f"🚀 Landing page running at: http://0.0.0.0:{LANDING_PORT}")
    print(f"🌐 Gradio app available at: {APP_URL}")


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    """Render the landing page."""

    context: Dict[str, Any] = {
        "request": request,
        "app_url": APP_URL,
        "enable_analytics": ENABLE_ANALYTICS,
        "analytics_provider": ANALYTICS_PROVIDER,
        "analytics_id": ANALYTICS_ID,
    }
    return templates.TemplateResponse("index.html", context)


@app.post("/analytics/log")
async def log_event(request: Request) -> JSONResponse:
    """Persist button click analytics when external provider is disabled."""

    payload = await request.json()
    action = str(payload.get("action", "unknown"))

    if ENABLE_ANALYTICS:
        return JSONResponse({"status": "external"}, status_code=status.HTTP_202_ACCEPTED)

    user_ip = request.client.host if request.client else "unknown"
    timestamp = datetime.now(timezone.utc).isoformat()

    async with _analytics_lock:
        _rotate_if_needed()
        with ANALYTICS_CSV_PATH.open("a", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow([timestamp, user_ip, action])

    return JSONResponse({"status": "logged"}, status_code=status.HTTP_201_CREATED)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "landing.main:app",
        host="0.0.0.0",
        port=LANDING_PORT,
        reload=False,
    )
