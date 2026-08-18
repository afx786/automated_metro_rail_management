# optimizer.py
from datetime import datetime
from .planner import build_plan

def run(db, params=None):
    # Let exceptions propagate so failures are loud instead of being masked
    service, standby, maintenance = build_plan(db, params)
    return {
        'generated_at': datetime.utcnow().isoformat(),
        'service': service,
        'standby': standby,
        'maintenance': maintenance,
        'alerts': []
    }