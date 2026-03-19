from pathlib import Path
from typing import Optional
import sys

import joblib
import numpy as np


XGBOOST_MODEL_PATH = Path(__file__).resolve().parent / "models" / "xgboost_biochem.joblib"
MODEL_PATH = Path(__file__).resolve().parent / "models" / "model.joblib"


def _load_joblib_with_numpy_compat(model_path: Path) -> dict:
    try:
        return joblib.load(model_path)
    except ModuleNotFoundError as exc:
        if not exc.name or not exc.name.startswith("numpy._core"):
            raise

        # Compatibility for model artifacts serialized on NumPy 2.x.
        import numpy.core as np_core

        sys.modules.setdefault("numpy._core", np_core)
        if hasattr(np_core, "multiarray"):
            sys.modules.setdefault("numpy._core.multiarray", np_core.multiarray)
        if hasattr(np_core, "numeric"):
            sys.modules.setdefault("numpy._core.numeric", np_core.numeric)

        return joblib.load(model_path)


class XGBoostModel:
    """Wrapper cho XGBoost Biochemical Model"""

    def __init__(self, model_path=XGBOOST_MODEL_PATH):
        self.model_package = _load_joblib_with_numpy_compat(model_path)
        self.model = self.model_package["model"]
        self.scaler = self.model_package["scaler"]

    def predict(self, features: np.ndarray) -> tuple[str, float]:
        features_scaled = self.scaler.transform(features.reshape(1, -1))
        proba_malignant = self.model.predict_proba(features_scaled)[0, 1]
        if proba_malignant >= 0.5:
            prediction = "malignant"
            confidence = proba_malignant
        else:
            prediction = "benign"
            confidence = 1 - proba_malignant
        return prediction, float(confidence)


def load_model() -> Optional[dict]:
    """Load XGBoost model and scaler."""
    if MODEL_PATH.exists():
        return _load_joblib_with_numpy_compat(MODEL_PATH)
    return None


def predict_with_model(model_package: dict, features: np.ndarray) -> tuple[str, float]:
    """Predict using XGBoost model with scaler."""
    model = model_package["model"]
    scaler = model_package["scaler"]

    features_scaled = scaler.transform(features.reshape(1, -1))
    proba_malignant = model.predict_proba(features_scaled)[0, 1]

    if proba_malignant >= 0.5:
        prediction = "malignant"
        confidence = proba_malignant
    else:
        prediction = "benign"
        confidence = 1 - proba_malignant

    return prediction, float(confidence)
