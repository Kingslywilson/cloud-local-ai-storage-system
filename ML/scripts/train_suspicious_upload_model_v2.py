#!/usr/bin/env python3
"""
Training & Evaluation Script for ML Model 2 V2: Suspicious Upload Detection.
Trains a RandomForestClassifier pipeline using suspicious_upload_train_v2.csv
and evaluates on suspicious_upload_test_v2.csv.

Generates:
  - ml/models/suspicious_upload_random_forest_v2.joblib
  - ml/models/suspicious_upload_model_results_v2.txt
  - ml/models/suspicious_upload_confusion_matrix_v2.png
  - ml/models/suspicious_upload_feature_importance_v2.csv
  - ml/models/suspicious_upload_feature_importance_v2.png
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

    train_csv = dataset_dir / "suspicious_upload_train_v2.csv"
    test_csv = dataset_dir / "suspicious_upload_test_v2.csv"

    if not train_csv.exists() or not test_csv.exists():
        print(f"Error: Required V2 training files not found in {dataset_dir}")
        sys.exit(1)

    print("==================================================")
    print("1. LOADING SUSPICIOUS UPLOAD V2 DATASETS")
    print("==================================================")

    df_train = pd.read_csv(train_csv)
    df_test = pd.read_csv(test_csv)

    print(f"Training samples: {len(df_train)}")
    print(f"Testing samples : {len(df_test)}")

    # Check for row overlap
    overlap = pd.merge(df_train, df_test, how="inner")
    print(f"Train/Test row overlap: {len(overlap)}")

    print("\n--- Training Class Distribution ---")
    print(df_train["label"].value_counts().to_string())

    print("\n--- Testing Class Distribution ---")
    print(df_test["label"].value_counts().to_string())

    target_col = "label"

    cat_cols = ["file_extension"]
    num_cols = [
        "file_size_mb",
        "upload_frequency",
        "uploads_last_hour",
        "uploads_last_24h",
        "user_file_count",
        "access_count",
        "unique_ip_count",
        "account_age_days"
    ]

    feature_names = cat_cols + num_cols
    print(f"\nFeature names used ({len(feature_names)}): {feature_names}")

    X_train = df_train[feature_names]
    y_train = df_train[target_col]

    X_test = df_test[feature_names]
    y_test = df_test[target_col]

    print("\n==================================================")
    print("2. BUILDING PIPELINE & TRAINING RANDOM FOREST V2")
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
    print("Training complete!")

    print("\n==================================================")
    print("3. EVALUATING MODEL V2 ON TEST SET")
    print("==================================================")

    y_pred = model_pipeline.predict(X_test)
    y_proba = model_pipeline.predict_proba(X_test)

    target_labels = sorted(list(df_train[target_col].unique()))  # ['Normal', 'Suspicious']

    acc = accuracy_score(y_test, y_pred)
    bal_acc = balanced_accuracy_score(y_test, y_pred)
    macro_prec = precision_score(y_test, y_pred, average="macro")
    weighted_prec = precision_score(y_test, y_pred, average="weighted")
    macro_rec = recall_score(y_test, y_pred, average="macro")
    weighted_rec = recall_score(y_test, y_pred, average="weighted")
    macro_f1 = f1_score(y_test, y_pred, average="macro")
    weighted_f1 = f1_score(y_test, y_pred, average="weighted")

    cm = confusion_matrix(y_test, y_pred, labels=target_labels)
    clf_rep = classification_report(y_test, y_pred, labels=target_labels)

    print(f"Accuracy         : {acc:.4f}")
    print(f"Balanced Accuracy: {bal_acc:.4f}")
    print(f"Macro Precision  : {macro_prec:.4f}")
    print(f"Weighted Precision: {weighted_prec:.4f}")
    print(f"Macro Recall     : {macro_rec:.4f}")
    print(f"Weighted Recall  : {weighted_rec:.4f}")
    print(f"Macro F1-score   : {macro_f1:.4f}")
    print(f"Weighted F1-score: {weighted_f1:.4f}")
    print("\nClassification Report:\n", clf_rep)

    print("\n==================================================")
    print("4. GENERATING V2 ARTIFACTS")
    print("==================================================")

    # 1. Confusion Matrix Plot V2
    cm_path = models_dir / "suspicious_upload_confusion_matrix_v2.png"
    plt.figure(figsize=(7, 5))
    sns.heatmap(cm, annot=True, fmt="d", cmap="Reds",
                xticklabels=target_labels, yticklabels=target_labels)
    plt.title("Suspicious Upload Detection V2 Confusion Matrix")
    plt.xlabel("Predicted Label")
    plt.ylabel("Actual Label")
    plt.tight_layout()
    plt.savefig(cm_path, dpi=300)
    plt.close()
    print(f"Saved confusion matrix plot V2: {cm_path}")

    # 2. Feature Importance CSV & Plot V2
    fitted_preprocessor = model_pipeline.named_steps["preprocessor"]
    fitted_clf = model_pipeline.named_steps["classifier"]

    raw_feature_names = fitted_preprocessor.get_feature_names_out()
    clean_feature_names = [name.replace("cat__", "").replace("num__", "") for name in raw_feature_names]

    importances = fitted_clf.feature_importances_

    df_importance = pd.DataFrame({
        "feature": clean_feature_names,
        "importance": importances
    }).sort_values(by="importance", ascending=False)

    fi_csv_path = models_dir / "suspicious_upload_feature_importance_v2.csv"
    df_importance.to_csv(fi_csv_path, index=False)
    print(f"Saved feature importance CSV V2: {fi_csv_path}")

    fi_img_path = models_dir / "suspicious_upload_feature_importance_v2.png"
    plt.figure(figsize=(10, 6))
    top_20 = df_importance.head(20).sort_values(by="importance", ascending=True)
    plt.barh(top_20["feature"], top_20["importance"], color="coral")
    plt.title("Top Feature Importances (Suspicious Upload Detection V2)")
    plt.xlabel("Importance")
    plt.ylabel("Feature")
    plt.tight_layout()
    plt.savefig(fi_img_path, dpi=300)
    plt.close()
    print(f"Saved feature importance plot V2: {fi_img_path}")

    # Print Top 10 Features
    print("\nTop 10 Feature Importances V2:")
    print(df_importance.head(10).to_string(index=False))

    # 3. Model Results Text File V2
    results_txt_path = models_dir / "suspicious_upload_model_results_v2.txt"
    results_content = f"""==================================================
SUSPICIOUS UPLOAD DETECTION MODEL V2 RESULTS
==================================================

Dataset Information:
-------------------
Dataset Version  : V2 (Realistic Feature Overlap & Noise)
Training samples : {len(df_train)}
Testing samples  : {len(df_test)}
Train/Test Overlap: {len(overlap)}

Training Class Distribution:
{df_train['label'].value_counts().to_string()}

Testing Class Distribution:
{df_test['label'].value_counts().to_string()}

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
Weighted Precision: {weighted_prec:.4f}
Macro Recall      : {macro_rec:.4f}
Weighted Recall   : {weighted_rec:.4f}
Macro F1-score    : {macro_f1:.4f}
Weighted F1-score : {weighted_f1:.4f}

Classification Report:
---------------------
{clf_rep}

Confusion Matrix:
----------------
{cm}

Top 10 Features:
---------------
{df_importance.head(10).to_string(index=False)}
"""
    with open(results_txt_path, "w", encoding="utf-8") as f:
        f.write(results_content)
    print(f"\nSaved model results text V2: {results_txt_path}")

    # 4. Save Trained Pipeline V2
    model_joblib_path = models_dir / "suspicious_upload_random_forest_v2.joblib"
    joblib.dump(model_pipeline, model_joblib_path)
    print(f"Saved model pipeline V2: {model_joblib_path}")


if __name__ == "__main__":
    main()
