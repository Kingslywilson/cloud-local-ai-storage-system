import os
import json
import time
from pathlib import Path

from dotenv import load_dotenv
from google import genai
from pypdf import PdfReader
from docx import Document


# ============================================================
# CONFIGURATION
# ============================================================

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print("Gemini client initialization error:", e)
        return None

MODEL_NAME = "gemini-3.6-flash"



# ============================================================
# TEXT EXTRACTION
# ============================================================

def extract_text_from_file(file_path: str, file_type: str = None):

    extension = Path(file_path).suffix.lower()

    # --------------------------------------------------------
    # PDF
    # --------------------------------------------------------

    if extension == ".pdf":

        try:
            reader = PdfReader(file_path)

            text = ""

            for page in reader.pages:

                page_text = page.extract_text()

                if page_text:
                    text += page_text + "\n"

            return text

        except Exception as e:

            print("PDF extraction error:", e)

            return ""


    # --------------------------------------------------------
    # DOCX
    # --------------------------------------------------------

    elif extension == ".docx":

        try:
            document = Document(file_path)

            text = "\n".join(
                paragraph.text
                for paragraph in document.paragraphs
            )

            return text

        except Exception as e:

            print("DOCX extraction error:", e)

            return ""


    # --------------------------------------------------------
    # TEXT FILES
    # --------------------------------------------------------

    elif extension in [
        ".txt",
        ".csv",
        ".json",
        ".md"
    ]:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                return file.read()

        except Exception as e:

            print("Text extraction error:", e)

            return ""


    # --------------------------------------------------------
    # CODE FILES
    # --------------------------------------------------------

    elif extension in [
        ".py",
        ".js",
        ".jsx",
        ".java",
        ".c",
        ".cpp",
        ".h",
        ".html",
        ".css",
        ".sql"
    ]:

        try:

            with open(
                file_path,
                "r",
                encoding="utf-8",
                errors="ignore"
            ) as file:

                return file.read()

        except Exception as e:

            print("Code extraction error:", e)

            return ""


    return ""


# ============================================================
# COMMON JSON PARSER
# ============================================================

def parse_ai_response(result_text: str):

    result_text = result_text.strip()

    # Remove accidental markdown fences

    if result_text.startswith("```json"):

        result_text = result_text[7:]

    elif result_text.startswith("```"):

        result_text = result_text[3:]

    if result_text.endswith("```"):

        result_text = result_text[:-3]

    result_text = result_text.strip()

    try:

        result = json.loads(result_text)

    except json.JSONDecodeError:

        print("Gemini returned invalid JSON:")
        print(result_text)

        result = {
            "summary": result_text,
            "description": "",
            "tags": [],
            "insights": ""
        }

    tags = result.get("tags", [])

    # Make sure tags are always a list

    if not isinstance(tags, list):

        tags = [str(tags)]

    return {
        "summary": result.get("summary", ""),
        "description": result.get("description", ""),
        "tags": json.dumps(tags),
        "insights": result.get("insights", "")
    }


# ============================================================
# TEXT / DOCUMENT ANALYSIS
# ============================================================

def analyze_text_file(
    file_path: str,
    file_name: str,
    file_type: str = None
):

    text = extract_text_from_file(
        file_path,
        file_type
    )

    # Limit content sent to AI

    max_chars = 30000

    if len(text) > max_chars:

        text = text[:max_chars]

    if not text.strip():

        text = "No readable text content was extracted from this file."

    prompt = f"""
You are an AI file analysis assistant for a cloud storage application.

Analyze the uploaded file and return ONLY valid JSON.

File name:
{file_name}

File type:
{file_type}

File content:
{text}

Generate the following:

1. summary
A short summary of what the file contains.

2. description
A useful description explaining the purpose or nature of the file.

3. tags
Generate 5 to 8 relevant smart tags.

4. insights
Mention important information, topics, technologies,
sections, or useful observations found in the file.

Return exactly this JSON structure:

{{
    "summary": "short summary",
    "description": "file description",
    "tags": ["tag1", "tag2", "tag3"],
    "insights": "important insights from the file"
}}

Do not include markdown.
Do not include ```json.
Return JSON only.
"""

    try:
        client = get_client()
        if not client:
            return {
                "summary": "AI analysis could not be completed at this time (API key unconfigured).",
                "description": "Please set a valid GEMINI_API_KEY in environment configuration.",
                "tags": "[\"document\"]",
                "insights": "You can retry later."
            }

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=prompt
        )

        return parse_ai_response(response.text)

    except Exception as e:

        print("Gemini text analysis error:", e)

        return {
            "summary": "AI analysis could not be generated.",
            "description": "",
            "tags": "[]",
            "insights": ""
        }


# ============================================================
# IMAGE ANALYSIS
# ============================================================

def analyze_image(
    file_path: str,
    file_name: str,
    file_type: str = None
):

    print("Starting image analysis:", file_name)

    prompt = f"""
You are an advanced computer vision AI assistant
inside a cloud file storage application.

Analyze the uploaded image carefully.

File name:
{file_name}

File type:
{file_type}

IMPORTANT:

Inspect the actual visual contents of the image.

Do NOT rely only on OCR.

Identify and describe:

- visible text
- numbers
- tables
- scorecards
- charts
- diagrams
- logos
- UI elements
- objects
- people or activities
- locations or scenes
- important visual information

If the image contains a sports scoreboard or scorecard,
read the visible scores, overs, player statistics,
team names and other relevant information.

If the image is a screenshot,
explain what application, webpage, interface,
or content is visible.

Generate:

1. summary
Short summary of the image.

2. description
Detailed description of what is visually present.

3. tags
Generate 5 to 8 relevant smart tags.

4. insights
Important information detected from the image,
including visible numbers, text, scores, tables,
or other useful observations.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "short image summary",
    "description": "detailed visual description",
    "tags": ["tag1", "tag2", "tag3"],
    "insights": "important visual information"
}}

Do not include markdown.
Do not include ```json.
Return JSON only.
"""

    try:
        client = get_client()
        if not client:
            return {
                "summary": "AI analysis could not be completed at this time (API key unconfigured).",
                "description": "Please set a valid GEMINI_API_KEY in environment configuration.",
                "tags": "[\"image\"]",
                "insights": "You can retry later."
            }

        # Upload image to Gemini Files API

        uploaded_file = client.files.upload(
            file=file_path
        )

        print("Image uploaded to Gemini")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                uploaded_file,
                prompt
            ]
        )

        print("Image analysis completed")

        return parse_ai_response(response.text)

    except Exception as e:

        print("Gemini image analysis error:", e)

        return {
            "summary": "Image analysis could not be generated.",
            "description": "",
            "tags": "[]",
            "insights": ""
        }


# ============================================================
# AUDIO ANALYSIS
# ============================================================

def analyze_audio(
    file_path: str,
    file_name: str,
    file_type: str = None
):

    print("Starting audio analysis:", file_name)

    prompt = f"""
You are an AI audio analysis assistant
inside a cloud file storage application.

Analyze the uploaded audio file.

File name:
{file_name}

File type:
{file_type}

Analyze the audio for:

- speech
- transcription
- important spoken information
- topics
- keywords
- music
- sound effects
- important events
- speaker changes when clearly detectable

If speech is present, summarize the important spoken content.

Generate:

1. summary
Short summary of the audio.

2. description
Explain what the audio contains.

3. tags
Generate 5 to 8 relevant smart tags.

4. insights
Mention important information detected from
speech, sounds, music, topics, or events.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "short audio summary",
    "description": "audio description",
    "tags": ["tag1", "tag2", "tag3"],
    "insights": "important audio information"
}}

Do not include markdown.
Do not include ```json.
Return JSON only.
"""

    try:
        client = get_client()
        if not client:
            return {
                "summary": "AI analysis could not be completed at this time (API key unconfigured).",
                "description": "Please set a valid GEMINI_API_KEY in environment configuration.",
                "tags": "[\"audio\"]",
                "insights": "You can retry later."
            }

        # Upload audio to Gemini

        uploaded_file = client.files.upload(
            file=file_path
        )

        print("Audio uploaded to Gemini")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                uploaded_file,
                prompt
            ]
        )

        print("Audio analysis completed")

        return parse_ai_response(response.text)

    except Exception as e:

        print("Gemini audio analysis error:", e)

        return {
            "summary": "Audio analysis could not be generated.",
            "description": "",
            "tags": "[]",
            "insights": ""
        }


# ============================================================
# VIDEO ANALYSIS
# ============================================================

def analyze_video(
    file_path: str,
    file_name: str,
    file_type: str = None
):

    print("Starting video analysis:", file_name)

    prompt = f"""
You are an advanced video analysis AI assistant
inside a cloud file storage application.

Analyze the uploaded video carefully.

File name:
{file_name}

File type:
{file_type}

Analyze:

- objects
- people
- activities
- scenes
- actions
- visible text
- numbers
- scoreboards
- charts
- UI elements
- locations
- important events
- speech/audio when present
- changes between scenes

If this is a sports video,
identify important sporting events and visible scoreboards.

If this is a tutorial or presentation,
identify the main topics and important information.

Generate:

1. summary
Short summary of the video.

2. description
Detailed description of the video content.

3. tags
Generate 5 to 8 relevant smart tags.

4. insights
Mention important events, text, numbers,
actions, topics, or other useful observations.

Return ONLY valid JSON.

Use exactly this structure:

{{
    "summary": "short video summary",
    "description": "detailed video description",
    "tags": ["tag1", "tag2", "tag3"],
    "insights": "important video information"
}}

Do not include markdown.
Do not include ```json.
Return JSON only.
"""

    try:
        client = get_client()
        if not client:
            return {
                "summary": "AI analysis could not be completed at this time (API key unconfigured).",
                "description": "Please set a valid GEMINI_API_KEY in environment configuration.",
                "tags": "[\"video\"]",
                "insights": "You can retry later."
            }

        # Upload video to Gemini

        uploaded_file = client.files.upload(
            file=file_path
        )

        print("Video uploaded to Gemini")

        # ----------------------------------------------------
        # Video needs processing before analysis
        # ----------------------------------------------------

        while (
            not uploaded_file.state
            or uploaded_file.state.name != "ACTIVE"
        ):

            print(
                "Video processing...",
                uploaded_file.state
            )

            time.sleep(5)

            uploaded_file = client.files.get(
                name=uploaded_file.name
            )

        print("Video processing completed")

        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=[
                uploaded_file,
                prompt
            ]
        )

        print("Video analysis completed")

        return parse_ai_response(response.text)

    except Exception as e:

        print("Gemini video analysis error:", e)

        return {
            "summary": "Video analysis could not be generated.",
            "description": "",
            "tags": "[]",
            "insights": ""
        }


# ============================================================
# MAIN FILE ANALYSIS FUNCTION
# ============================================================

def analyze_file(
    file_path: str,
    file_name: str,
    file_type: str = None
):

    extension = Path(file_path).suffix.lower()

    print("----------------------------------------")
    print("AI ANALYSIS")
    print("File:", file_name)
    print("Type:", file_type)
    print("Extension:", extension)
    print("----------------------------------------")


    # ========================================================
    # IMAGE
    # ========================================================

    image_extensions = [
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
        ".gif"
    ]

    if extension in image_extensions:

        return analyze_image(
            file_path,
            file_name,
            file_type
        )


    # ========================================================
    # AUDIO
    # ========================================================

    audio_extensions = [
        ".mp3",
        ".wav",
        ".m4a",
        ".aac",
        ".ogg",
        ".flac"
    ]

    if extension in audio_extensions:

        return analyze_audio(
            file_path,
            file_name,
            file_type
        )


    # ========================================================
    # VIDEO
    # ========================================================

    video_extensions = [
        ".mp4",
        ".mov",
        ".avi",
        ".mkv",
        ".webm",
        ".mpeg",
        ".mpg"
    ]

    if extension in video_extensions:

        return analyze_video(
            file_path,
            file_name,
            file_type
        )


    # ========================================================
    # EVERYTHING ELSE → TEXT/DOCUMENT ANALYSIS
    # ========================================================

    return analyze_text_file(
        file_path,
        file_name,
        file_type
    )