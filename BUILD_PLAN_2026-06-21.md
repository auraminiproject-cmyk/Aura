# AURA BUILD PLAN — Session 2026-06-21

## Build Order Rationale

Critical gaps first → backend before frontend → low-cost quick wins before high-cost items → dependencies before dependents.

---

## Build Item #1: Render Sleep Prevention
```
Requirement:       Render free tier sleeps after 15min inactivity (C2 / Section 9.4)
Status:            MISSING
Files to Create:   services/api/core/keep_alive.py
Files to Modify:   services/api/main.py, .github/workflows/ci.yml
What to Build:     Background async task that pings /health every 10min to prevent Render sleep.
                   Also add UptimeRobot-compatible external ping endpoint.
Blueprint Ref:     9.4 — Render sleep detection/prevention/recovery
Depends On:        None
Token Cost:        LOW
Risk:              None — additive only, no existing feature touched
Verification:      curl https://aura1-3rk2.onrender.com/health → 200
```

---

## Build Item #2: LiteLLM Proxy Integration
```
Requirement:       Backend must route LLM calls through LiteLLM proxy (C1 / Section 4.5)
Status:            PARTIAL — config exists, code bypasses it
Files to Modify:   services/agent/llm.py
What to Build:     Refactor llm.py to call LiteLLM proxy (localhost:4000 in Docker,
                   direct Groq/Ollama in prod) with automatic fallback chain.
                   Keep existing circuit breaker + offline fallback intact.
Blueprint Ref:     4.5 — LiteLLM Proxy, 5.23 — Model Router
Depends On:        None
Token Cost:        LOW
Risk:              LOW — llm.py is used by graph.py and response_gen.py. Same interface.
Verification:      curl -X POST https://aura1-3rk2.onrender.com/api/v1/chat/classify
                   -H "Authorization: Bearer <jwt>" -d '{"message":"hello"}' → 200
```

---

## Build Item #3: Per-User Rate Limiting
```
Requirement:       Rate limiting must be per-JWT user, not just per-IP (H7 / Section 3.2)
Status:            PARTIAL — IP-only via SlowAPI
Files to Modify:   services/api/core/rate_limit.py
What to Build:     Add user-aware key function that extracts user ID from JWT for
                   authenticated routes, falls back to IP for unauthenticated.
Blueprint Ref:     3.2 — API Gateway rate limiting
Depends On:        None
Token Cost:        LOW
Risk:              LOW — rate_limit.py is only 5 lines, limiter is global
Verification:      Rapid-fire 35 requests with same JWT → 429 after 30
```

---

## Build Item #4: VLM Integration (Qwen2.5-VL)
```
Requirement:       Vision-Language Model for analyzing clothing photos (C5 / Section 4.10)
Status:            MISSING
Files to Create:   services/agent/vlm.py
Files to Modify:   services/api/api/v1/design.py, services/agent/graph.py
What to Build:     VLM service that sends images to Groq's Llama Vision or HF Inference
                   for Qwen2.5-VL. Endpoints: analyze clothing in photo, describe outfit,
                   suggest improvements. Integrate into LangGraph as a new node.
Blueprint Ref:     4.10 — VLM: Qwen2.5-VL 7B
Depends On:        #2 (LiteLLM for routing)
Token Cost:        MED
Risk:              LOW — new file + new endpoint, existing design.py gets one new route
Verification:      curl -X POST .../api/v1/design/analyze-image with test image → 200 + description
```

---

## Build Item #5: TTS Kokoro Integration
```
Requirement:       Text-to-speech must produce real audio (H4 / Section 4.12)
Status:            PARTIAL — code exists, Kokoro not in requirements
Files to Modify:   requirements.txt, services/api/services/tts.py
What to Build:     Add kokoro and sounddevice to requirements. Update TTS to use
                   HF Inference API for Kokoro when local install unavailable
                   (Render has no GPU). Graceful: Kokoro local → HF TTS → silent WAV.
Blueprint Ref:     4.12 — TTS: Kokoro-82M
Depends On:        None
Token Cost:        LOW
Risk:              LOW — tts.py already has graceful fallback
Verification:      curl .../api/v1/chat/message with voice → response contains audio_base64 ≠ silent
```

---

## Build Item #6: Stateful Agent Orchestration
```
Requirement:       LangGraph agent must maintain conversation memory (H6 / Section 3.3)
Status:            PARTIAL — stateless per request
Files to Modify:   services/agent/graph.py, services/api/api/v1/chat.py
What to Build:     Add conversation history to GraphState. Load last N messages from
                   Redis/DB before each graph invocation. Pass history to LLM prompt
                   for context-aware responses.
Blueprint Ref:     3.3 — Stateful orchestration
Depends On:        #2 (LLM routing)
Token Cost:        MED
Risk:              MEDIUM — touches chat.py (working feature). Will use additive approach only.
Verification:      Send 2 messages in same session → 2nd response references 1st
```

---

## Build Item #7: Real Product Data Ingestion
```
Requirement:       RAG pipeline needs real product catalog (C4 / Section 6.3)
Status:            PARTIAL — only 3 hardcoded items
Files to Create:   scripts/ingest_products.py
Files to Modify:   services/api/core/startup.py, data/catalog/ (add JSON files)
What to Build:     Create product catalog JSON with 50+ Indian fashion items
                   (sarees, lehengas, kurtas, sherwanis) with real Myntra/AJIO/Amazon
                   affiliate URLs. Auto-ingest into Qdrant on startup via embeddings.
Blueprint Ref:     6.3 — Product ingestion, embedding pipeline
Depends On:        None (Qdrant + embeddings already work)
Token Cost:        MED
Risk:              LOW — startup.py seed is already called, just expanding it
Verification:      curl .../api/v1/search/products -d '{"query":"red wedding saree"}' → 5+ results
```

---

## Build Item #8: SDXL Outfit Generation via HF
```
Requirement:       Design screen must show AI-generated outfits (H1 / Section 4.13)
Status:            PARTIAL — returns placeholder PNGs
Files to Modify:   services/vision/generate_outfit.py
What to Build:     Call HF Inference API for Stable Diffusion XL with fashion-specific
                   prompts. ControlNet/LCM-LoRA via HF when available. Graceful fallback
                   to placeholder if HF is down or rate-limited.
Blueprint Ref:     4.13 — Diffusion: SDXL + LCM-LoRA
Depends On:        None
Token Cost:        MED
Risk:              LOW — same interface, just replacing placeholder with real API call
Verification:      curl .../api/v1/design/outfits → image_base64 is a real PNG (not solid color)
```

---

## Build Item #9: Virtual Try-On via HF Spaces
```
Requirement:       Try-on feature must composite outfit onto user photo (H2 / Section 4.14)
Status:            PARTIAL — returns input unchanged
Files to Modify:   services/vision/tryon.py
What to Build:     Call Kolors VTON via HF Spaces Gradio API. Send user photo + outfit
                   image → receive composited result. Fallback: simple overlay blend.
Blueprint Ref:     4.14 — Virtual Try-On: Kolors VTON
Depends On:        #8 (needs outfit images)
Token Cost:        MED
Risk:              LOW — same interface, replacing placeholder
Verification:      curl .../api/v1/avatar/tryon with images → result_image differs from input
```

---

## Build Item #10: Body Reconstruction via HF
```
Requirement:       Avatar must use real body measurements from photo (H3 / Section 4.16)
Status:            PARTIAL — returns placeholder SMPL-X params
Files to Modify:   services/vision/body_reconstruct.py
What to Build:     Use HF Inference API for body measurement estimation from photo.
                   Extract height, chest, waist, hip from pose estimation model output.
                   Keep placeholder SMPL-X structure but fill with real measurements.
Blueprint Ref:     4.16 — Body Reconstruct: HMR 2.0 + SMPL-X
Depends On:        None
Token Cost:        MED
Risk:              LOW — same interface, avatar endpoint already works
Verification:      curl .../api/v1/avatar/analyze with real photo → measurements vary by input
```

---

## Build Item #11: Drift Local DB (Offline-First)
```
Requirement:       Flutter must use Drift SQLite for offline data (C3 / Section 4.3)
Status:            PARTIAL — deps exist but no tables defined
Files to Create:   apps/mobile/lib/core/database.dart, apps/mobile/lib/core/database.g.dart
Files to Modify:   apps/mobile/lib/core/local_db.dart
What to Build:     Define Drift tables: CachedOutfits, CachedProducts, SyncQueue, UserPrefs.
                   Run build_runner to generate. Update local_db.dart to use Drift instead
                   of SharedPreferences for structured data.
Blueprint Ref:     4.3 — Mobile Local DB: Drift, 11.9 — Offline-first
Depends On:        None
Token Cost:        MED
Risk:              MEDIUM — touches local_db.dart. Will keep SharedPrefs for auth tokens.
Verification:      flutter analyze → 0 errors
```

---

## Build Item #12: i18n Runtime Loading
```
Requirement:       Flutter must load Telugu/Hindi/English strings at runtime (H5 / Section 6.1)
Status:            PARTIAL — flutter_i18n dep exists
Files to Create:   apps/mobile/assets/i18n/en.json, te.json, hi.json
Files to Modify:   apps/mobile/lib/app.dart (add FlutterI18n delegate)
What to Build:     Create i18n JSON files with all UI strings in en/te/hi. Wire up
                   FlutterI18n delegate in MaterialApp. Add language selector in profile.
Blueprint Ref:     6.1 — i18n
Depends On:        None
Token Cost:        LOW
Risk:              LOW — additive to app.dart, no existing feature broken
Verification:      flutter analyze → 0 errors
```

---

## Execution Order Summary

| Order | Item | ID | Cost | Deps |
|---|---|---|---|---|
| 1 | Render Sleep Prevention | C2 | LOW | — |
| 2 | LiteLLM Proxy Integration | C1 | LOW | — |
| 3 | Per-User Rate Limiting | H7 | LOW | — |
| 4 | VLM Integration (Qwen2.5-VL) | C5 | MED | #2 |
| 5 | TTS Kokoro/HF | H4 | LOW | — |
| 6 | Stateful Agent Orchestration | H6 | MED | #2 |
| 7 | Real Product Data Ingestion | C4 | MED | — |
| 8 | SDXL Outfit Generation | H1 | MED | — |
| 9 | Virtual Try-On | H2 | MED | #8 |
| 10 | Body Reconstruction | H3 | MED | — |
| 11 | Drift Local DB | C3 | MED | — |
| 12 | i18n Runtime Loading | H5 | LOW | — |

> [!IMPORTANT]
> **STOP** — Please confirm the build plan before I begin execution (Section 3).
> - Confirm order is acceptable
> - Reorder if needed
> - Any items to defer to next session?
