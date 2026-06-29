from fastapi import APIRouter
from pydantic import BaseModel
from app import ml_models
from fastapi import APIRouter, UploadFile, File, HTTPException
from app.csv_predictor import predict_certificate_expiry_csv, predict_maintenance_urgency_csv
import os
import tempfile



router = APIRouter(prefix="/ml", tags=["ml"])

class FitnessFeatures(BaseModel):
    sensor_aggregate: float
    days_since_inspection: int
    open_job_card_count: int

@router.post("/csv/certificate_expiry/")
async def csv_certificate_expiry(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, "Only CSV files accepted.")
    # Use tempfile for safe temp file creation
    with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
        tmp.write(await file.read())
        tmp.flush()
        results = predict_certificate_expiry_csv(tmp.name)
    os.unlink(tmp.name)  # optionally delete manually after reading
    return {"results": results}

@router.post("/predict_fitness_expiry")
def predict_fitness_expiry(features: FitnessFeatures):
    pred = ml_models.FitnessExpiryModel.predict(features.dict())
    return {"certificate_expiry_pred": bool(pred)}

class JobCardDescription(BaseModel):
    description: str

@router.post("/maintenance_urgency")
def predict_maintenance_urgency(data: JobCardDescription):
    urgency = ml_models.MaintenanceUrgencyModel.predict(data.description)
    return {"maintenance_urgency": urgency}

@router.post("/csv/certificate_expiry/")
async def csv_certificate_expiry(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, detail="Only CSV files are accepted.")
    contents = await file.read()
    tmp_path = f"/tmp/cert_expiry_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(contents)
    results = predict_certificate_expiry_csv(tmp_path)
    return {"results": results}

@router.post("/csv/maintenance_urgency/")
async def csv_maintenance_urgency(file: UploadFile = File(...)):
    if not file.filename.endswith('.csv'):
        raise HTTPException(400, detail="Only CSV files are accepted.")
    contents = await file.read()
    tmp_path = f"/tmp/maint_urgency_{file.filename}"
    with open(tmp_path, "wb") as f:
        f.write(contents)
    results = predict_maintenance_urgency_csv(tmp_path)
    return {"results": results}