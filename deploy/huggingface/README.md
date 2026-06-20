# Deploy API on Hugging Face Spaces (no credit card)

1. Create account at https://huggingface.co (email only).
2. New Space → **Docker** → name `fashion-ai-api`.
3. Upload or connect this repo; set **Root directory** to repo root.
4. Use `deploy/huggingface/Dockerfile` as the Space Dockerfile (or copy its contents to the Space root `Dockerfile`).
5. Space **Settings → Variables** (secrets):
   - `GROQ_API_KEY`
   - `HUGGINGFACE_API_KEY`
   - `APP_SECRET_KEY` (random string)
   - `DATABASE_URL=sqlite+aiosqlite:///./data/fashionai.db`
   - `STORAGE_BACKEND=local`
   - `STORAGE_LOCAL_PATH=./data/storage`
6. Open the Space URL from your Flutter app (`API_BASE_URL`).

Free tier limits apply (CPU, sleep). For 24/7 uptime without card, run `docker compose` on a home PC or use Tailscale.
