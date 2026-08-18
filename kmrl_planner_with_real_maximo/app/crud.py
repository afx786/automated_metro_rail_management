# crud.py
from sqlalchemy.orm import Session
from . import models
from datetime import datetime
import random

PLAN_MAINTENANCE_FIELDS = [
    'maintenance_priority', 'priority_level', 'urgency_score',
    'maintenance_score', 'fitness_status'
]
PLAN_CLEANING_FIELDS = [
    'assigned_bay', 'assigned_team', 'estimated_time',
    'manpower', 'estimated_completion', 'complexity'
]


def ensure_seed_trainsets(db: Session):
    """Seed 25 synthetic trainsets (KM01..KM25) when the DB is empty.

    Uses deterministic (seeded) random data so the app works out of the box
    without a pre-committed database file.
    """
    if db.query(models.Trainset).count() >= 25:
        return

    existing_codes = {r.code for r in db.query(models.Trainset).all()}
    rng = random.Random(42)
    brands = ["Alstom", "Siemens", "Bombardier", "Hyundai Rotem", "CRRC", None]

    for i in range(1, 26):
        code = f"KM{i:02d}"
        if code in existing_codes:
            continue
        complexity = rng.choice(["low", "medium", "high"])
        train = models.Trainset(
            code=code,
            fitness_valid=rng.random() >= 0.15,
            job_card_open=rng.random() < 0.2,
            branding=rng.choice(brands),
            mileage=round(rng.uniform(500, 5000), 1),
            needs_deep_clean=rng.random() < 0.2,
            deep_clean_complexity=complexity,
            estimated_clean_time=calculate_clean_time(complexity),
            required_manpower=calculate_manpower(complexity),
            sensor_aggregate=round(rng.uniform(0, 100), 1),
            days_since_inspection=rng.randint(0, 180),
            age_months=rng.randint(6, 120),
        )
        db.add(train)
    db.commit()


def create_plan(db: Session, params: dict, items: list):
    plan = models.Plan(params=params or {}, created_at=datetime.utcnow())
    db.add(plan)
    db.flush()

    for it in items:
        pi = models.PlanItem(
            plan_id=plan.id,
            trainset_code=it['trainset'],
            status=it['status'],
            reason=it.get('reason'),
            brand=it.get('brand'),
            mileage=it.get('mileage', 0.0),
            needs_deep_clean=it.get('needs_deep_clean', False),
        )

        for field in PLAN_MAINTENANCE_FIELDS:
            value = it.get(field)
            if value is not None:
                setattr(pi, field, value)

        for field in PLAN_CLEANING_FIELDS:
            value = it.get(field)
            if value is None:
                continue
            if field == 'estimated_completion':
                if isinstance(value, str):
                    value = datetime.fromisoformat(value.replace('Z', '+00:00'))
                elif not isinstance(value, datetime):
                    continue  # Unsupported type, skip rather than silently drop a DB error
            setattr(pi, field, value)

        db.add(pi)

    db.commit()
    db.refresh(plan)
    return plan


def get_available_bays(db: Session):
    return db.query(models.CleaningBay).filter(models.CleaningBay.is_occupied == False).order_by(models.CleaningBay.id).all()


def get_available_teams(db: Session):
    return db.query(models.CleaningTeam).filter(models.CleaningTeam.is_available == True).order_by(models.CleaningTeam.id).all()


def assign_cleaning_resources(db: Session, trainset_code: str, complexity: str):
    """Deterministically assign the first available bay and team, and persist it.

    Returns (bay_number, team_name), or (None, None) if no resources are free.
    """
    available_bays = get_available_bays(db)
    available_teams = get_available_teams(db)

    if not available_bays or not available_teams:
        return None, None

    assigned_bay = available_bays[0]
    assigned_team = available_teams[0]

    assigned_bay.is_occupied = True
    assigned_bay.current_trainset = trainset_code
    assigned_team.is_available = False
    assigned_team.current_assignment = trainset_code

    db.commit()
    return assigned_bay.bay_number, assigned_team.team_name


def release_cleaning_resources(db: Session, trainset_code: str):
    """Free any bay/team currently assigned to the given trainset."""
    bay = db.query(models.CleaningBay).filter(models.CleaningBay.current_trainset == trainset_code).first()
    if bay:
        bay.is_occupied = False
        bay.current_trainset = None
    team = db.query(models.CleaningTeam).filter(models.CleaningTeam.current_assignment == trainset_code).first()
    if team:
        team.is_available = True
        team.current_assignment = None
    db.commit()


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


def plan_to_payload(plan: models.Plan, db: Session):
    sections = {'service': [], 'standby': [], 'maintenance': []}

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

        if it.status == 'maintenance':
            for field in PLAN_MAINTENANCE_FIELDS:
                value = getattr(it, field, None)
                if value is not None:
                    row[field] = value

            for field in PLAN_CLEANING_FIELDS:
                value = getattr(it, field, None)
                if value is not None:
                    if field == 'estimated_completion' and hasattr(value, 'isoformat'):
                        row[field] = value.isoformat()
                    else:
                        row[field] = value

        if it.status == 'service':
            sections['service'].append(row)
        elif it.status == 'standby':
            sections['standby'].append(row)
        else:
            sections['maintenance'].append(row)

    payload = {'generated_at': plan.created_at.isoformat(), 'alerts': [], **sections}
    return payload


def get_stats(db: Session):
    lp = latest_plan(db)
    if not lp:
        return {'counts': {'service': 0, 'standby': 0, 'maintenance': 0}, 'mileage_distribution': []}

    payload = plan_to_payload(lp, db)

    counts = {
        'service': len(payload['service']),
        'standby': len(payload['standby']),
        'maintenance': len(payload['maintenance'])
    }
    mileage_dist = []
    for cat in ['service', 'standby', 'maintenance']:
        for t in payload[cat]:
            mileage_dist.append({'trainset': t['trainset'], 'mileage': t.get('mileage', 0)})
    return {'counts': counts, 'mileage_distribution': mileage_dist}


def get_history(db: Session, limit: int = 30):
    rows = db.query(models.Plan).order_by(models.Plan.created_at.desc()).limit(limit).all()
    out = []
    for r in rows:
        counts = {'service': 0, 'standby': 0, 'maintenance': 0}
        items = db.query(models.PlanItem).filter(models.PlanItem.plan_id == r.id).all()
        for it in items:
            if it.status == 'service':
                counts['service'] += 1
            elif it.status == 'standby':
                counts['standby'] += 1
            else:
                counts['maintenance'] += 1
        out.append({'id': r.id, 'created_at': r.created_at.isoformat(), 'counts': counts})
    return out


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

    bays = [
        models.CleaningBay(bay_number="Bay-1", capacity=1, available_manpower=4, specialization="interior"),
        models.CleaningBay(bay_number="Bay-2", capacity=1, available_manpower=4, specialization="exterior"),
        models.CleaningBay(bay_number="Bay-3", capacity=1, available_manpower=4, specialization="general"),
    ]

    for bay in bays:
        db.add(bay)
    db.commit()


def ensure_cleaning_teams(db: Session):
    """Create cleaning teams if they don't exist"""
    existing = db.query(models.CleaningTeam).count()
    if existing >= 3:
        return

    teams = [
        models.CleaningTeam(team_name="Team-A", team_size=4, specialization="interior"),
        models.CleaningTeam(team_name="Team-B", team_size=4, specialization="exterior"),
        models.CleaningTeam(team_name="Team-C", team_size=4, specialization="general"),
    ]

    for team in teams:
        db.add(team)
    db.commit()
