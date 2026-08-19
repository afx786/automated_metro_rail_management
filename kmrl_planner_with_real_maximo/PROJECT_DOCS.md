# PROJECT_DOCS.md

Team documentation for the KMRL Planner prototype. Written for people who have never seen
this codebase. Everything below was verified against the actual code in this repo (and, where
marked, by running the app from a clean checkout). If it says "this does not work" or "this is
only simulated", take it literally.

---

## 1. Overview

KMRL Planner is a decision-support **prototype** for Kochi Metro (KMRL) trainset maintenance
planning. Every night, a fleet of 25 trainsets (id `KM01`–`KM25`) has to be split across:

- **Service** — trains in active passenger service.
- **Standby** — healthy trains held as spare.
- **Maintenance** — trains that need cleaning, have open job cards, expired/invalid fitness
  certificates, or other issues.

The app fuses three data sources: trainset master data stored in a local SQLite database,
simulated IoT sensor readings, and simulated Maximo job-card status. The backend
(`planner.py`) applies business rules plus ML predictions to produce a recommended nightly
plan. There is also a CSV batch API and a small admin console for tweaking trainsets and
cleaning bays/teams.

- **Who it is for:** the planning/ops team (and developers extending it). There is no real
  end-user deployment.
- **Status:** a working prototype that runs locally and produces plans. It is **not**
  production software. Most external integrations are simulated (see §7).

---

## 2. Architecture

```
React (Vite) frontend   frontend/
      |
      | HTTP (default http://localhost:8000)
      v
FastAPI app             app/main.py
      |  mounts routers: health, trainsets, plans, iot, ml, admin
      v
Routers                 app/routers/*.py
      |
      +-- services: app/planner.py (rules + ML), app/optimizer.py (orchestration)
      +-- app/crud.py  (DB reads/writes, seeding, plan persistence)
      +-- app/ml_models.py   (loads scikit-learn models, with fallbacks)
      +-- app/csv_predictor.py (batch CSV predictions)
      +-- app/iot.py         (SIMULATED sensor data)
      +-- app/connectors_mock_maximo.py (SIMULATED Maximo job cards)
      v
SQLAlchemy ORM          app/models.py  ->  app/database.py
      v
SQLite                 kmrl_mock_maximo.db (created + seeded on first run)
```

Important: the **Maximo integration is simulated**. `connectors_mock_maximo.py` generates
synthetic job cards from a local JSON file (or generates them in code); it never talks to a
real Maximo instance. The IoT module (`iot.py`) generates random-but-cached sensor readings.
Treat them as demo data sources. There is one real thing here: the FastAPI + SQLAlchemy +
SQLite app itself, the planning logic, and the React frontend.

---

## 3. Setup instructions

These steps were executed on a clean `git clone` and verified to work (Python 3.13 on
Windows; the scripts target Python 3.11+, and requirements are pinned in `requirements.txt`).

### Backend

```bash
# clone and enter the project folder (note: the repo root contains one nested
# folder also named kmrl_planner_with_real_maximo/ with the actual project)
git clone <repo-url>
cd kmrl_planner_with_real_maximo/kmrl_planner_with_real_maximo

# virtualenv (Python 3.11+)
python -m venv venv
venv\Scripts\activate          # Windows
# source venv/bin/activate     # macOS/Linux

pip install -r requirements.txt

# run the API
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

On first start the app:

1. creates `kmrl_mock_maximo.db` (SQLite) next to the folder you launched from
   (`app/database.py` defaults to `sqlite:///./kmrl_mock_maximo.db`),
2. seeds 25 trainsets (`KM01`–`KM25`) with deterministic random data, and
3. seeds 3 cleaning bays (`Bay-1`..`Bay-3`) and 3 cleaning teams (`Team-A`..`Team-C`).

No manual "seed" step exists or is needed — it happens automatically at startup
(`app/main.py`, module scope).

Open the interactive API docs at `http://localhost:8000/docs`.

### Frontend

```bash
cd frontend
npm install
npm run dev      # serves at http://localhost:5173 (Vite, default)
```

The frontend calls the backend at `http://localhost:8000` by default. To point it elsewhere,
set the Vite env var before building/starting:

```bash
# Windows (PowerShell)
$env:VITE_API_BASE_URL="https://api.example.com"
# or put VITE_API_BASE_URL=... in frontend/.env
```

`VITE_API_BASE_URL` is read in `frontend/src/services/api.js`.

### Environment variables (backend)

| Variable        | Default                | Effect                                              |
| --------------- | ---------------------- | --------------------------------------------------- |
| `DATABASE_URL`  | `sqlite:///./kmrl_mock_maximo.db` | SQLAlchemy DB URL                        |
| `ADMIN_API_KEY` | `kmrl-admin-secret`    | API key required on every `/admin/*` request        |
| `CORS_ORIGINS`  | `http://localhost:5173`| Comma-separated allowed browser origins             |

Caveat verified in code: `python-dotenv` is in `requirements.txt` **but is never imported
anywhere**. `.env` files are therefore **not** loaded. Set these variables in your shell or
process environment; a `.env` file in the project will have no effect.

### ML models: committed, zero setup needed

The trained models are **committed to the repo** under `models/`
(`certificate_expiry_predictor.joblib` + `certificate_expiry_feature_columns.pkl`, and
`maintenance_urgency_scorer.joblib`), so a fresh clone loads the **real** models with no
manual steps. On startup the console prints one unambiguous line per model:

```
[ml] certificate_expiry: TRAINED MODEL LOADED (models/certificate_expiry_predictor.joblib)
[ml] maintenance_urgency: TRAINED MODEL LOADED (models/maintenance_urgency_scorer.joblib)
```

If a model file is missing (deleted, or the load fails), the app logs
`[ml] <name>: FALLBACK (DummyFitnessModel / DummyUrgencyModel) - no trained model found` and
uses rule/random fallbacks instead. That is the deliberate escape hatch for quick iteration
without model files — it is loudly announced, never silent.

To retrain from scratch (e.g. after editing a retrain script):

```bash
python models/retain_certificate_model.py
python models/retain_maintenance_model.py
```

The scripts save **directly into `models/`** — the same directory the app reads from — and
their output is plain ASCII, so no `PYTHONIOENCODING`/UTF-8 console workaround is needed.
After retraining, restart the backend and the startup log above should show
`TRAINED MODEL LOADED` for both models.

### Admin access

Every `/admin/*` route requires the header `X-API-Key: <key>`. Default dev key:
`kmrl-admin-secret` (change it with `ADMIN_API_KEY`). The Admin panel in the React app
stores whatever key you type in `localStorage` and sends it automatically.

---

## 4. API reference

Verified by enumerating the mounted app (`app.main`). **20 routes total.** Admin routes
require `X-API-Key` (marked 🔑).

### Root

| Method | Path  | Purpose | Auth |
| ------ | ----- | ------- | ---- |
| GET    | `/`   | Service banner + list of known endpoints | none |

### health — `app/routers/health.py`

| Method | Path      | Purpose        | Auth |
| ------ | --------- | -------------- | ---- |
| GET    | `/health` | Liveness check → `{"status":"ok"}` | none |

### trainsets — `app/routers/trainsets.py`

| Method | Path                     | Purpose                         | Auth |
| ------ | ------------------------ | ------------------------------- | ---- |
| GET    | `/trainsets/`            | List all trainsets (id, fitness, mileage, job-card open, needs-deep-clean) | none |
| POST   | `/trainsets/refresh/maximo` | Pull job-card status from the **simulated** Maximo connector and update rows | none |

### plans — `app/routers/plans.py`

| Method | Path            | Purpose | Auth |
| ------ | --------------- | ------- | ---- |
| POST   | `/plans/run`    | Generate a plan (optional JSON body: `target_service`, `target_standby`, `available_manpower`, `available_bays`), persist it, return payload | none |
| GET    | `/plans/stats`  | Counts + mileage distribution for the latest plan | none |
| GET    | `/plans/history`| Recent plans: `id`, `created_at`, and per-category counts | none |
| GET    | `/plans/{plan_id}` | Fetch one persisted plan by id (same payload shape as `/plans/run`); 404 if missing | none |

Response keys throughout plans endpoints: `generated_at`, `service`, `standby`,
`maintenance`, `alerts`. (Do not look for `revenue`/`ibl` — those were renamed away.)

### iot — `app/routers/iot.py`

| Method | Path                   | Purpose                      | Auth |
| ------ | ---------------------- | ---------------------------- | ---- |
| GET    | `/iot/trainsets/{code}`| Simulated sensor packet for one trainset (`brake_temp`, `hvac_status`, `signal_comm_ok`, `last_updated`); 404 for unknown code | none |

### ml — `app/routers/ml.py`

| Method | Path                          | Purpose | Auth |
| ------ | ----------------------------- | ------- | ---- |
| POST   | `/ml/predict_fitness_expiry`  | Live single-sample certificate-expiry prediction. Body: `sensor_aggregate`, `days_since_inspection`, `open_job_card_count`, `age_months` | none |
| POST   | `/ml/maintenance_urgency`     | Live job-card urgency score. Body: `description` (text) | none |
| POST   | `/ml/csv/certificate_expiry/` | Upload CSV (`multipart/form-data`, max 10 MB, `.csv` only) with the 4 feature columns → per-row predictions; `certificate_expired` column optional for actuals | none |
| POST   | `/ml/csv/maintenance_urgency/`| Upload CSV with a `description` column → per-row urgency scores; `urgency` column optional for actuals | none |

CSV validation errors return 422. Non-CSV extensions and files over 10 MB are rejected with 400.

### admin — `app/routers/admin.py` 🔑

| Method | Path                         | Purpose                                   | Auth |
| ------ | ---------------------------- | ----------------------------------------- | ---- |
| GET    | `/admin/trainsets`           | All trainsets, full ORM rows               | 🔑 |
| GET    | `/admin/trainsets/{code}`    | One trainset by code (404 if missing)     | 🔑 |
| PUT    | `/admin/trainsets/{code}`    | Update train fields (send only what changed) | 🔑 |
| GET    | `/admin/bays`                | All cleaning bays                          | 🔑 |
| PUT    | `/admin/bays/{bay_number}`   | Update a bay (occupancy, current trainset, manpower, etc.) | 🔑 |
| POST   | `/admin/config/reset-bays`   | Mark all bays unoccupied                  | 🔑 |
| POST   | `/admin/config/reset-teams`  | Mark all teams available                  | 🔑 |

---

## 5. ML models

Both models were trained only on synthetic or hand-written data — no real operational data
went into them. They are loaded/used in `app/ml_models.py` and trained by the scripts in
`models/`.

### Fitness-certificate expiry predictor

- **Model:** `RandomForestClassifier` (100 estimators), saved as
  `certificate_expiry_predictor.joblib` plus `certificate_expiry_feature_columns.pkl`.
- **Task:** binary — predicts whether a train's fitness certificate expires within the next
  6 months (180 days).
- **Features (must exactly match):** `sensor_aggregate`, `days_since_inspection`,
  `open_job_card_count`, `age_months`.
- **Training data:** synthetic, generated in `models/retain_certificate_model.py`
  (`generate_training_data()`): 1,000 random rows with a hardcoded expiry-in-5–7-months
  window. This is **not real operational data** — treat the accuracy numbers as meaningless
  for real decisions. In a verification run the model hit train accuracy ~1.00 / test ~0.52.
- **Used by:** the planner (`app/planner.py`) to flag trains for maintenance, and the
  live/CSV ML endpoints.

### Maintenance-urgency scorer

- **Model:** `Pipeline(TfidfVectorizer, RandomForestClassifier)` saved as
  `maintenance_urgency_scorer.joblib`.
- **Task:** scores a job-card description's urgency as 0 (low), 1 (medium), 2 (high).
- **Training data:** **exactly 8 hand-written example descriptions** (see the module-level
  `data` dict in `models/retain_maintenance_model.py`), no train/test split. This is a
  **placeholder**, not production-grade — any real-world description is almost certainly
  out-of-distribution.

### Fallback behavior (important)

If a `.joblib` file is missing — which is the default state of a fresh clone — or prediction
raises `TypeError`/`ValueError`, `ml_models.py` silently falls back to:

- `DummyFitnessModel`: threshold rules (`age_months > 48`, `days_since_inspection > 180`,
  `sensor_aggregate > 90`) with a probability blend for `predict_proba`.
- `DummyUrgencyModel`: **a random integer in 1–9** — it is not derived from the input text at
  all. Do not mistake this output for a real score.

Startup logs say `[ml] certificate_expiry: FALLBACK (DummyFitnessModel) - no trained model
found` and `[ml] maintenance_urgency: FALLBACK (DummyUrgencyModel) - no trained model found`
when this happens. (If the model files are present, the log instead says
`TRAINED MODEL LOADED (models/...)` — see §3.)

---

## 6. Database schema

SQLAlchemy models in `app/models.py`. Three bay/team tables were added as part of the
cleaning-planner work.

| Table           | One-line purpose                                                              |
| --------------- | ----------------------------------------------------------------------------- |
| `trainsets`     | Master data per train: code, fitness validity, job-card flag, branding, mileage, needs-deep-clean, cleaning plan fields, and the 4 ML feature inputs (`sensor_aggregate`, `days_since_inspection`, `age_months`, plus `open_job_card_count` derived from `job_card_open`). |
| `plans`         | One row per generated plan: `created_at`, `params` (JSON of planner inputs).   |
| `plan_items`    | One row per train per plan: which bucket (`service`/`standby`/`maintenance`), the reason, and optional maintenance + cleaning-assignment columns. |
| `cleaning_bays` | Cleaning bay slots (`Bay-1`..`Bay-3`): capacity, `is_occupied`, `current_trainset`, available manpower, specialization. |
| `cleaning_teams`| Cleaning crews (`Team-A`..`Team-C`): size, `is_available`, `current_assignment`, specialization. |

Relationships:

- `plans` → `plan_items`: 1-to-many via `plan_items.plan_id` (FK) → `plans.id`. ORM
  relationship `Plan.items`.
- `trainsets` → `plan_items`: **not a foreign-key relationship.** `plan_items.trainset_code`
  is a plain indexed string that matches `trainsets.code` by convention. It is safe to
  drop/rename a trainset without FK cascade behavior.
- `cleaning_bays` / `cleaning_teams` are standalone tables; they reference a trainset only by
  string (`current_trainset` / `current_assignment`), no FK.

Schema management: `Base.metadata.create_all(bind=engine)` at startup creates missing tables.
**There is no migration tool** (no Alembic). Schema changes only apply to fresh databases or
after manually recreating the `.db` file.

Most DB access goes through `app/crud.py` (seeding, plan persistence, plan payload
serialization, bay/team assignment), but several routers query the ORM directly with
`db.query(...)` (`app/routers/admin.py`, `trainsets.py`, `iot.py`, and `plans.get_plan`).
No raw SQL strings are used anywhere in `app/`.

---

## 7. Known limitations / what is NOT real

Read this before you demo anything. Every item is a live fact about this codebase, verified
in the repo.

1. **Maximo is simulated.** `connectors_mock_maximo.py` serves locally-generated job cards
   from `app/dummy_maximo.json` (or generates them in code). No real Maximo/API credentials,
   no real connection. The `/trainsets/refresh/maximo` endpoint only shuffles the
   `job_card_open` flags in your local SQLite DB.
2. **IoT is simulated.** `iot.py` returns `random` temperatures/status with a 30-second cache.
   There is no hardware, no MQTT, no telemetry.
3. **ML models are trained on small/synthetic data** — and the urgency model's training set is
   exactly 8 hand-written examples. Neither model should be trusted to make real operational
   decisions. If a model file is ever missing/deleted, the app falls back to rule/random logic
   (announced loudly at startup — see §3 and #9).
4. **No automated test suite.** There are no pytest tests. The only test artifact,
   `backend_test.py`, is a hand-run smoke script: it hits a *live* server at
   `http://localhost:8000` with `requests` and asserts a handful of status codes. It is not on
   CI, is not a pytest module, and does nothing unless a server is already running.
5. **No CI/CD.** No GitHub Actions, no build pipeline.
6. **Auth is a single static API key**, compared byte-for-byte against `ADMIN_API_KEY`
   (`app/security.py`). It is not user accounts, roles, sessions, or tokens. Frontend sends
   it from `localStorage` (an XSS risk in a real deployment).
7. **No database migrations.** `create_all` only creates missing tables; it never alters
   existing ones.
8. **`python-dotenv` is unused.** `.env` files have no effect; set real environment
   variables instead.
9. **The ML model binaries are in git now (FIXED).** The trained artifacts are committed under
   `models/`, so a fresh clone starts with the real trained models — no manual retrain/copy
   step (see §3). The retrain scripts save directly to `models/`; the old `models/models/`
   path mismatch is gone. Fallback logic remains in `app/ml_models.py` and only fires if a
   model file is deleted or fails to load, and the startup log announces that loudly
   (`[ml] <name>: FALLBACK (...)`), so it is never silent.
10. **Retrain scripts are Windows-console safe (FIXED).** They previously printed emoji and
    crashed on a default cp1252 console unless `PYTHONIOENCODING=utf-8` was set. The emoji are
    gone and the scripts now run fine on a stock Windows console.
11. **The DB file is created in the directory you launch from.** `DATABASE_URL` is relative
    (`sqlite:///./kmrl_mock_maximo.db`), so the file lands in your shell's working directory,
    not a fixed application directory.
12. **Two stray binary files remain in the local working tree** (`test_data/kmrl_dummy_maximo.db`,
    `test_data/kmrl_real_maximo.db`) — they are gitignored and not tracked, but they exist on
    disk and are stale copies, not live data.
13. **A misnamed binary is committed to git.** `kmrl_real_maximo.csv` (project root) is actually
    a raw SQLite database file — the first bytes are `SQLite format 3` — committed under a `.csv`
    filename. It is not a CSV data dump and is not used by the app.
14. **`db.py` and `create_db.py` are dead legacy scripts.** `db.py` mutates
    `kmrl_mock_maximo.db` directly with raw `sqlite3` calls (and has corrupt characters in its
    print output); `create_db.py` hand-builds the schema. Neither is imported by the app — the
    running app creates and manages its own schema via SQLAlchemy `create_all`. Do not run them
    against a live DB.

The name "automated_metro_rail_management" suggests the repo is on GitHub at
`github.com/afx786/automated_metro_rail_management`. The code is a demonstrator, not a
system of record.

---

## 8. How to contribute / where things live

```
kmrl_planner_with_real_maximo/
├── app/
│   ├── main.py                    # FastAPI app; mount new routers here
│   ├── database.py                # engine/session; DATABASE_URL
│   ├── models.py                  # SQLAlchemy tables (the schema)
│   ├── schemas.py                 # Pydantic request/response models
│   ├── crud.py                    # all DB reads/writes + seeding + plan payloads
│   ├── planner.py                 # the nightly planning rules + ML hooks
│   ├── optimizer.py               # thin orchestration shell around planner
│   ├── ml_models.py               # model loading + fallbacks (add new models here)
│   ├── csv_predictor.py           # CSV batch prediction helpers
│   ├── iot.py                     # simulated IoT client
│   ├── connectors_mock_maximo.py  # simulated Maximo connector
│   ├── security.py                # X-API-Key check for /admin
│   ├── dependencies.py            # get_db() dependency
│   └── routers/                   # one file per URL group
│       ├── health.py  trainsets.py  plans.py  iot.py  ml.py  admin.py
├── models/                        # serialized models + retrain scripts
├── test_data/                     # sample CSVs for the batch endpoints
├── frontend/
│   ├── index.html
│   └── src/
│       ├── main.jsx               # app entry; Dashboard/AdminPanel toggle
│       ├── index.css
│       ├── services/api.js        # axios instance, API_URL, admin key interceptor
│       └── components/
│           ├── Dashboard.jsx      # trainset cards, run-optimizer, plan table
│           └── AdminPanel.jsx     # admin key input, trainset/bay forms, plan history
├── README.md  project.md  PROJECT_DOCS.md   # docs
├── requirements.txt  start_backend.sh       # deps + launch helper
├── backend_test.py                          # hand-run smoke script (needs a live server on :8000)
├── kmrl_real_maximo.csv                     # SQLite binary mislabeled as CSV (legacy; unused)
├── create_db.py  db.py                      # dead legacy raw-SQL scripts (not imported)
└── notes on untracked local files:          # .DS_Store, *.db at project root, temp_uploads/,
                                             # models/*.joblib — trained ML artifacts, now committed
```

The backend lives entirely in `app/`, the frontend in `frontend/`, and the rest of the
committed files are root-level support: docs, `requirements.txt`, `start_backend.sh`,
`backend_test.py` (smoke script), the legacy `create_db.py`/`db.py`/`kmrl_real_maximo.csv`, and
`models/` (retrain scripts **plus** the trained `.joblib`/`.pkl` artifacts, which are committed
so a fresh clone starts with real models).

Recipe for each change type:

- **New API route:** add a file (or extend an existing one) in `app/routers/`. Give the
  router a `prefix` and `tags`. If it should be admin-only, add
  `dependencies=[Depends(require_admin_key)]` on the router and import from
  `..security`. Register it in `app/main.py` with `app.include_router(...)`.
- **New DB table/column:** edit `app/models.py` (and `app/schemas.py` if it's exposed on the
  API). Remember there are no migrations — you'll need to delete/recreate the dev DB for
  schema changes to apply (or write the migration yourself).
- **New ML model:** add training to a script in `models/`, save the `.joblib`, add a loader
  class in `app/ml_models.py` with a graceful fallback, and expose it through
  `app/routers/ml.py` if you want an endpoint.
- **New frontend component:** add it under `frontend/src/components/`, call APIs through
  `frontend/src/services/api.js` (which already injects the admin key), and mount it from
  `frontend/src/main.jsx`.

Keep every new feature working with the fallback path (models absent) even though a fresh
clone now ships the trained models — the fallback is the deliberate low-setup dev escape hatch,
and it is loudly logged so nobody mistakes it for the real models.