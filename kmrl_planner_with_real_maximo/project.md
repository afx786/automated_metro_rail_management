# KMRL Planner — Project Documentation

> Team-facing documentation for the Kochi Metro trainset maintenance planning prototype.
> For quick start and API reference, see [README.md](README.md).

## Overview

KMRL Planner is a decision-support prototype that helps KMRL plan nightly deployment of
trainsets (KM01–KM25) across **service**, **standby**, and **maintenance** lines. It combines
trainset master data, simulated IoT sensor streams, and simulated Maximo job-card data, applies
business rules plus ML predictions, and produces an optimized, explainable plan.

The Maximo integration is **simulated** (see `app/connectors_mock_maximo.py`). It provides a
realistic HTTP/SQLAlchemy-shaped interface so the real connector can be swapped in later without
changing the rest of the app.

## Architecture

- **Backend API**: FastAPI (Python 3.11+) REST service — trainsets, plans, IoT simulation,
  ML inference, admin, CSV batch prediction.
- **Database**: SQLAlchemy ORM over SQLite by default; `DATABASE_URL` makes it configurable.
- **Machine Learning**: scikit-learn models for certificate-expiry classification and
  maintenance-urgency scoring, loaded from `models/` with rule-based fallbacks.
- **Frontend**: React (Vite) single-page app in `frontend/` — trainset table, planning
  dashboard, admin panel, CSV upload. It is part of this repo, not a separate repository.

## Project structure

```
kmrl_planner_with_real_maximo/
├── app/
│   ├── main.py                      # FastAPI server entrypoint, CORS, router mounting
│   ├── database.py                  # SQLAlchemy engine/session setup
│   ├── models.py                    # SQLAlchemy ORM models (Trainset, Plan, PlanItem, Bay…)
│   ├── schemas.py                   # Pydantic request/response models
│   ├── crud.py                      # DB read/write + seeding (25 synthetic trainsets)
│   ├── planner.py                   # Core planning algorithm (heuristics + ML)
│   ├── optimizer.py                 # Plan orchestration and formatting
│   ├── ml_models.py                 # Loads joblib models, exposes prediction functions
│   ├── csv_predictor.py             # Batch CSV prediction logic
│   ├── iot.py                       # Simulated IoT sensor data provider
│   ├── connectors_mock_maximo.py    # Simulated Maximo job-card connector
│   ├── security.py                  # API-key auth for /admin endpoints
│   └── routers/
│       ├── health.py                # Health/status endpoints
│       ├── trainsets.py             # Trainset endpoints (list, refresh from Maximo)
│       ├── plans.py                 # Plan run/stats/history endpoints
│       ├── iot.py                   # IoT sensor endpoints
│       ├── ml.py                    # ML live + CSV prediction endpoints
│       └── admin.py                 # Trainset/bay management (X-API-Key protected)
├── models/                          # Serialized ML models + retrain scripts
├── test_data/                       # Sample CSVs for batch predictions
├── frontend/                        # React (Vite) frontend
├── requirements.txt                 # Pinned Python dependencies
└── start_backend.sh                 # Backend startup script
```

There is no `Dockerfile` and no separate frontend repo — the frontend lives in `frontend/`.

## Setup

1. Clone the repo.
2. Python venv (Python 3.11+):
   ```bash
   python -m venv venv
   source venv/bin/activate        # Windows: venv\Scripts\activate
   ```
3. `pip install -r requirements.txt`
4. ML models are optional; the app falls back to rule-based logic if a `.joblib` file is missing.
   To enable ML, place models in `models/` (or retrain with the scripts there).
5. Run the API:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
6. API docs: `http://localhost:8000/docs`
7. Frontend:
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

On first start the backend creates `kmrl_mock_maximo.db` and seeds 25 trainsets plus cleaning
bays/teams automatically.

## Backend modules

| Module | Responsibility |
| ------ | -------------- |
| `main.py` | Entrypoint; mounts routers; CORS config. |
| `database.py` | Engine/session; reads `DATABASE_URL`. |
| `models.py` | ORM tables: Trainsets, Plans, PlanItems, Bays, Teams, etc. |
| `schemas.py` | Pydantic schemas for validation/serialization. |
| `crud.py` | Seeding, plan creation, stats/history queries. |
| `planner.py` | Nightly planning: assigns trainsets to service/standby/maintenance using rules + ML. |
| `optimizer.py` | Calls the planner and shapes the response. |
| `ml_models.py` | Loads models at startup; inference with fallback. |
| `csv_predictor.py` | Validates and predicts on uploaded CSVs. |
| `iot.py` | Generates deterministic simulated sensor data. |
| `connectors_mock_maximo.py` | Simulates Maximo job-card status/updates. |
| `security.py` | Verifies `X-API-Key` for admin routes. |
| `routers/*` | REST endpoints grouped by domain. |

## Machine learning

Two scikit-learn models:

- **Certificate expiry predictor** — binary classifier (expires within 6 months or not).
  Features: `sensor_aggregate`, `days_since_inspection`, `open_job_card_count`, `age_months`.
- **Maintenance urgency scorer** — text pipeline scoring job-card descriptions for urgency.

Both are served live (`/ml/*`) and as batch CSV endpoints (`/ml/csv/*`). The planner consumes the
certificate-expiry prediction when selecting maintenance candidates. Retrain scripts live in
`models/`.

## API overview

| Endpoint | Description |
| -------- | ----------- |
| `GET /trainsets/` | List all trainsets with status + IoT data. |
| `POST /trainsets/refresh/maximo` | Pull job-card status from the simulated Maximo connector. |
| `POST /plans/run` | Run the planner and return the recommended plan. |
| `GET /plans/stats` | Plan summary counts + mileage distribution. |
| `GET /plans/history` | Historical plans. |
| `GET /iot/trainsets/{code}` | Simulated sensor data for a trainset. |
| `POST /ml/predict_fitness_expiry` | Live single-sample certificate-expiry prediction. |
| `POST /ml/maintenance_urgency` | Live job-card urgency scoring. |
| `POST /ml/csv/certificate_expiry/` | Batch certificate-expiry predictions from uploaded CSV. |
| `POST /ml/csv/maintenance_urgency/` | Batch urgency scoring from uploaded CSV. |
| `/admin/*` | Trainset/bay management; requires `X-API-Key`. |

## Frontend

- Trainset listing with search/sort.
- Plan dashboard showing the generated nightly plan.
- CSV upload UI for ML batch predictions with per-row results.
- Admin panel (React Router route) for trainset/bay management; sends `X-API-Key` from
  `localStorage`.
- Backend base URL defaults to `http://localhost:8000`; override via `VITE_API_BASE_URL`.

## Security

- All `/admin/*` endpoints require `X-API-Key` header (default dev key `kmrl-admin-secret`,
  configurable via `ADMIN_API_KEY`).
- CORS restricted to `http://localhost:5173` by default; override via `CORS_ORIGINS`.
- No secrets in the repo; keys come from environment variables.

## Development & deployment notes

- Local dev: `uvicorn --reload` + Vite dev server with proxy.
- Production: containerize the backend (no Dockerfile yet) or run behind a reverse proxy;
  frontend is a static build served separately.
- Add automated tests (pytest) before production rollout — none exist yet.
