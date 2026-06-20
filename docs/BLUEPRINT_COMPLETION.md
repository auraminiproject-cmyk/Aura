# Blueprint v3.0 — Completion Matrix

Legend: **Done** | **Partial** (works with fallback/local) | **Deferred** (needs GPU/cloud training, no card)

| Phase | Item | Status | Location |
|-------|------|--------|----------|
| 0 | Monorepo structure | Done | `fashion-ai/` |
| 0 | Docker Compose | Done | `docker-compose.yml` |
| 0 | FastAPI + all routers | Done | `services/api/api/v1/` |
| 0 | LiteLLM config | Done | `infra/litellm/config.yaml` |
| 0 | Alembic migrations | Done | `infra/migrations/` |
| 0 | Flutter 5-tab app | Done | `apps/mobile/` |
| 0 | CI/CD | Done | `.github/workflows/ci.yml` |
| 1 | ASR Whisper + 16kHz | Done | `services/api/services/asr.py` |
| 1 | TTS Kokoro + fallback | Done | `services/api/services/tts.py` |
| 1 | LangGraph agent | Done | `services/agent/graph.py` |
| 1 | WebSocket chat | Done | `api/v1/chat.py` |
| 1 | Flutter chat + WS | Done | `features/chat/` |
| 1 | i18n en/hi/te | Done | `assets/i18n/` |
| 1 | response_gen + style profile | Done | `services/agent/response_gen.py` |
| 2 | Avatar capture UI | Done | `avatar_capture_screen.dart` |
| 2 | Image compress 800px | Done | `services/api/core/image_utils.py` |
| 2 | Body reconstruction | Partial | `vision/body_reconstruct.py` + HF hook |
| 2 | Celery async vision | Done | `services/api/tasks/` |
| 2 | Outfit generation | Partial | `vision/generate_outfit.py` + HF hook |
| 2 | Virtual try-on | Partial | `vision/tryon.py` + HF hook |
| 2 | Avatar viewer GLB | Done | `avatar_viewer_screen.dart` |
| 2 | GLB WebSocket stream | Done | `api/v1/avatar.py` ws |
| 3 | Product ingestion | Done | `retrieval/ingestion.py` + JSON catalog |
| 3 | FashionCLIP embeddings | Partial | `retrieval/embeddings.py` |
| 3 | Qdrant HNSW config | Done | `retrieval/qdrant_store.py` |
| 3 | Hybrid search + RRF | Done | `retrieval/product_match.py` |
| 3 | Tailoring PDF agent | Done | `agent/tailor_guide.py` |
| 3 | Style feedback loop | Done | `api/v1/feedback.py` |
| 4 | cleaning_pipeline.py | Done | `data/cleaning_pipeline.py` |
| 4 | Training configs | Done | `training/configs/` |
| 4 | Evals DeepEval | Done | `evals/run_eval.py` |
| 4 | export_model.py | Done | `scripts/export_model.py` |
| 4 | Unsloth training run | Deferred | Colab/Kaggle (free GPU) |
| 5 | JWT auth | Done | `core/security.py` |
| 5 | Refresh tokens | Done | `api/v1/auth.py` |
| 5 | Rate limiting | Done | slowapi on chat/session |
| 5 | Input validation + EXIF strip | Done | `image_utils.py`, Pydantic |
| 5 | Privacy export + consent | Done | `api/v1/privacy.py` |
| 5 | AES photo encryption | Done | `core/encryption.py` |
| 5 | pytest suite | Done | `tests/` (20+ tests) |
| 5 | Locust load test | Done | `tests/locust/locustfile.py` |
| 5 | Maestro E2E spec | Done | `maestro/flow.yaml` |
| 6 | Prometheus /metrics | Done | `main.py` |
| 6 | Grafana dashboards | Done | `infra/grafana/` |
| 6 | MLflow tracking stub | Done | `services/mlops/mlflow_client.py` |
| 6 | Scheduled retrain workflow | Done | `.github/workflows/retrain.yml` |
| 7 | Circuit breakers | Done | `core/resilience.py` |
| 7 | Celery DLQ | Done | `tasks/celery_app.py` |
| 7 | Offline Drift (Flutter) | Done | `apps/mobile/lib/core/local_db.dart` |
| 7 | Content moderation | Done | `core/moderation.py` |
| 7 | Local backup script | Done | `scripts/backup_db.py` |
| 7 | Zero-card stack | Done | `docs/FREE_STACK.md` |
| — | Cloudflare R2 | **Removed** | Use local/MinIO |
| — | Supabase required | **Optional** | SQLite + JWT default |

**Deferred by design (free GPU / training hours):** Full HMR2+SMPL-X, SDXL LCM on-device, 150K finetune runs, Kolors VTON production quality — use HF Inference API keys when available.
