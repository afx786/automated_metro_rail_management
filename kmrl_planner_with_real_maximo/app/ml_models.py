from pathlib import Path
import joblib
import pandas as pd
from sklearn.impute import SimpleImputer
import numpy as np

BASE_DIR = Path(__file__).parent.parent / "models"
feature_cols = ['sensor_aggregate', 'days_since_inspection', 'open_job_card_count', 'age_months']

class FitnessExpiryModel:
    _model = None
    _feature_cols = None

    @classmethod
    def load(cls):
        if cls._model is None:
            try:
                cls._model = joblib.load(BASE_DIR / "certificate_expiry_predictor.joblib")
                cls._feature_cols = joblib.load(BASE_DIR / "certificate_expiry_feature_columns.pkl")
            except FileNotFoundError:
                # Fallback to dummy model
                print("⚠️  No trained model found, using fallback logic")
                cls._model = DummyFitnessModel()
                cls._feature_cols = feature_cols
        return cls._model

    @classmethod
    def predict(cls, features: dict):
        """Predict if certificate will expire in the next 6 months"""
        try:
            model = cls.load()
            
            # Create DataFrame with expected features
            df = pd.DataFrame([features], columns=cls._feature_cols)
            
            # Handle missing values
            imputer = SimpleImputer(strategy='constant', fill_value=0)
            df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=cls._feature_cols)
            
            # Convert to numpy array for compatibility
            X_array = df_imputed.values
            
            # Predict probability of expiry in 6 months
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(X_array)[0][1]  # Probability of expiry
                # Consider it expired if probability > 50%
                return bool(probability > 0.5)
            else:
                # For models without probability
                return bool(model.predict(X_array)[0])
                
        except Exception as e:
            print(f"❌ ML prediction error: {e}")
            # Fallback to simple rule-based prediction
            return cls._fallback_prediction(features)

    @classmethod
    def predict_days_until_expiry(cls, features: dict):
        """Predict approximate days until expiry"""
        try:
            model = cls.load()
            
            df = pd.DataFrame([features], columns=cls._feature_cols)
            imputer = SimpleImputer(strategy='constant', fill_value=0)
            df_imputed = pd.DataFrame(imputer.fit_transform(df), columns=cls._feature_cols)
            
            X_array = df_imputed.values
            
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(X_array)[0][1]
                # Convert probability to days (0-180 days scale)
                days_until_expiry = int(180 * (1 - probability))
                return max(0, min(180, days_until_expiry))
            else:
                # Fallback: if model predicts expiry, assume 30 days, else 200 days
                return 30 if cls.predict(features) else 200
                
        except Exception as e:
            print(f"❌ Days prediction error: {e}")
            return 90  # Default fallback

    @classmethod
    def _fallback_prediction(cls, features: dict):
        """Simple fallback prediction without ML"""
        # Extract values with defaults
        sensor_value = features.get('sensor_aggregate', 0)
        inspection_days = features.get('days_since_inspection', 30)
        job_card_count = features.get('open_job_card_count', 0)
        age_months = features.get('age_months', 12)
        
        # Simple rule-based prediction
        age_risk = min(1.0, age_months / 120.0)
        inspection_risk = min(1.0, inspection_days / 365.0)
        sensor_risk = min(1.0, sensor_value / 100.0)
        
        total_risk = (age_risk + inspection_risk + sensor_risk) / 3.0
        return total_risk > 0.6

class DummyFitnessModel:
    def predict(self, X):
        """Fallback prediction logic for 6-month expiry"""
        # Convert to numpy array if it's a DataFrame
        if hasattr(X, 'values'):
            X_array = X.values
        else:
            X_array = X
            
        predictions = []
        for i in range(len(X_array)):
            # Get feature values safely with defaults
            sensor_value = X_array[i, 0] if X_array.shape[1] > 0 else 0
            inspection_days = X_array[i, 1] if X_array.shape[1] > 1 else 30
            job_card_count = X_array[i, 2] if X_array.shape[1] > 2 else 0
            age_months = X_array[i, 3] if X_array.shape[1] > 3 else 12
            
            # Simple rule: expire if older than 4 years OR not inspected in 6 months
            will_expire = (age_months > 48) or (inspection_days > 180)
            predictions.append(1 if will_expire else 0)
        
        return np.array(predictions)
    
    def predict_proba(self, X):
        # Convert to numpy array if it's a DataFrame
        if hasattr(X, 'values'):
            X_array = X.values
        else:
            X_array = X
            
        probas = []
        for i in range(len(X_array)):
            # Get feature values safely with defaults
            sensor_value = X_array[i, 0] if X_array.shape[1] > 0 else 0
            inspection_days = X_array[i, 1] if X_array.shape[1] > 1 else 30
            job_card_count = X_array[i, 2] if X_array.shape[1] > 2 else 0
            age_months = X_array[i, 3] if X_array.shape[1] > 3 else 12
            
            # Calculate risk factors
            age_risk = min(1.0, age_months / 120.0)
            inspection_risk = min(1.0, inspection_days / 365.0)
            sensor_risk = min(1.0, sensor_value / 100.0)
            
            total_risk = (age_risk + inspection_risk + sensor_risk) / 3.0
            
            # Ensure probabilities sum to 1
            prob_no_expiry = max(0.1, min(0.9, 1 - total_risk))
            prob_expiry = 1 - prob_no_expiry
            
            probas.append([prob_no_expiry, prob_expiry])
        
        return np.array(probas)

class MaintenanceUrgencyModel:
    _model = None

    @classmethod
    def load(cls):
        if cls._model is None:
            try:
                cls._model = joblib.load(BASE_DIR / "maintenance_urgency_scorer.joblib")
            except FileNotFoundError:
                # Fallback to dummy model
                cls._model = DummyUrgencyModel()
        return cls._model

    @classmethod
    def predict(cls, description: str):
        return int(cls.load().predict([description])[0])

class DummyUrgencyModel:
    def predict(self, X):
        import numpy as np
        return np.array([np.random.randint(1, 10) for _ in range(len(X))])