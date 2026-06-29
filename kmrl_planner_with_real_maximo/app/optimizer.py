# optimizer.py - This should only contain the run function
from datetime import datetime
from .planner import build_plan

def run(db, params=None):
    try:
        service, standby, maintenance = build_plan(db, params)
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'revenue': service,
            'standby': standby,
            'ibl': maintenance,
            'alerts': []
        }
    except Exception as e:
        print(f"❌ Error in optimizer: {e}")
        # Return empty plan on error
        return {
            'generated_at': datetime.utcnow().isoformat(),
            'revenue': [],
            'standby': [],
            'ibl': [],
            'alerts': [f"Error generating plan: {str(e)}"]
        }