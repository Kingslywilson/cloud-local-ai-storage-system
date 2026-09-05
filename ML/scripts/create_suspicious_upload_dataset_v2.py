#!/usr/bin/env python3
"""
Suspicious Upload Detection Dataset Generator V2.
Generates a realistic synthetic behavioral dataset V2 for ML Model 2 with
multi-dimensional feature overlap, continuous statistical noise, and realistic user/threat profiles.

Features:
  - file_size_mb (float)
  - file_extension (categorical)
  - upload_frequency (float, uploads/day)
  - uploads_last_hour (int)
  - uploads_last_24h (int)
  - user_file_count (int)
  - access_count (int)
  - unique_ip_count (int)
  - account_age_days (int)

Target:
  - label ("Normal" or "Suspicious")

Outputs:
  - ml/dataset/suspicious_upload_dataset_v2.csv
  - ml/dataset/suspicious_upload_train_v2.csv
  - ml/dataset/suspicious_upload_test_v2.csv
  - ml/dataset/suspicious_upload_dataset_v2_summary.txt
"""

import os
from pathlib import Path
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split


def generate_dataset_v2(num_samples=3000, random_state=42):
    np.random.seed(random_state)

    common_extensions = ["pdf", "docx", "png", "jpg", "mp4", "py", "zip", "wav", "txt", "xlsx", "js", "sh", "json", "csv"]
    risky_extensions = ["exe", "bat", "vbs", "dll", "iso", "apk", "bin", "scr"]

    records = []

    n_suspicious = int(num_samples * 0.15)  # 450 records
    n_normal = num_samples - n_suspicious   # 2,550 records

    # -------------------------------------------------------------------------
    # GENERATE NORMAL RECORDS (2,550 samples across 4 user personas)
    # -------------------------------------------------------------------------
    for i in range(n_normal):
        persona = np.random.choice(["casual", "power", "media", "new_user"], p=[0.50, 0.25, 0.10, 0.15])

        if persona == "casual":
            account_age_days = int(np.random.gamma(shape=4.0, scale=40.0)) + 15
            user_file_count = int(np.random.gamma(shape=2.0, scale=40.0)) + 5
            uploads_last_hour = int(np.random.poisson(lam=0.8))
            uploads_last_24h = uploads_last_hour + int(np.random.poisson(lam=5.0))
            upload_frequency = round(float(np.random.uniform(0.1, 6.0) + np.random.normal(0, 0.5)), 2)
            upload_frequency = max(0.1, upload_frequency)
            access_count = int(np.random.poisson(lam=4.0)) + 1
            unique_ip_count = int(np.random.choice([1, 2, 3], p=[0.80, 0.16, 0.04]))
            file_size_mb = round(float(np.random.exponential(scale=4.0)) + 0.05, 2)
            ext = np.random.choice(["pdf", "docx", "png", "jpg", "txt", "xlsx"], p=[0.25, 0.20, 0.20, 0.20, 0.10, 0.05])

        elif persona == "power":
            # Power user / dev: high upload frequency, multiple IPs, dev scripts, burst uploads
            account_age_days = int(np.random.gamma(shape=5.0, scale=50.0)) + 30
            user_file_count = int(np.random.gamma(shape=3.0, scale=150.0)) + 50
            uploads_last_hour = int(np.random.negative_binomial(n=3, p=0.2))  # can reach 15-30
            uploads_last_24h = uploads_last_hour + int(np.random.negative_binomial(n=5, p=0.15))
            upload_frequency = round(float(np.random.uniform(5.0, 35.0) + np.random.normal(0, 2.0)), 2)
            upload_frequency = max(1.0, upload_frequency)
            access_count = int(np.random.poisson(lam=18.0)) + 5
            unique_ip_count = int(np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.35, 0.15, 0.07, 0.03]))
            file_size_mb = round(float(np.random.exponential(scale=12.0)) + 0.1, 2)
            ext = np.random.choice(["py", "js", "sh", "zip", "json", "csv", "pdf", "png", "txt"],
                                    p=[0.25, 0.15, 0.10, 0.15, 0.10, 0.05, 0.10, 0.05, 0.05])

        elif persona == "media":
            # Media creator: large file sizes, moderate upload rates
            account_age_days = int(np.random.gamma(shape=4.0, scale=45.0)) + 20
            user_file_count = int(np.random.gamma(shape=2.5, scale=80.0)) + 20
            uploads_last_hour = int(np.random.poisson(lam=2.5))
            uploads_last_24h = uploads_last_hour + int(np.random.poisson(lam=12.0))
            upload_frequency = round(float(np.random.uniform(2.0, 18.0) + np.random.normal(0, 1.0)), 2)
            upload_frequency = max(0.5, upload_frequency)
            access_count = int(np.random.poisson(lam=10.0)) + 2
            unique_ip_count = int(np.random.choice([1, 2, 3, 4], p=[0.60, 0.28, 0.09, 0.03]))
            file_size_mb = round(float(np.random.uniform(30.0, 420.0) + np.random.normal(0, 15.0)), 2)
            file_size_mb = max(1.0, file_size_mb)
            ext = np.random.choice(["mp4", "wav", "zip", "png", "jpg", "iso"], p=[0.40, 0.20, 0.15, 0.12, 0.10, 0.03])

        else:  # new_user
            # New legitimate user: fresh account, moderate activity
            account_age_days = int(np.random.uniform(0, 10))
            user_file_count = int(np.random.poisson(lam=4.0)) + 1
            uploads_last_hour = int(np.random.poisson(lam=1.5))
            uploads_last_24h = uploads_last_hour + int(np.random.poisson(lam=6.0))
            upload_frequency = round(float(np.random.uniform(1.0, 12.0) + np.random.normal(0, 1.0)), 2)
            upload_frequency = max(0.2, upload_frequency)
            access_count = int(np.random.poisson(lam=6.0)) + 1
            unique_ip_count = int(np.random.choice([1, 2, 3], p=[0.70, 0.23, 0.07]))
            file_size_mb = round(float(np.random.exponential(scale=6.0)) + 0.1, 2)
            ext = np.random.choice(["pdf", "docx", "jpg", "png", "py", "zip"], p=[0.30, 0.25, 0.20, 0.15, 0.05, 0.05])

        records.append({
            "file_size_mb": file_size_mb,
            "file_extension": ext,
            "upload_frequency": upload_frequency,
            "uploads_last_hour": uploads_last_hour,
            "uploads_last_24h": uploads_last_24h,
            "user_file_count": user_file_count,
            "access_count": access_count,
            "unique_ip_count": unique_ip_count,
            "account_age_days": account_age_days,
            "label": "Normal"
        })

    # -------------------------------------------------------------------------
    # GENERATE SUSPICIOUS RECORDS (450 samples across 4 threat scenarios)
    # -------------------------------------------------------------------------
    for i in range(n_suspicious):
        scenario = i % 4

        if scenario == 0:
            # Scenario A: Bot burst / spam (overlaps with power users)
            account_age_days = int(np.random.uniform(1, 60) + np.random.normal(0, 5))
            account_age_days = max(0, account_age_days)
            user_file_count = int(np.random.gamma(shape=2.0, scale=40.0)) + 10
            uploads_last_hour = int(np.random.uniform(12, 65) + np.random.normal(0, 3))
            uploads_last_hour = max(5, uploads_last_hour)
            uploads_last_24h = uploads_last_hour + int(np.random.uniform(25, 180))
            upload_frequency = round(float(np.random.uniform(18.0, 85.0) + np.random.normal(0, 4.0)), 2)
            upload_frequency = max(10.0, upload_frequency)
            access_count = int(np.random.uniform(20, 140))
            unique_ip_count = int(np.random.choice([2, 3, 4, 5, 6, 7, 8, 9, 10], p=[0.05, 0.10, 0.20, 0.25, 0.15, 0.10, 0.08, 0.04, 0.03]))
            file_size_mb = round(float(np.random.uniform(0.1, 35.0) + np.random.normal(0, 2.0)), 2)
            file_size_mb = max(0.05, file_size_mb)
            ext = np.random.choice(common_extensions + ["exe", "bat", "js", "bin"],
                                    p=[0.15, 0.10, 0.10, 0.10, 0.05, 0.10, 0.15, 0.05, 0.05, 0.03, 0.02, 0.02, 0.03, 0.02, 0.01, 0.01, 0.005, 0.005])

        elif scenario == 1:
            # Scenario B: Stealthy Account Takeover / ATO (compromised established accounts)
            account_age_days = int(np.random.uniform(60, 850) + np.random.normal(0, 30))  # Established accounts!
            account_age_days = max(15, account_age_days)
            user_file_count = int(np.random.gamma(shape=3.0, scale=100.0)) + 30
            uploads_last_hour = int(np.random.uniform(3, 18) + np.random.normal(0, 1.5))   # Stealthy / low rate!
            uploads_last_hour = max(1, uploads_last_hour)
            uploads_last_24h = uploads_last_hour + int(np.random.uniform(10, 55))
            upload_frequency = round(float(np.random.uniform(8.0, 38.0) + np.random.normal(0, 2.0)), 2)
            upload_frequency = max(3.0, upload_frequency)
            access_count = int(np.random.uniform(12, 55))
            unique_ip_count = int(np.random.choice([3, 4, 5, 6, 7, 8], p=[0.20, 0.30, 0.25, 0.13, 0.08, 0.04]))
            file_size_mb = round(float(np.random.uniform(0.5, 65.0)), 2)
            ext = np.random.choice(["pdf", "docx", "zip", "exe", "vbs", "py", "sh", "dll", "png", "txt"],
                                    p=[0.20, 0.15, 0.20, 0.10, 0.05, 0.10, 0.05, 0.05, 0.05, 0.05])

        elif scenario == 2:
            # Scenario C: High-risk payload upload attempt (moderate activity, disguised)
            account_age_days = int(np.random.uniform(1, 120))
            user_file_count = int(np.random.gamma(shape=1.8, scale=30.0)) + 1
            uploads_last_hour = int(np.random.poisson(lam=3.0)) + 1                          # Low / moderate!
            uploads_last_24h = uploads_last_hour + int(np.random.poisson(lam=10.0))
            upload_frequency = round(float(np.random.uniform(2.0, 22.0) + np.random.normal(0, 1.0)), 2)
            upload_frequency = max(0.5, upload_frequency)
            access_count = int(np.random.poisson(lam=8.0)) + 2
            unique_ip_count = int(np.random.choice([1, 2, 3, 4, 5], p=[0.40, 0.30, 0.18, 0.08, 0.04]))
            file_size_mb = round(float(np.random.uniform(0.2, 55.0)), 2)
            ext = np.random.choice(risky_extensions + ["zip", "pdf", "py", "sh"],
                                    p=[0.20, 0.15, 0.12, 0.10, 0.08, 0.08, 0.07, 0.05, 0.05, 0.05, 0.03, 0.02])

        else:
            # Scenario D: Data exfiltration dump (overlaps with media creators)
            account_age_days = int(np.random.uniform(10, 350))
            user_file_count = int(np.random.gamma(shape=2.5, scale=60.0)) + 10
            uploads_last_hour = int(np.random.uniform(4, 24))
            uploads_last_24h = uploads_last_hour + int(np.random.uniform(12, 60))
            upload_frequency = round(float(np.random.uniform(10.0, 45.0) + np.random.normal(0, 2.0)), 2)
            upload_frequency = max(4.0, upload_frequency)
            access_count = int(np.random.uniform(18, 85))
            unique_ip_count = int(np.random.choice([2, 3, 4, 5, 6, 7], p=[0.15, 0.30, 0.28, 0.15, 0.08, 0.04]))
            file_size_mb = round(float(np.random.uniform(70.0, 460.0) + np.random.normal(0, 15.0)), 2)
            file_size_mb = max(20.0, file_size_mb)
            ext = np.random.choice(["zip", "iso", "mp4", "bin", "pdf", "docx", "png", "exe"],
                                    p=[0.35, 0.15, 0.15, 0.10, 0.08, 0.07, 0.05, 0.05])

        records.append({
            "file_size_mb": file_size_mb,
            "file_extension": ext,
            "upload_frequency": upload_frequency,
            "uploads_last_hour": uploads_last_hour,
            "uploads_last_24h": uploads_last_24h,
            "user_file_count": user_file_count,
            "access_count": access_count,
            "unique_ip_count": unique_ip_count,
            "account_age_days": account_age_days,
            "label": "Suspicious"
        })

    df = pd.DataFrame(records)
    # Shuffle dataset
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df


def main():
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / "dataset"
    dataset_dir.mkdir(parents=True, exist_ok=True)

    master_csv_v2 = dataset_dir / "suspicious_upload_dataset_v2.csv"
    train_csv_v2 = dataset_dir / "suspicious_upload_train_v2.csv"
    test_csv_v2 = dataset_dir / "suspicious_upload_test_v2.csv"
    summary_txt_v2 = dataset_dir / "suspicious_upload_dataset_v2_summary.txt"

    print("==================================================")
    print("GENERATING SUSPICIOUS UPLOAD DETECTION DATASET V2")
    print("==================================================")

    df = generate_dataset_v2(num_samples=3000, random_state=42)

    # Validation: No duplicate records
    dup_count = df.duplicated().sum()
    assert dup_count == 0, f"Found {dup_count} duplicate records!"

    # Save Master V2 CSV
    df.to_csv(master_csv_v2, index=False)
    print(f"Saved master V2 dataset ({len(df)} records) -> {master_csv_v2}")

    # Stratified 80/20 train/test split
    df_train, df_test = train_test_split(
        df,
        test_size=0.2,
        random_state=42,
        stratify=df["label"]
    )

    # Validation: Train/Test overlap check
    overlap = pd.merge(df_train, df_test, how="inner")
    assert len(overlap) == 0, f"Found {len(overlap)} overlapping records between train and test V2!"

    df_train.to_csv(train_csv_v2, index=False)
    df_test.to_csv(test_csv_v2, index=False)
    print(f"Saved train V2 dataset ({len(df_train)} records) -> {train_csv_v2}")
    print(f"Saved test V2 dataset  ({len(df_test)} records) -> {test_csv_v2}")

    # Class counts
    total_counts = df["label"].value_counts().to_dict()
    train_counts = df_train["label"].value_counts().to_dict()
    test_counts = df_test["label"].value_counts().to_dict()

    # Create Summary Document V2
    summary_content = f"""==================================================
SUSPICIOUS UPLOAD DETECTION DATASET V2 SUMMARY
==================================================

DISCLAIMER:
This dataset is a SYNTHETIC/SIMULATED behavioral dataset V2 designed to model
realistic multi-dimensional user behaviors and security threat scenarios.
Feature distributions between Normal and Suspicious records intentionally contain
realistic continuous overlap to model production environment complexity.

Total Dataset Size: {len(df)}
Training Set Size : {len(df_train)} (80%)
Testing Set Size  : {len(df_test)} (20%)

Overall Class Distribution:
  Normal    : {total_counts.get('Normal', 0)}
  Suspicious: {total_counts.get('Suspicious', 0)}

Training Set Distribution:
  Normal    : {train_counts.get('Normal', 0)}
  Suspicious: {train_counts.get('Suspicious', 0)}

Testing Set Distribution:
  Normal    : {test_counts.get('Normal', 0)}
  Suspicious: {test_counts.get('Suspicious', 0)}

Behavioral Features (9):
  - file_size_mb
  - file_extension
  - upload_frequency
  - uploads_last_hour
  - uploads_last_24h
  - user_file_count
  - access_count
  - unique_ip_count
  - account_age_days

Target Column:
  label ("Normal" / "Suspicious")

Random Seed: 42
Train/Test Split: 80/20 Stratified
"""
    with open(summary_txt_v2, "w", encoding="utf-8") as f:
        f.write(summary_content)

    print(f"Saved dataset summary V2 -> {summary_txt_v2}\n")

    # -------------------------------------------------------------------------
    # PRINT REQUIRED STATISTICAL REPORT
    # -------------------------------------------------------------------------
    print("==================================================")
    print("DATASET V2 STATISTICAL REPORT")
    print("==================================================")
    print(f"Total records   : {len(df)}")
    print(f"Normal count    : {total_counts.get('Normal', 0)}")
    print(f"Suspicious count: {total_counts.get('Suspicious', 0)}")
    print(f"Train count     : {len(df_train)}")
    print(f"Test count      : {len(df_test)}")

    num_cols = [
        "file_size_mb", "upload_frequency", "uploads_last_hour",
        "uploads_last_24h", "user_file_count", "access_count",
        "unique_ip_count", "account_age_days"
    ]

    print("\n--------------------------------------------------")
    print("NUMERICAL FEATURES STATISTICAL SUMMARY BY CLASS")
    print("--------------------------------------------------")

    for col in num_cols:
        print(f"\nFeature: {col}")
        for cls in ["Normal", "Suspicious"]:
            sub = df[df["label"] == cls][col]
            print(f"  Class [{cls:10s}] -> Min: {sub.min():8.2f} | Max: {sub.max():8.2f} | Mean: {sub.mean():8.2f} | Median: {sub.median():8.2f}")

    print("\n--------------------------------------------------")
    print("FILE EXTENSION DISTRIBUTION BY CLASS")
    print("--------------------------------------------------")
    ext_df = pd.crosstab(df["file_extension"], df["label"])
    print(ext_df.to_string())


if __name__ == "__main__":
    main()
