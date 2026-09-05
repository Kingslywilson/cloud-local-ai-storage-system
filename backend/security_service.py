import os
import re
import json
from pathlib import Path
from typing import Dict, Any, List, Tuple
from sqlalchemy.orm import Session

from ml_service import detect_suspicious_upload, predict_file_classification


# Blacklisted dangerous executable/script extensions
DANGEROUS_EXTENSIONS = {
    "exe", "bat", "cmd", "vbs", "vbe", "js", "jse", "wsf", "wsh",
    "ps1", "ps1xml", "ps2", "ps2xml", "psc1", "psc2", "msh", "msh1",
    "msh2", "mshxml", "msh1xml", "msh2xml", "scf", "lnk", "inf",
    "reg", "dll", "scr", "cpl", "com", "iso", "img", "hta", "jar"
}

# Known Magic Byte Signatures
MAGIC_BYTES = {
    b"MZ": {"type": "Windows Executable/DLL", "risk": "High"},
    b"\x7fELF": {"type": "Linux ELF Binary", "risk": "High"},
    b"%PDF": {"type": "PDF Document", "risk": "Low"},
    b"\x89PNG\r\n\x1a\n": {"type": "PNG Image", "risk": "Low"},
    b"GIF87a": {"type": "GIF Image", "risk": "Low"},
    b"GIF89a": {"type": "GIF Image", "risk": "Low"},
    b"\xff\xd8\xff": {"type": "JPEG Image", "risk": "Low"},
    b"PK\x03\x04": {"type": "Zip Archive / Office Container", "risk": "Medium"},
    b"Rar!\x1a\x07": {"type": "RAR Archive", "risk": "Medium"},
    b"7z\xbc\xaf\x27\x1c": {"type": "7z Archive", "risk": "Medium"}
}

# Malicious Code Regex Signatures
MALICIOUS_PATTERNS = [
    (r"eval\s*\(\s*base64_decode", "Obfuscated Base64 PHP Payload Execution"),
    (r"exec\s*\(\s*bytes\.fromhex", "Hex Obfuscated Code Execution"),
    (r"powershell(\.exe)?\s+-[a-z\s]*nop[a-z\s]*-w\s+hidden", "PowerShell Hidden Execution Stager"),
    (r"system\s*\(\s*\$_GET|\$_POST|\$_REQUEST", "PHP Webshell Command Injection"),
    (r"passthru\s*\(\s*\$_GET|\$_POST", "PHP Webshell Passthru Execution"),
    (r"shell_exec\s*\(", "Raw Shell Command Execution Routine"),
    (r"WScript\.Shell", "Windows Script Host Command Execution"),
    (r"AutoOpen\s*\(\s*\)|Workbook_Open\s*\(\s*\)", "VBA Macro Auto-Execution Trigger"),
    (r"cmd\.exe\s+/c\s+start", "Hidden Subprocess Spawner"),
    (r"<script[\s>].*?document\.cookie", "Cross-Site Scripting Cookie Stealer")
]


# ============================================================
# LAYER 1: FILE PROPERTY & HEADER VALIDATION
# ============================================================

def validate_file_properties(
    file_path: str,
    original_name: str,
    content_type: str = None
) -> Tuple[bool, List[str], str]:
    """
    Validates file properties, double extensions, filename safety, and binary magic bytes.
    Returns: (is_suspicious: bool, risk_factors: list, detected_header_type: str)
    """
    risk_factors = []
    filename_lower = original_name.lower().strip()

    # 1. Check Double Extension Spoofing (e.g. invoice.pdf.exe, photo.jpg.vbs)
    parts = filename_lower.split(".")
    if len(parts) > 2:
        secondary_ext = parts[-2]
        final_ext = parts[-1]
        if final_ext in DANGEROUS_EXTENSIONS or secondary_ext in ["pdf", "doc", "docx", "jpg", "png"]:
            risk_factors.append(f"Double extension spoofing detected: '{original_name}' (.{secondary_ext}.{final_ext})")

    # 2. Check Blacklisted Extension
    final_ext = Path(filename_lower).suffix.lstrip(".")
    if final_ext in DANGEROUS_EXTENSIONS:
        risk_factors.append(f"Blacklisted executable/script extension detected: '.{final_ext}'")

    # 3. Magic Bytes Header Inspection
    detected_header_type = "Unknown"
    header_bytes = b""
    if os.path.exists(file_path):
        try:
            with open(file_path, "rb") as f:
                header_bytes = f.read(16)
        except Exception as e:
            print("Error reading header bytes:", e)

    # Detect header binary type
    if header_bytes.startswith(b"MZ"):
        detected_header_type = "Windows Executable/DLL (MZ)"
    elif header_bytes.startswith(b"\x7fELF"):
        detected_header_type = "Linux ELF Binary"
    elif header_bytes.startswith(b"%PDF"):
        detected_header_type = "PDF Document"
    elif header_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
        detected_header_type = "PNG Image"
    elif header_bytes.startswith(b"\xff\xd8\xff"):
        detected_header_type = "JPEG Image"
    elif header_bytes.startswith(b"GIF87a") or header_bytes.startswith(b"GIF89a"):
        detected_header_type = "GIF Image"
    elif header_bytes.startswith(b"PK\x03\x04"):
        detected_header_type = "Zip Archive / Office Container"

    # Detect Header Spoofing / MIME Mismatch
    # E.g. Filename claims to be .pdf or .png, but binary header is MZ executable
    if final_ext in ["pdf", "png", "jpg", "jpeg", "gif", "txt", "csv", "doc", "docx"]:
        if header_bytes.startswith(b"MZ") or header_bytes.startswith(b"\x7fELF"):
            risk_factors.append(
                f"Binary Header Spoofing Attack! File '.{final_ext}' contains executable binary header ({detected_header_type})"
            )

    is_suspicious = len(risk_factors) > 0
    return is_suspicious, risk_factors, detected_header_type


# ============================================================
# LAYER 3: CONTENT THREAT & SAFETY SCANNER
# ============================================================

def scan_content_threats(
    file_path: str,
    original_name: str
) -> Tuple[bool, List[str]]:
    """
    Scans readable file content for malicious code signatures, obfuscated scripts,
    webshell payloads, and macro threats.
    """
    risk_factors = []
    ext = Path(original_name).suffix.lower()

    # Only scan text-based, code, or document formats
    scannable_extensions = [
        ".txt", ".csv", ".json", ".md", ".html", ".js", ".py", ".php",
        ".sh", ".bat", ".ps1", ".sql", ".vbs", ".xml", ".sub"
    ]

    if ext not in scannable_extensions:
        return False, []

    if not os.path.exists(file_path):
        return False, []

    try:
        # Read up to first 500 KB of text content for scanning
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            content_snippet = f.read(500000)

        for pattern, threat_desc in MALICIOUS_PATTERNS:
            if re.search(pattern, content_snippet, re.IGNORECASE):
                risk_factors.append(f"Malicious Content Signature Detected: {threat_desc}")

    except Exception as e:
        print("Content threat scanning error:", e)

    is_suspicious = len(risk_factors) > 0
    return is_suspicious, risk_factors


# ============================================================
# UNIFIED PRE-STORAGE SECURITY SCANNER
# ============================================================

def perform_pre_storage_security_scan(
    file_path: str,
    original_name: str,
    content_type: str,
    file_size_bytes: int,
    user_id: int,
    db: Session
) -> Dict[str, Any]:
    """
    Executes a 3-tier pre-storage security scan:
    - Layer 1: Property & Magic Bytes Header Validation
    - Layer 2: Random Forest ML Behavioral Anomaly Detection
    - Layer 3: Malicious Content Threat Scanner

    Returns full security status dictionary. If is_suspicious == True,
    the calling endpoint MUST delete the file and cancel the upload.
    """
    all_risk_factors = []

    # --------------------------------------------------------
    # LAYER 1: PROPERTY & MAGIC BYTES VALIDATION
    # --------------------------------------------------------
    l1_suspicious, l1_risks, header_type = validate_file_properties(
        file_path=file_path,
        original_name=original_name,
        content_type=content_type
    )
    all_risk_factors.extend(l1_risks)

    # --------------------------------------------------------
    # LAYER 2: RANDOM FOREST ML BEHAVIORAL ANOMALY DETECTION
    # --------------------------------------------------------
    ml_behavior_result = detect_suspicious_upload(
        user_id=user_id,
        file_size_bytes=file_size_bytes,
        original_name=original_name,
        db=db
    )
    l2_suspicious = ml_behavior_result.get("is_suspicious", False)
    if l2_suspicious:
        ml_details = ml_behavior_result.get("details", "Anomalous upload behavior pattern")
        all_risk_factors.append(f"Random Forest ML Behavioral Anomaly: {ml_details}")

    # --------------------------------------------------------
    # LAYER 3: CONTENT THREAT & SAFETY SCANNER
    # --------------------------------------------------------
    l3_suspicious, l3_risks = scan_content_threats(
        file_path=file_path,
        original_name=original_name
    )
    all_risk_factors.extend(l3_risks)

    # --------------------------------------------------------
    # AGGREGATE SECURITY RESULT
    # --------------------------------------------------------
    is_suspicious = l1_suspicious or l2_suspicious or l3_suspicious

    if is_suspicious:
        if l1_suspicious or l3_suspicious:
            security_status = "HIGH_THREAT"
        else:
            security_status = "SUSPICIOUS"

        primary_reason = all_risk_factors[0] if all_risk_factors else "Unusual file or upload anomaly detected"
        cancellation_reason = f"Upload Canceled Due to Security Risk: {primary_reason}"
    else:
        security_status = "CLEAN"
        cancellation_reason = ""

    return {
        "is_suspicious": is_suspicious,
        "security_status": security_status,
        "cancellation_reason": cancellation_reason,
        "risk_factors": all_risk_factors,
        "header_type": header_type,
        "ml_behavior": ml_behavior_result,
        "layer_results": {
            "property_validation": "FAILED" if l1_suspicious else "PASSED",
            "ml_behavior": "ANOMALOUS" if l2_suspicious else "NORMAL",
            "content_threat": "THREAT_DETECTED" if l3_suspicious else "CLEAN"
        }
    }
