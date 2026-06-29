from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .database import Base, engine, SessionLocal
from .routers import health, trainsets, plans, iot, ml, admin
from . import crud

app = FastAPI(title="KMRL Planner (Real Maximo)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

Base.metadata.create_all(bind=engine)
with SessionLocal() as db:
    crud.ensure_seed_trainsets(db)
    crud.ensure_cleaning_bays(db)

@app.get("/")
def read_root():
    return {
        "message": "KMRL Planner API is running",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health",
        "endpoints": [
            "/trainsets/",
            "/plans/run",
            "/plans/stats",
            "/plans/history",
            "/iot/trainsets/{code}",
            "/ml/predict_fitness_expiry",
            "/ml/maintenance_urgency"
        ]
    }

app.include_router(health.router)
app.include_router(trainsets.router)
app.include_router(plans.router)
app.include_router(iot.router)
app.include_router(ml.router)
app.include_router(admin.router)

