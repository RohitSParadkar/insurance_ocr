from insertData import insert_json 
from all_extraction_gemini import extract_insurance_metadata , extract_text_from_pdf
import json

PDF_PATH = "../data/healthData/2800000000547300_policy.pdf"
# MAIN — JSON ONLY OUTPUT
def main():
    pdf_text = extract_text_from_pdf(PDF_PATH)
    result = extract_insurance_metadata(pdf_text)
    print(json.dumps(result, ensure_ascii=False))
    insert_json(result)

# RUN
if __name__ == "__main__":
    main()
