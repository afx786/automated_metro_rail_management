# plans.py - Updated to include cleaning assignment fields
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from ..dependencies import get_db
from .. import optimizer, crud
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/plans", tags=["plans"])

@router.post("/run")
def run_plan(params: dict = None, db: Session = Depends(get_db)):
    payload = optimizer.run(db, params or {})
    items = []
    
    for cat, status in [('revenue', 'service'), ('standby', 'standby'), ('ibl', 'maintenance')]:
        for t in payload[cat]:
            item = {
                'trainset': t.get('trainset'),
                'status': status,
                'reason': t.get('reason'),
                'brand': t.get('brand'),
                'mileage': float(t.get('mileage', 0)),
                'needs_deep_clean': bool(t.get('needs_deep_clean', False))
            }
            
            # Add maintenance fields for maintenance trains
            if status == 'maintenance':
                maintenance_fields = [
                    'maintenance_priority', 'priority_level', 'urgency_score',
                    'maintenance_score', 'fitness_status'
                ]
                
                for field in maintenance_fields:
                    if field in t:
                        item[field] = t[field]
                
                # ADD CLEANING ASSIGNMENT FIELDS
                cleaning_fields = [
                    'assigned_bay', 'assigned_team', 'estimated_time',
                    'manpower', 'estimated_completion', 'complexity'
                ]
                
                for field in cleaning_fields:
                    if field in t:
                        # Handle different data types appropriately
                        value = t[field]
                        if field == 'estimated_completion' and value:
                            # Convert datetime to string for JSON serialization
                            item[field] = value.isoformat() if hasattr(value, 'isoformat') else str(value)
                        else:
                            item[field] = value
            
            items.append(item)
    
    plan = crud.create_plan(db, params or {}, items)
    response_payload = crud.plan_to_payload(plan, db)
    
    encoded = jsonable_encoder(response_payload)
    return JSONResponse(content=encoded)

@router.get("/stats")
def stats(db: Session = Depends(get_db)):
    return crud.get_stats(db)

@router.get("/history")
def history(limit: int = 30, db: Session = Depends(get_db)):
    return crud.get_history(db, limit)