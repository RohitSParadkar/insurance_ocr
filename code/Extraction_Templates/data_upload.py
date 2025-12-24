from pathlib import Path
import json
import traceback

from mongo_push import insert_json
from NivaBupa import (
    extract_text_from_pdf_via_svg_all_pages,
    extract_policy_metadata,
)

# ==============================
# CONFIG
# ==============================
PDF_FOLDER_PATH = "../../data/healthData/Niva Buppa/"

# ==============================
# PROCESS SINGLE PDF
# ==============================
def process_pdf(pdf_path: Path):
    try:
        print(f"\nProcessing: {pdf_path.name}")

        pdf_text = extract_text_from_pdf_via_svg_all_pages(str(pdf_path))
        text = pdf_text.get("full_text", "")

        if not text.strip():
            print("No text extracted, skipping.")
            return

        result = extract_policy_metadata(text)

        # Optional: add source file info
        result["source_file"] = pdf_path.name

        print(json.dumps(result, ensure_ascii=False, indent=2))

        insert_json(result)
        print("Inserted into MongoDB")

    except Exception as e:
        print(f" Failed for {pdf_path.name}")
        traceback.print_exc()


# ==============================
# MAIN — FOLDER MODE
# ==============================
def main():
    folder = Path(PDF_FOLDER_PATH)

    if not folder.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    pdf_files = list(folder.glob("*.pdf"))

    if not pdf_files:
        print(" No PDF files found.")
        return

    print(f" Found {len(pdf_files)} PDF(s)\n")

    for pdf_file in pdf_files:
        process_pdf(pdf_file)


# ==============================
# RUN
# ==============================
if __name__ == "__main__":
    main()
