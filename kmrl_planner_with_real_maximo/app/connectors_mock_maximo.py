import json
import os
from sqlalchemy.orm import Session
from . import models

DATA_FILE = os.path.join(os.path.dirname(__file__), "dummy_maximo.json")


class MaximoMockConnector:
    """Simulated Maximo job-card connector.

    This is a mock/simulated data source used for development and demos.
    It serves synthetic job-card data instead of querying a real Maximo
    instance. Replace this with a real connector (e.g. app/connectors/
    maximo.py) once a live Maximo API is available.
    """

    def __init__(self, data_file: str = None):
        self.data_file = data_file or DATA_FILE

    def load(self) -> list:
        """Load mock job-card entries from JSON, or generate them if missing."""
        if not os.path.exists(self.data_file):
            return self._generate_mock_jobcards()
        with open(self.data_file, "r", encoding="utf-8") as f:
            return json.load(f)

    def _generate_mock_jobcards(self) -> list:
        """Generate deterministic mock job cards for trainsets KM01..KM25."""
        jobcards = []
        for i in range(1, 26):
            code = f"KM{i:02d}"
            status = "OPEN" if i % 3 == 0 else "CLOSED"
            jobcards.append({
                "train_id": code,
                "job_card_status": status,
                "work_order_id": f"WO{i:04d}",
            })
        return jobcards

    def update_trainsets_from_mock(self, db: Session):
        data = self.load()
        for entry in data:
            train_id = entry.get("train_id")
            status = entry.get("job_card_status", "").upper()
            job_open = status in ("OPEN", "WAPPR", "INPRG")
            row = db.query(models.Trainset).filter(models.Trainset.code == train_id).first()
            if row:
                row.job_card_open = job_open
        db.commit()
