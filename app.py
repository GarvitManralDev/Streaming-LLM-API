import asyncio
import json
from pathlib import Path
import uvicorn
from fastapi import (
    BackgroundTasks,
    Depends,
    FastAPI,
    Header,
    HTTPException,
    Request
)
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import settings
from src.models import ChatRequest, ChatResponse
from src.rate_limiter import check_rate_limit
from src.security import verify_api_key
from src.services.llm_service import (
    call_llm_with_retry,
    stream_llm_words
)


# --------------------------------------------------
# APP SETUP
# --------------------------------------------------

app = FastAPI(
    title=settings.app_name,
    version="1.0.0"
)


# --------------------------------------------------
# TEMPLATES + STATIC FILES
# --------------------------------------------------

# Find the project root safely.
BASE_DIR = Path(__file__).resolve().parent

# Serve CSS and JavaScript from /static.
app.mount(
    "/static",
    StaticFiles(directory=BASE_DIR / "static"),
    name="static"
)

# Load HTML templates from /templates.
templates = Jinja2Templates(
    directory=BASE_DIR / "templates"
)


# --------------------------------------------------
# SIMPLE IN-MEMORY IDEMPOTENCY STORE
# --------------------------------------------------

# For teaching only.
#
# Production systems should normally use
# Redis or a database.
idempotency_store: dict[str, ChatResponse] = {}


# --------------------------------------------------
# BACKGROUND LOGGING
# --------------------------------------------------

def save_chat_log(message: str, answer: str):
    """
    Save chat information after the user receives
    the API response.
    """

    with open(
        BASE_DIR / "chat_logs.txt",
        "a",
        encoding="utf-8"
    ) as file:

        file.write(
            json.dumps(
                {
                    "message": message,
                    "answer": answer
                },
                ensure_ascii=False
            )
            + "\n"
        )


# --------------------------------------------------
# WEB PAGE
# --------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """
    Render the beginner-friendly frontend.
    """

    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "app_name": settings.app_name,
            "environment": settings.environment
        }
    )


# --------------------------------------------------
# HEALTH CHECK
# --------------------------------------------------

@app.get("/health")
async def health():
    """
    Monitoring tools can call this endpoint
    to check whether the API is alive.
    """

    return {
        "status": "healthy",
        "environment": settings.environment,
        "model": settings.llm_model
    }


# --------------------------------------------------
# NORMAL CHAT API
# --------------------------------------------------

@app.post(
    "/v1/chat",
    response_model=ChatResponse
)
async def chat(
    request: ChatRequest,
    background_tasks: BackgroundTasks,

    # Authentication happens before our main logic.
    api_key: str = Depends(verify_api_key),

    # Optional idempotency key.
    idempotency_key: str | None = Header(
        default=None,
        alias="Idempotency-Key"
    )
):
    """
    Normal non-streaming AI endpoint.
    """

    # Protect the API from too many requests.
    check_rate_limit(api_key)

    # --------------------------------------------------
    # IDEMPOTENCY
    # --------------------------------------------------

    # If we already processed this request,
    # return the old result instead of doing the work again.
    if (
        idempotency_key
        and idempotency_key in idempotency_store
    ):
        stored = idempotency_store[idempotency_key]

        return ChatResponse(
            answer=stored.answer,
            model=stored.model,
            cached=True
        )

    # --------------------------------------------------
    # RETRY + TIMEOUT
    # --------------------------------------------------

    try:

        # Allow maximum 8 seconds for the LLM operation.
        answer = await asyncio.wait_for(
            call_llm_with_retry(
                message=request.message,
                temperature=request.temperature
            ),
            timeout=8
        )

    except asyncio.TimeoutError:
        raise HTTPException(
            status_code=504,
            detail="LLM request timed out"
        )

    except Exception as error:
        raise HTTPException(
            status_code=503,
            detail=f"LLM service failed: {error}"
        )

    # Build our typed response.
    response = ChatResponse(
        answer=answer,
        model=settings.llm_model,
        cached=False
    )

    # Save result if an idempotency key was supplied.
    if idempotency_key:
        idempotency_store[idempotency_key] = response

    # Save logs after sending the response.
    background_tasks.add_task(
        save_chat_log,
        request.message,
        answer
    )

    return response


# --------------------------------------------------
# STREAMING CHAT API
# --------------------------------------------------

@app.post("/v1/chat/stream")
async def stream_chat(
    request: ChatRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Stream AI output using Server-Sent Events (SSE).
    """

    # Apply the same simple rate limiting.
    check_rate_limit(api_key)

    return StreamingResponse(
        stream_llm_words(request.message),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive"
        }
    )




if __name__ == "__main__":

    uvicorn.run(
        "app:app",
        app_dir=str(BASE_DIR),
        host="127.0.0.1",
        port=8080,
        reload=True
    )