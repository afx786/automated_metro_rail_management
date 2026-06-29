from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..connectors_maximo import MaximoDummyConnector
from .. import models

router = APIRouter(prefix="/trainsets", tags=["trainsets"])

@router.get("/")
def list_trainsets(db: Session = Depends(get_db)):
    rows = db.query(models.Trainset).order_by(models.Trainset.code).all()
    return [{
        "code": r.code,
        "fitness_valid": r.fitness_valid,
        "job_card_open": r.job_card_open,
        "branding": r.branding,
        "mileage": r.mileage,
        "needs_deep_clean": r.needs_deep_clean
    } for r in rows]

@router.post("/refresh/maximo")
def refresh_from_maximo(db: Session = Depends(get_db)):
    conn = MaximoDummyConnector()
    conn.update_trainsets_from_dummy(db)
    return {"message": "Fetched and updated trainsets from Maximo"}
