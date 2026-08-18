from pathlib import Path
import joblib
import pandas as pd
import numpy as np

BASE_DIR = Path(__file__).parent.parent / "models"
DEFAULT_FEATURE_COLS = ['sensor_aggregate', 'days_since_inspection', 'open_job_card_count', 'age_months']


class FitnessExpiryModel:
    _model = None
    _feature_cols = None

    @classmethod
    def load(cls):
        if cls._model is None:
            model_path = BASE_DIR / "certificate_expiry_predictor.joblib"
            cols_path = BASE_DIR / "certificate_expiry_feature_columns.pkl"
            if not model_path.exists():
                print("No trained certificate-expiry model found; using fallback logic")
                cls._model = DummyFitnessModel()
                cls._feature_cols = DEFAULT_FEATURE_COLS
            else:
                cls._model = joblib.load(model_path)
                if cols_path.exists():
                    cls._feature_cols = joblib.load(cols_path)
                else:
                    cls._feature_cols = DEFAULT_FEATURE_COLS
        return cls._model

    @classmethod
    def _build_input(cls, features: dict):
        """Build a DataFrame with the expected feature columns, padding missing ones with 0."""
        row = {col: features.get(col, 0.0) for col in cls._feature_cols}
        return pd.DataFrame([row], columns=cls._feature_cols)

    @classmethod
    def predict(cls, features: dict):
        """Predict if certificate will expire in the next 6 months."""
        try:
            model = cls.load()
            df = cls._build_input(features)
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(df)[0][1]
                return bool(probability > 0.5)
            return bool(model.predict(df)[0])
        except (TypeError, ValueError) as e:
            print(f"ML prediction error: {e}")
            return cls._fallback_prediction(features)

    @classmethod
    def predict_days_until_expiry(cls, features: dict):
        """Predict approximate days until expiry."""
        try:
            model = cls.load()
            df = cls._build_input(features)
            if hasattr(model, 'predict_proba'):
                probability = model.predict_proba(df)[0][1]
                days_until_expiry = int(180 * (1 - probability))
                return max(0, min(180, days_until_expiry))
            return 30 if cls.predict(features) else 200
        except (TypeError, ValueError) as e:
            print(f"Days prediction error: {e}")
            return 90

    @classmethod
    def _fallback_prediction(cls, features: dict):
        """Simple rule-based prediction without ML."""
        sensor_value = features.get('sensor_aggregate', 0)
        inspection_days = features.get('days_since_inspection', 30)
        age_months = features.get('age_months', 12)

        age_risk = min(1.0, age_months / 120.0)
        inspection_risk = min(1.0, inspection_days / 365.0)
        sensor_risk = min(1.0, sensor_value / 100.0)

        total_risk = (age_risk + inspection_risk + sensor_risk) / 3.0
        return total_risk > 0.6


class DummyFitnessModel:
    def predict(self, X):
        if hasattr(X, 'values'):
            X_array = X.values
        else:
            X_array = X

        predictions = []
        for i in range(len(X_array)):
            sensor_value = X_array[i, 0] if X_array.shape[1] > 0 else 0
            inspection_days = X_array[i, 1] if X_array.shape[1] > 1 else 30
            age_months = X_array[i, 3] if X_array.shape[1] > 3 else 12

            will_expire = (age_months > 48) or (inspection_days > 180) or (sensor_value > 90)
            predictions.append(1 if will_expire else 0)

        return np.array(predictions)

    def predict_proba(self, X):
        if hasattr(X, 'values'):
            X_array = X.values
        else:
            X_array = X

        probas = []
        for i in range(len(X_array)):
            sensor_value = X_array[i, 0] if X_array.shape[1] > 0 else 0
            inspection_days = X_array[i, 1] if X_array.shape[1] > 1 else 30
            age_months = X_array[i, 3] if X_array.shape[1] > 3 else 12

            age_risk = min(1.0, age_months / 120.0)
            inspection_risk = min(1.0, inspection_days / 365.0)
            sensor_risk = min(1.0, sensor_value / 100.0)

            total_risk = (age_risk + inspection_risk + sensor_risk) / 3.0

            prob_no_expiry = max(0.1, min(0.9, 1 - total_risk))
            prob_expiry = 1 - prob_no_expiry

            probas.append([prob_no_expiry, prob_expiry])

        return np.array(probas)


class MaintenanceUrgencyModel:
    _model = None

    @classmethod
    def load(cls):
        if cls._model is None:
            model_path = BASE_DIR / "maintenance_urgency_scorer.joblib"
            if not model_path.exists():
                print("No trained maintenance-urgency model found; using fallback logic")
                cls._model = DummyUrgencyModel()
            else:
                cls._model = joblib.load(model_path)
        return cls._model

    @classmethod
    def predict(cls, description: str):
        return int(cls.load().predict([description])[0])


class DummyUrgencyModel:
    def predict(self, X):
        import numpy as np
        return np.array([np.random.randint(1, 10) for _ in range(len(X))])
