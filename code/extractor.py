# import pdfplumber
# import pandas as pd
# import pytesseract
# from PIL import Image
# import cv2
# import re 

# def extract_text_from_pdf(file_path):
#     text = ""
#     with pdfplumber.open(file_path) as pdf:
#         for page in pdf.pages:
#             text += page.extract_text() or ""
#     return text

# path = "../data/MotorprivateCarPolicyWording.pdf"
# data = extract_text_from_pdf(path)



# def extract_text_from_excel(file_path):
#     df = pd.read_excel(file_path)
#     return " ".join(df.astype(str).values.flatten())



# INSURANCE_SCHEMA = {
#     "policy_type": "",
#     "policy_number": "",
#     "insurer_name": "",
#     "insured_name": "",
#     "policy_start_date": "",
#     "policy_end_date": "",
#     "premium_amount": "",
#     "sum_insured": "",
# }


# def extract_text_from_image(file_path):
#     img = cv2.imread(file_path)
#     gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
#     return pytesseract.image_to_string(gray)

# img_data = extract_text_from_image("../data/car-insurance-policy.jpg")
# print("image data",img_data)



# def normalize_text(text):
#     text = text.replace('\xa0', ' ')           # remove non-breaking spaces
#     text = re.sub(r'\n+', '\n', text)           # multiple newlines → single
#     text = re.sub(r'[ \t]+', ' ', text)         # extra spaces
#     text = text.strip()
#     return text

# text = extract_text_from_pdf(path)
# clean_text = normalize_text(text)

# with open("motor_policy_clean.txt", "w", encoding="utf-8") as f:
#     f.write(clean_text)

import pdfplumber
import re
import json
from pathlib import Path


# ---------- TEXT NORMALIZATION ----------
def normalize_text(text: str) -> str:
    """
    Cleans PDF text so regex works reliably
    """
    if not text:
        return ""

    text = text.replace("\xa0", " ")                # non-breaking space
    text = re.sub(r"[ \t]+", " ", text)             # extra spaces
    text = re.sub(r"\n+", "\n", text)               # multiple newlines
    text = re.sub(r"\n\s+", "\n", text)             # newline + spaces
    return text.strip()


# ---------- PDF EXTRACTION ----------
def extract_pdf(file_path: str):
    full_text = ""
    pages_data = []

    with pdfplumber.open(file_path) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            page_text = page.extract_text() or ""
            clean_page_text = normalize_text(page_text)

            pages_data.append({
                "page_number": i,
                "text": clean_page_text
            })

            full_text += clean_page_text + "\n"

    return normalize_text(full_text), pages_data


# ---------- SAVE FILES ----------
def save_outputs(text, pages_data, output_dir="output"):
    Path(output_dir).mkdir(exist_ok=True)

    # Save clean TXT
    with open(f"{output_dir}/policy_clean.txt", "w", encoding="utf-8") as f:
        f.write(text)

    # Save JSON (page-wise)
    with open(f"{output_dir}/policy_pages.json", "w", encoding="utf-8") as f:
        json.dump(
            {
                "document_type": "Motor Insurance Policy",
                "source": "PDF",
                "pages": pages_data
            },
            f,
            indent=2,
            ensure_ascii=False
        )




