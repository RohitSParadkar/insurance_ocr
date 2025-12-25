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
    """
    Extract policy holder name from:
    - 'Dear MR. NAVEEN RANJAN'
    - Between 'Name' and 'Address'
    """
    patterns = [
        r"\bDear\.?\s+([^\n\r]+)",                       # Dear MR. XYZ
        r"Name\s*[\r\n]+([A-Z\s]+?)\s*[\r\n]+Address"    # Name ... Address
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip()
    return None



def extract_company_name(text: str) -> Optional[str]:
    """
    Extract company/domain name from email
    Example: customersupport@tataaig.com → tataaig
    """
    pattern = r"@([a-zA-Z0-9-]+)\."
    match = re.search(pattern, text)
    return match.group(1) if match else None

def extract_policy_number(text: str) -> Optional[str]:
    """
    Extract policy number:
    - Supports multi-part numbers (e.g. 6301931391 01 00)
    - Stops before next label like 'Insured’s Name'
    """
    pattern = (
        r"Policy\s*(?:No|Number)\.?\s*"
        r"([\d\s]+?)"
        r"(?=\n[A-Za-z]|$)"
    )

    match = re.search(pattern, text, re.IGNORECASE)
    return match.group(1).strip() if match else None

def extract_contact_number(text: str) -> Optional[str]:
    """
    Extract contact number from policy text.

    Supports:
    - Insured Contact No
    - Customer contact number
    - Contact No
    - Contact number appearing BETWEEN Contact No and Email ID
    - Masked numbers (X, x, *)
    - Optional country code
    """

    patterns = [
        # 1. Contact number BETWEEN Contact No and Email ID
        r"Contact\s*No\.?\s*(.*?)\s*Email\s*ID",

        # 2. Standard labeled formats
        r"(?:Insured\s+Contact\s+No|Customer\s+contact\s+number|Contact\s+No)"
        r"\s*[:\-]?\s*"
        r"(\+?\d{1,3}\s*)?([0-9Xx*]{8,15})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            # BETWEEN Contact & Email case
            if match.lastindex == 1:
                return re.sub(r"\s+", " ", match.group(1)).strip()

            # Labeled contact case
            country = match.group(1) or ""
            number = match.group(2)
            return f"{country}{number}".strip()

    return None

def extract_tp_cover_dates(text: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Extract TP cover start and end dates.
    Supports multiple date formats.
    Returns (start_date, end_date)
    """

    patterns = [
        # Format: 29/10/2025 (00:00 Hrs)
        r"Cover\s*Period.*?"
        r"(\d{2}/\d{2}/\d{4}\s*\([^)]*\)).*?"
        r"(\d{2}/\d{2}/\d{4}\s*\([^)]*\))",

        # Format: 30 Jun '25
        r"Cover\s*Period\s+"
        r"(\d{1,2}\s+[A-Za-z]{3}\s+'\d{2}).*?"
        r"(\d{1,2}\s+[A-Za-z]{3}\s+'\d{2})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip(), match.group(2).strip()

    return None, None


def extract_premium_amount(text: str) -> Optional[str]:
    """
    Extract premium amount from insurance policy text.
    Supports:
    - Premium Amount (Including GST) ... 3945
    - Premium amount : ₹ 843.00
    - ₹ on separate line
    Returns amount as string without commas.
    """

    patterns = [
        # Format: Premium Amount (Including GST) ₹ 3945
        r"Premium\s*Amount\s*\(Including\s*GST\)[\s₹Rs\.]*"
        r"(\d{3,7}(?:\.\d{2})?)",

        # Format: Premium amount : ₹ 843.00
        r"Premium\s*amount\s*:\s*₹?\s*([\d,]+(?:\.\d{2})?)"
    ]

    for pattern in patterns:
        matches = re.findall(pattern, text, re.IGNORECASE | re.DOTALL)
        if matches:
            return matches[-1].replace(",", "").strip()

    return None

def extract_registration_number(text: str) -> Optional[str]:
    """
    Extracts vehicle registration number from policy text.

    Supported formats:
    - Registration No.
      GJ 01 HW 2389
    - Registration no : JH 18 C 5476
    """

    patterns = [
        # Format: Registration No.\nGJ 01 HW 2389
        r"Registration\s*No\.?\s*"
        r"([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{3,4})",

        # Format: Registration no : JH 18 C 5476
        r"Registration\s*no\s*:\s*"
        r"([A-Z]{2}\s*\d{1,2}\s*[A-Z]{1,2}\s*\d{3,4})"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            # Normalize spaces
            return re.sub(r"\s+", " ", match.group(1)).strip()

    return None

def extract_vehicle_idv(text: str) -> Optional[float]:
    """
    Extract Vehicle IDV from policy text.
    Supports multiple OCR / PDF formats.
    Returns float value or None.
    """

    patterns = [
        # Format: IDV (₹) 88093 (with OCR noise)
        r"IDV\s*\(\s*₹\s*\)\s*(?:\d+\s*)?(\d{3,8})",

        # Format: Vehicle IDV ... Total IDV ... 88,093.00
        r"Vehicle\s+IDV.*?Total\s+IDV.*?([\d,]+\.\d{2})",

        # Format: Total IDV : 88093 / 88,093.00
        r"Total\s+IDV\s*[:\-]?\s*₹?\s*([\d,]+(?:\.\d{2})?)"
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            return float(match.group(1).replace(",", ""))
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
    Extract policy variant using two separate logics:
    
    1. After 'Company Limited. Auto Secure -' and before 'UIN :'
    2. Between 'CIN: ...' and 'UIN:', removing bullets (•) and hyphens (-)
    
    Returns first match found from logic 1, else logic 2.
    """
    
    # -----------------------
    # Logic 1: Company Limited
    # -----------------------
    pattern1 = (
        r"Company\s+Limited\.\s*"
        r"Auto\s+Secure\s*-\s*"
        r"(.*?)\s*"
        r"UIN\s*:"
    )

    match1 = re.search(pattern1, text, re.IGNORECASE | re.DOTALL)
    if match1:
        return match1.group(1).strip().rstrip("-").strip()

    # -----------------------
    # Logic 2: Between CIN and UIN
    # -----------------------
    pattern2 = (
        r"CIN\s*:\s*[A-Z0-9]+\s*•?\s*"  # CIN with optional bullet
        r"(.*?)"                        # capture policy name
        r"\s*•?\s*UIN\s*:"              # until UIN
    )

    match2 = re.search(pattern2, text, re.IGNORECASE | re.DOTALL)
    if match2:
        policy_name = match2.group(1)
        # Remove bullets, hyphens, extra spaces
        policy_name = re.sub(r"[•\-]", "", policy_name)
        policy_name = " ".join(policy_name.split())
        return policy_name.strip()

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
    txt_path = output_dir / f"full_text.txt"

    # 'w' mode ALWAYS overwrites the file
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write(full_text)

    return str(txt_path)


PDF_PATH = "../../data/motorData/TATA_6100021729-00.pdf"
# PDF_PATH = "../../data/motorData/TATA_6100021729-00.pdf"

result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)

text = result["full_text"]

# SAVE TO TXT FILE
txt_file_path = save_full_text_to_file(text, PDF_PATH)

# print("Text saved at:", txt_file_path)

# Continue regex extraction
metadata = extract_policy_metadata(text)
print(metadata)


