# Meeting Processor

Web application for automatic processing of meeting recordings. Upload audio, video, or text — the app transcribes (with speaker diarization) and produces structured results (summary, tasks, decisions) via an LLM.

## Stack

- **Frontend:** Vue 3 + Vite + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Celery + Redis
- **Database:** PostgreSQL + SQLAlchemy + Alembic
- **Transcription:** OpenAI Whisper + pyannote.audio
- **LLM:** OpenAI API
- **Auth:** Yandex OAuth 2.0 with corporate email domain allowlist (primary). Bitrix24 OAuth 2.0 is also implemented but hidden in the UI.

## Quick start

### 1. Infrastructure

```bash
docker compose up -d  # starts Postgres + Redis
```

### 2. Backend

```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill in Yandex OAuth + OpenAI keys
alembic upgrade head
uvicorn app.main:app --reload
# In another terminal:
celery -A app.tasks.worker worker --loglevel=info
```

System requirement: `ffmpeg` must be installed on the host for video processing.

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:5173

## Configuration

Required environment variables (see `backend/.env.example`):

- `DATABASE_URL`
- `REDIS_URL`
- `SECRET_KEY` — JWT signing key
- `YANDEX_CLIENT_ID`, `YANDEX_CLIENT_SECRET` — from Yandex OAuth app
- `ALLOWED_EMAIL_DOMAINS` — comma-separated list, e.g. `company.ru,company.com`
- `OPENAI_API_KEY`
- `BITRIX24_*` — optional; only needed if you re-enable the Bitrix24 login button

### How to get Yandex OAuth credentials

1. Go to https://oauth.yandex.ru and click **«Зарегистрировать приложение»**.
2. **Платформа:** «Веб-сервисы». **Callback URI:** `http://localhost:8000/api/v1/auth/yandex/callback` (add your prod URL later).
3. **Права (Scopes):** `login:email`, `login:info`.
4. Copy **ClientID** → `YANDEX_CLIENT_ID`, **Client secret** → `YANDEX_CLIENT_SECRET`.
5. Set `ALLOWED_EMAIL_DOMAINS` to your corporate email domain(s). Leave empty only for local dev — it disables the domain check.

The domain check runs on the `default_email` returned by Yandex after the user logs in. Users with personal `@yandex.ru` accounts (or any other non-allowlisted domain) are redirected back to the login page with a clear Russian error message.

### Enabling Bitrix24 login

The Bitrix24 flow is fully implemented on the backend (`/api/v1/auth/bitrix24/*`) but hidden in the UI. To enable it:

1. Create a local application on your Bitrix24 portal with redirect URI `http://localhost:8000/api/v1/auth/bitrix24/callback`. Requires a paid Bitrix24 plan.
2. Fill in `BITRIX24_CLIENT_ID`, `BITRIX24_CLIENT_SECRET`, `BITRIX24_DOMAIN` in `.env`.
3. Set `const BITRIX24_ENABLED = true` in `frontend/src/pages/LoginPage.vue`.
