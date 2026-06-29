from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from ..iot import get_trainset_fitness
from .. import models

router = APIRouter(prefix="/iot", tags=["iot"])

@router.get("/trainsets/{code}")
def trainset_fitness(code: str, db: Session = Depends(get_db)):
    # Verify the trainset exists
    ts = db.query(models.Trainset).filter(models.Trainset.code == code).first()
    if not ts:
        raise HTTPException(status_code=404, detail="Trainset not found")
    # Fetch sensor data
    data = get_trainset_fitness(code)
    return data
