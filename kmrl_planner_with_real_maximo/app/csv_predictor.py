import pandas as pd
import joblib
from pathlib import Path

MODEL_DIR = Path(__file__).parent.parent / "models"
DEFAULT_FEATURE_COLS = ["sensor_aggregate", "days_since_inspection", "open_job_card_count", "age_months"]


def _native(value):
    """Convert numpy scalars (np.int64, np.float64, np.bool_) to native Python types."""
    if hasattr(value, "item"):
        return value.item()
    return value


def _load_model(filename: str):
    path = MODEL_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Model not found: {path}. Run the retrain scripts in models/ to generate it.")
    return joblib.load(path)


def _load_feature_columns() -> list:
    path = MODEL_DIR / "certificate_expiry_feature_columns.pkl"
    if path.exists():
        cols = joblib.load(path)
        if isinstance(cols, (list, tuple)):
            return list(cols)
    return list(DEFAULT_FEATURE_COLS)


def predict_certificate_expiry_csv(csv_file_path: str):
    model = _load_model("certificate_expiry_predictor.joblib")
    feat_cols = _load_feature_columns()
    df = pd.read_csv(csv_file_path)

    missing = [c for c in feat_cols if c not in df.columns]
    if missing:
        raise ValueError(
            f"CSV is missing required feature columns: {missing}. Found columns: {list(df.columns)}"
        )

    preds = model.predict(df[feat_cols])
    results = []
    for i, pred in enumerate(preds):
        actual = df["certificate_expired"].iloc[i] if "certificate_expired" in df.columns else None
        results.append({
            "index": i,
            "predicted": bool(pred),
            "actual": _native(actual) if actual is not None else None,
            "inputs": {col: _native(df[col].iloc[i]) for col in feat_cols}
        })
    return results


def predict_maintenance_urgency_csv(csv_file_path: str):
    model = _load_model("maintenance_urgency_scorer.joblib")
    df = pd.read_csv(csv_file_path)

    if "description" not in df.columns:
        raise ValueError(f"CSV is missing required column 'description'. Found columns: {list(df.columns)}")

    preds = model.predict(df["description"])
    results = []
    for i, pred in enumerate(preds):
        actual = df["urgency"].iloc[i] if "urgency" in df.columns else None
        results.append({
            "index": i,
            "predicted": int(pred),
            "actual": int(_native(actual)) if actual is not None else None,
            "description": df["description"].iloc[i]
        })
    return results
