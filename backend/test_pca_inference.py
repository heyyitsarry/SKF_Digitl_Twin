"""
Test the PCA-based inference module
"""

import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent / "ml"))

from spindle_inference_PCA import run_inference
import pandas as pd

# Load sample data
DATA_PATH = Path(__file__).parent.parent / "public" / "data" / "spindle_data.csv"
df = pd.read_csv(DATA_PATH)

print("=" * 60)
print("Testing PCA-based Inference")
print("=" * 60)

# Test on 5 random samples
test_indices = [100, 500, 1000, 5000, 10000]

for idx in test_indices:
    if idx >= len(df):
        continue
    
    print(f"\n--- Sample #{idx} ---")
    row = df.iloc[idx].to_dict()
    
    result = run_inference(row)
    
    print(f"Health Score:     {result['health_score']}")
    print(f"Failure Risk:     {result['failure_risk']}")
    print(f"Status:           {result['status']}")
    print(f"Anomaly Score:    {result['anomaly_score']:.6f}")

print("\n" + "=" * 60)
print("✓ PCA Inference Test Complete")
print("=" * 60)
