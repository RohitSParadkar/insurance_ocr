import os
import json
from insertData import insert_json
from gemini_extract import extract_insurance_metadata, extract_text_from_pdf

# ==============================
# CONFIG
# ==============================
PDF_FOLDER_PATH = "../data/multiPdf"   # folder containing PDFs

# ==============================
# FUNCTION: Process single PDF
# ==============================
def process_single_pdf(pdf_path: str) -> dict:
    """
    Extract text from a single PDF and return structured insurance metadata
    """
    try:
        pdf_text = extract_text_from_pdf(pdf_path)
        result = extract_insurance_metadata(pdf_text)

        # add source file info (recommended)
        result["source_file"] = os.path.basename(pdf_path)

        return result

    except Exception as e:
        return {
            "source_file": os.path.basename(pdf_path),
            "error": str(e)
        }


# FUNCTION: Process all PDFs in folder
def process_pdf_folder(folder_path: str):
    """
    Iterate through all PDF files in a folder, extract metadata,
    print JSON output, and insert into DB
    """
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(".pdf"):
            pdf_path = os.path.join(folder_path, file_name)

            print(f"\n Processing: {file_name}")

            result = process_single_pdf(pdf_path)

            # JSON-only output
            print(json.dumps(result, ensure_ascii=False, indent=2))

            # insert into DB
            insert_json(result)



# MAIN

def main():
    process_pdf_folder(PDF_FOLDER_PATH)


# RUN
if __name__ == "__main__":
    main()
