import os
import joblib
import numpy as np
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
from sqlalchemy.orm import Session

# Global model caches
_FILE_CLASSIFIER_MODEL = None
_FILE_CLASSIFIER_EXPECTED_FEATURES = None

_SUSPICIOUS_MODEL_V2 = None
_SUSPICIOUS_EXPECTED_FEATURES_V2 = None


def get_base_ml_dir() -> Path:
    """Returns absolute path to ML directory."""
    return Path(__file__).resolve().parent.parent / "ML"


def get_file_classifier_model():
    """Loads file classification Random Forest model pipeline."""
    global _FILE_CLASSIFIER_MODEL, _FILE_CLASSIFIER_EXPECTED_FEATURES
    if _FILE_CLASSIFIER_MODEL is None:
        model_path = get_base_ml_dir() / "models" / "file_classifier_random_forest.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Model file not found at {model_path}")
        
        _FILE_CLASSIFIER_MODEL = joblib.load(model_path)
        preprocessor = _FILE_CLASSIFIER_MODEL.named_steps["preprocessor"]
        _FILE_CLASSIFIER_EXPECTED_FEATURES = []
        for name, trans, cols in preprocessor.transformers_:
            _FILE_CLASSIFIER_EXPECTED_FEATURES.extend(cols)
            
    return _FILE_CLASSIFIER_MODEL, _FILE_CLASSIFIER_EXPECTED_FEATURES


def get_suspicious_upload_model():
    """Loads suspicious upload detection Random Forest V2 model pipeline."""
    global _SUSPICIOUS_MODEL_V2, _SUSPICIOUS_EXPECTED_FEATURES_V2
    if _SUSPICIOUS_MODEL_V2 is None:
        model_path = get_base_ml_dir() / "models" / "suspicious_upload_random_forest_v2.joblib"
        if not model_path.exists():
            raise FileNotFoundError(f"Suspicious model file not found at {model_path}")
            
        _SUSPICIOUS_MODEL_V2 = joblib.load(model_path)
        preprocessor = _SUSPICIOUS_MODEL_V2.named_steps["preprocessor"]
        _SUSPICIOUS_EXPECTED_FEATURES_V2 = []
        for name, trans, cols in preprocessor.transformers_:
            _SUSPICIOUS_EXPECTED_FEATURES_V2.extend(cols)
            
    return _SUSPICIOUS_MODEL_V2, _SUSPICIOUS_EXPECTED_FEATURES_V2


def predict_file_classification(
    original_name: str,
    file_type: str,
    file_size_bytes: int
) -> dict:
    """
    Predicts file category using trained Random Forest model.
    Categories: Document, Image, Video, Audio, Code Files (or Other).
    """
    try:
        pipeline, expected_features = get_file_classifier_model()
        ext = Path(original_name).suffix.lower().lstrip(".")
        if not ext:
            ext = "unknown"
            
        mime = file_type or "application/octet-stream"
        file_size_kb = round(file_size_bytes / 1024, 2)
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        file_metadata = {
            "extension": ext,
            "mime_type": mime,
            "file_size_bytes": file_size_bytes,
            "file_size_kb": file_size_kb,
            "file_size_mb": file_size_mb,
            "page_count": 1,
            "text_length": 0
        }

        df_input = pd.DataFrame([file_metadata])
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

        # Normalize category naming to specification standard
        category_map = {
            "Document": "Document (PDF, DOC)",
            "Documents": "Document (PDF, DOC)",
            "Image": "Image",
            "Images": "Image",
            "Video": "Video",
            "Videos": "Video",
            "Audio": "Audio",
            "Code": "Code Files",
            "Code Files": "Code Files"
        }
        normalized_category = category_map.get(predicted_cat, predicted_cat)

        return {
            "predicted_category": normalized_category,
            "raw_category": predicted_cat,
            "confidence": round(float(confidence), 4),
            "confidence_percentage": round(float(confidence) * 100, 1),
            "class_probabilities": class_probs,
            "status": "success"
        }
    except Exception as e:
        print("ML File Classification error:", e)
        # Fallback based on extension rule if ML model fails
        ext = Path(original_name).suffix.lower()
        if ext in [".pdf", ".doc", ".docx", ".txt", ".csv", ".json", ".md"]:
            fallback_cat = "Document (PDF, DOC)"
        elif ext in [".jpg", ".jpeg", ".png", ".webp", ".gif", ".svg"]:
            fallback_cat = "Image"
        elif ext in [".mp4", ".mov", ".avi", ".mkv", ".webm"]:
            fallback_cat = "Video"
        elif ext in [".mp3", ".wav", ".m4a", ".flac", ".aac", ".ogg"]:
            fallback_cat = "Audio"
        elif ext in [".py", ".js", ".jsx", ".java", ".c", ".cpp", ".h", ".html", ".css", ".sql"]:
            fallback_cat = "Code Files"
        else:
            fallback_cat = "Other"

        return {
            "predicted_category": fallback_cat,
            "raw_category": fallback_cat,
            "confidence": 0.85,
            "confidence_percentage": 85.0,
            "class_probabilities": {},
            "status": "fallback",
            "error": str(e)
        }


def detect_suspicious_upload(
    user_id: int,
    file_size_bytes: int,
    original_name: str,
    db: Session
) -> dict:
    """
    Evaluates upload behavior using trained Random Forest V2 Suspicious Upload Detector.
    Features: file_size_mb, upload_frequency, uploads_last_hour, uploads_last_24h,
              user_file_count, account_age_days, etc.
    """
    try:
        from models import File, User, ActivityLog
        pipeline, expected_features = get_suspicious_upload_model()

        ext = Path(original_name).suffix.lower().lstrip(".")
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)

        # Retrieve user record
        user = db.query(User).filter(User.id == user_id).first()
        now = datetime.utcnow()

        if user and user.created_at:
            account_age_days = max(1, (now - user.created_at).days)
        else:
            account_age_days = 30

        # Query user uploads
        user_file_count = db.query(File).filter(File.user_id == user_id).count()

        one_hour_ago = now - timedelta(hours=1)
        uploads_last_hour = db.query(File).filter(
            File.user_id == user_id,
            File.uploaded_at >= one_hour_ago
        ).count() + 1  # count current upload

        twenty_four_hours_ago = now - timedelta(hours=24)
        uploads_last_24h = db.query(File).filter(
            File.user_id == user_id,
            File.uploaded_at >= twenty_four_hours_ago
        ).count() + 1

        # Activity frequency (uploads/actions in last hour)
        upload_frequency = uploads_last_hour

        # Unique IP count estimate from activity logs or fallback
        unique_ip_count = 1

        # File access counts for user
        access_count = db.query(ActivityLog).filter(ActivityLog.user_id == user_id).count()

        upload_metadata = {
            "file_size_mb": file_size_mb,
            "file_extension": ext,
            "upload_frequency": upload_frequency,
            "uploads_last_hour": uploads_last_hour,
            "uploads_last_24h": uploads_last_24h,
            "user_file_count": user_file_count,
            "access_count": access_count,
            "unique_ip_count": unique_ip_count,
            "account_age_days": account_age_days
        }

        df_input = pd.DataFrame([upload_metadata])
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
        is_suspicious = bool(predicted_label == "Suspicious")

        # Determine specific reasons for user feedback if suspicious
        reasons = []
        if file_size_mb > 100:
            reasons.append(f"Unusually large upload size ({file_size_mb} MB)")
        if uploads_last_hour > 10:
            reasons.append(f"High upload burst frequency ({uploads_last_hour} files in 1 hour)")
        if account_age_days < 3 and uploads_last_24h > 15:
            reasons.append("High volume activity on new user account")
        if ext in ["exe", "bat", "sh", "vbs", "cmd", "scr", "dll"]:
            reasons.append(f"Potentially sensitive/executable file extension (.{ext})")

        reasons_text = "; ".join(reasons) if reasons else ("Unusual upload pattern detected by Random Forest model" if is_suspicious else "Normal user behavior pattern")

        return {
            "prediction": predicted_label,
            "is_suspicious": is_suspicious,
            "confidence": round(float(confidence), 4),
            "confidence_percentage": round(float(confidence) * 100, 1),
            "class_probabilities": class_probs,
            "details": reasons_text,
            "metrics": upload_metadata,
            "status": "success"
        }

    except Exception as e:
        print("ML Suspicious Upload Detection error:", e)
        # Fallback check
        file_size_mb = round(file_size_bytes / (1024 * 1024), 2)
        ext = Path(original_name).suffix.lower().lstrip(".")
        is_susp = (file_size_mb > 200 or ext in ["exe", "bat", "sh", "dll"])

        return {
            "prediction": "Suspicious" if is_susp else "Normal",
            "is_suspicious": is_susp,
            "confidence": 0.90,
            "confidence_percentage": 90.0,
            "class_probabilities": {"Normal": 0.1 if is_susp else 0.9, "Suspicious": 0.9 if is_susp else 0.1},
            "details": "Flagged by security heuristic fallback" if is_susp else "Normal upload",
            "status": "fallback",
            "error": str(e)
        }
