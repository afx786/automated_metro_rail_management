import pandas as pd
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"

def predict_certificate_expiry_csv(csv_file_path: str):
    model = joblib.load(MODEL_DIR / "certificate_expiry_predictor.joblib")
    df = pd.read_csv(csv_file_path)
    feat_cols = ["sensor_aggregate", "days_since_inspection", "open_job_card_count"]
    preds = model.predict(df[feat_cols])
    results = []
    for i, pred in enumerate(preds):
        actual = df["certificate_expired"].iloc[i] if "certificate_expired" in df.columns else None
        results.append({
            "index": i,
            "predicted": bool(pred),
            "actual": bool(actual) if actual is not None else None,
            "inputs": {col: df[col].iloc[i] for col in feat_cols}
        })
    return results

def predict_maintenance_urgency_csv(csv_file_path: str):
    model = joblib.load(MODEL_DIR / "maintenance_urgency_scorer.joblib")
    df = pd.read_csv(csv_file_path)
    desc_col = "description"
    preds = model.predict(df[desc_col])
    results = []
    for i, pred in enumerate(preds):
        actual = df["urgency"].iloc[i] if "urgency" in df.columns else None
        results.append({
            "index": i,
            "predicted": int(pred),
            "actual": int(actual) if actual is not None else None,
            "description": df[desc_col].iloc[i]
        })
    return results
