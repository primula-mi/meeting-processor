# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meeting Processor — a web application for automatic processing of meeting recordings. Users upload video, audio, or text. The app transcribes audio/video with speaker diarization, processes the transcript via LLM using a configurable system prompt, and outputs structured results (summary, task list, decisions).

**Authentication:** Two OAuth providers are implemented. **Yandex** (primary) is the default login shown in the UI and is restricted to a whitelist of corporate email domains via `ALLOWED_EMAIL_DOMAINS`. **Bitrix24** SSO is fully implemented on the backend but hidden in the UI via a `BITRIX24_ENABLED` flag in `frontend/src/pages/LoginPage.vue` — it can be enabled when a paid Bitrix24 plan is available. The `User` model stores both `yandex_id` and `bitrix24_id` (both nullable); each user is created with exactly one of them depending on the provider used.

## Tech Stack

- **Frontend:** Vue 3 (Vite) + TypeScript, Tailwind CSS, shadcn-vue components. Dark/light theme support.
- **Backend:** Python (FastAPI), Celery + Redis for async task queues.
- **Database:** PostgreSQL with SQLAlchemy ORM and Alembic migrations.
- **File Storage:** MinIO / S3-compatible (local storage for MVP).
- **Transcription:** Three providers selectable per-user: `local` (OpenAI Whisper `large-v3` + pyannote-audio speaker diarization, requires GPU), `openai` (Whisper API, cloud, no diarization), `assemblyai` (cloud with built-in speaker diarization). Default set via `TRANSCRIPTION_PROVIDER` env var.
- **LLM:** Two providers selectable per-user: `openai` (OpenAI API) or `ollama` (local LLM server). Default set via `LLM_PROVIDER` env var. Users can switch providers and models from the Settings page.
- **System dependency:** `ffmpeg` for extracting audio from video files.

## Project Structure

```
frontend/          # Vue 3 + Vite + TypeScript app
backend/           # FastAPI application
  app/
    api/           # REST API route handlers
    models/        # SQLAlchemy models
    schemas/       # Pydantic schemas
    services/      # Business logic (transcription, LLM processing)
    tasks/         # Celery task definitions
    core/          # Config, security, dependencies
  alembic/         # Database migrations
```

## Build & Run Commands

### Backend
```bash
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload              # Dev server
celery -A app.tasks.worker worker --loglevel=info  # Celery worker
alembic upgrade head                        # Run migrations
alembic revision --autogenerate -m "msg"    # Create migration
```

### Frontend
```bash
cd frontend
npm install
npm run dev          # Dev server
npm run build        # Production build
npm run lint         # Lint
npm run type-check   # TypeScript check
```

## Architecture

- Frontend communicates with Backend via REST API. All endpoints except `/auth/*` require JWT authentication.
- Long-running tasks (transcription, LLM processing) run asynchronously via Celery workers. The frontend polls task status every 5 seconds.
- Processing pipeline: Upload -> Extract audio (if video, via ffmpeg) -> Whisper transcription -> pyannote speaker diarization -> LLM analysis -> Structured JSON result.
- Meeting status flow: `pending` -> `transcribing` -> `processing` -> `done` | `failed`.

## Database Schema

- **User:** `id`, `yandex_id` (nullable), `bitrix24_id` (nullable), `email`, `name`, `system_prompt` (text), `created_at`
- **Meeting:** `id`, `user_id` (FK), `title`, `input_type` (audio/video/text), `original_file_url`, `transcript` (text), `result_json` (jsonb), `status` (pending/transcribing/processing/done/failed), `created_at`

All queries must be scoped to the authenticated user (row-level security at API layer).

## LLM Output Structure

The LLM must return structured JSON with these fields:
- `summary` — meeting summary
- `tasks` — array of objects: task description, assigner, assignee (if identified), deadline
- `decisions` — list of decisions made

Use JSON Mode or Function Calling to enforce structure.

## Key Constraints

- File size limits: audio 500 MB, video 1 GB.
- Accepted audio formats: `.mp3, .wav, .ogg, .m4a`. Video: `.mp4, .mkv, .webm`. Text: `.txt, .docx`.
- Each user has a customizable system prompt stored in the DB, with a "reset to default" option.
- The language of the UI and prompts is Russian.
