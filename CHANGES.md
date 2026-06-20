# Dependency / environment changes

| Item | Blueprint | Implemented | Reason |
|------|-----------|-------------|--------|
| Python | 3.11+ | 3.12 in Docker, 3.13 tested locally | Host runtime |
| Local DB default | PostgreSQL 16 | SQLite async fallback | Docker not available on initial dev host |
| Redis | Required | In-memory fallback when SQLite dev mode | Zero-deps local smoke tests |
| Kokoro TTS | Required | Optional (`kokoro` package) | Silent WAV placeholder when not installed |
| Flutter | `flutter create` | Manual scaffold | Flutter CLI not on PATH; CI uses `subosito/flutter-action` |
| httpx | 0.28.1 | `>=0.27.0,<0.28.0` | Resolves `litellm` dependency conflict |
| GPU vision models | HMR2/SMPL-X/SDXL | Dev placeholders + HF hooks | GPU stack deferred to Colab/Modal training phase |
| Object storage | Cloudflare R2 | Local `storage/` + MinIO | R2 requires card even for free tier |
| API hosting | Render primary | HF Spaces + docker compose | Avoid card-gated clouds |
| Supabase | Required in blueprint | Optional | Guest JWT + SQLite default |
| Qdrant Cloud | Cloud free tier | Docker Qdrant only | No cloud account required |
| Modal training | $30 credit | Colab + Kaggle only | Modal needs payment method |
