# Intelligent Media Processing Pipeline ("MediaIntel AI")

An asynchronous, AI-assisted image analysis platform. Users upload images
(e.g. vehicle photos), the backend queues them for background processing,
and a Celery worker runs a battery of OpenCV/Tesseract-based heuristic
checks (blur, brightness, duplicates, OCR, Indian vehicle-number format
validation, registration-state detection, screenshot/photo-of-photo/
tampering heuristics, EXIF metadata) before writing structured results to
PostgreSQL. A React dashboard (branded "MediaIntel AI") shows live status,
detailed per-image results, state-wise vehicle analytics, history, and a
public marketing homepage.

## 1. Project Overview

This is a backend + AI engineering take-home implementation. It is built to
be run and explained end-to-end, not just skimmed: every check the spec
calls "bonus" is implemented (retries, concurrency safety, rate limiting,
analytics, Docker, tests, benchmarking) rather than stubbed out.

## 2. Problem Statement

Manually reviewing large volumes of uploaded images (e.g. vehicle photos
submitted through a mobile app) for basic quality and format problems -
blur, poor lighting, duplicates, unreadable plates - doesn't scale. This
system automates that first pass: it doesn't decide "fraud or not", it
surfaces structured, confidence-scored signals a human reviewer can act on
quickly.

## 3. Features

- JWT auth: register / login / logout / current-user, protected routes
- Drag-and-drop image upload with client + server-side validation
- Fully asynchronous processing via FastAPI -> Redis -> Celery
- 10 analysis checks: blur, brightness, duplicate (perceptual hash), OCR,
  Indian vehicle-number format validation, dimension/aspect-ratio checks,
  screenshot heuristic, photo-of-photo heuristic, EXIF metadata, tampering
  heuristic
- **Indian vehicle registration state detection**: once OCR + format
  validation succeed, the plate's 2-letter prefix is resolved to its
  registration state/UT via a data-driven mapping (all 28 states + 8 UTs,
  including dual-code states like Odisha OD/OR, Telangana TS/TG,
  Uttarakhand UK/UA). Clearly labeled as registration state, never the
  vehicle's current location.
- Confidence scores on every heuristic result, including state detection
- Status polling (pending -> processing -> completed/failed) with automatic
  retry (up to 3 attempts, exponential backoff) and manual retry
- Concurrency-safe worker (status-guarded job claiming, `task_acks_late`)
- Public marketing homepage ("MediaIntel AI") + About page, professional
  SaaS dashboard with stat cards + charts, image history with search/
  filter/state/date-range/pagination, analytics page with a dedicated
  State-wise Vehicle Analysis section (bar + pie charts, ranking cards, CSV
  export), profile page
- Structured logging, `/health` check, rate limiting (login/register/upload)
- Fully responsive (desktop/tablet/mobile) with a collapsible sidebar/navbar
- Dockerized (Postgres, Redis, backend, worker, frontend) - one command up
- pytest suite (auth, upload validation, status/result/vehicle/state-wise
  endpoints, unit tests for each heuristic including state lookup, health
  check)
- `benchmark.py` for measuring upload/processing latency
- Optional seed script for dashboard demo data (includes state-tagged
  sample vehicles)

## 4. Architecture

```
React Frontend (Vite, port 5173)
        |
FastAPI API (port 8000) --- JWT auth, validation, REST
        |
PostgreSQL (persistent state: users, images, analysis_results, processing_jobs)
        |
Redis (Celery broker + result backend)
        |
Celery Worker (--concurrency=4) --- runs app/analysis/pipeline.py
        |
Image Analysis Pipeline (OpenCV, Pillow, pytesseract, imagehash)
        |
PostgreSQL (results written back)
        |
React Dashboard polls GET /api/images/{id}/status until completed/failed
```

The upload endpoint never blocks on analysis - it validates, persists
metadata, enqueues a Celery task, and returns `202 Accepted` immediately.

## 5. System Flow

1. User registers/logs in -> receives a JWT.
2. User uploads an image -> server validates type/size/content, stores the
   file with a UUID-based filename, creates an `images` row (`status=pending`),
   and enqueues `process_image_task`.
3. Worker claims the job (`pending -> processing`, guarded so a second
   worker can't double-claim it), runs the full analysis pipeline, writes an
   `analysis_results` row, and sets `status=completed` (or `failed` after
   exhausting retries).
4. Frontend polls `/api/images/{id}/status` every 2s until `completed` or
   `failed`, then loads `/api/images/{id}/result`.

## 6. Database Design

**users**: id, name, email (unique), password_hash, created_at

**images**: id, processing_id (UUID, unique), user_id (FK), filename,
file_path, mime_type, file_size, width, height, status, created_at,
completed_at, error_message
- indexes: processing_id, user_id, status, composite (user_id, status)

**analysis_results**: id, image_id (FK, unique - one result per image), all
per-check fields (blur/brightness/duplicate/ocr/vehicle/screenshot/
photo-of-photo/metadata/tampering/dimensions), plus **vehicle_number,
vehicle_number_valid, state_code, state_name, state_confidence**,
overall_score, created_at
- indexes: phash (duplicate lookups), vehicle_number, state_code,
  state_name, composite (state_code, state_name) for state-wise analytics

**processing_jobs**: id, image_id (FK), status, retry_count, started_at,
completed_at, last_error, created_at
- one row per processing *attempt*, so retry history is fully auditable

All foreign keys use `ondelete="CASCADE"` so deleting a user or image
cleans up dependent rows.

### Registration-state mapping

`backend/app/analysis/vehicle_state_codes.py` holds a single data-driven
dict (`STATE_CODE_MAP`) mapping every Indian state/UT registration prefix
to its state name - not if/else branches - so adding/adjusting a code is a
one-line change. It covers all 28 states and 8 union territories, including
states with more than one valid prefix (Odisha OD/OR, Telangana TS/TG,
Uttarakhand UK/UA).

## 7. API Documentation

Interactive docs (Swagger UI) are available at `http://localhost:8000/docs`
once the backend is running. Summary:

```
POST   /api/auth/register
POST   /api/auth/login
POST   /api/auth/logout
GET    /api/auth/me

POST   /api/images/upload
GET    /api/images                          (supports ?status, ?search, ?state, ?date_from, ?date_to)
GET    /api/images/{processing_id}
GET    /api/images/{processing_id}/status
GET    /api/images/{processing_id}/result
GET    /api/images/{processing_id}/vehicle   (number + registration state)
GET    /api/images/{processing_id}/failure
POST   /api/images/{processing_id}/retry
DELETE /api/images/{processing_id}

GET    /api/analytics/summary
GET    /api/analytics/state-wise             (?date_from, ?date_to, ?status)
GET    /api/analytics/state-wise/export      (CSV download)
GET    /health
```

## 8. Setup Instructions

### Prerequisites
- Docker + Docker Compose (recommended path), OR
- Python 3.12+, Node 20+, PostgreSQL 16, Redis 7, Tesseract OCR (manual path)

### Fastest path: Docker Compose
```bash
git clone <this-repo>
cd intelligent-media-processing
cp .env.example .env        # edit JWT_SECRET_KEY and DB password before real use
docker compose up --build
```
- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Health check: http://localhost:8000/health

## 9. Environment Variables

See `.env.example` at the repo root (and `backend/.env.example`). Key
variables: `DATABASE_URL`, `CELERY_BROKER_URL`, `CELERY_RESULT_BACKEND`,
`JWT_SECRET_KEY`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `UPLOAD_DIR`,
`MAX_UPLOAD_SIZE_MB`, `ALLOWED_MIME_TYPES`, `CORS_ORIGINS`, and the three
rate-limit settings. Never commit a real `.env` - only `.env.example` is
tracked.

## 10. Docker Instructions

```bash
docker compose up --build          # start everything
docker compose up -d               # start in background
docker compose logs -f backend     # tail backend logs
docker compose logs -f worker      # tail worker logs
docker compose down                # stop
docker compose down -v             # stop + wipe volumes (DB, uploads)
```
Services: `postgres`, `redis`, `backend`, `worker`, `frontend`. Postgres and
Redis have healthchecks; `backend`/`worker` wait on those before starting.

## 11. Frontend Instructions (manual, without Docker)

```bash
cd frontend
npm install
npm run dev          # http://localhost:5173
```
Set `VITE_API_BASE_URL` in a `frontend/.env` file if the backend isn't on
`http://localhost:8000`.

## 12. Backend Instructions (manual, without Docker)

```bash
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
# install tesseract-ocr for your OS, e.g. `apt install tesseract-ocr` / `brew install tesseract`
cp .env.example .env   # point DATABASE_URL / REDIS at your local services
uvicorn app.main:app --reload
```
Tables are created automatically on startup via `init_db()`. For a
production-style workflow, replace this with Alembic migrations.

## 13. Celery / Redis Instructions

```bash
# Terminal 1: Redis (or use Docker: docker run -p 6379:6379 redis:7-alpine)
redis-server

# Terminal 2: Celery worker
cd backend
celery -A app.workers.celery_app worker --loglevel=info --concurrency=4
```
Increase `--concurrency` to run more parallel jobs on one worker process, or
run multiple `docker compose up --scale worker=3` replicas for horizontal
scaling (see Section 21, Scalability).

## 14. Testing

```bash
cd backend
# point .env / DATABASE_URL at a disposable test database first
pytest -v
```
Covers: registration, login (valid/invalid), current-user auth guard,
upload validation (valid image, rejected type, rejected corrupted file,
auth-required), status/result/failure endpoints, unit tests for blur/
brightness/vehicle-number/duplicate-hash heuristics, and `/health`.

## 15. Sample API Requests

```bash
# Register
curl -X POST http://localhost:8000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"name":"Asha Rao","email":"asha@example.com","password":"SecurePass123!"}'

# Upload (use the access_token from the response above)
curl -X POST http://localhost:8000/api/images/upload \
  -H "Authorization: Bearer <token>" \
  -F "file=@vehicle.jpg"

# Poll status
curl http://localhost:8000/api/images/<processing_id>/status \
  -H "Authorization: Bearer <token>"
```

## 16. Sample API Responses

Upload:
```json
{"processing_id": "b1e2...", "status": "pending", "message": "Image uploaded successfully"}
```

Result (completed):
```json
{
  "processing_id": "b1e2...",
  "status": "completed",
  "image": {"filename": "a1b2c3.jpg", "width": 1920, "height": 1080, "file_size": 482113, "mime_type": "image/jpeg"},
  "analysis": {
    "blur": {"score": 245.4, "is_blurry": false, "confidence": 0.91},
    "brightness": {"score": 132.5, "is_low_light": false, "confidence": 0.88},
    "duplicate": {"is_duplicate": false, "duplicate_of": null, "similarity": null},
    "ocr": {"text": "KA05MN1234", "confidence": 0.87},
    "vehicle_number": {"value": "KA05MN1234", "valid_format": true},
    "vehicle_state": {"state_code": "KA", "state": "Karnataka", "confidence": 0.91},
    "screenshot": {"detected": false, "confidence": 0.2},
    "photo_of_photo": {"detected": false, "confidence": 0.15},
    "tampering": {"detected": false, "confidence": 0.41},
    "metadata": {"has_exif": true, "camera_make": "Samsung", "camera_model": "SM-G991B", "exif_datetime": "2026:03:11 14:22:01", "has_gps": false, "editing_software": null},
    "overall_score": "GOOD"
  }
}
```

Vehicle detail (`GET /api/images/{processing_id}/vehicle`):
```json
{
  "vehicle_number": "KA05MN1234",
  "valid_format": true,
  "state_code": "KA",
  "state": "Karnataka",
  "confidence": 0.91
}
```

State-wise analytics (`GET /api/analytics/state-wise`):
```json
{
  "total_vehicles_detected": 156,
  "top_state": "Karnataka",
  "top_state_count": 45,
  "by_state": [
    {"state": "Karnataka", "state_code": "KA", "count": 45},
    {"state": "Maharashtra", "state_code": "MH", "count": 32},
    {"state": "Tamil Nadu", "state_code": "TN", "count": 27}
  ]
}
```

## 17. Screenshots

Not included in this generated deliverable - run the app locally and the
Dashboard/Upload/Result/History/Analytics pages described in Section 3 will
render as described. Add screenshots here once you've run it.

## 18. Assumptions

- "Indian vehicle number validation" means structural/regex format
  validation only, using OCR'd text - it does not call any government RTO
  database and cannot confirm a plate is genuine or currently registered.
- Registration-state detection is derived purely from the plate prefix
  once the format validates - it identifies where the plate was
  **registered**, never where the vehicle currently is; the UI and API
  responses label this explicitly as "Registration State" for this reason.
- Local filesystem storage for uploads is acceptable for development
  (see Section 21/25 for the production alternative).
- One `analysis_results` row per image (no need to store history of
  historical re-analyses beyond the current retry's outcome).
- A user's images are private to that user (no shared/admin view) since the
  spec didn't call for a multi-tenant admin role.

## 19. Trade-offs

| Choice | Why | Production alternative |
|---|---|---|
| Local disk storage | Simple for dev | S3 / GCS with signed URLs |
| Redis + Celery | Battle-tested, simple to run locally | Same, or managed (SQS+Lambda, Cloud Tasks) |
| Heuristic analysis (OpenCV/regex) instead of trained ML models | Fast, explainable, no GPU/training data needed | Fine-tuned CV models for blur/tamper detection where accuracy matters more |
| Tesseract OCR instead of a paid OCR API | Free, self-hosted, no per-call cost | Google Vision / AWS Textract for higher accuracy on hard plates |
| Basic ELA-based tampering heuristic | Cheap, explainable | Forensic tooling (e.g. dedicated ELA/CFA-analysis libraries), or a trained tamper-detection model |
| JWT (stateless) auth instead of OAuth | Simpler for a take-home scope | OAuth2/OIDC if integrating with external identity providers |
| Polling for status instead of WebSockets | Simpler client/server code, works everywhere | WebSocket or SSE push for lower latency at scale |

## 20. Limitations

- Heuristics (screenshot / photo-of-photo / tampering / blur / brightness)
  are threshold-based and were tuned on general assumptions, not a labeled
  dataset - false positives/negatives are expected and confidence scores
  reflect heuristic certainty, not calibrated probability.
- OCR accuracy depends heavily on plate angle, lighting, and font; no
  plate-specific super-resolution or perspective correction is applied.
- Duplicate detection compares only against a given user's own prior
  uploads, not the whole system (by design, to avoid cross-user data
  exposure) - this can be extended if cross-user dedup is required.
- No admin/moderation UI is included.

## 21. Scalability

- **Worker concurrency**: increase `--concurrency` per worker, or run more
  worker containers/pods (`docker compose up --scale worker=N`, or a
  Kubernetes Deployment/HPA on CPU or Celery queue length in production).
- **Database**: add read replicas for analytics queries as volume grows;
  the existing indexes (user_id, status, phash) cover the current query
  patterns.
- **Storage**: swap local disk for S3/GCS (Section 25) to decouple worker
  count from any single machine's disk.
- **Queue**: Redis is fine at moderate scale; for very high throughput,
  consider a managed broker (SQS, RabbitMQ cluster) sized for the load.

## 22. Failure Handling

- Upload-time errors (bad type/size/corrupted content) return `400`/`413`
  immediately and never reach the queue.
- Processing errors are caught in the Celery task, logged with
  `processing_id`, and retried up to 3 times with backoff
  (`10s, 20s, 30s`) via `self.retry(...)`. After the final attempt, the
  image is marked `failed` with `error_message` set, and the failure is
  queryable via `GET /api/images/{id}/failure`.
- The task claims a job only if it's still `pending`, so a worker crash
  mid-job (caught by `task_acks_late` + `task_reject_on_worker_lost`)
  results in the task being redelivered rather than silently lost, without
  two workers racing on the same image.

## 23. Security

- Passwords hashed with bcrypt (`passlib`); never logged or returned.
- JWT bearer auth on all non-auth, non-health endpoints; tokens expire
  (`ACCESS_TOKEN_EXPIRE_MINUTES`, default 60m).
- Upload validation: declared MIME type checked against an allow-list,
  actual bytes verified with Pillow (`Image.verify()`), size capped
  (`MAX_UPLOAD_SIZE_MB`), filenames replaced with a fresh UUID (no
  user-controlled filenames ever touch the filesystem - prevents path
  traversal).
- SQL injection protected by SQLAlchemy's parameterized queries throughout.
- CORS restricted to the configured origins (`CORS_ORIGINS`).
- Rate limiting on `/api/auth/login`, `/api/auth/register`, and
  `/api/images/upload` via `slowapi` (429 on limit exceeded).
- No secrets in source; all configuration is environment-variable driven
  (`.env`, gitignored).

## 24. Performance Benchmark

Run:
```bash
cd backend
python benchmark.py --image sample.jpg --count 5 --base-url http://localhost:8000 --token <JWT>
```
This measures upload response time and end-to-end processing time (upload
-> `completed`/`failed`) for N concurrent uploads. Example output shape:
```
Avg upload response time: 0.18 sec
Avg end-to-end processing time: 2.8 sec
```
Actual numbers depend entirely on your hardware, image resolution, and
whether Tesseract has to process a large image - treat these as relative
indicators, not fixed guarantees.

## 25. Cost Optimization

**Development** (as configured here): local Postgres, local disk storage,
local Redis, local Celery worker - $0 infra cost, everything in Docker
Compose on one machine.

**Production path**:
- Object storage (S3/GCS) instead of local disk - pay per GB stored/served,
  and decouples storage from compute so workers can scale independently.
- Managed PostgreSQL (RDS/Cloud SQL) - offloads backup/patching/HA.
- Managed Redis (ElastiCache/Memorystore) for the Celery broker.
- Autoscaling workers, scaled on queue depth rather than a fixed replica
  count, so you pay for capacity only when there's a backlog.

**Ways to cut cost further**:
- Resize/compress images before running OpenCV/Tesseract on them (most
  cost is proportional to pixel count).
- Cache duplicate-check phashes in Redis instead of hitting Postgres for
  every comparison at high volume.
- Batch OCR calls if migrating to a paid OCR API (per-image API costs
  usually beat per-request overhead when batched).
- Scale workers to zero during idle periods if using a serverless queue
  consumer (e.g. Cloud Run jobs, Lambda) instead of always-on containers.

## 26. Deployment

- **Backend**: build `backend/Dockerfile`, push to a registry, deploy to
  any container platform (ECS/Cloud Run/Render/Fly.io). Set all vars from
  Section 9 via the platform's secret/env management - never bake them into
  the image.
- **Worker**: same image as backend, different `command`
  (`celery -A app.workers.celery_app worker ...`) - deploy as a separate
  service so it scales independently of the API.
- **Frontend**: `npm run build` produces static assets in `frontend/dist`;
  serve via any static host (Vercel/Netlify/S3+CloudFront/Nginx). Set
  `VITE_API_BASE_URL` to the deployed backend URL at build time.
- **Database**: managed Postgres; run `init_db()` once (or migrate to
  Alembic) against it before first traffic.
- **Redis**: managed Redis reachable by both backend and worker.
- No live URL is provided with this deliverable - it was generated as
  source code, not deployed to a hosting account.

## 27. Future Improvements

- Replace `Base.metadata.create_all` with Alembic migrations for schema
  versioning.
- WebSocket/SSE push instead of polling for status updates.
- Admin/moderation dashboard across all users.
- Cross-user duplicate detection (with appropriate access controls).
- Swap heuristic tamper/screenshot detection for trained models once
  labeled data is available.
- Refresh-token rotation and true server-side JWT invalidation on logout.

## AI Usage Disclosure

AI tools (Claude) were used to generate the full initial implementation of
this project from the take-home specification - backend (FastAPI models,
schemas, routers, Celery task, all ten analysis heuristics), frontend
(React pages/components/styling), Docker configuration, pytest suite,
benchmark script, and this README - in a single generation pass based on
the provided requirements document. A second pass then added Indian
vehicle registration-state detection (data-driven state/UT mapping, a new
`/vehicle` endpoint, new `analysis_results` columns and indexes,
state-wise analytics + CSV export) and a frontend redesign (public
homepage, "MediaIntel AI" branding, state filters, mobile-responsive
navigation) on top of the existing codebase, without removing or
simplifying any previously implemented feature.

What this means in practice for anyone extending this repo:
- Architectural decisions (async pipeline via Celery, one-result-per-image
  schema, status-guarded job claiming for concurrency safety, heuristic
  vs. ML-model approach for analysis, JWT vs OAuth, polling vs WebSockets,
  a single data-driven dict for state-code lookups instead of branching
  logic) were made deliberately based on the spec's stated priorities
  (functional over demo-only, explainable over black-box, easy to run
  locally, easy to extend).
- The code has **not** been executed against a live PostgreSQL/Redis/
  Tesseract/npm stack in the environment that generated it (no network
  access was available there to install dependencies or run Docker).
  What *was* done in that environment: every backend `.py` file was
  syntax-checked with `py_compile` (passes cleanly, including after the
  state-detection changes), and every frontend `.jsx`/`.js` file was
  checked for balanced brackets and for every relative import resolving
  to a real file (also clean). That is a syntax/reference check, not a
  runtime test - it doesn't catch logic errors, dependency-version
  incompatibilities, or database-level issues. Before relying on this in
  an interview or production setting, run it locally end-to-end using
  Section 8-14 above, run `pytest`, and review the worker logs on a real
  upload - that is the recommended verification step and hasn't been
  substituted with a claim of "tested and passing."
- Bugs to watch for on first run are typical of generated-but-unexecuted
  code: dependency version mismatches (see `requirements.txt` /
  `package.json` if `pip`/`npm` resolve slightly different transitive
  versions), environment-specific issues (Tesseract binary path, Postgres
  UUID extension availability on older Postgres versions - 16 is assumed
  here), and the state-detection confidence formula in
  `analysis/vehicle.py` is a heuristic starting point, not a calibrated
  model - worth tuning once you have real OCR output to compare against.

## 28. Rate Limits (reference)

| Endpoint | Limit |
|---|---|
| `POST /api/auth/login` | 5/minute/IP |
| `POST /api/auth/register` | 5/minute/IP |
| `POST /api/images/upload` | 20/minute/IP |

Exceeding a limit returns `429 Too Many Requests`.

## 29. Exact Commands To Run The Project

```bash
cd intelligent-media-processing
cp .env.example .env
# edit .env: set a real JWT_SECRET_KEY and POSTGRES_PASSWORD
docker compose up --build
# App: http://localhost:5173   API docs: http://localhost:8000/docs
```
Optional demo data:
```bash
docker compose exec backend python seed.py
```
Run tests (point DATABASE_URL at a disposable DB first, e.g. locally):
```bash
cd backend && pytest -v
```
Run benchmark (after logging in via the API to get a token):
```bash
cd backend && python benchmark.py --image sample.jpg --count 5 --token <JWT>
```

## 30. Project Structure & Key Files (for interview walkthrough)

```
backend/app/main.py               - FastAPI app, router registration, CORS, rate-limit wiring
backend/app/config.py             - env-driven settings (pydantic-settings)
backend/app/database.py           - SQLAlchemy engine/session/init_db
backend/app/models/               - users, images, analysis_results, processing_jobs
backend/app/schemas/              - Pydantic request/response models
backend/app/api/auth.py           - register/login/logout/me
backend/app/api/images.py         - upload/status/result/vehicle/failure/retry/list/delete
backend/app/api/analytics.py      - dashboard summary + state-wise vehicle analytics + CSV export
backend/app/api/health.py         - DB/Redis/worker health check
backend/app/utils/security.py     - password hashing + JWT
backend/app/utils/files.py        - upload validation, path-traversal-safe storage
backend/app/analysis/*.py         - one file per heuristic check (explain any of these first)
backend/app/analysis/vehicle_state_codes.py - data-driven state/UT code mapping
backend/app/analysis/pipeline.py  - orchestrates all checks for one image
backend/app/workers/celery_app.py - Celery config (acks_late, prefetch=1 for fair concurrency)
backend/app/workers/tasks.py      - the actual background job: claim -> analyze -> persist -> retry-on-failure
backend/tests/                    - pytest suite
backend/benchmark.py              - latency/concurrency measurement script
backend/seed.py                   - demo data for the dashboard (state-tagged)
frontend/src/pages/Home.jsx       - public marketing homepage (hero, features, how-it-works, stats, CTA)
frontend/src/pages/About.jsx      - public about page
frontend/src/pages/               - one file per page listed in Section 3, plus Home/About
frontend/src/components/PublicNavbar.jsx / SiteFooter.jsx - public site chrome
frontend/src/utils/indianStates.js - shared state dropdown list (mirrors the backend mapping)
frontend/src/services/api.js      - single Axios instance + auth interceptor
frontend/src/context/AuthContext.jsx - token/user state, used by ProtectedRoute
docker-compose.yml                - postgres, redis, backend, worker, frontend
```

If asked "walk me through a request": start at `frontend/src/pages/Upload.jsx`
-> `POST /api/images/upload` (`backend/app/api/images.py`) -> validation
(`utils/files.py`) -> DB insert -> `process_image_task.delay(...)`
(`workers/tasks.py`) -> `analysis/pipeline.py` runs all ten checks plus
state detection (`analysis/vehicle.py` + `vehicle_state_codes.py`) ->
result persisted -> frontend polling (`ProcessingDetails.jsx`) picks up
`status=completed` -> `AnalysisResult.jsx` renders the stored result,
including the Vehicle Information card and Final Assessment Summary.
