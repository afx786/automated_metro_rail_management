# KMRL Planner

A FastAPI + React prototype for KMRL (Kochi Metro) trainset maintenance planning. It consolidates
trainset data, simulated IoT sensor readings, and job-card data, applies business rules plus ML
predictions, and generates an optimized nightly maintenance plan (service / standby / maintenance).

> Note: the Maximo connector is a **simulated/mock** data source for development and demos.
> No real Maximo instance is required. See `app/connectors_mock_maximo.py`.

## Project structure

```
kmrl_planner_with_real_maximo/
├── app/
│   ├── main.py                 # FastAPI server entrypoint
│   ├── database.py             # DB engine/session setup (SQLite by default)
│   ├── models.py               # SQLAlchemy ORM models
│   ├── schemas.py              # Pydantic request/response models
│   ├── crud.py                 # DB create/read/update/delete + seeding
│   ├── planner.py              # Planning algorithm (heuristics + ML)
│   ├── optimizer.py            # Plan orchestration layer
│   ├── ml_models.py            # ML model loading & inference
│   ├── csv_predictor.py        # Batch CSV prediction
│   ├── iot.py                  # Simulated IoT sensor data
│   ├── connectors_mock_maximo.py  # Simulated Maximo job-card connector
│   ├── security.py             # API-key auth for admin endpoints
│   └── routers/                # health, trainsets, plans, iot, ml, admin
├── models/                     # Serialized ML models + retrain scripts
├── test_data/                  # Sample CSVs for batch predictions
├── frontend/                   # React (Vite) frontend
├── requirements.txt            # Python dependencies (pinned)
└── start_backend.sh            # Backend startup script
```

## Backend setup

Requires Python 3.11+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API docs are at `http://localhost:8000/docs`.

On first start the app creates the SQLite database (`kmrl_mock_maximo.db`), seeds 25 synthetic
trainsets (KM01–KM25), and seeds cleaning bays/teams — no pre-committed database file is needed.

## Frontend setup

```bash
cd frontend
npm install
npm run dev      # serves at http://localhost:5173
```

The frontend calls the backend at `http://localhost:8000` by default. Override with
`VITE_API_BASE_URL` in a `frontend/.env` file (e.g. `VITE_API_BASE_URL=https://api.example.com`).

## Configuration (environment variables)

| Variable          | Default                     | Purpose                                  |
| ----------------- | --------------------------- | ---------------------------------------- |
| `DATABASE_URL`    | `sqlite:///./kmrl_mock_maximo.db` | SQLAlchemy database URL           |
| `ADMIN_API_KEY`   | `kmrl-admin-secret`         | API key required for all `/admin/*` endpoints |
| `CORS_ORIGINS`    | `http://localhost:5173`     | Comma-separated list of allowed origins  |

## API overview

- `GET /trainsets/` — list all trainsets
- `POST /trainsets/refresh/maximo` — pull job-card status from the simulated connector
- `POST /plans/run` — generate a maintenance plan
- `GET /plans/stats` — plan summary counts + mileage distribution
- `GET /plans/history` — recent plans
- `GET /iot/trainsets/{code}` — simulated sensor data for a trainset
- ML endpoints (in `/ml`): live prediction (`/predict_fitness_expiry`, `/maintenance_urgency`)
  and CSV batch prediction (`/csv/certificate_expiry/`, `/csv/maintenance_urgency/`)
- `/admin/*` — trainset/bay management (requires `X-API-Key` header)

## Machine learning

Two scikit-learn models are used:

- `certificate_expiry_predictor.joblib` — binary classifier predicting certificate expiry within
  6 months. Features: `sensor_aggregate`, `days_since_inspection`, `open_job_card_count`,
  `age_months`.
- `maintenance_urgency_scorer.joblib` — text pipeline scoring job-card descriptions for urgency.

Models are loaded from `models/`. If a model file is missing, the app falls back to rule-based
logic. Retrain with the scripts in `models/`:

```bash
python models/retrain_certificate_model.py
python models/retrain_maintenance_model.py
```

## Admin access

All `/admin/*` endpoints require the header `X-API-Key: <key>`. The default dev key is
`kmrl-admin-secret`; set `ADMIN_API_KEY` to change it. The React Admin panel stores the key in
`localStorage` and sends it automatically.
