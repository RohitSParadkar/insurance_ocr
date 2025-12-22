import json
import re
import os
from datetime import datetime, timezone
from pypdf import PdfReader
from dotenv import load_dotenv
from google import genai
from google.genai import types

# ==================================================
# LOAD ENV
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file")

PDF_PATH = "../data/NivaBupa/35388760202500.pdf"
MODEL_NAME = "gemini-2.0-flash-lite"

# ==================================================
# FINAL DATABASE SCHEMA
FINAL_SCHEMA = {
    "created_at": "",
    "insurance_company": "",
    "policy_number": "",
    "policy_holder": "",
    "policy_start_date": "",
    "policy_end_date": "",
    "address": "",
    "insured_persons": [],
    "nominee_details": []
}

# ==================================================
# PDF TEXT EXTRACTION
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ==================================================
# GEMINI CLIENT (NEW SDK)
client = genai.Client(api_key=GEMINI_API_KEY)

# ==================================================
# TOKEN COUNT (AS PER GEMINI DOCS)
def count_tokens(text: str) -> int:
    token_response = client.models.count_tokens(
        model=MODEL_NAME,
        contents=text
    )
    return token_response.total_tokens

# ==================================================
# GEMINI EXTRACTION (STRICT JSON)
def extract_insurance_metadata(text: str) -> dict:
    prompt = f"""
Extract insurance policy information.

Rules:
- Output ONLY valid JSON
- No markdown
- No explanation
- Missing values must be empty strings

JSON format:
{{
  "insurance_company": "",
  "policy_number": "",
  "policy_holder": "",
  "policy_start_date": "",
  "policy_end_date": "",
  "address": "",
  "insured_persons": [
    {{
      "name": "",
      "relationship": "",
      "date_of_birth": "",
      "age": "",
      "gender": "",
      "sum_insured": ""
    }}
  ],
  "nominee_details": [
    {{
      "name": "",
      "date_of_birth": "",
      "age": "",
      "gender": ""
    }}
  ]
}}

Document text:
{text}
"""

    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0,
            response_mime_type="application/json"
        )
    )

    # ---------- TOKEN USAGE (BILLABLE) ----------
    usage = response.usage_metadata
    print("\n--- Gemini Token Usage ---")
    print("Prompt tokens:", usage.prompt_token_count)
    print("Output tokens:", usage.candidates_token_count)
    print("Total billed tokens:", usage.total_token_count)

    raw = response.text.strip()

    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        data = FINAL_SCHEMA.copy()
    else:
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            data = FINAL_SCHEMA.copy()

    for key in FINAL_SCHEMA:
        data.setdefault(key, FINAL_SCHEMA[key])

    data["created_at"] = datetime.now(timezone.utc).astimezone().isoformat()

    return data

# ==================================================
# MAIN
def main():
    pdf_text = extract_text_from_pdf(PDF_PATH)

    char_count = len(pdf_text)
    token_count = count_tokens(pdf_text)

    print("================================")
    print("Document statistics")
    print("Characters:", char_count)
    print("Estimated tokens:", token_count)
    print("================================")

    # Run extraction
    result = extract_insurance_metadata(pdf_text)

    print("\n--- Extracted JSON ---")
    print(json.dumps(result, ensure_ascii=False, indent=2))

# ==================================================
# RUN
if __name__ == "__main__":
    main()
