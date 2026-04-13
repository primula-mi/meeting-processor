# Meeting Processor

Web application for automatic processing of meeting recordings. Upload audio, video, or text — the app transcribes (with speaker diarization) and produces structured results (summary, tasks, decisions) via an LLM.

## Stack

- **Frontend:** Vue 3 + Vite + TypeScript + Tailwind CSS
- **Backend:** FastAPI + Celery + Redis
- **Database:** PostgreSQL + SQLAlchemy + Alembic
- **Transcription:** OpenAI Whisper + pyannote.audio
- **LLM:** OpenAI API
- **Auth:** Bitrix24 SSO (OAuth 2.0)

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
cp .env.example .env  # fill in Bitrix24 + OpenAI keys
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
- `BITRIX24_CLIENT_ID`, `BITRIX24_CLIENT_SECRET`, `BITRIX24_DOMAIN`
- `OPENAI_API_KEY`
