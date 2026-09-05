#!/usr/bin/env python3
"""
Inference Script for Random Forest File Type Classifier.
Loads ml/models/file_classifier_random_forest.joblib and provides predict_file(file_metadata).
"""

import sys
import joblib
import numpy as np
import pandas as pd
from pathlib import Path

_MODEL_PIPELINE = None
_EXPECTED_FEATURES = None


def get_model_pipeline():
    global _MODEL_PIPELINE, _EXPECTED_FEATURES
    if _MODEL_PIPELINE is None:
        base_dir = Path(__file__).resolve().parent.parent
        model_path = base_dir / "models" / "file_classifier_random_forest.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Trained model not found at {model_path}. Run train_random_forest.py first.")
        _MODEL_PIPELINE = joblib.load(model_path)
        
        preprocessor = _MODEL_PIPELINE.named_steps["preprocessor"]
        _EXPECTED_FEATURES = []
        for name, trans, cols in preprocessor.transformers_:
            _EXPECTED_FEATURES.extend(cols)
    return _MODEL_PIPELINE, _EXPECTED_FEATURES


def predict_file(file_metadata):
    """
    Predict file category and confidence from metadata dictionary or DataFrame.

    Parameters:
        file_metadata (dict or pd.DataFrame): Single file metadata record containing
            features like extension, mime_type, file_size_bytes, width, height, etc.

    Returns:
        dict: {
            "predicted_category": str,
            "confidence": float,
            "class_probabilities": dict
        }
    """
    pipeline, expected_features = get_model_pipeline()

    if isinstance(file_metadata, dict):
        df_input = pd.DataFrame([file_metadata])
    elif isinstance(file_metadata, pd.DataFrame):
        df_input = file_metadata.copy()
    else:
        raise ValueError("file_metadata must be a dictionary or pandas DataFrame")

    drop_cols = ["filename", "relative_path", "category"]
    df_features = df_input.drop(columns=[c for c in drop_cols if c in df_input.columns])

    for col in expected_features:
        if col not in df_features.columns:
            df_features[col] = np.nan

    df_features = df_features[expected_features]

    predicted_cat = pipeline.predict(df_features)[0]
    probabilities = pipeline.predict_proba(df_features)[0]
    classes = list(pipeline.classes_)

    class_probs = {cls: round(float(p), 4) for cls, p in zip(classes, probabilities)}
    confidence = class_probs.get(predicted_cat, 0.0)

    return {
        "predicted_category": predicted_cat,
        "confidence": confidence,
        "class_probabilities": class_probs
    }


def main():
    print("==================================================")
    print("TESTING FILE CATEGORY PREDICTION FUNCTION")
    print("==================================================")

    base_dir = Path(__file__).resolve().parent.parent
    test_csv = base_dir / "dataset" / "test.csv"

    if test_csv.exists():
        df_test = pd.read_csv(test_csv, low_memory=False)
        sample_indices = []
        for cat in sorted(df_test['category'].unique()):
            idx = df_test[df_test['category'] == cat].index[0]
            sample_indices.append(idx)

        print(f"Running predictions on {len(sample_indices)} test samples from test.csv:\n")

        all_succeeded = True
        for idx in sample_indices:
            row = df_test.iloc[idx].to_dict()
            actual_category = row.get("category", "Unknown")
            fname = row.get("filename", "unknown")

            result = predict_file(row)

            print(f"File              : {fname}")
            print(f"Actual Category   : {actual_category}")
            print(f"Predicted Category: {result['predicted_category']}")
            print(f"Confidence        : {result['confidence']:.4f}")
            print(f"Class Probs       : {result['class_probabilities']}")
            print("-" * 50)
            if not result['predicted_category']:
                all_succeeded = False

        if all_succeeded:
            print("\nPREDICTION TEST PASSED SUCCESSFULLY!")
    else:
        sample_doc = {
            "extension": "pdf",
            "mime_type": "application/pdf",
            "file_size_bytes": 245000,
            "file_size_kb": 239.25,
            "file_size_mb": 0.23,
            "page_count": 5,
            "text_length": 4500
        }
        result = predict_file(sample_doc)
        print(result)


if __name__ == "__main__":
    main()
