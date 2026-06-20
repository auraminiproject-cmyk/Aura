# Deployment Report — Fashion AI v1.0 (zero-card stack)

**Date:** 2026-05-24 (updated)  
**Repository:** `d:\AURA\fashion-ai`  
**Policy:** No credit card required for any default service.

## Architecture (revised)

```
Flutter → FastAPI → Agent (Groq → Ollama → offline)
              ├─ SQLite / Docker Postgres
              ├─ Local storage (storage/) or MinIO
              ├─ Qdrant (Docker, not Cloud)
              └─ HF Inference (optional token)
```

**Removed from default path:** Cloudflare R2, Supabase (required), Qdrant Cloud, paid observability SaaS.

## Environment variables

### Required (free, no card)

- `GROQ_API_KEY`
- `HUGGINGFACE_API_KEY`
- `STORAGE_BACKEND` (`local` or `minio`)
- `STORAGE_LOCAL_PATH` (if `local`)
- `DATABASE_URL` (default SQLite)
- `APP_SECRET_KEY`

### Optional (self-hosted Docker)

- `REDIS_URL`
- `QDRANT_URL` (default `http://localhost:6333`)
- `S3_*` (only for MinIO)
- `OLLAMA_BASE_URL`

### Optional (verify no card before use)

- `SUPABASE_*`
- `RENDER_*`
- `LANGFUSE_*`, `POSTHOG_*`, `SENTRY_*`

## Run locally

```powershell
cd d:\AURA\fashion-ai
.\.venv\Scripts\activate
copy .env.example .env
$env:PYTHONPATH = "d:\AURA\fashion-ai"
uvicorn services.api.main:app --reload --port 8000
```

## Deploy without card

| Method | Steps |
|--------|--------|
| **HF Space** | Follow `deploy/huggingface/README.md`; set secrets in Space settings |
| **Docker home** | `docker compose up -d`; expose via Tailscale or LAN |
| **Render** | Only if your account needs no card — use `render.yaml` + env vars above |

**Do not use Cloudflare R2** for this project unless you accept card verification.

## Service audit summary

| Service | Card? | Project default |
|---------|-------|-----------------|
| Groq | No | Yes |
| Hugging Face | No | Yes |
| Ollama | N/A | Yes (local/Docker) |
| Cloudflare R2 | **Yes** | **No — use local/MinIO** |
| Supabase hosted | Sometimes | No — SQLite + JWT |
| Qdrant Cloud | Varies | No — Docker Qdrant |
| Render | Varies | Optional |
| HF Spaces | No | Recommended deploy |
| GitHub Actions | No | CI |

Full table: [docs/FREE_STACK.md](docs/FREE_STACK.md)

## Verification

- **pytest: 17/17 passed** — run `pytest tests/ -q`
- Full blueprint audit: [BLUEPRINT_AUDIT_FINAL.md](BLUEPRINT_AUDIT_FINAL.md)
- Storage: local + MinIO (no R2)
- All API routes: chat, avatar, design, search, wardrobe, tailor, auth, feedback, session, privacy, tasks, status
