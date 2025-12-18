import json
import re
from pypdf import PdfReader
import google.generativeai as genai
from dotenv import load_dotenv
import os

load_dotenv() 
# ==================================================
# CONFIG
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file")

PDF_PATH = "../data/2742112600033469_POLICY_DOC.pdf"

# ==================================================
# FINAL JSON SCHEMA (MongoDB Ready)
# ==================================================
FINAL_SCHEMA = {
    "insurer_name": "",
    "policy_number": "",
    "policy_holder": "",
    "policy_start_date": "",
    "policy_end_date": "",
    "address": "",
    "nominee_details": []
}

# ==================================================
# PDF TEXT EXTRACTION
# ==================================================
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ==================================================
# GEMINI SETUP
# ==================================================
genai.configure(api_key=GEMINI_API_KEY)

model = genai.GenerativeModel(
    model_name="models/gemini-2.5-flash"
)

# ==================================================
# GEMINI EXTRACTION (STRICT JSON)
# ==================================================
def extract_insurance_metadata(text: str) -> dict:
    prompt = f"""
Extract insurance policy data from the text below.

Rules:
- Output ONLY valid JSON
- No markdown, no comments, no extra text
- Missing values must be empty strings

Required JSON format:
{{
  "insurer_name": "",
  "policy_number": "",
  "policy_holder": "",
  "policy_start_date": "",
  "policy_end_date": "",
  "address": "",
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

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Remove markdown if present
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Extract JSON only
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        return FINAL_SCHEMA

    try:
        data = json.loads(match.group())
    except json.JSONDecodeError:
        return FINAL_SCHEMA

    # Ensure MongoDB-safe structure
    data.setdefault("nominee_details", [])

    return data

# ==================================================
# MAIN (JSON ONLY OUTPUT)
# ==================================================
def main():
    pdf_text = extract_text_from_pdf(PDF_PATH)
    result = extract_insurance_metadata(pdf_text)

    # FINAL OUTPUT — JSON ONLY
    print(json.dumps(result, ensure_ascii=False))

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    main()
