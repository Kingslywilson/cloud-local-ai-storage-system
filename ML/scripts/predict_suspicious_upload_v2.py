#!/usr/bin/env python3
"""
Inference Script for ML Model 2 V2: Suspicious Upload Detection.
Loads ml/models/suspicious_upload_random_forest_v2.joblib and provides predict_suspicious_upload_v2(upload_metadata).
"""

import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

_MODEL_PIPELINE_V2 = None
_EXPECTED_FEATURES_V2 = None


def get_model_pipeline_v2():
    global _MODEL_PIPELINE_V2, _EXPECTED_FEATURES_V2
    if _MODEL_PIPELINE_V2 is None:
        base_dir = Path(__file__).resolve().parent.parent
        model_path = base_dir / "models" / "suspicious_upload_random_forest_v2.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Trained V2 model not found at {model_path}. Run train_suspicious_upload_model_v2.py first.")
        _MODEL_PIPELINE_V2 = joblib.load(model_path)
        
        preprocessor = _MODEL_PIPELINE_V2.named_steps["preprocessor"]
        _EXPECTED_FEATURES_V2 = []
        for name, trans, cols in preprocessor.transformers_:
            _EXPECTED_FEATURES_V2.extend(cols)
    return _MODEL_PIPELINE_V2, _EXPECTED_FEATURES_V2


def predict_suspicious_upload_v2(upload_metadata):
    """
    Predict whether an upload behavior is Normal or Suspicious using Model 2 V2.

    Parameters:
        upload_metadata (dict or pd.DataFrame): Upload metadata containing behavioral features.

    Returns:
        dict: {
            "prediction": "Normal" | "Suspicious",
            "is_suspicious": bool,
            "confidence": float,
            "class_probabilities": {
                "Normal": float,
                "Suspicious": float
            }
        }
    """
    pipeline, expected_features = get_model_pipeline_v2()

    if isinstance(upload_metadata, dict):
        df_input = pd.DataFrame([upload_metadata])
    elif isinstance(upload_metadata, pd.DataFrame):
        df_input = upload_metadata.copy()
    else:
        raise ValueError("upload_metadata must be a dictionary or pandas DataFrame")

    drop_cols = ["label", "is_suspicious"]
    df_features = df_input.drop(columns=[c for c in drop_cols if c in df_input.columns])

    for col in expected_features:
        if col not in df_features.columns:
            df_features[col] = np.nan

    df_features = df_features[expected_features]

    predicted_label = pipeline.predict(df_features)[0]
    probabilities = pipeline.predict_proba(df_features)[0]
    classes = list(pipeline.classes_)

    class_probs = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}
    confidence = class_probs.get(predicted_label, 0.0)
    is_suspicious = (predicted_label == "Suspicious")

    return {
        "prediction": predicted_label,
        "is_suspicious": is_suspicious,
        "confidence": confidence,
        "class_probabilities": class_probs
    }


def main():
    print("==================================================")
    print("TESTING SUSPICIOUS UPLOAD PREDICTION V2")
    print("==================================================")

    # 1. Manual Example 1: Normal User Behavior
    normal_sample = {
        "file_size_mb": 5,
        "file_extension": "pdf",
        "upload_frequency": 3,
        "uploads_last_hour": 1,
        "uploads_last_24h": 8,
        "user_file_count": 80,
        "access_count": 5,
        "unique_ip_count": 1,
        "account_age_days": 180
    }

    # 2. Manual Example 2: Suspicious Bot / ATO / Exfiltration Behavior
    suspicious_sample = {
        "file_size_mb": 250,
        "file_extension": "zip",
        "upload_frequency": 60,
        "uploads_last_hour": 25,
        "uploads_last_24h": 100,
        "user_file_count": 100,
        "access_count": 80,
        "unique_ip_count": 8,
        "account_age_days": 2
    }

    res_normal = predict_suspicious_upload_v2(normal_sample)
    print("\n--- Manual Test Case 1 (Expected: Normal) ---")
    print(f"Prediction         : {res_normal['prediction']}")
    print(f"Is Suspicious      : {res_normal['is_suspicious']}")
    print(f"Confidence         : {res_normal['confidence']:.4f}")
    print(f"Class Probabilities: {res_normal['class_probabilities']}")

    res_suspicious = predict_suspicious_upload_v2(suspicious_sample)
    print("\n--- Manual Test Case 2 (Expected: Suspicious) ---")
    print(f"Prediction         : {res_suspicious['prediction']}")
    print(f"Is Suspicious      : {res_suspicious['is_suspicious']}")
    print(f"Confidence         : {res_suspicious['confidence']:.4f}")
    print(f"Class Probabilities: {res_suspicious['class_probabilities']}")

    base_dir = Path(__file__).resolve().parent.parent
    test_csv = base_dir / "dataset" / "suspicious_upload_test_v2.csv"

    if test_csv.exists():
        df_test = pd.read_csv(test_csv)
        print(f"\nEvaluating batch test set ({len(df_test)} samples)...")
        correct = 0
        for idx in range(len(df_test)):
            row = df_test.iloc[idx].to_dict()
            actual = row.get("label")
            pred = predict_suspicious_upload_v2(row)["prediction"]
            if pred == actual:
                correct += 1
        print(f"Batch Test Accuracy: {correct / len(df_test):.4f} ({correct}/{len(df_test)})")


if __name__ == "__main__":
    main()
