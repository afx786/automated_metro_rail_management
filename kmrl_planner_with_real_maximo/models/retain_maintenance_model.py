# retrain_maintenance_model.py
import pandas as pd
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.ensemble import RandomForestClassifier
import joblib
from pathlib import Path

BASE_DIR = Path(__file__).parent / "models"
BASE_DIR.mkdir(exist_ok=True)

# Dummy dataset (replace with your real maintenance/job card history!)
data = pd.DataFrame({
    "description": [
        "brake overheating", "HVAC fan noise", "door stuck", "routine checkup",
        "unexpected shutdown", "branding film peeling", "battery low", "minor scratch"
    ],
    "urgency": [2, 1, 2, 0, 2, 0, 1, 0]  # Labels: 0=low, 1=medium, 2=high
})

# Use full dataset for training (tiny demo set → no test split)
X_train, y_train = data["description"], data["urgency"]

# Build pipeline
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(max_features=1000)),
    ("clf", RandomForestClassifier(n_estimators=100, random_state=42)),
])

# Train model
pipeline.fit(X_train, y_train)

# Save cleanly
model_path = BASE_DIR / "maintenance_urgency_scorer.joblib"
joblib.dump(pipeline, model_path)

print(f"✅ Model retrained and saved at {model_path}")
