import google.generativeai as genai
import os
import json
from code.extractor import extract_text_from_pdf 


genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")

def extract_metadata_with_gemini(text):
    prompt = f"""
    You are an insurance document parser.

    Extract metadata and return ONLY valid JSON.

    Fields:
    policy_type
    policy_number
    insurer_name
    insured_name
    policy_start_date
    policy_end_date
    premium_amount
    sum_insured

    Vehicle fields (if applicable):
    registration_number
    engine_number
    chassis_number
    make
    model
    idv

    CWR fields (if applicable):
    project_name
    project_location
    contract_value
    risk_cover

    Document Text:
    {text}
    """

    response = model.generate_content(prompt)
    return json.loads(response.text)

path = "../data/MotorprivateCarPolicyWording.pdf"
data = extract_text_from_pdf(path)
print(data)
json_data = extract_metadata_with_gemini(data)
print(json_data)