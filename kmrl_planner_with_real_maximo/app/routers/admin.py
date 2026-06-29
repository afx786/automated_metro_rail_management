# routers/admin.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..dependencies import get_db
from .. import models
from pydantic import BaseModel
from typing import Optional, List

router = APIRouter(prefix="/admin", tags=["admin"])

# Pydantic models for request validation
class TrainsetUpdate(BaseModel):
    fitness_valid: Optional[bool] = None
    job_card_open: Optional[bool] = None
    branding: Optional[str] = None
    mileage: Optional[float] = None
    needs_deep_clean: Optional[bool] = None
    deep_clean_complexity: Optional[str] = None
    estimated_clean_time: Optional[int] = None
    required_manpower: Optional[int] = None

class BayUpdate(BaseModel):
    capacity: Optional[int] = None
    is_occupied: Optional[bool] = None
    current_trainset: Optional[str] = None
    available_manpower: Optional[int] = None
    specialization: Optional[str] = None

# Trainset Management Endpoints
@router.get("/trainsets")
def get_all_trainsets(db: Session = Depends(get_db)):
    """Get all trainsets with full details"""
    return db.query(models.Trainset).all()

@router.get("/trainsets/{code}")
def get_trainset(code: str, db: Session = Depends(get_db)):
    """Get specific trainset details"""
    trainset = db.query(models.Trainset).filter(models.Trainset.code == code).first()
    if not trainset:
        raise HTTPException(status_code=404, detail="Trainset not found")
    return trainset

@router.put("/trainsets/{code}")
def update_trainset(code: str, update_data: TrainsetUpdate, db: Session = Depends(get_db)):
    """Update trainset properties"""
    trainset = db.query(models.Trainset).filter(models.Trainset.code == code).first()
    if not trainset:
        raise HTTPException(status_code=404, detail="Trainset not found")
    
    # Update only provided fields
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(trainset, field, value)
    
    db.commit()
    db.refresh(trainset)
    return {"message": "Trainset updated successfully", "trainset": trainset}

# Bay Management Endpoints
@router.get("/bays")
def get_all_bays(db: Session = Depends(get_db)):
    """Get all cleaning bays"""
    return db.query(models.CleaningBay).all()

@router.put("/bays/{bay_number}")
def update_bay(bay_number: str, update_data: BayUpdate, db: Session = Depends(get_db)):
    """Update bay properties"""
    bay = db.query(models.CleaningBay).filter(models.CleaningBay.bay_number == bay_number).first()
    if not bay:
        raise HTTPException(status_code=404, detail="Bay not found")
    
    update_dict = update_data.dict(exclude_unset=True)
    for field, value in update_dict.items():
        setattr(bay, field, value)
    
    db.commit()
    db.refresh(bay)
    return {"message": "Bay updated successfully", "bay": bay}

# System Configuration Endpoints
@router.post("/config/reset-bays")
def reset_all_bays(db: Session = Depends(get_db)):
    """Reset all bays to available status"""
    try:
        bays = db.query(models.CleaningBay).all()
        for bay in bays:
            bay.is_occupied = False
            bay.current_trainset = None
        
        db.commit()
        return {"message": "All bays reset to available", "reset_count": len(bays)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting bays: {str(e)}")

@router.post("/config/reset-teams")
def reset_all_teams(db: Session = Depends(get_db)):
    """Reset all teams to available status"""
    try:
        teams = db.query(models.CleaningTeam).all()
        for team in teams:
            team.is_available = True
            team.current_assignment = None
        
        db.commit()
        return {"message": "All teams reset to available", "reset_count": len(teams)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error resetting teams: {str(e)}")