"""
Simple model generator to test compatibility and generate artifacts.
Uses PCA-based reconstruction instead of TensorFlow/Keras to avoid compatibility issues.
"""

import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA

# Paths
BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR.parent / "public" / "data" / "spindle_data.csv"
MODEL_DIR = BASE_DIR / "models"

print("=" * 60)
print("SIMPLE MODEL GENERATOR - Testing Approach")
print("=" * 60)

# Step 1: Load data
print("\n1. Loading CSV data...")
df = pd.read_csv(DATA_PATH)
print(f"   - Loaded {len(df)} rows, {len(df.columns)} columns")
print(f"   - First few columns: {list(df.columns[:10])}")

# Step 2: Select numeric features only
print("\n2. Selecting numeric features...")
numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()

# Remove id and timestamp-like columns
exclude_cols = ['id', 'machine_id', 'timestamp']
numeric_cols = [col for col in numeric_cols if col not in exclude_cols]

print(f"   - Selected {len(numeric_cols)} numeric features")
print(f"   - Sample features: {numeric_cols[:10]}")

# Step 3: Prepare data
print("\n3. Preparing data...")
X = df[numeric_cols].copy()

# Handle missing values
print(f"   - Missing values before: {X.isnull().sum().sum()}")
X = X.ffill().bfill().fillna(0)
print(f"   - Missing values after: {X.isnull().sum().sum()}")

# Step 4: Scale data
print("\n4. Scaling data...")
scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
print(f"   - Scaled shape: {X_scaled.shape}")
print(f"   - Scaled mean: {X_scaled.mean():.6f}, std: {X_scaled.std():.6f}")

# Step 5: Create PCA-based "autoencoder"
print("\n5. Creating PCA model (simpler than neural network)...")
n_components = min(20, len(numeric_cols))  # Use 20 components or less
pca = PCA(n_components=n_components)
X_encoded = pca.fit_transform(X_scaled)
X_reconstructed = pca.inverse_transform(X_encoded)

print(f"   - PCA components: {n_components}")
print(f"   - Explained variance: {pca.explained_variance_ratio_.sum():.4f}")

# Step 6: Calculate reconstruction errors
print("\n6. Calculating reconstruction errors (MSE)...")
reconstruction_errors = np.mean((X_scaled - X_reconstructed) ** 2, axis=1)

mse_mean = np.mean(reconstruction_errors)
mse_std = np.std(reconstruction_errors)
mse_p95 = np.percentile(reconstruction_errors, 95)
mse_p99 = np.percentile(reconstruction_errors, 99)
mse_max = np.max(reconstruction_errors)

print(f"   - MSE mean: {mse_mean:.6f}")
print(f"   - MSE std: {mse_std:.6f}")
print(f"   - MSE 95th percentile: {mse_p95:.6f}")
print(f"   - MSE 99th percentile: {mse_p99:.6f}")
print(f"   - MSE max: {mse_max:.6f}")

# Step 7: Save artifacts
print("\n7. Saving artifacts...")
MODEL_DIR.mkdir(exist_ok=True)

# Save scaler
scaler_path = MODEL_DIR / "spindle_scaler.pkl"
joblib.dump(scaler, scaler_path)
print(f"   ✓ Saved scaler: {scaler_path.name}")

# Save PCA model (as "autoencoder")
pca_path = MODEL_DIR / "spindle_pca_model.pkl"
joblib.dump(pca, pca_path)
print(f"   ✓ Saved PCA model: {pca_path.name}")

# Save feature names
features_path = MODEL_DIR / "spindle_features.pkl"
joblib.dump(numeric_cols, features_path)
print(f"   ✓ Saved features ({len(numeric_cols)} features): {features_path.name}")

# Save thresholds
thresholds = {
    "MSE_MEAN": float(mse_mean),
    "MSE_STD": float(mse_std),
    "MSE_P95": float(mse_p95),
    "MSE_P99": float(mse_p99),
    "MSE_MAX": float(mse_max)
}
thresholds_path = MODEL_DIR / "spindle_thresholds.pkl"
joblib.dump(thresholds, thresholds_path)
print(f"   ✓ Saved thresholds: {thresholds_path.name}")

# Step 8: Test inference on a sample
print("\n8. Testing inference on sample row...")
sample_row = df.iloc[100][numeric_cols].to_dict()
sample_df = pd.DataFrame([sample_row])
sample_df = sample_df.ffill().bfill().fillna(0)

# Scale
X_sample = scaler.transform(sample_df)

# Reconstruct using PCA
X_sample_encoded = pca.transform(X_sample)
X_sample_reconstructed = pca.inverse_transform(X_sample_encoded)

# Calculate MSE
sample_mse = float(np.mean((X_sample - X_sample_reconstructed) ** 2))

# Calculate health score
health_score = max(0.0, 100.0 - (sample_mse / mse_max * 100.0))

# Calculate failure risk
if health_score > 80:
    failure_risk = 0.05
elif health_score > 60:
    failure_risk = min(0.5, sample_mse / mse_p95)
else:
    failure_risk = min(1.0, sample_mse / mse_p95)

status = (
    "CRITICAL" if health_score < 50 else
    "WARNING" if health_score < 70 else
    "NORMAL"
)

print(f"   - Sample MSE: {sample_mse:.6f}")
print(f"   - Health Score: {health_score:.2f}")
print(f"   - Failure Risk: {failure_risk:.3f}")
print(f"   - Status: {status}")

print("\n" + "=" * 60)
print("✓ MODEL GENERATION COMPLETE")
print("=" * 60)
print("\nNext steps:")
print("1. Update spindle_inference.py to use PCA instead of ONNX")
print("2. Test with ml_worker.py")
print("=" * 60)
