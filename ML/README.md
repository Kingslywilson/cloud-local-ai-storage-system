# Machine Learning Architecture Plan — Suspicious File Detection

This directory is reserved for the upcoming **Random Forest Machine Learning Module**.

---

## Planned Architecture & Data Flow

```text
User File Upload
        │
        ▼
Extract File Metadata & Features
(File size, extension ratio, entropy, MIME consistency, header bytes)
        │
        ▼
Random Forest Classifier (ML Model)
        │
        ├──► Normal File ────────┐
        │                       ▼
        └──► Suspicious File ──► Flag Security Alert / Admin Review
                                │
                                ▼
                       Generative AI Analysis
                       (Gemini 3.6 Flash)
                                │
                                ▼
                       MySQL Database Storage
```

---

## Planned Model Specifications

- **Algorithm**: Random Forest Classifier (`sklearn.ensemble.RandomForestClassifier`)
- **Key Features**:
  - `file_size_bytes`: Raw byte size of file
  - `entropy_score`: File byte entropy
  - `extension_mismatch`: Binary flag (1 if extension does not match MIME header, 0 otherwise)
  - `is_executable`: Binary flag for `.exe`, `.dll`, `.bat`, `.sh`, `.vbs`, `.ps1`
  - `suspicious_keyword_density`: Density of suspicious script tags in content
- **Target Output**: `0 = Normal`, `1 = Suspicious / High Risk`

*Note: The Random Forest model implementation, dataset training scripts, joblib model serialization, and prediction APIs will be added in the next project phase as requested.*
