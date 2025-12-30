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
MODEL_DIR = BASE_DIR.parent / "models"            # backend/models

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


def normalize_column_name(col_name: str) -> str:
    """
    Converts database column names to match the training data format.
    Replaces spaces and special chars with underscores.
    """
    # Replace common patterns
    normalized = col_name.strip()
    normalized = normalized.replace(' ', '_')
    normalized = normalized.replace('-', '_')
    normalized = normalized.replace(',', '')
    normalized = normalized.replace('(', '')
    normalized = normalized.replace(')', '')
    normalized = normalized.replace('.', '_')
    
    # Handle specific known mappings
    name_mapping = {
        "Worn_out_grinding_wheel": "Worn_out_grinding_wheel",
        "WAITING TIME": "WAITING_TIME",
        "TOTAL GRINDING TIME": "TOTAL_GRINDING_TIME",
        "SPARK OUT TIME": "SPARK_OUT_TIME",
        "ROUGH GRINDING TIME": "ROUGH_GRINDING_TIME",
        "Rough_ 1 Grinding Distance": "Rough__1_Grinding_Distance",
        "Rough__1_Grinding_Dicmdstance": "Rough__1_Grinding_Distance",
        "RING CHANGE TIME": "RING_CHANGE_TIME",
        "New wheel diameter when dressed": "New_wheel_diameter_when_dressed",
        "Incremental retreat 1 initial": "Incremental_retreat_1_initial",
        "Grinding Wheel Speed": "Grinding_Wheel_Speed",
        "Grinding compensation interval ctr": "Grinding_compensation_interval_ctr",
        "Grinding compensation interval": "Grinding_compensation_interval",
        "Grinding reference position": "Grinding_reference_position",
        "Grinding_reference_position": "Grinding_reference_position",
        "DRESSING TIME": "DRESSING_TIME",
        "Constant Grinding Wheel Speed If SA48 = 1": "Constant_Grinding_Wheel_Speed_If_SA48_=_1",
        "Compensation memory": "Compensation_memory",
        "AIR GRINDING TIME": "AIR_GRINDING_TIME",
        "Actual wheel diameter": "Actual_wheel_diameter",
        "Grinding slide jump in position": "Grinding_slide_jump_in_position",
        "DRESSING PARK OUT TIME": "DRESSING_PARK_OUT_TIME"
    }
    
    return name_mapping.get(col_name, normalized)


def run_inference(raw_row: dict):
    """
    Takes ONE DB row (dict) and returns health metrics
    """

    # Normalize column names from database to match training data
    normalized_row = {normalize_column_name(k): v for k, v in raw_row.items()}
    
    # Align features
    df = pd.DataFrame([normalized_row]).reindex(columns=FEATURES)
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


