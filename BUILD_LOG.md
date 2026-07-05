# AURA BUILD LOG
Last updated: 2026-07-05, by Voice Assistant brick

## Live & Frozen
- Backend: https://aura1-3rk2.onrender.com
- Frozen files/routes:
  - `services/api/api/v1/avatar.py` — POST /analyze, POST /check-quality, GET /measurements, POST /upload
  - `apps/mobile/lib/core/api_client.dart` — analyzeBody(), checkImageQuality(), getMeasurements() signatures
  - `services/api/core/models.py` — BodyProfile schema
  - Auth/JWT flow (all auth routes)
  - Router route names
- Env vars set on Render: GROQ_API_KEY, HUGGINGFACE_API_KEY, DATABASE_URL, SECRET_KEY
- Env vars NOT yet set: SARVAM_API_KEY (TTS falls back to HF MMS without it)

## Bricks shipped
| Brick | Date | What shipped | New frozen items | Open issues |
|---|---|---|---|---|
| Phase 2 (Voice+BodyMesh+TryOn) | earlier | Voice pipeline, body mesh, try-on | auth flow, router | body-mesh confidence was hardcoded |
| Measurement Extraction | 2026-07-04 | Hybrid MediaPipe+VLM measurement pipeline, real confidence scoring, hard-reject <80%, retake UI dialog | avatar.py endpoints, api_client.dart avatar methods, BodyProfile model | Need to verify MediaPipe model download on Render cold start |
| Voice Assistant | 2026-07-05 | Real conversational voice: Groq Whisper ASR → language-mirroring Stylist LLM → Sarvam TTS. Removed mock ASR + silent WAV. Voice-first mobile UI. | groq_asr.py, voice.py ConverseResponse schema (reply_audio_b64) | Deploy pending on Render (Docker rebuild). User must set SARVAM_API_KEY on Render for TTS. |

## Process notes (from Step 7 of each brick)
- Phase 2: (pre-existing)
- Measurement Extraction: Direct path. Step 1 trace found the hardcoded confidence issue immediately. Step 2 research confirmed VLMs can't do geometric measurement — chose hybrid approach. No avoidable backtracks.
- Voice Assistant: Direct path. Discovery found 3 landmines (mock ASR, silent TTS, on-device STT bypass). Approach A (Groq+Sarvam) scored highest. One minor bugfix (te-IN normalization case mismatch). Render Docker deploy is slow on free tier (~20-30 min) — still pending at commit time.