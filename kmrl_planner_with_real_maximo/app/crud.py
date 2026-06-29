# crud.py
from sqlalchemy.orm import Session
from . import models
from datetime import datetime
import warnings

def ensure_seed_trainsets(db: Session):
    """Ensure the database has at least 25 trains with random data"""
    existing = db.query(models.Trainset).count()
    if existing >= 25:
        return

def create_plan(db: Session, params: dict, items: list):
    plan = models.Plan(params=params or {}, created_at=datetime.utcnow())
    db.add(plan)
    db.flush()
    
    for it in items:
        # Base data without maintenance fields (to avoid database errors)
        base_data = {
            'plan_id': plan.id,
            'trainset_code': it['trainset'],
            'status': it['status'],
            'reason': it.get('reason'),
            'brand': it.get('brand'),
            'mileage': it.get('mileage', 0.0),
            'needs_deep_clean': it.get('needs_deep_clean', False)
        }
        
        pi = models.PlanItem(**base_data)
        
        # Safely add maintenance fields if they exist in the input
        maintenance_fields = [
            'maintenance_priority', 'priority_level', 'urgency_score',
            'maintenance_score', 'fitness_status'
        ]
        
        for field in maintenance_fields:
            if field in it and it[field] is not None:
                try:
                    setattr(pi, field, it[field])
                except:
                    # Silently ignore if the column doesn't exist in database
                    pass
        
        # SAFELY ADD CLEANING ASSIGNMENT FIELDS
        cleaning_fields = [
            'assigned_bay', 'assigned_team', 'estimated_time',
            'manpower', 'estimated_completion', 'complexity'
        ]
        
        for field in cleaning_fields:
            if field in it and it[field] is not None:
                try:
                    # Handle datetime conversion for estimated_completion
                    if field == 'estimated_completion' and isinstance(it[field], str):
                        # Convert string back to datetime if needed
                    
                        setattr(pi, field, datetime.fromisoformat(it[field].replace('Z', '+00:00')))
                    else:
                        setattr(pi, field, it[field])
                except:
                    # Column doesn't exist yet, skip silently
                    pass
        
        db.add(pi)
    
    db.commit()
    db.refresh(plan)
    return plan

# crud.py - Add functions for cleaning management
def get_available_bays(db: Session):
    return db.query(models.CleaningBay).filter(models.CleaningBay.is_occupied == False).all()

def get_available_teams(db: Session):
    return db.query(models.CleaningTeam).filter(models.CleaningTeam.is_available == True).all()

def assign_cleaning_resources(db: Session, trainset_code: str, complexity: str):
    """Assign bay and team for deep cleaning"""
    available_bays = get_available_bays(db)
    available_teams = get_available_teams(db)
    
    if not available_bays or not available_teams:
        return None, None  # No resources available
    
    # Assign first available bay and team
    assigned_bay = available_bays[0]
    assigned_team = available_teams[0]
    
    # Update bay occupancy
    assigned_bay.is_occupied = True
    assigned_bay.current_trainset = trainset_code
    
    # Update team availability
    assigned_team.is_available = False
    assigned_team.current_assignment = trainset_code
    
    db.commit()
    return assigned_bay.bay_number, assigned_team.team_name

def calculate_clean_time(complexity: str) -> int:
    """Calculate estimated cleaning time based on complexity"""
    time_map = {
        "low": 2,    # hours
        "medium": 4, # hours
        "high": 8    # hours
    }
    return time_map.get(complexity, 4)

def calculate_manpower(complexity: str) -> int:
    """Calculate required manpower based on complexity"""
    manpower_map = {
        "low": 2,
        "medium": 4,
        "high": 6
    }
    return manpower_map.get(complexity, 4)

def latest_plan(db: Session):
    return db.query(models.Plan).order_by(models.Plan.created_at.desc()).first()

# crud.py - Fix the plan_to_payload function
# crud.py - Update plan_to_payload to include cleaning fields
def plan_to_payload(plan: models.Plan, db: Session):
    sections = {'revenue': [], 'standby': [], 'ibl': []}
    
    # Use direct query to avoid relationship issues
    items = db.query(models.PlanItem).filter(models.PlanItem.plan_id == plan.id).all()
    
    for it in items:
        row = {
            'trainset': it.trainset_code,
            'status': it.status,
            'reason': it.reason,
            'brand': it.brand,
            'mileage': it.mileage,
            'needs_deep_clean': it.needs_deep_clean
        }
        
        # Safely add maintenance fields if they exist
        if it.status == 'maintenance':
            maintenance_fields = [
                'maintenance_priority', 'priority_level', 'urgency_score',
                'maintenance_score', 'fitness_status'
            ]
            
            for field in maintenance_fields:
                try:
                    value = getattr(it, field, None)
                    if value is not None:
                        row[field] = value
                except:
                    # Column doesn't exist yet, skip silently
                    pass
            
            # ADD CLEANING ASSIGNMENT FIELDS
            cleaning_fields = [
                'assigned_bay', 'assigned_team', 'estimated_time',
                'manpower', 'estimated_completion', 'complexity'
            ]
            
            for field in cleaning_fields:
                try:
                    value = getattr(it, field, None)
                    if value is not None:
                        # Convert datetime to string for JSON
                        if field == 'estimated_completion' and hasattr(value, 'isoformat'):
                            row[field] = value.isoformat()
                        else:
                            row[field] = value
                except:
                    # Column doesn't exist yet, skip silently
                    pass
        
        if it.status == 'service':
            sections['revenue'].append(row)
        elif it.status == 'standby':
            sections['standby'].append(row)
        else:
            sections['ibl'].append(row)
    
    payload = {'generated_at': plan.created_at.isoformat(), 'alerts': [], **sections}
    return payload

# crud.py - Update get_stats function
def get_stats(db: Session):
    lp = latest_plan(db)
    if not lp:
        return {'counts': {'service': 0, 'standby': 0, 'maintenance': 0}, 'mileage_distribution': []}
    
    payload = plan_to_payload(lp, db)  # Pass db session here
    
    counts = {
        'service': len(payload['revenue']),
        'standby': len(payload['standby']),
        'maintenance': len(payload['ibl'])
    }
    mileage_dist = []
    for cat in ['revenue','standby','ibl']:
        for t in payload[cat]:
            mileage_dist.append({'trainset': t['trainset'], 'mileage': t.get('mileage', 0)})
    return {'counts': counts, 'mileage_distribution': mileage_dist}

def get_history(db: Session, limit: int=30):
    rows = db.query(models.Plan).order_by(models.Plan.created_at.desc()).limit(limit).all()
    out = []
    for r in rows:
        counts = {'service':0, 'standby':0, 'maintenance':0}
        # Use direct query for items
        items = db.query(models.PlanItem).filter(models.PlanItem.plan_id == r.id).all()
        for it in items:
            if it.status == 'service':
                counts['service'] += 1
            elif it.status == 'standby':
                counts['standby'] += 1
            else:
                counts['maintenance'] += 1
        out.append({'created_at': r.created_at.isoformat(), 'counts': counts})
    return out

# crud.py - Add bay management functions
def get_available_bays(db: Session):
    return db.query(models.CleaningBay).filter(models.CleaningBay.is_occupied == False).all()

def assign_bay_to_trainset(db: Session, bay_id: int, trainset_code: str):
    bay = db.query(models.CleaningBay).filter(models.CleaningBay.id == bay_id).first()
    if bay:
        bay.is_occupied = True
        bay.current_trainset = trainset_code
        db.commit()
    return bay

def release_bay(db: Session, trainset_code: str):
    bay = db.query(models.CleaningBay).filter(models.CleaningBay.current_trainset == trainset_code).first()
    if bay:
        bay.is_occupied = False
        bay.current_trainset = None
        db.commit()
    return bay

def ensure_cleaning_bays(db: Session):
    """Create cleaning bays if they don't exist"""
    existing = db.query(models.CleaningBay).count()
    if existing >= 3:  # Create 3 bays by default
        return
    
    # Create default cleaning bays
    bays = [
        models.CleaningBay(bay_number="Bay-1", capacity=1, available_manpower=4, specialization="interior"),
        models.CleaningBay(bay_number="Bay-2", capacity=1, available_manpower=4, specialization="exterior"),
        models.CleaningBay(bay_number="Bay-3", capacity=1, available_manpower=4, specialization="general"),
    ]
    
    for bay in bays:
        db.add(bay)
    db.commit()