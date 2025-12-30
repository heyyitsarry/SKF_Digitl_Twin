# backend/ml/spindle_inference_PCA.py

import numpy as np
import pandas as pd
import joblib
from pathlib import Path

# ------------------------
# Paths
# ------------------------
BASE_DIR = Path(__file__).resolve().parent        # backend/ml
MODEL_DIR = BASE_DIR.parent / "models"            # backend/models

# ------------------------
# Load artifacts
# ------------------------
scaler = joblib.load(MODEL_DIR / "spindle_scaler.pkl")
pca_model = joblib.load(MODEL_DIR / "spindle_pca_model.pkl")
FEATURES = joblib.load(MODEL_DIR / "spindle_features.pkl")
thresholds = joblib.load(MODEL_DIR / "spindle_thresholds.pkl")

MSE_MAX = thresholds["MSE_MAX"]
MSE_P95 = thresholds["MSE_P95"]
MSE_MEAN = thresholds["MSE_MEAN"]

# print(f"Loaded PCA-based inference model")
# print(f"  - Features: {len(FEATURES)}")
# print(f"  - PCA components: {pca_model.n_components_}")
# print(f"  - Thresholds: MSE_MAX={MSE_MAX:.6f}, MSE_P95={MSE_P95:.6f}")


def run_inference(raw_row: dict):
    """
    Takes ONE DB row (dict) and returns health metrics
    Using PCA-based reconstruction instead of neural network
    """

    # Align features - use only the features the model was trained on
    df = pd.DataFrame([raw_row]).reindex(columns=FEATURES)
    df = df.ffill().bfill().fillna(0)

    # Scale
    X = scaler.transform(df).astype(np.float32)

    # PCA encode and reconstruct
    X_encoded = pca_model.transform(X)
    X_reconstructed = pca_model.inverse_transform(X_encoded)

    # Calculate reconstruction error (MSE)
    mse = float(np.mean((X - X_reconstructed) ** 2))

    # Health score: 100 = perfect, 0 = worst
    health = max(0.0, 100.0 - (mse / MSE_MAX * 100.0))

    # Failure probability
    if health > 80:
        risk = 0.05
    elif health > 60:
        risk = min(0.5, mse / MSE_P95)
    else:
        risk = min(1.0, mse / MSE_P95)

    # Status determination
    status = (
        "CRITICAL" if health < 50 else
        "WARNING" if health < 70 else
        "NORMAL"
    )

    return {
        "health_score": round(health, 2),
        "failure_risk": round(risk, 3),
        "anomaly_score": round(mse, 6),
        "status": status,
        "reconstruction_error": round(mse, 6),
        "threshold_p95": round(MSE_P95, 6),
        "threshold_max": round(MSE_MAX, 6)
    }
