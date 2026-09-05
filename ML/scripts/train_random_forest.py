#!/usr/bin/env python3
"""
Random Forest File Classification Training & Evaluation Script.
Trains RandomForestClassifier using ONLY ml/dataset/train.csv and evaluates on ml/dataset/test.csv.

Generates:
  - ml/models/file_classifier_random_forest.joblib
  - ml/models/model_results.txt
  - ml/models/confusion_matrix.png
  - ml/models/feature_importance.csv
  - ml/models/feature_importance.png
"""

import os
import sys
import joblib
from pathlib import Path
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import OneHotEncoder
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    balanced_accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    confusion_matrix,
    classification_report
)


def main():
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / "dataset"
    models_dir = base_dir / "models"
    models_dir.mkdir(parents=True, exist_ok=True)

    # Clean existing old model files if present
    for old_file in ["file_classifier_random_forest.joblib", "model_results.txt",
                      "confusion_matrix.png", "feature_importance.csv", "feature_importance.png"]:
        old_path = models_dir / old_file
        if old_path.exists():
            old_path.unlink()

    train_csv = dataset_dir / "train.csv"
    test_csv = dataset_dir / "test.csv"

    if not train_csv.exists() or not test_csv.exists():
        print(f"Error: Required train.csv or test.csv not found in {dataset_dir}")
        sys.exit(1)

    print("==================================================")
    print("1. LOADING REDUCED TRAIN & TEST DATASETS")
    print("==================================================")

    df_train = pd.read_csv(train_csv, low_memory=False)
    df_test = pd.read_csv(test_csv, low_memory=False)

    print(f"Train samples: {len(df_train)}")
    print(f"Test samples : {len(df_test)}")

    # Check overlap
    train_paths = set(df_train["relative_path"])
    test_paths = set(df_test["relative_path"])
    overlap_count = len(train_paths.intersection(test_paths))
    print(f"Train/Test overlap: {overlap_count}")

    print("\n--- Training Class Distribution ---")
    print(df_train["category"].value_counts().to_string())

    print("\n--- Testing Class Distribution ---")
    print(df_test["category"].value_counts().to_string())

    target_col = "category"
    ignore_cols = ["filename", "relative_path", target_col]

    # Explicit Feature Identification
    cat_cols = ["extension", "mime_type", "codec"]
    num_cols = [
        "file_size_bytes", "file_size_kb", "file_size_mb",
        "width", "height", "duration_seconds", "fps",
        "sample_rate", "channels", "page_count", "text_length",
        "line_count", "character_count", "comment_line_count", "blank_line_count"
    ]

    # Filter to features present in dataset
    cat_cols = [c for c in cat_cols if c in df_train.columns]
    num_cols = [c for c in num_cols if c in df_train.columns]

    X_train = df_train[cat_cols + num_cols]
    y_train = df_train[target_col]

    X_test = df_test[cat_cols + num_cols]
    y_test = df_test[target_col]

    print(f"\nCategorical features ({len(cat_cols)}): {cat_cols}")
    print(f"Numerical features ({len(num_cols)}): {num_cols}")

    print("\n==================================================")
    print("2. BUILDING PIPELINE & TRAINING RANDOM FOREST")
    print("==================================================")

    cat_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="constant", fill_value="missing")),
        ("encoder", OneHotEncoder(handle_unknown="ignore", sparse_output=False))
    ])

    num_pipeline = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median"))
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ("cat", cat_pipeline, cat_cols),
            ("num", num_pipeline, num_cols)
        ],
        remainder="drop"
    )

    clf = RandomForestClassifier(
        n_estimators=300,
        random_state=42,
        class_weight="balanced",
        n_jobs=-1
    )

    model_pipeline = Pipeline(steps=[
        ("preprocessor", preprocessor),
        ("classifier", clf)
    ])

    model_pipeline.fit(X_train, y_train)
    print("Model training complete!")

    print("\n==================================================")
    print("3. EVALUATING MODEL ON TEST SET")
    print("==================================================")

    y_pred = model_pipeline.predict(X_test)
    y_proba = model_pipeline.predict_proba(X_test)

    target_labels = sorted(list(df_train[target_col].unique()))

    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    macro_prec = precision_score(y_test, y_pred, average="macro")
    macro_rec = recall_score(y_test, y_pred, average="macro")
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    cm = confusion_matrix(y_test, y_pred, labels=target_labels)
    clf_rep = classification_report(y_test, y_pred, labels=target_labels)

    print(f"Accuracy         : {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"Macro Precision  : {macro_prec:.4f}")
    print(f"Macro Recall     : {macro_rec:.4f}")
    print(f"Macro F1-score   : {macro_f1:.4f}")
    print(f"Weighted F1-score: {weighted_f1:.4f}")
    print("\nClassification Report:\n", clf_rep)

    print("\n==================================================")
    print("4. GENERATING ARTIFACTS")
    print("==================================================")

    # 1. Confusion Matrix Plot
    cm_path = models_dir / "confusion_matrix.png"
    plt.figure(figsize=(8, 6))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Blues",
                xticklabels=target_labels, yticklabels=target_labels)
    plt.title("Random Forest File Classification Confusion Matrix")
    plt.xlabel("Predicted Category")
    plt.ylabel("Actual Category")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot: {cm_path}")

    # 2. Feature Importance CSV & Plot
    fitted_preprocessor = model_pipeline.named_steps["preprocessor"]
    fitted_clf = model_pipeline.named_steps["classifier"]

    raw_feature_names = fitted_preprocessor.get_feature_names_out()
    clean_feature_names = [name.replace("cat__", "").replace("num__", "") for name in raw_feature_names]

    importances = fitted_clf.feature_importances_

    df_importance = pd.DataFrame({
        "feature": clean_feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    fi_csv_path = models_dir / "feature_importance.csv"
    df_importance.to_csv(fi_csv_path, index=False)
    print(f"Saved feature importance CSV: {fi_csv_path}")

    fi_img_path = models_dir / "feature_importance.png"
    plt.figure(figsize=(10, 8))
    top_20 = df_importance.head(20).sort_values(by="importance", ascending=True)
    plt.barh(top_20["feature"], top_20["importance"], color="skyblue")
    plt.title("Top 20 Feature Importances (Random Forest)")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(fi_img_path, dpi=300)
    plt.close()
    print(f"Saved feature importance plot: {fi_img_path}")

    # 3. Model Results Text File
    results_txt_path = models_dir / "model_results.txt"
    results_content = f"""==================================================
RANDOM FOREST FILE CLASSIFICATION MODEL RESULTS
==================================================

Dataset Information:
-------------------
Training samples: {len(df_train)}
Testing samples : {len(df_test)}

Training Class Distribution:
{df_train['category'].value_counts().to_string()}

Testing Class Distribution:
{df_test['category'].value_counts().to_string()}

Model Configuration:
-------------------
Algorithm     : RandomForestClassifier
n_estimators  : 300
random_state  : 42
class_weight  : balanced
n_jobs        : -1

Evaluation Results:
-------------------
Accuracy          : {acc:.4f}
Balanced Accuracy : {bal_acc:.4f}
Macro Precision   : {macro_prec:.4f}
Macro Recall      : {macro_rec:.4f}
Macro F1-score    : {macro_f1:.4f}
Weighted F1-score : {weighted_f1:.4f}

Classification Report:
---------------------
{clf_rep}
"""
    with open(results_txt_path, "w", encoding="utf-8") as f:
        f.write(results_content)
    print(f"Saved model results text: {results_txt_path}")

    # 4. Save Trained Pipeline
    model_joblib_path = models_dir / "file_classifier_random_forest.joblib"
    joblib.dump(model_pipeline, model_joblib_path)
    print(f"Saved model pipeline: {model_joblib_path}")


if __name__ == "__main__":
    main()
