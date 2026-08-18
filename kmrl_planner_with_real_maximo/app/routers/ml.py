from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from .. import ml_models
from ..csv_predictor import predict_certificate_expiry_csv, predict_maintenance_urgency_csv
import os
import tempfile

router = APIRouter(prefix="/ml", tags=["ml"])

MAX_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB


class FitnessFeatures(BaseModel):
    sensor_aggregate: float
    days_since_inspection: int
    open_job_card_count: int
    age_months: int = 12


class JobCardDescription(BaseModel):
    description: str


def _save_upload(file: UploadFile) -> str:
    """Validate and save an uploaded CSV to a temp file; returns its path."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only CSV files are accepted.")
    filename = os.path.basename(file.filename).replace("\x00", "")
    contents = file.file.read()
    if len(contents) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=400, detail="File too large (max 10 MB).")
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".csv", prefix="kmrl_")
    try:
        tmp.write(contents)
        tmp.flush()
        os.fsync(tmp.fileno())
    finally:
        tmp.close()
    return tmp.name


@router.post("/csv/certificate_expiry/")
async def csv_certificate_expiry(file: UploadFile = File(...)):
    tmp_path = _save_upload(file)
    try:
        results = predict_certificate_expiry_csv(tmp_path)
    except (ValueError, FileNotFoundError, KeyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)
    return {"results": results}


@router.post("/csv/maintenance_urgency/")
async def csv_maintenance_urgency(file: UploadFile = File(...)):
    tmp_path = _save_upload(file)
    try:
        results = predict_maintenance_urgency_csv(tmp_path)
    except (ValueError, FileNotFoundError, KeyError) as e:
        raise HTTPException(status_code=422, detail=str(e))
    finally:
        os.unlink(tmp_path)
    return {"results": results}


@router.post("/predict_fitness_expiry")
def predict_fitness_expiry(features: FitnessFeatures):
    pred = ml_models.FitnessExpiryModel.predict(features.model_dump())
    return {"certificate_expiry_pred": bool(pred)}


@router.post("/maintenance_urgency")
def predict_maintenance_urgency(data: JobCardDescription):
    urgency = ml_models.MaintenanceUrgencyModel.predict(data.description)
    return {"maintenance_urgency": urgency}
