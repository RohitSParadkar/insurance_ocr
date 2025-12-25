import json
import re
import os
from datetime import datetime, timezone
from pypdf import PdfReader
import google.generativeai as genai
from extractor import  resolve_data_path
from dotenv import load_dotenv
from Extraction_Templates.img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages


# LOAD ENV
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found in .env file")


# FINAL DATABASE SCHEMA

FINAL_SCHEMA = {
    "insurance_company_name": "",
    "policy_number": "",
    "insured_name": "",
    "insured_contact_no": "",
    "product_name": "",
    "policy_start_date": "",
    "policy_expiry_date": "",
    "sum_assured_idv": "",
    "net_premium": "",
    "vehicle_registration_no": "",
    "posp_name": "",
    "area_manager_rm_name": "",
    "business_retention_type": "",
    "created_at": ""
}

# GEMINI SETUP

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

def extract_insurance_metadata(text: str) -> dict:
    prompt = f"""
Extract insurance policy information.

Rules:
- Output ONLY valid JSON
- No markdown, no explanation
- Do NOT hallucinate values
- Missing values must be empty strings

JSON format:
{{
  "insurance_company_name": "",
  "policy_number": "",
  "insured_name": "",
  "insured_contact_no": "",
  "product_name": "",
  "policy_start_date": "",
  "policy_expiry_date": "",
  "sum_assured_idv": "",
  "net_premium": "",
  "vehicle_registration_no": "",
  "posp_name": "",
  "area_manager_rm_name": "",
  "business_retention_type": ""
}}

Document text:
{text}
"""

    response = model.generate_content(prompt)
    raw = response.text.strip()

    # Clean markdown if any
    raw = raw.replace("```json", "").replace("```", "").strip()

    # Extract JSON block
    match = re.search(r"\{.*\}", raw, re.DOTALL)
    if not match:
        data = FINAL_SCHEMA.copy()
    else:
        try:
            data = json.loads(match.group())
        except json.JSONDecodeError:
            data = FINAL_SCHEMA.copy()

    # Ensure all schema keys exist
    for key in FINAL_SCHEMA:
        data.setdefault(key, "")

    # Add current date & time (ISO-8601, timezone-aware)
    data["created_at"] = datetime.now(timezone.utc).astimezone().isoformat()

    return data



# MAIN — JSON ONLY OUTPUT
def main():
    PDF_PATH = resolve_data_path("../data/motorData/Go_Digital/DG_4W_SCHEDULESC_D169759143_1736159709682.pdf")
    result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)
    text = result["full_text"]
    total_characters = len(text)
    print("Total number of characters in document:", total_characters)
    result = extract_insurance_metadata(text)
    print(json.dumps(result, ensure_ascii=False))

# RUN
if __name__ == "__main__":
    main()