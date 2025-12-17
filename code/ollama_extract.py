
import ollama
import json 
from code.extractor import extract_text_from_pdf 

INSURANCE_SCHEMA = {
    "policy_type": "",
    "policy_number": "",
    "insured_name": "",
    "vehicle_number": "",
    "engine_number": "",
    "chassis_number": "",
    "insurer_name": "",
    "policy_start_date": "",
    "policy_end_date": "",
    "sum_insured": "",
    "premium_amount": ""
}

def build_prompt(ocr_text):
    return f"""
You are an information extraction system.

Extract insurance policy details from the text below.

Rules:
- Return ONLY valid JSON
- Do NOT add explanation
- If a field is missing, return null
- Dates must be YYYY-MM-DD
- Numbers must not contain commas

JSON Schema:
{INSURANCE_SCHEMA}

Text:
\"\"\"{ocr_text}\"\"\"
"""


def extract_with_ollama(text):
    response = ollama.chat(
        model="llama3.2",
        messages=[{"role": "user", "content": build_prompt(text)}],
        options={
            "temperature": 0,
            "num_predict": 512
        }
    )

    raw = response["message"]["content"]

    # Safety JSON parsing
    try:
        return json.loads(raw)
    except:
        return {"error": "Invalid JSON", "raw_output": raw}

path = "../data/MotorprivateCarPolicyWording.pdf"
data = extract_text_from_pdf(path)
print(data)
json_data = extract_with_ollama(data)
print(json_data)
