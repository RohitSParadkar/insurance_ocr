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
    """
    Extract insurer name between 'for choosing' and 'as your'
    """
    pattern = r"for\s+choosing\s+(.*?)\s+as\s+your"
    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None

def extract_policy_number(text: str) -> Optional[str]:
    pattern = r"Policy\s*(?:No|Number)\.?\s*([0-9]+)"
    return extract_with_regex(text, pattern)


def extract_contact_number(text: str) -> Optional[str]:
    """
    Extract mobile number that appears between 'Email ID' and 'Invoice Number'.
    Handles partially masked numbers as well.
    """
    pattern = re.compile(
        r"Email ID\s*[\n:]?.*?\n\s*(\d{2}\*+\d{2,4})\s*.*?Invoice Number",
        re.DOTALL
    )
    
    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None

def extract_tp_cover_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract Policy Start Date and End Date between
    'Policy Number' and 'Base Sum Insured'

    Supports:
    - DD/MM/YYYY
    - DD-MMM-YYYY (09-Sep-2025)
    """

    date_pattern = r"(?:\d{2}/\d{2}/\d{4}|\d{2}-[A-Za-z]{3}-\d{4})"

    block_pattern = (
        r"Policy\s+Number.*?"
        r"(?:Policy\s+Commencement\s+Date.*?From\s+)?"
        rf"(From\s+{date_pattern})\s+\d{{2}}:\d{{2}}.*?"
        r"(?:Policy\s+Expiry\s+Date.*?To\s+)?"
        rf"(To\s+{date_pattern})\s+\d{{2}}:\d{{2}}.*?"
        r"Base\s+Sum\s+Insured"
    )

    match = re.search(block_pattern, text, re.IGNORECASE | re.DOTALL)

    if not match:
        return None, None

    start_date = match.group(1).replace("From", "").strip()
    end_date = match.group(2).replace("To", "").strip()

    return start_date, end_date

def extract_premium_amount(text: str) -> Optional[str]:
    """
    Extract Net Premium amount after 'Net Premium / Taxable value'
    """
    pattern = r"Net\s+Premium.*?\(Rs\.\)\s*([\d,]+\.\d{2})"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


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

def extract_sum_insured_value(text: str) -> Optional[str]:
    """
    Extract Base Sum Insured value between
    'Base Sum Insured' and 'Policy Commencement Date'

    Supports:
    - 10,00,000
    - Unlimited
    """

    pattern = (
        r"Base\s+Sum\s+Insured\s*"
        r"((?:[\d,]+)|Unlimited)\s*"
        r"(?:Policy\s+Commencement\s+Date|Policy\s+Commencement\s+Date\s+and\s+Time)"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None


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
    Extract product name between 'Product Name' and 'Product UIN'

    Supports:
    - Product Name: Aspire, Product UIN:
    - Product Name: ReAssure 2.0 | Product UIN:
    """

    pattern = (
        r"Product\s*Name\s*[:\-]?\s*"
        r"(.*?)\s*"
        r"(?:,|\||)\s*"
        r"Product\s*UIN"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    return match.group(1).strip() if match else None

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
        "sum_insured ":extract_sum_insured_value(text),
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
    txt_path = output_dir / f"full_text.txt"

    # 'w' mode ALWAYS overwrites the file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return str(txt_path)


PDF_PATH = "../../data/healthData/Niva Buppa/35829924202500.pdf"

result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)

text = result["full_text"]

# SAVE TO TXT FILE
txt_file_path = save_full_text_to_file(text, PDF_PATH)

# print("Text saved at:", txt_file_path)

# Continue regex extraction
metadata = extract_policy_metadata(text)
print(metadata)


