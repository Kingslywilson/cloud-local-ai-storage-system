import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()

def get_client():
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key or api_key == "your_gemini_api_key_here":
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception as e:
        print("Gemini client error:", e)
        return None



def generate_file_analysis(filename, content):
    prompt = f"""
You are an AI assistant for a cloud file storage application.

Analyze the following uploaded file.

File name:
{filename}

File content:
{content[:30000]}

Generate the following:

1. summary
A short summary of what the document contains.

2. description
A useful description of the file.

3. tags
Generate 5 to 8 relevant smart tags.

4. insights
Important information, topics, or useful observations from the content.

Return ONLY valid JSON in this exact format:

{{
    "summary": "short summary",
    "description": "file description",
    "tags": ["tag1", "tag2", "tag3"],
    "insights": "important content insights"
}}
"""

    client = get_client()
    if not client:
        return {
            "summary": "AI analysis unavailable (Gemini key unconfigured).",
            "description": "Please set GEMINI_API_KEY in environment.",
            "tags": [],
            "insights": "Retry later."
        }

    try:
        response = client.models.generate_content(
            model="gemini-3.6-flash",
            contents=prompt
        )
    except Exception as e:
        print("Gemini API error:", e)
        return {
            "summary": "AI analysis could not be completed.",
            "description": str(e),
            "tags": [],
            "insights": ""
        }

    text = response.text.strip()

    if text.startswith("```json"):
        text = text[7:]

    if text.startswith("```"):
        text = text[3:]

    if text.endswith("```"):
        text = text[:-3]

    text = text.strip()

    try:
        result = json.loads(text)
    except json.JSONDecodeError:
        return {
            "summary": text,
            "description": "",
            "tags": [],
            "insights": ""
        }

    return result