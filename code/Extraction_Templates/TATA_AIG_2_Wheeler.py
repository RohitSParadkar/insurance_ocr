from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages 
import pdfplumber
import re
from typing import Optional ,Tuple
from pathlib import Path



# PDF TEXT EXTRACTION
def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text


def extract_with_regex(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None

def extract_policy_holder_name(text: str) -> Optional[str]:
    pattern = r"\bDear\.?\s+([^\n\r]+)"
    return extract_with_regex(text, pattern)

def extract_company_name(text: str) -> Optional[str]:
    pattern = r"Welcome\s+to\s+(.+?)\s+family"
    return extract_with_regex(text, pattern)

def extract_policy_number(text: str) -> Optional[str]:
    pattern = r"Policy\s*(?:No|Number)\.?\s*([0-9]+)"
    return extract_with_regex(text, pattern)

def extract_contact_number(text: str) -> Optional[str]:
    pattern = (
        r"(?:Insured\s+Contact\s+No|Customer\s+contact\s+number|Contact\s+No)"
        r"\s*[:\-]?\s*"
        r"([0-9Xx*]{8,15})"
    )
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None

def extract_tp_cover_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract TP cover start and end dates
    Returns (start_date, end_date)
    """
    pattern = (
        r"Cover\s+Period\s+"
        r"(\d{1,2}\s+[A-Za-z]{3}\s+'\d{2})"
        r".*?"
        r"(\d{1,2}\s+[A-Za-z]{3}\s+'\d{2})"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)

    if not match:
        return None, None

    start_date = match.group(1)
    end_date = match.group(2)

    return start_date, end_date

def extract_premium_amount(text: str) -> str | None:
    """
    Extracts premium amount from insurance policy text.
    Example match: ₹ 843.00
    """
    pattern = r"Premium\s*amount\s*:\s*₹?\s*([\d,]+(?:\.\d{2})?)"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).replace(",", "").strip()

    return None

def extract_registration_number(text: str) -> str | None:
    """
    Extracts vehicle registration number from policy text.
    Example match: JH 18 C 5476
    """
    pattern = r"Registration\s*no\s*:\s*([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{3,4})"

    match = re.search(pattern, text, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None

def extract_vehicle_idv(text: str) -> Optional[float]:
    """
    Extract Vehicle IDV from policy text.
    Returns float value or None.
    """

    # Pattern: Header followed by numeric row
    pattern = (
        r"Vehicle\s+IDV.*?Total\s+IDV.*?\n"
        r"([\d,]+\.\d{2})"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        value = match.group(1).replace(",", "")
        return float(value)

    return None
def extract_digital_signer(text: str) -> Optional[str]:
    """
    Extracts signer name between:
    'Digitally Signed by:' and 'Date:'
    Whitespace tolerant
    """
    pattern = r"Digitally\s*Signed\s*by\s*:\s*(.*?)\s*Date\s*:"
    
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    return None


def extract_policy_variant(text: str) -> Optional[str]:
    """
    Extract policy name appearing after:
    'Company Limited. Auto Secure -'
    and before:
    'UIN :'
    Whitespace and line-break tolerant
    """
    pattern = (
        r"Company\s+Limited\.\s*"
        r"Auto\s+Secure\s*-\s*"
        r"(.*?)\s*"
        r"UIN\s*:"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().rstrip("-").strip()

    return None

def extract_policy_metadata(text: str) -> dict:
    start_date, end_date = extract_tp_cover_dates(text)
    return {
        "policy_holder_name": extract_policy_holder_name(text),
        "company_name": extract_company_name(text),
        "product_name" : extract_policy_variant(text),
        "policy_number": extract_policy_number(text),
        "insured_contact_number":extract_contact_number(text),
        "tp_policy_start_date": start_date,
        "tp_policy_end_date": end_date,
        "net_premium": extract_premium_amount(text),
        "Vehicle_Registration_No":extract_registration_number(text),
        "vehicle_idv ":extract_vehicle_idv(text),
        "area_manager" :extract_digital_signer(text)
    }


def save_full_text_to_file(full_text: str, pdf_path: str, output_dir="temp_text"):
    """
    Saves full_text to a fixed temp file.
    Overwrites the same file on every run.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(exist_ok=True)

    # Fixed filename per PDF (same file reused)
    pdf_name = Path(pdf_path).stem
    txt_path = output_dir / f"{pdf_name}_full_text.txt"

    # 'w' mode ALWAYS overwrites the file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return str(txt_path)


PDF_PATH = "../../data/motorData/TATA_6100021729-00.pdf"

result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)

text = result["full_text"]

# SAVE TO TXT FILE
txt_file_path = save_full_text_to_file(text, PDF_PATH)

# print("Text saved at:", txt_file_path)

# Continue regex extraction
metadata = extract_policy_metadata(text)
print(metadata)


