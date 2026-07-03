# AURA BUILD LOG
Last updated: 2026-07-04, by Measurement Extraction brick

## Live & Frozen
- Backend: https://aura1-3rk2.onrender.com
- Frozen files/routes:
  - `services/api/api/v1/avatar.py` — POST /analyze, POST /check-quality, GET /measurements, POST /upload
  - `apps/mobile/lib/core/api_client.dart` — analyzeBody(), checkImageQuality(), getMeasurements() signatures
  - `services/api/core/models.py` — BodyProfile schema
  - Auth/JWT flow (all auth routes)
  - Router route names
- Env vars set on Render: GROQ_API_KEY, HUGGINGFACE_API_KEY, DATABASE_URL, SECRET_KEY

## Bricks shipped
| Brick | Date | What shipped | New frozen items | Open issues |
|---|---|---|---|---|
| Phase 2 (Voice+BodyMesh+TryOn) | earlier | Voice pipeline, body mesh, try-on | auth flow, router | body-mesh confidence was hardcoded |
| Measurement Extraction | 2026-07-04 | Hybrid MediaPipe+VLM measurement pipeline, real confidence scoring, hard-reject <80%, retake UI dialog | avatar.py endpoints, api_client.dart avatar methods, BodyProfile model | Need to verify MediaPipe model download on Render cold start |

## Process notes (from Step 7 of each brick)
- Phase 2: (pre-existing)
- Measurement Extraction: Direct path. Step 1 trace found the hardcoded confidence issue immediately. Step 2 research confirmed VLMs can't do geometric measurement — chose hybrid approach. No avoidable backtracks.