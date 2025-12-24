from img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages 
import pdfplumber
import re
from typing import Optional ,Tuple
from pathlib import Path




def extract_with_regex(text: str, pattern: str) -> Optional[str]:
    match = re.search(pattern, text, re.IGNORECASE | re.MULTILINE)
    return match.group(1).strip() if match else None

def extract_policy_holder_name(text: str) -> Optional[str]:
    pattern = r"\bDear\.?\s+([^\n\r]+)"
    return extract_with_regex(text, pattern)


def extract_company_name(text: str) -> Optional[str]:
    pattern = re.compile(
        r"Thank\s+you\s+for\s+choosing\s+([\s\S]*?)\s+as\s+your\s+preferred\s+insurance\s+partner\.?",
        re.IGNORECASE
    )

    match = pattern.search(text)
    if match:
        return match.group(1).strip()
    return None

def extract_policy_number(text: str) -> Optional[str]:
    pattern = r"Policy\s*(?:No|Number)\.?\s*([0-9]+)"
    return extract_with_regex(text, pattern)




def extract_contact_number(text: str) -> Optional[str]:
    """
    Extract contact number after 'Contact Number'
    Handles masked and unmasked numbers
    """
    pattern = r"Contact\s*Number\s*([Xx\d-]+)"
    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1) if match else None


def extract_tp_cover_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract policy start (Valid From) and end date (Renewal Date)
    Returns (start_date, end_date)
    """
    pattern = (
        r"Valid\s*From\s*[:\-]?\s*"
        r"(\d{2}-\d{2}-\d{4}).*?"
        r"Renewal\s*Date\s*[:\-]?\s*"
        r"(\d{2}-\d{2}-\d{4})"
    )

    match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1), match.group(2)

    return None, None


def extract_premium_amount(text: str) -> Optional[str]:
    """
    Extract the Total Premium (last number) between 'Premium Details' and 'Nominee Details'.
    """
    # Get the block between Premium Details and Nominee Details
    block_pattern = re.compile(r"Premium Details(.*?)Nominee Details", re.DOTALL)
    block_match = block_pattern.search(text)
    
    if block_match:
        block = block_match.group(1)
        # Find all numbers with commas and decimals
        numbers = re.findall(r"[\d,]+\.\d{2}", block)
        if numbers:
            return numbers[-1].strip()  # Last number is Total Premium
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


def extract_sum_insured_value(text: str) -> Optional[str]:
    """
    Extract Sum Insured value from messy PDF/SVG text
    """
    # Normalize first (CRITICAL)
    cleaned = (
        text.replace("₹", "")
            .replace("(", " ")
            .replace(")", " ")
    )
    cleaned = re.sub(r"\n+", " ", cleaned)

    pattern = re.compile(
        r"Sum\s+Insured.*?([\d,]+(?:\.\d{1,2})?)\s+Loyalty\s+Bonus",
        re.IGNORECASE
    )

    match = pattern.search(cleaned)
    if match:
        return match.group(1).replace(",", "").strip()

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
    pattern = re.compile(
        r"for\s+(.+?)\s*,?\s*Policy\s+No",
        re.IGNORECASE
    )

    match = pattern.search(text)
    if match:
        return match.group(1).strip()
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


PDF_PATH = f"../../data/healthData/HDFC ERGO health/2800000000547300_policy.pdf"

result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)

text = result["full_text"]

# SAVE TO TXT FILE
txt_file_path = save_full_text_to_file(text, PDF_PATH)

# print("Text saved at:", txt_file_path)

# Continue regex extraction
metadata = extract_policy_metadata(text)
print(metadata)


