# backend/ml/spindle_inference.py

import numpy as np
import pandas as pd
import joblib
import onnxruntime as ort
from pathlib import Path

# ------------------------
# Paths
# ------------------------
BASE_DIR = Path(__file__).resolve().parent        # backend/ml
MODEL_DIR = BASE_DIR / "models"            # backend/models

# ------------------------
# Load artifacts
# ------------------------
session = ort.InferenceSession(
    str(MODEL_DIR / "spindle_autoencoder.onnx"),
    providers=["CPUExecutionProvider"]
)

scaler = joblib.load(MODEL_DIR / "spindle_scaler.pkl")
FEATURES = joblib.load(MODEL_DIR / "spindle_features.pkl")
thresholds = joblib.load(MODEL_DIR / "spindle_thresholds.pkl")

MSE_MAX = thresholds["MSE_MAX"]
MSE_P95 = thresholds["MSE_P95"]

INPUT_NAME = session.get_inputs()[0].name


def run_inference(raw_row: dict):
    """
    Takes ONE DB row (dict) and returns health metrics
    """

    # Align features
    df = pd.DataFrame([raw_row]).reindex(columns=FEATURES)
    df = df.ffill().bfill().fillna(0)

    X = scaler.transform(df).astype(np.float32)

    # ONNX inference
    recon = session.run(None, {INPUT_NAME: X})[0]

    mse = float(np.mean((X - recon) ** 2))

    # Health score
    health = max(0.0, 100.0 - (mse / MSE_MAX * 100.0))

    # Failure probability
    if health > 80:
        risk = 0.05
    elif health > 60:
        risk = min(0.5, mse / MSE_P95)
    else:
        risk = min(1.0, mse / MSE_P95)

    status = (
        "CRITICAL" if health < 50 else
        "WARNING" if health < 70 else
        "NORMAL"
    )

    return {
        "health_score": round(health, 2),
        "failure_risk": round(risk, 3),
        "anomaly_score": round(mse, 6),
        "status": status
    }


