in cd ml #!/usr/bin/env python3
"""
Metadata Extraction Script for Optimized File Classification Dataset.
Scans all 1,500 cleaned dataset files across Document, Image, Video, Audio, Code
and writes ML/dataset/file_classification_metadata.csv.
"""

import os
import sys
import csv
import shutil
import mimetypes
import argparse
import subprocess
import wave
from pathlib import Path

# Optional metadata libraries
try:
    import cv2
except ImportError:
    cv2 = None

try:
    import imageio_ffmpeg
except ImportError:
    imageio_ffmpeg = None

try:
    import pypdf
except ImportError:
    pypdf = None


def find_ffmpeg_executable():
    """Find FFmpeg executable if available."""
    ffmpeg_path = shutil.which("ffmpeg")
    if ffmpeg_path:
        return ffmpeg_path
    if imageio_ffmpeg is not None:
        try:
            return imageio_ffmpeg.get_ffmpeg_exe()
        except Exception:
            pass
    return None


def get_pdf_page_count(filepath):
    """Extract page count for PDF files."""
    if pypdf is not None:
        try:
            reader = pypdf.PdfReader(str(filepath))
            return len(reader.pages)
        except Exception:
            pass

    # Fallback byte pattern search for /Count or /Type /Page
    try:
        with open(filepath, "rb") as f:
            content = f.read(500000)  # read header/trailer
            # crude check for page objects
            count = content.count(b"/Type /Page")
            return max(count, 1)
    except Exception:
        return 1


def get_audio_info(filepath, ffmpeg_exe):
    """Extract audio duration, sample rate, channels, codec."""
    info = {"duration_seconds": 0.0, "sample_rate": 0, "channels": 0, "codec": "pcm"}

    # Method 1: Python standard wave module
    if filepath.suffix.lower() == ".wav":
        try:
            with wave.open(str(filepath), "rb") as wf:
                channels = wf.getnchannels()
                rate = wf.getframerate()
                frames = wf.getnframes()
                info["channels"] = channels
                info["sample_rate"] = rate
                info["duration_seconds"] = round(frames / float(rate), 2) if rate > 0 else 0.0
                info["codec"] = "pcm_s16le"
                return info
        except Exception:
            pass

    # Method 2: FFmpeg probe
    if ffmpeg_exe:
        try:
            cmd = [ffmpeg_exe, "-i", str(filepath)]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    dur_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = dur_str.split(":")
                    info["duration_seconds"] = round(float(h) * 3600 + float(m) * 60 + float(s), 2)
                if "Audio:" in line:
                    parts = line.split("Audio:")[1].split(",")
                    if len(parts) > 0:
                        info["codec"] = parts[0].strip().split()[0].lower()
                    for p in parts:
                        ps = p.strip()
                        if "Hz" in ps:
                            try:
                                info["sample_rate"] = int(ps.replace("Hz", "").strip().split()[0])
                            except ValueError:
                                pass
                        if "stereo" in ps:
                            info["channels"] = 2
                        elif "mono" in ps:
                            info["channels"] = 1
        except Exception:
            pass

    return info


def get_video_info(filepath, ffmpeg_exe):
    """Extract video duration, resolution, fps, codec."""
    info = {"duration_seconds": 0.0, "width": 0, "height": 0, "fps": 0.0, "codec": "unknown"}

    if ffmpeg_exe:
        try:
            cmd = [ffmpeg_exe, "-i", str(filepath)]
            res = subprocess.run(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
            for line in res.stderr.splitlines():
                if "Duration:" in line:
                    dur_str = line.split("Duration:")[1].split(",")[0].strip()
                    h, m, s = dur_str.split(":")
                    info["duration_seconds"] = round(float(h) * 3600 + float(m) * 60 + float(s), 2)
                if "Stream #" in line and "Video:" in line:
                    parts = line.split("Video:")[1].split(",")
                    if len(parts) > 0:
                        info["codec"] = parts[0].strip().split()[0].lower()
                    for part in parts:
                        part_s = part.strip()
                        if "x" in part_s and any(c.isdigit() for c in part_s):
                            tokens = part_s.split()[0].split("x")
                            if len(tokens) == 2 and tokens[0].isdigit() and tokens[1].isdigit():
                                info["width"] = int(tokens[0])
                                info["height"] = int(tokens[1])
                        if "fps" in part_s:
                            fps_val = part_s.replace("fps", "").strip()
                            try:
                                info["fps"] = round(float(fps_val), 2)
                            except ValueError:
                                pass
        except Exception:
            pass

    if cv2 is not None and (info["width"] == 0 or info["duration_seconds"] == 0):
        try:
            cap = cv2.VideoCapture(str(filepath))
            if cap.isOpened():
                fps = cap.get(cv2.CAP_PROP_FPS)
                frames = cap.get(cv2.CAP_PROP_FRAME_COUNT)
                info["width"] = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                info["height"] = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                info["fps"] = round(fps, 2) if fps > 0 else 0.0
                info["duration_seconds"] = round(frames / fps, 2) if fps > 0 and frames > 0 else 0.0
                cap.release()
        except Exception:
            pass

    return info


def get_image_dimensions(filepath):
    """Extract image width and height."""
    if cv2 is not None:
        try:
            img = cv2.imread(str(filepath))
            if img is not None:
                h, w, _ = img.shape
                return w, h
        except Exception:
            pass
    return 0, 0


def main():
    base_dir = Path(__file__).resolve().parent.parent
    dataset_dir = base_dir / "ml" / "dataset"
    output_csv = dataset_dir / "file_classification_metadata.csv"

    if not dataset_dir.exists():
        print(f"Error: Dataset directory '{dataset_dir}' does not exist.")
        sys.exit(1)

    ffmpeg_exe = find_ffmpeg_executable()

    fieldnames = [
        "filename",
        "category",
        "extension",
        "mime_type",
        "file_size_kb",
        "file_size_mb",
        "duration_seconds",
        "width",
        "height",
        "fps",
        "codec",
        "sample_rate",
        "channels",
        "page_count"
    ]

    # Category Mapping Strategy
    # PDF, DOC, DOCX -> Document
    # images/Image -> Image
    # Video -> Video
    # audio/Audio -> Audio
    # code/Code -> Code
    category_map = {
        "pdf": "Document", "doc": "Document", "docx": "Document",
        "pdf": "Document", "doc": "Document", "docx": "Document",
        "image": "Image", "images": "Image",
        "video": "Video",
        "audio": "Audio",
        "code": "Code"
    }

    rows = []
    all_files = sorted([f for f in dataset_dir.rglob("*") if f.is_file() and f.name != "file_classification_metadata.csv" and f.name != "video_metadata.csv"])

    print(f"Scanning '{dataset_dir}' for metadata extraction...")
    print(f"Found {len(all_files)} dataset files.")

    for fpath in all_files:
        rel_parts = fpath.relative_to(dataset_dir).parts
        top_folder = rel_parts[0].lower()

        # Determine Category
        category = category_map.get(top_folder, "Unknown")
        ext = fpath.suffix.lstrip(".").lower()

        # File Size
        size_bytes = fpath.stat().st_size
        size_kb = round(size_bytes / 1024, 2)
        size_mb = round(size_bytes / (1024 * 1024), 2)

        # MIME Type
        mime_type, _ = mimetypes.guess_type(str(fpath))
        if not mime_type:
            mime_defaults = {
                "py": "text/x-python", "java": "text/x-java-source", "js": "application/javascript",
                "c": "text/x-c", "cpp": "text/x-c++", "rs": "text/x-rust", "rb": "text/x-ruby",
                "doc": "application/msword", "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                "wav": "audio/wav", "mp4": "video/mp4"
            }
            mime_type = mime_defaults.get(ext, "application/octet-stream")

        # Technical Metadata Defaults
        duration = 0.0
        width = 0
        height = 0
        fps = 0.0
        codec = ""
        sample_rate = 0
        channels = 0
        page_count = 0

        # Technical Extraction based on Category
        if category == "Video":
            vinfo = get_video_info(fpath, ffmpeg_exe)
            duration = vinfo["duration_seconds"]
            width = vinfo["width"]
            height = vinfo["height"]
            fps = vinfo["fps"]
            codec = vinfo["codec"]

        elif category == "Audio":
            ainfo = get_audio_info(fpath, ffmpeg_exe)
            duration = ainfo["duration_seconds"]
            sample_rate = ainfo["sample_rate"]
            channels = ainfo["channels"]
            codec = ainfo["codec"]

        elif category == "Image":
            w, h = get_image_dimensions(fpath)
            width = w
            height = h

        elif category == "Document":
            if ext == "pdf":
                page_count = get_pdf_page_count(fpath)
            else:
                page_count = 1  # Standard document estimate

        row = {
            "filename": fpath.name,
            "category": category,
            "extension": ext,
            "mime_type": mime_type,
            "file_size_kb": size_kb,
            "file_size_mb": size_mb,
            "duration_seconds": duration,
            "width": width,
            "height": height,
            "fps": fps,
            "codec": codec,
            "sample_rate": sample_rate,
            "channels": channels,
            "page_count": page_count
        }
        rows.append(row)

    # Write CSV
    with open(output_csv, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nMetadata extraction completed.")
    print(f"Extracted metadata for {len(rows)} files.")
    print(f"Saved to: {output_csv}")


if __name__ == "__main__":
    main()
