import os, requests
from sqlalchemy.orm import Session
from . import models

DATA_FILE = os.path.join(os.path.dirname(__file__), 'data', './kmrl_real_maximo.db')

class MaximoDummyConnector:
    def __init__(self, data_file: str = None):
        self.data_file = data_file or DATA_FILE

    def load(self):
        with open(self.data_file, 'r') as f:
            return json.load(f)

    def update_trainsets_from_dummy(self, db: Session):
        data = self.load()
        for entry in data:
            train_id = entry.get('train_id')
            status = entry.get('job_card_status','').upper()
            job_open = status == 'OPEN'
            # match trainset code: support KM01 style
            row = db.query(models.Trainset).filter(models.Trainset.code == train_id).first()
            if row:
                row.job_card_open = job_open
        db.commit()


# class MaximoConnector:
#     def __init__(self, base_url=None, api_key=None, username=None, password=None):
#         self.base_url = base_url or os.getenv('MAXIMO_URL')
#         self.api_key = api_key or os.getenv('MAXIMO_APIKEY')
#         self.username = username or os.getenv('MAXIMO_USER')
#         self.password = password or os.getenv('MAXIMO_PASS')
#         if not self.base_url:
#             raise ValueError('MAXIMO_URL not set')

#     def fetch_jobcards(self):
#         # Example Maximo REST endpoint; adjust path as needed for your instance
#         url = f"{self.base_url.rstrip('/')}/rest/os/mxwo"
#         headers = {}
#         if self.api_key:
#             headers['apik']= self.api_key
#         auth = (self.username, self.password) if self.username and self.password else None
#         resp = requests.get(url, headers=headers, auth=auth, timeout=30)
#         resp.raise_for_status()
#         return resp.json()

#     def update_trainsets_from_maximo(self, db: Session):
#         data = self.fetch_jobcards()
#         # Expecting simple schema: {'member': [ { 'assetnum': 'KM01', 'status': 'OPEN' }, ... ] }
#         members = data.get('member') or data.get('members') or data.get('results') or data
#         for entry in members:
#             code = entry.get('assetnum') or entry.get('train_id') or entry.get('asset')
#             status = (entry.get('status') or entry.get('job_card_status') or '').upper()
#             job_open = status == 'OPEN' or status == 'WAPPR' or status == 'INPRG'
#             row = db.query(models.Trainset).filter(models.Trainset.code == code).first()
#             if row:
#                 row.job_card_open = job_open
#         db.commit()
