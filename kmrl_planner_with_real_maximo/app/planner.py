# planner.py
from sqlalchemy.orm import Session
from typing import Dict, Any, Tuple, List
from datetime import datetime, timedelta
from . import models
from . import crud
from .ml_models import FitnessExpiryModel

def build_plan(db: Session, params: Dict[str, Any] | None = None) -> Tuple[List[Dict], List[Dict], List[Dict]]:
    """Build maintenance plan and return (service, standby, maintenance) tuples"""
    params = params or {}
    target_service = int(params.get('target_service', 18))
    target_standby = int(params.get('target_standby', 4))
    available_manpower = int(params.get('available_manpower', 12))
    available_bays = int(params.get('available_bays', 3))

    trains = db.query(models.Trainset).all()
    maintenance_set = set()
    maintenance_reasons = {}
    cleaning_assignments = {}

    # Track resource usage
    used_manpower = 0
    used_bays = 0

    for t in trains:
        reasons = []

        # 1. Check current fitness validity
        if not t.fitness_valid:
            reasons.append("Fitness certificate invalid")

        # 2. ML prediction for 6-month expiry using per-train feature values
        features = {
            'sensor_aggregate': t.sensor_aggregate or 0.0,
            'days_since_inspection': t.days_since_inspection or 30,
            'open_job_card_count': 1 if t.job_card_open else 0,
            'age_months': t.age_months or 12,
        }

        will_expire_soon = FitnessExpiryModel.predict(features)
        if will_expire_soon:
            days_until_expiry = FitnessExpiryModel.predict_days_until_expiry(features)
            reasons.append(f"Predicted certificate expiry in {days_until_expiry} days")

        # 3. Other maintenance criteria
        if t.job_card_open:
            reasons.append("Open job card")

        if t.needs_deep_clean:
            reasons.append("Needs deep cleaning")
            clean_complexity = get_cleaning_complexity(t.mileage, t.age_months or 12)
            clean_time = crud.calculate_clean_time(clean_complexity)
            required_manpower = crud.calculate_manpower(clean_complexity)

            if used_manpower + required_manpower <= available_manpower and used_bays < available_bays:
                bay_number, team_name = crud.assign_cleaning_resources(db, t.code, clean_complexity)
                if bay_number and team_name:
                    used_manpower += required_manpower
                    used_bays += 1
                    cleaning_assignments[t.code] = {
                        'assigned_bay': bay_number,
                        'assigned_team': team_name,
                        'estimated_time': clean_time,
                        'manpower': required_manpower,
                        'complexity': clean_complexity,
                        'estimated_completion': datetime.utcnow() + timedelta(hours=clean_time)
                    }
                    reasons.append(f"Assigned to Bay {bay_number} (Team: {team_name}, {clean_time}h)")
                else:
                    reasons.append("Waiting for cleaning resources")
            else:
                reasons.append("Insufficient cleaning resources")

        # 4. Mileage-based maintenance
        if t.mileage > 4000:
            reasons.append(f"High mileage: {t.mileage} km")

        if reasons:
            maintenance_set.add(t.code)
            maintenance_reasons[t.code] = reasons

    # Sort candidates: healthy trains first (by mileage low to high), then maintenance trains
    candidates = sorted(trains, key=lambda x: (
        x.code in maintenance_set,  # False (0) first, then True (1)
        0 if x.branding else 1,     # Branded trains first
        x.mileage                   # Lower mileage first
    ))

    service, standby, maintenance = [], [], []

    for t in candidates:
        row = {
            'trainset': t.code,
            'brand': t.branding,
            'mileage': t.mileage,
            'needs_deep_clean': t.needs_deep_clean,
            'fitness_status': 'valid' if t.fitness_valid else 'invalid'
        }

        if t.code in maintenance_set:
            priority = calculate_maintenance_priority(maintenance_reasons[t.code])
            row.update({
                'status': 'maintenance',
                'reason': '; '.join(maintenance_reasons[t.code]),
                'maintenance_priority': priority,
                'priority_level': get_priority_level(priority)
            })

            if t.code in cleaning_assignments:
                row.update(cleaning_assignments[t.code])

            maintenance.append(row)
            continue

        # Healthy trains - assign to service or standby
        if len(service) < target_service:
            row.update({
                'status': 'service',
                'reason': 'Meets all operational requirements'
            })
            service.append(row)
        elif len(standby) < target_standby:
            row.update({
                'status': 'standby',
                'reason': 'Standby pool'
            })
            standby.append(row)
        else:
            row.update({
                'status': 'maintenance',
                'reason': 'Preventive inspection - excess capacity',
                'maintenance_priority': 2,
                'priority_level': 'LOW'
            })
            maintenance.append(row)

    return service, standby, maintenance


def calculate_maintenance_priority(reasons):
    """Calculate maintenance priority based on reasons (1-10 scale)"""
    priority = 5  # Default medium priority

    for reason in reasons:
        if "invalid" in reason.lower():
            priority = max(priority, 9)  # Highest priority
        elif "expiry" in reason.lower():
            priority = max(priority, 8)
        elif "high mileage" in reason.lower():
            priority = max(priority, 7)
        elif "open job card" in reason.lower():
            priority = max(priority, 6)
        elif "cleaning" in reason.lower():
            priority = max(priority, 3)

    return priority


def get_priority_level(priority_score):
    """Convert numeric priority score to text level"""
    if priority_score >= 8:
        return "CRITICAL"
    elif priority_score >= 6:
        return "HIGH"
    elif priority_score >= 4:
        return "MEDIUM"
    else:
        return "LOW"


def get_cleaning_complexity(mileage: float, age_months: int) -> str:
    """Determine cleaning complexity based on mileage and age"""
    if mileage > 5000 or age_months > 60:
        return "high"
    elif mileage > 3000 or age_months > 36:
        return "medium"
    else:
        return "low"