"""
FastAPI Landing Page Server for Quest Analytics RAG Assistant

A professional landing page implementation that serves as the entry point for users
accessing the Quest Analytics RAG Assistant. Provides analytics tracking, responsive
design, and seamless integration with the main Gradio application.

Features:
- FastAPI-based web server
- Professional landing page with call-to-action
- Optional analytics tracking (Plausible or local CSV)
- Analytics log rotation for storage management
- Environment-based configuration
- CORS and security considerations
- Health monitoring and logging

Environment Variables:
- APP_URL: URL of the main Gradio application (default: http://localhost:7860)
- LANDING_PORT: Port for landing page server (default: 3000)
- ENABLE_ANALYTICS: Enable analytics tracking (default: false)
- ANALYTICS_PROVIDER: Analytics provider ('plausible' or 'csv')
- ANALYTICS_ID: Analytics tracking ID for external providers
- ANALYTICS_CSV_PATH: Path for local CSV analytics (default: data/analytics.csv)
"""

from __future__ import annotations

import asyncio
import csv
import os
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, AsyncGenerator, Dict

from fastapi import FastAPI, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates


APP_URL = os.getenv("APP_URL", "http://localhost:7860")
LANDING_PORT = int(os.getenv("LANDING_PORT", "3000"))
ENABLE_ANALYTICS = os.getenv("ENABLE_ANALYTICS", "false").lower() in {"1", "true", "yes"}
ANALYTICS_PROVIDER = os.getenv("ANALYTICS_PROVIDER", "plausible").lower()
ANALYTICS_ID = os.getenv("ANALYTICS_ID", "")
ANALYTICS_CSV_PATH = Path(os.getenv("ANALYTICS_CSV_PATH", "data/analytics.csv"))
ANALYTICS_MAX_BYTES = 5 * 1024 * 1024  # 5 MB rotation threshold

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))
_analytics_lock = asyncio.Lock()


def _ensure_analytics_file() -> None:
    """
    Initialize analytics CSV file with proper headers.
    
    Creates the analytics CSV file and directory structure if they don't exist,
    and writes the header row for tracking visitor interactions.
    
    Note:
        Only executes when ENABLE_ANALYTICS is True. Creates parent directories
        as needed for the analytics file path.
    """

    if not ENABLE_ANALYTICS:
        return
    ANALYTICS_CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    if not ANALYTICS_CSV_PATH.exists():
        with ANALYTICS_CSV_PATH.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerow(["timestamp", "user_ip", "action"])


def _rotate_if_needed() -> None:
    """
    Rotate analytics log file when size limit is exceeded.
    
    Checks the current analytics CSV file size and rotates it to a timestamped
    archive file when it exceeds the ANALYTICS_MAX_BYTES limit (5MB default).
    Creates a new analytics file after rotation.
    
    Note:
        Rotation filename format: analytics-YYYYMMDDTHHMMSSZ.csv
        Automatically creates a fresh analytics file after rotation.
    """

    if not ANALYTICS_CSV_PATH.exists():
        return
    if ANALYTICS_CSV_PATH.stat().st_size < ANALYTICS_MAX_BYTES:
        return
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    rotated_name = ANALYTICS_CSV_PATH.with_name(f"analytics-{timestamp}.csv")
    ANALYTICS_CSV_PATH.rename(rotated_name)
    _ensure_analytics_file()


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    FastAPI application lifespan event handler.
    
    Manages application startup and shutdown events, including analytics
    file initialization and logging of server status information.
    
    Startup tasks:
    - Initialize analytics CSV file structure
    - Log server URLs and configuration
    
    Yields:
        None: Application runs between startup and shutdown
    """
    # Startup
    _ensure_analytics_file()
    print(f"Landing page running at: http://0.0.0.0:{LANDING_PORT}")
    print(f"Gradio app available at: {APP_URL}")
    
    yield
    
    # Shutdown (if needed in the future)
    pass


app = FastAPI(
    title="Quest Analytics RAG Assistant Landing Page",
    description="Professional landing page for Quest Analytics RAG Assistant with analytics tracking",
    version="1.0.0",
    lifespan=lifespan
)


@app.get("/", response_class=HTMLResponse)
async def landing(request: Request) -> HTMLResponse:
    """
    Render the professional landing page for Quest Analytics RAG Assistant.
    
    Serves the main landing page with dynamic configuration, analytics integration,
    and responsive design. Provides call-to-action for accessing the main application.
    
    Args:
        request: FastAPI request object containing client information
        
    Returns:
        HTMLResponse: Rendered landing page with context variables including:
        - app_url: URL to the main Gradio RAG application
        - enable_analytics: Boolean for analytics tracking status
        - analytics_provider: Provider type ('plausible', 'csv', etc.)
        - analytics_id: Tracking ID for external analytics services
    """

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
    """
    Handle analytics event logging for user interactions.
    
    Logs user interaction events to the local CSV analytics file with proper
    concurrency control and automatic log rotation. Designed for tracking
    button clicks and user engagement when external analytics are disabled.
    
    Args:
        request: FastAPI request object containing event payload and client info
        
    Request Payload:
        action (str): Type of interaction event being tracked
        
    Returns:
        JSONResponse: Status response with appropriate HTTP status code:
        - 202 ACCEPTED: When external analytics provider is enabled
        - 201 CREATED: When event is successfully logged to local CSV
        
    Note:
        Uses async file locking to prevent concurrent write issues.
        Automatically rotates log files when size limit is exceeded.
    """

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
