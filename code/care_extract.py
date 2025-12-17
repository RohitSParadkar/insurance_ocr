from extractor import save_outputs, extract_pdf
import re


def care_health_metadata_with_regex(text):
    patterns = {
        "insurer_name": r"care\s+health\s+insurance",
        "policy_number": r"Policy No\. (\d+)",
        "policy_holder": r"(?:Policyholder|Dear)\s+([A-Za-z]+(?:\s+[A-Za-z]+){1,2})",
        "policy_start_date": r"Policy Period.*?(\d{2}-[A-Za-z]{3}-\d{4})",
        "policy_end_date": r"to\s+(\d{2}-[A-Za-z]{3}-\d{4})",
        # Address starts after the policy_holder line, goes up to 'Policy Period'
        "address": r"Policyholder\s+[A-Za-z]+(?:\s+[A-Za-z]+){1,2}\s*\n(.*?)\nPolicy Period",
        # Insured persons block between header line and Nominee Details
        "insured_block": r"Name Client ID Relationship Age the Company Sum Insured.*?\n\(dd-mm-yyyy\).*?\n\(since\)\s*\n(.*?)\nNominee Details",
    }

    extracted = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            extracted[key] = match.group(1).strip() if match.groups() else match.group(0).strip()
        else:
            extracted[key] = None

    # Extract multiple insured persons if the block exists
    insured_details = []
    if extracted.get("insured_block"):
        block_text = extracted["insured_block"]
        lines = [line.strip() for line in block_text.split("\n") if line.strip()]
        for line in lines:
            # Extract Name (first group of words before Client ID)
            name_match = re.match(r"([A-Za-z\s]+)\s+[A-Z0-9]+", line)
            name = name_match.group(1).strip() if name_match else None

            # Extract Date of Birth (dd-mm-yyyy)
            dob_match = re.search(r"(\d{2}-\d{2}-\d{4})", line)
            dob = dob_match.group(1) if dob_match else None

            # Extract Age
            age_match = re.search(r"\b(\d{1,3})\b", line)
            age = age_match.group(1) if age_match else None

            # Extract Gender if present (optional)
            gender_match = re.search(r"\b(Male|Female|M|F)\b", line, re.IGNORECASE)
            gender = gender_match.group(1).capitalize() if gender_match else None

            if name or dob or age or gender:
                insured_details.append({
                    "name": name,
                    "date_of_birth": dob,
                    "age": age,
                    "gender": gender
                })

    extracted["insured_details"] = insured_details
    extracted.pop("insured_block", None)  # remove temporary field

    return extracted



# ---------- MAIN ----------
pdf_path = "../data/21140690.PDF"

# Extract text and JSON from PDF
clean_text, pages_json = extract_pdf(pdf_path)

# Save outputs
save_outputs(clean_text, pages_json)

# Extract metadata
metadata = care_health_metadata_with_regex(clean_text)

# Display results
print("Extraction completed")
print("Metadata:")
for k, v in metadata.items():
    print(f"{k}: {v}")
