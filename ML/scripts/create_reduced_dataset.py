#!/usr/bin/env python3
"""
Create Reduced File Classification Dataset.

Reduces ONLY the Code class in ml/dataset/file_classification_dataset.csv to 499 samples,
leaving Document (499), Audio (250), Image (145), and Video (99) unchanged.
Total reduced dataset size: 1,492 records.

Generates:
  - ml/dataset/file_classification_reduced.csv
  - ml/dataset/train.csv
  - ml/dataset/test.csv
  - ml/dataset/reduced_dataset_summary.txt
"""

import os
from pathlib import Path
import pandas as pd
from sklearn.model_selection import train_test_split


def main():
    # Define file paths
    base_dir = Path(__file__).resolve().parent.parent
    master_csv_path = base_dir / "dataset" / "file_classification_dataset.csv"
    reduced_csv_path = base_dir / "dataset" / "file_classification_reduced.csv"
    train_csv_path = base_dir / "dataset" / "train.csv"
    test_csv_path = base_dir / "dataset" / "test.csv"
    summary_path = base_dir / "dataset" / "reduced_dataset_summary.txt"

    # Step 1: Load master dataset and record master state
    if not master_csv_path.exists():
        raise FileNotFoundError(f"Master dataset not found at {master_csv_path}")

    master_size_bytes_before = master_csv_path.stat().st_size
    df_master = pd.read_csv(master_csv_path, low_memory=False)
    original_size = len(df_master)

    # Step 2: Verify original class distribution
    class_counts_orig = df_master["category"].value_counts().to_dict()
    print(f"Original dataset size: {original_size}")
    print("Original class distribution:")
    for cat, count in class_counts_orig.items():
        print(f"  {cat}: {count}")

    # Step 3: Keep all non-Code records
    df_non_code = df_master[df_master["category"] != "Code"].copy()

    # Step 4: Randomly sample exactly 499 Code records with random_state = 42
    df_code = df_master[df_master["category"] == "Code"].sample(n=499, random_state=42).copy()

    # Step 5: Combine records
    df_reduced = pd.concat([df_non_code, df_code], ignore_index=True)

    # Step 6: Shuffle final dataset using random_state = 42
    df_reduced = df_reduced.sample(frac=1.0, random_state=42).reset_index(drop=True)
    reduced_size = len(df_reduced)

    # Step 7: Save file_classification_reduced.csv
    df_reduced.to_csv(reduced_csv_path, index=False)

    # Step 8: Create stratified train.csv (80%) and test.csv (20%) using random_state = 42
    df_train, df_test = train_test_split(
        df_reduced,
        test_size=0.2,
        random_state=42,
        stratify=df_reduced["category"]
    )

    df_train.to_csv(train_csv_path, index=False)
    df_test.to_csv(test_csv_path, index=False)

    # Step 9 & 10: Validation checks
    # Check duplicate rows
    duplicate_rows = df_reduced.duplicated().sum()
    # Check duplicate file paths (relative_path)
    duplicate_paths = df_reduced["relative_path"].duplicated().sum()
    # Check train/test overlap
    train_paths = set(df_train["relative_path"])
    test_paths = set(df_test["relative_path"])
    overlap_paths = len(train_paths.intersection(test_paths))
    # Missing categories
    missing_categories = df_reduced["category"].isna().sum()
    # Unique categories
    unique_categories = set(df_reduced["category"])

    assert duplicate_rows == 0, f"Found {duplicate_rows} duplicate rows in reduced dataset!"
    assert duplicate_paths == 0, f"Found {duplicate_paths} duplicate file paths!"
    assert overlap_paths == 0, f"Found {overlap_paths} overlapping file paths between train and test!"
    assert missing_categories == 0, f"Found {missing_categories} missing category values!"
    expected_classes = {"Code", "Document", "Audio", "Image", "Video"}
    assert unique_categories == expected_classes, f"Unexpected categories: {unique_categories}"

    # Verify master dataset was not modified
    master_size_bytes_after = master_csv_path.stat().st_size
    master_modified = "YES" if master_size_bytes_before != master_size_bytes_after else "NO"

    # Step 11: Create reduced_dataset_summary.txt
    summary_content = f"""Original dataset size: {original_size}
Reduced dataset size: {reduced_size}

Class distribution:
Code: {sum(df_reduced['category'] == 'Code')}
Document: {sum(df_reduced['category'] == 'Document')}
Audio: {sum(df_reduced['category'] == 'Audio')}
Image: {sum(df_reduced['category'] == 'Image')}
Video: {sum(df_reduced['category'] == 'Video')}

Random seed: 42
Train/test split: 80/20

Original master dataset modified: {master_modified}
"""
    with open(summary_path, "w", encoding="utf-8") as f:
        f.write(summary_content)

    # Final Required Print Output
    print("\nREDUCED DATASET CREATED SUCCESSFULLY\n")
    print(f"Original:\n{original_size:,}\n")
    print(f"New:\n{reduced_size:,}\n")
    print(f"Code:\n{sum(df_reduced['category'] == 'Code')}\n")
    print(f"Document:\n{sum(df_reduced['category'] == 'Document')}\n")
    print(f"Audio:\n{sum(df_reduced['category'] == 'Audio')}\n")
    print(f"Image:\n{sum(df_reduced['category'] == 'Image')}\n")
    print(f"Video:\n{sum(df_reduced['category'] == 'Video')}\n")
    print(f"Train samples:\n{len(df_train):,}\n")
    print(f"Test samples:\n{len(df_test):,}\n")
    print(f"Train/Test overlap:\n{overlap_paths}\n")
    print(f"Master dataset modified:\n{master_modified}")


if __name__ == "__main__":
    main()
