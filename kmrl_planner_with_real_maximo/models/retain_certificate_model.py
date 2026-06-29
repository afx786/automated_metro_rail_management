# retrain_fitness_model.py
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
import joblib
from pathlib import Path
import numpy as np
from datetime import datetime, timedelta

BASE_DIR = Path(__file__).parent / "models"
BASE_DIR.mkdir(exist_ok=True)

# Generate training data that predicts expiration in 6 months
def generate_training_data():
    """Generate training data where certificate expires in ~6 months"""
    np.random.seed(42)
    n_samples = 1000
    
    data = {
        'sensor_aggregate': np.random.uniform(0, 100, n_samples),
        'days_since_inspection': np.random.randint(0, 365, n_samples),
        'open_job_card_count': np.random.randint(0, 3, n_samples),
        'age_months': np.random.randint(0, 120, n_samples),
        'certificate_expires_in_days': np.random.randint(150, 210, n_samples)  # 5-7 months
    }
    
    df = pd.DataFrame(data)
    
    # Create binary target: 1 if expires in <= 180 days (6 months), 0 otherwise
    df['certificate_expiry_6mo'] = (df['certificate_expires_in_days'] <= 180).astype(int)
    
    return df

# Train the model
def train_fitness_model():
    print("🔄 Training fitness certificate expiry model...")
    
    # Generate training data
    df = generate_training_data()
    
    # Features and target
    feature_cols = ['sensor_aggregate', 'days_since_inspection', 'open_job_card_count', 'age_months']
    X = df[feature_cols]
    y = df['certificate_expiry_6mo']
    
    # Split data
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train model
    model = RandomForestClassifier(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    
    # Evaluate
    train_score = model.score(X_train, y_train)
    test_score = model.score(X_test, y_test)
    print(f"✅ Model trained - Train accuracy: {train_score:.3f}, Test accuracy: {test_score:.3f}")
    
    # Save model and feature columns
    model_path = BASE_DIR / "certificate_expiry_predictor.joblib"
    joblib.dump(model, model_path)
    
    feature_path = BASE_DIR / "certificate_expiry_feature_columns.pkl"
    joblib.dump(feature_cols, feature_path)
    
    print(f"💾 Model saved to {model_path}")
    print(f"💾 Feature columns saved to {feature_path}")
    
    return model, feature_cols

if __name__ == "__main__":
    train_fitness_model()