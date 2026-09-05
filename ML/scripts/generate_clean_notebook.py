import json
import os
from pathlib import Path

def create_notebook():
    cells = [
        # Cell 1: Title & Overview
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "# Gradious AI-Enhanced Cloud Storage Platform\n",
                "## Machine Learning Module: File Classification & Suspicious Upload Detection\n",
                "\n",
                "This notebook contains the end-to-end machine learning pipeline for:\n",
                "1. **File Category Classifier**: Classifying files into `Document`, `Image`, `Video`, `Audio`, and `Code` using **Random Forest**.\n",
                "2. **Suspicious Upload Anomaly Detector**: Identifying normal vs. suspicious/malicious upload behaviors based on metadata and user activity patterns using **Random Forest**.\n",
                "\n",
                "---"
            ]
        },
        # Cell 2: Imports
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1. Environment Setup & Library Imports"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "import os\n",
                "import joblib\n",
                "import pandas as pd\n",
                "import numpy as np\n",
                "import matplotlib.pyplot as plt\n",
                "import seaborn as sns\n",
                "from pathlib import Path\n",
                "\n",
                "from sklearn.ensemble import RandomForestClassifier\n",
                "from sklearn.model_selection import train_test_split\n",
                "from sklearn.metrics import classification_report, confusion_matrix, accuracy_score, f1_score\n",
                "from sklearn.preprocessing import OneHotEncoder, StandardScaler\n",
                "from sklearn.compose import ColumnTransformer\n",
                "from sklearn.pipeline import Pipeline\n",
                "from sklearn.impute import SimpleImputer\n",
                "\n",
                "print(\"All Machine Learning dependencies imported successfully.\")"
            ]
        },
        # Cell 3: File Category Classifier Section Header
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "--- \n",
                "## Part 1: File Category Classification Model (Random Forest)\n",
                "\n",
                "### 1.1 Load File Classification Dataset"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "dataset_dir = Path(\"dataset\")\n",
                "train_path = dataset_dir / \"train.csv\"\n",
                "test_path = dataset_dir / \"test.csv\"\n",
                "\n",
                "if not train_path.exists():\n",
                "    train_path = dataset_dir / \"file_classification_reduced.csv\"\n",
                "\n",
                "df_train = pd.read_csv(train_path)\n",
                "df_test = pd.read_csv(test_path) if test_path.exists() else None\n",
                "\n",
                "print(f\"Training dataset shape: {df_train.shape}\")\n",
                "if df_test is not None:\n",
                "    print(f\"Testing dataset shape: {df_test.shape}\")\n",
                "\n",
                "df_train.head()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1.2 Feature Engineering & Pipeline Construction"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "target_col = \"category\"\n",
                "drop_cols = [c for c in [\"filename\", \"relative_path\", target_col] if c in df_train.columns]\n",
                "\n",
                "X_train = df_train.drop(columns=drop_cols)\n",
                "y_train = df_train[target_col]\n",
                "\n",
                "if df_test is not None:\n",
                "    X_test = df_test.drop(columns=drop_cols)\n",
                "    y_test = df_test[target_col]\n",
                "else:\n",
                "    X_train, X_test, y_train, y_test = train_test_split(X_train, y_train, random_state=42, test_size=0.2, stratify=y_train)\n",
                "\n",
                "numeric_features = X_train.select_dtypes(include=[\"int64\", \"float64\"]).columns.tolist()\n",
                "categorical_features = X_train.select_dtypes(include=[\"object\"]).columns.tolist()\n",
                "\n",
                "numeric_transformer = Pipeline(steps=[\n",
                "    (\"imputer\", SimpleImputer(strategy=\"median\")),\n",
                "    (\"scaler\", StandardScaler())\n",
                "])\n",
                "\n",
                "categorical_transformer = Pipeline(steps=[\n",
                "    (\"imputer\", SimpleImputer(strategy=\"constant\", fill_value=\"unknown\")),\n",
                "    (\"onehot\", OneHotEncoder(handle_unknown=\"ignore\", sparse_output=False))\n",
                "])\n",
                "\n",
                "preprocessor = ColumnTransformer(transformers=[\n",
                "    (\"num\", numeric_transformer, numeric_features),\n",
                "    (\"cat\", categorical_transformer, categorical_features)\n",
                "])\n",
                "\n",
                "clf_pipeline = Pipeline(steps=[\n",
                "    (\"preprocessor\", preprocessor),\n",
                "    (\"classifier\", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))\n",
                "])\n",
                "\n",
                "print(\"File Category Pipeline constructed successfully.\")"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1.3 Model Training & Performance Evaluation"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "clf_pipeline.fit(X_train, y_train)\n",
                "y_pred = clf_pipeline.predict(X_test)\n",
                "\n",
                "acc = accuracy_score(y_test, y_pred)\n",
                "print(f\"File Classification Accuracy: {acc * 100:.2f}%\")\n",
                "print(\"\\nClassification Report:\")\n",
                "print(classification_report(y_test, y_pred))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 1.4 Confusion Matrix Visualization"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "cm = confusion_matrix(y_test, y_pred, labels=clf_pipeline.classes_)\n",
                "plt.figure(figsize=(8, 6))\n",
                "sns.heatmap(cm, annot=True, fmt=\"d\", cmap=\"Blues\", xticklabels=clf_pipeline.classes_, yticklabels=clf_pipeline.classes_)\n",
                "plt.title(\"File Category Confusion Matrix\")\n",
                "plt.xlabel(\"Predicted Category\")\n",
                "plt.ylabel(\"Actual Category\")\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "--- \n",
                "## Part 2: Suspicious Upload Anomaly Detection Model (Random Forest)\n",
                "\n",
                "### 2.1 Load Behavioral Metadata Dataset"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "susp_train_path = dataset_dir / \"suspicious_upload_train_v2.csv\"\n",
                "susp_test_path = dataset_dir / \"suspicious_upload_test_v2.csv\"\n",
                "\n",
                "if not susp_train_path.exists():\n",
                "    susp_train_path = dataset_dir / \"suspicious_upload_dataset_v2.csv\"\n",
                "\n",
                "df_susp_train = pd.read_csv(susp_train_path)\n",
                "df_susp_test = pd.read_csv(susp_test_path) if susp_test_path.exists() else None\n",
                "\n",
                "print(f\"Suspicious Upload Training shape: {df_susp_train.shape}\")\n",
                "df_susp_train.head()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2.2 Preprocessing & Random Forest Classifier Training"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "susp_target = \"label\" if \"label\" in df_susp_train.columns else \"is_suspicious\"\n",
                "susp_drop = [c for c in [\"upload_id\", \"filename\", \"user_id\", \"upload_timestamp\", susp_target] if c in df_susp_train.columns]\n",
                "\n",
                "X_susp_train = df_susp_train.drop(columns=susp_drop)\n",
                "y_susp_train = df_susp_train[susp_target]\n",
                "\n",
                "if df_susp_test is not None:\n",
                "    X_susp_test = df_susp_test.drop(columns=susp_drop)\n",
                "    y_susp_test = df_susp_test[susp_target]\n",
                "else:\n",
                "    X_susp_train, X_susp_test, y_susp_train, y_susp_test = train_test_split(X_susp_train, y_susp_train, test_size=0.2, random_state=42, stratify=y_susp_train)\n",
                "\n",
                "susp_num_features = X_susp_train.select_dtypes(include=[\"int64\", \"float64\"]).columns.tolist()\n",
                "susp_cat_features = X_susp_train.select_dtypes(include=[\"object\"]).columns.tolist()\n",
                "\n",
                "susp_preprocessor = ColumnTransformer(transformers=[\n",
                "    (\"num\", Pipeline(steps=[(\"imputer\", SimpleImputer(strategy=\"median\")), (\"scaler\", StandardScaler())]), susp_num_features),\n",
                "    (\"cat\", Pipeline(steps=[(\"imputer\", SimpleImputer(strategy=\"constant\", fill_value=\"unknown\")), (\"onehot\", OneHotEncoder(handle_unknown=\"ignore\", sparse_output=False))]), susp_cat_features)\n",
                "])\n",
                "\n",
                "susp_pipeline = Pipeline(steps=[\n",
                "    (\"preprocessor\", susp_preprocessor),\n",
                "    (\"classifier\", RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1))\n",
                "])\n",
                "\n",
                "susp_pipeline.fit(X_susp_train, y_susp_train)\n",
                "y_susp_pred = susp_pipeline.predict(X_susp_test)\n",
                "\n",
                "susp_acc = accuracy_score(y_susp_test, y_susp_pred)\n",
                "print(f\"Suspicious Upload Detection Accuracy: {susp_acc * 100:.2f}%\")\n",
                "print(\"\\nClassification Report:\")\n",
                "print(classification_report(y_susp_test, y_susp_pred))"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "### 2.3 Confusion Matrix Visualization"
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "susp_cm = confusion_matrix(y_susp_test, y_susp_pred)\n",
                "plt.figure(figsize=(6, 5))\n",
                "sns.heatmap(susp_cm, annot=True, fmt=\"d\", cmap=\"Reds\", xticklabels=[\"Normal (0)\", \"Suspicious (1)\"], yticklabels=[\"Normal (0)\", \"Suspicious (1)\"])\n",
                "plt.title(\"Suspicious Upload Anomaly Confusion Matrix\")\n",
                "plt.xlabel(\"Predicted\")\n",
                "plt.ylabel(\"Actual\")\n",
                "plt.tight_layout()\n",
                "plt.show()"
            ]
        },
        {
            "cell_type": "markdown",
            "metadata": {},
            "source": [
                "--- \n",
                "## Part 3: Model Serialization & Export\n",
                "\n",
                "Save trained Random Forest pipelines using `joblib` for backend inference."
            ]
        },
        {
            "cell_type": "code",
            "execution_count": None,
            "metadata": {},
            "outputs": [],
            "source": [
                "models_dir = Path(\"models\")\n",
                "models_dir.mkdir(exist_ok=True)\n",
                "\n",
                "joblib.dump(clf_pipeline, models_dir / \"file_classifier_random_forest.joblib\")\n",
                "joblib.dump(susp_pipeline, models_dir / \"suspicious_upload_random_forest_v2.joblib\")\n",
                "\n",
                "print(\"Both Random Forest models successfully serialized to models/\")"
            ]
        }
    ]

    notebook_json = {
        "cells": cells,
        "metadata": {
            "language_info": {
                "name": "python",
                "version": "3.11.0"
            },
            "kernelspec": {
                "display_name": "Python 3",
                "language": "python",
                "name": "python3"
            }
        },
        "nbformat": 4,
        "nbformat_minor": 5
    }

    out_path = Path("ML/ML_File_Classification_and_Suspicious_Detection.ipynb")
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(notebook_json, f, indent=1, ensure_ascii=False)
    print(f"Successfully generated clean notebook at: {out_path}")

if __name__ == "__main__":
    create_notebook()
