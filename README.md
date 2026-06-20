# Fashion AI — AI-Powered Personal Fashion Designer

Multilingual voice-first fashion stylist (Telugu / Hindi / English). Built for a **zero credit-card** stack — see **[docs/FREE_STACK.md](docs/FREE_STACK.md)**.

## Free stack (default)

| Layer | Choice | Card? |
|-------|--------|-------|
| LLM | Groq + Ollama + offline fallback | No |
| ASR / models | Hugging Face token | No |
| DB | SQLite (or Postgres in Docker) | No |
| Storage | **Local `storage/`** or MinIO in Docker | No |
| Vectors | Qdrant in Docker | No |
| Auth | Guest JWT built-in | No |
| Deploy | HF Spaces or `docker compose` | No |

**Not used:** Cloudflare R2 (requires card), Supabase/Render unless you opt in after verifying policy.

## Quick start

```powershell
cd d:\AURA\fashion-ai
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
# Add GROQ_API_KEY + HUGGINGFACE_API_KEY (free, no card)

$env:PYTHONPATH = "d:\AURA\fashion-ai"
uvicorn services.api.main:app --reload --host 0.0.0.0 --port 8000
```

- Docs: http://localhost:8000/docs  
- Health: http://localhost:8000/health  

### Docker (full stack, no cloud accounts)

```bash
docker compose up -d
```

Postgres, Redis, Qdrant, MinIO, Ollama — all self-hosted.

## Tests

```powershell
$env:PYTHONPATH = "d:\AURA\fashion-ai"
pytest tests/ -v
python scripts/verify_setup.py
```

**17 tests** — full API, agent, session flow, privacy, ingestion, moderation.

See **[BLUEPRINT_AUDIT_FINAL.md](BLUEPRINT_AUDIT_FINAL.md)** for phase-by-phase completion vs blueprint v3.0.

### One-command local start (Windows)

```powershell
.\scripts\run_local.ps1
```

### Key API routes

| Route | Purpose |
|-------|---------|
| `POST /api/v1/chat/message` | Chat (+ outfits/products on design intent) |
| `POST /api/v1/session/design-flow` | Full pipeline in one call |
| `GET /api/v1/status/services` | Zero-card stack status |
| `WS /api/v1/chat/ws/{session_id}` | Streaming chat + voice |

## Mobile

```powershell
cd apps\mobile
flutter pub get
flutter run --dart-define=API_BASE_URL=http://10.0.2.2:8000
```

Supabase in `pubspec.yaml` is optional; app uses API guest login by default.

## Deploy (no card)

1. **[Hugging Face Space](deploy/huggingface/README.md)** — recommended  
2. **Home server** — `docker compose` + Tailscale  
3. `render.yaml` — optional only; confirm Render still needs no card in your region  

Details: [DEPLOYMENT_REPORT.md](./DEPLOYMENT_REPORT.md)
