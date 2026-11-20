# Streaming LLM API

> 📚 **This is a learning project.** It isn't a production-ready app. It's a small FastAPI project where I put together the backend patterns used around LLM APIs.
>
> 🎓 **I didn't build this all by myself.** It's part of the **Production Agentic AI Engineering Bootcamp** by **Krish Naik** on Udemy. See [Credits](#credits).

## What I Was Trying to Learn

Calling an LLM is the easy part. I wanted to understand everything around it that a real LLM backend needs: authentication, rate limits, validation, retries, timeouts, and streaming answers word by word the way ChatGPT does.

So I built one small FastAPI app that combines all of these in one place, with a simple web UI to try it out.

```text
  Browser / curl  ──▶  FastAPI (auth → rate limit → validation → retry/timeout)  ──▶  LLM
```

> The LLM is **simulated** (`asyncio.sleep` plus a canned answer), so you don't need any paid API key to run it.

## What's in the Project

Each concept is a small piece of the app:

1. **API-key authentication:** clients must send an `X-API-Key` header (`src/security.py`)
2. **Rate limiting:** an in-memory sliding window per API key (`src/rate_limiter.py`)
3. **Request validation:** Pydantic models for requests and responses (`src/models.py`)
4. **Retry + timeout:** retries the LLM call and gives up after 8 seconds (`src/services/llm_service.py`)
5. **Idempotency:** sending the same `Idempotency-Key` twice returns the cached answer
6. **SSE streaming:** `POST /v1/chat/stream` sends the answer word by word
7. **Background logging:** writes each chat to `chat_logs.txt` after the response is sent
8. **Config from** `.env`**:** settings loaded with `pydantic-settings` (`src/config.py`)
9. **A simple web UI:** a Jinja2 template plus a little JavaScript that reads the SSE stream

```text
├── app.py                  # routes, idempotency, background logging
├── src/
│   ├── config.py           # settings from .env
│   ├── models.py           # Pydantic models
│   ├── security.py         # API-key auth
│   ├── rate_limiter.py     # rate limiter
│   └── services/
│       └── llm_service.py  # fake LLM, retry, streaming
├── templates/index.html    # web UI
└── static/                 # app.js, style.css
```

## Running It Yourself

```bash
conda create -n streaming-api python=3.11 -y
conda activate streaming-api
pip install -r requirements.txt

cp .env.example .env
python app.py
```

- Web UI: <http://127.0.0.1:8080>
- Swagger docs: <http://127.0.0.1:8080/docs>

The default API key is `course-secret`, and the web UI fills it in for you.

### Trying it with curl

```bash
# Health check (no key needed)
curl http://127.0.0.1:8080/health

# Normal response
curl -X POST http://127.0.0.1:8080/v1/chat \
  -H "Content-Type: application/json" -H "X-API-Key: course-secret" \
  -d '{"message": "Explain RAG"}'

# Streaming response (SSE)
curl -N -X POST http://127.0.0.1:8080/v1/chat/stream \
  -H "Content-Type: application/json" -H "X-API-Key: course-secret" \
  -d '{"message": "Explain RAG"}'

# Idempotency: the 2nd call comes back instantly with "cached": true
curl -X POST http://127.0.0.1:8080/v1/chat \
  -H "Content-Type: application/json" -H "X-API-Key: course-secret" \
  -H "Idempotency-Key: demo-123" -d '{"message": "Explain RAG"}'
```

Things to try breaking:

- Use the wrong API key → **401**
- Send an empty message or `"temperature": 5` → **422**
- Send more than 10 requests in a minute → **429**

## Things to Keep in Mind

- This is a **learning project**, so the code is kept simple on purpose.
- The LLM is fake. To use a real one, replace the functions in `src/services/llm_service.py` with a real provider (OpenAI, Groq, etc.).
- Rate limiting and idempotency are stored **in memory**, so they reset on restart and won't work across multiple servers. A real setup would use Redis or a database.
- The API-key check is a single shared key, just enough to show the idea.

## Key Takeaways

- Most of an LLM backend is **plumbing**: auth, limits, validation and error handling.
- **Streaming (SSE)** makes responses feel much faster, even when the total time is the same.
- **Retries and timeouts** stop one slow or failed LLM call from hanging the whole API.
- **Idempotency** keeps retried requests from doing the same (and paying for the same) work twice.
- **Background tasks** let you log things without making the user wait.

## Credits

This project is the capstone project of **Module 4: FastAPI** in the **Production Agentic AI Engineering Bootcamp** by **Krish Naik** on Udemy.

The code is based on the course's [Build-a-Production-Ready-Streaming-LLM-API](https://github.com/entbappy/Build-a-Production-Ready-Streaming-LLM-API) project (Apache-2.0, see [`LICENSE`](./LICENSE)). I worked through it and ran it myself, but I didn't build it from scratch.

All credit for the course content goes to Krish Naik and the course team. This repo is only my personal learning copy.

---

*Made for learning. Feedback and suggestions are welcome!*
