# Zero-cost stack (no credit card required)

Verified policy for this project: **do not use services that require a payment method**, even for “free” tiers. Cloudflare R2 was removed for this reason.

## Approved services (sign up, API key only — no card)

| Role | Service | Sign up | Notes |
|------|---------|---------|--------|
| LLM (primary) | [Groq](https://console.groq.com) | Email / GitHub | Free tier: ~30 RPM, no card |
| LLM (local) | [Ollama](https://ollama.com) | None | Runs on your machine / Docker |
| ASR / models | [Hugging Face](https://huggingface.co) | Email | Free inference token, no card |
| CI | [GitHub Actions](https://github.com) | Free for public repos | 2000 min/mo |
| Training GPU | Google Colab, Kaggle | Google / Kaggle account | No card for basic notebooks |
| Mobile build | Flutter (local or CI) | — | Open source |

## Self-hosted / local (no account)

| Role | Default in this repo |
|------|---------------------|
| Database | SQLite (`DATABASE_URL=sqlite+aiosqlite:///./fashionai.db`) or Postgres in `docker-compose` |
| Cache | In-memory Redis fallback, or Redis in Docker |
| Vector search | Qdrant in Docker (`localhost:6333`) — **not** Qdrant Cloud unless you confirm no card |
| Object storage | **Local disk** (`storage/`) or **MinIO** in Docker — **not** Cloudflare R2 |
| Auth | Built-in guest JWT (`/api/v1/auth/guest`) |
| Metrics | Prometheus + Grafana in Docker |
| TTS | Kokoro (local, Apache 2.0) or silent WAV fallback |

## Removed or optional (often require card)

| Blueprint item | Status | Use instead |
|----------------|--------|-------------|
| **Cloudflare R2** | **Removed** | `STORAGE_BACKEND=local` or MinIO in Docker |
| Supabase (hosted) | Optional | SQLite + JWT; Postgres in Docker |
| Qdrant Cloud | Optional | Qdrant container in `docker-compose.yml` |
| Render | Optional only | [Hugging Face Spaces](https://huggingface.co/spaces) Docker deploy (see `deploy/huggingface/`) or run API on your PC |
| Railway / Fly.io / Modal | Not used | Colab/Kaggle for training |
| Langfuse Cloud | Optional | Prometheus `/metrics` only |
| PostHog / Sentry cloud | Optional | Skip for MVP |
| Firebase Auth | Not used | Guest JWT |

## Minimum `.env` to run with real AI (no card)

```env
GROQ_API_KEY=gsk_...          # console.groq.com
HUGGINGFACE_API_KEY=hf_...    # huggingface.co/settings/tokens
STORAGE_BACKEND=local
DATABASE_URL=sqlite+aiosqlite:///./fashionai.db
QDRANT_URL=http://localhost:6333   # after: docker compose up qdrant -d
```

## Production without card (recommended order)

1. **Local / home server** — `docker compose up -d` + port forward or Tailscale.
2. **Hugging Face Space** — Docker Space, secrets for `GROQ_API_KEY` only (`deploy/huggingface/`).
3. **GitHub Actions** — build APK; API stays local or on HF Space.

Do **not** create a Cloudflare account for R2 unless you accept card verification.

## Quick verify

```powershell
python scripts/verify_setup.py
pytest tests/ -q
curl http://127.0.0.1:8000/api/v1/status/services
```

Expected: `"cloudflare_r2": "disabled"`, `"stack": "zero-card"`.
