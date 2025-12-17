# import re
# from main import extract_text_from_pdf 
# from insertData import insert_json
# def extract_with_regex(text):
#     return {
#         "Email": re.findall(r'Email:\s*([a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,})', text),
#     }

# def get_value(match):
#     return match.group(1) if match else None

# path = "../data/100009809000.pdf"
# data = extract_text_from_pdf(path)
# json_data = extract_with_regex(data)
# print(json_data)
# # insert_json(json_data)

from extractor import save_outputs,extract_pdf
import re


#100009809000.pdf
def icici_lombard_metadata_with_regex(text):
    patterns = {
        "insurer_name": r"(ICICI\s+Lombard)",
        "policy_number": r"Policy\s*Number\s*[:\-]?\s*([A-Z0-9\/\-]+)",
        "policy_start_datetime": (
            r"Policy Start Date\s*&\s*Time\s*"
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4}),\s*"
            r"(\d{2}:\d{2})\s*hrs"
        ),
        "policy_end_datetime": (
            r"Policy End Date\s*&\s*Time\s*"
            r"([A-Za-z]+\s+\d{1,2},\s+\d{4}),\s*"
            r"(\d{2}:\d{2})\s*hrs"
        ),
        "policy_holder": r"(?:Policy\s*holder|Dear)\s+([A-Za-z]+(?:\s+[A-Za-z]+){2})",
    }

    extracted = {}

    # -------- Single-value fields --------
    for key, pattern in patterns.items():
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            if key in ["policy_start_datetime", "policy_end_datetime"]:
                extracted[key] = f"{match.group(1)} {match.group(2)}"
            else:
                extracted[key] = match.group(1).strip()
        else:
            extracted[key] = None

    # -------- MULTIPLE policyholder name + DOB --------
    policyholder_dob_pattern = re.compile(
        r"Policyholder name Date of Birth\s*"
        r"([A-Za-z]+(?:\s+[A-Za-z]+){1,3})\s+"
        r"([A-Za-z]+\s+\d{1,2},\s+\d{4})",
        re.IGNORECASE | re.MULTILINE
    )

    # -------- MULTIPLE INSURED DETAILS: name, DOB, age, gender --------
    insured_section_pattern = re.compile(
        r"Insured Details\s*(.*?)\s*ABHA ID",
        re.DOTALL | re.IGNORECASE
    )

    insured_section_match = insured_section_pattern.search(text)
    if insured_section_match:
        insured_text = insured_section_match.group(1)

        # Extract individual fields
        names = re.findall(r"Insured Name\s*(.*)", insured_text, re.IGNORECASE)
        dobs = re.findall(r"Date of Birth\s*(.*)", insured_text, re.IGNORECASE)
        ages = re.findall(r"Age\s*(.*)", insured_text, re.IGNORECASE)
        genders = re.findall(r"Gender\s*(.*)", insured_text, re.IGNORECASE)

        if names and dobs and ages and genders:
            name_list = names[0].split()
            dob_list = dobs[0].split()
            age_list = ages[0].split()
            gender_list = genders[0].split()

            insureds = []
            name_index = 0
            dob_index = 0
            for i in range(len(age_list)):
                full_name = " ".join(name_list[name_index:name_index+3])
                insureds.append({
                    "name": full_name.strip(),
                    "date_of_birth": dob_list[dob_index] + " " + dob_list[dob_index+1] + ", " + dob_list[dob_index+2],
                    "age": age_list[i],
                    "gender": gender_list[i]
                })
                name_index += 3
                dob_index += 3

            extracted["insured_details"] = insureds
        else:
            extracted["insured_details"] = []
    else:
        extracted["insured_details"] = []

    # -------- ADDRESS extraction --------
    address_pattern = re.compile(
        r"To,\s*(.*?)\s*(?:ANNUAL|Subject:)",
        re.DOTALL | re.IGNORECASE
    )

    address_match = address_pattern.search(text)
    if address_match:
        # Clean up extra whitespace and line breaks
        address = " ".join(line.strip() for line in address_match.group(1).splitlines() if line.strip())

        # Remove policy_holder name if it exists in address
        if extracted.get("policy_holder"):
            address = address.replace(extracted["policy_holder"], "").strip()

        extracted["address"] = address
    else:
        extracted["address"] = None

    return extracted





# ---------- MAIN ----------
pdf_path = "../data/100009809000.pdf"

clean_text, pages_json = extract_pdf(pdf_path)
save_outputs(clean_text, pages_json)

metadata = icici_lombard_metadata_with_regex(clean_text)

print("Extraction completed")
print("Metadata:")
for k, v in metadata.items():
    print(f"{k}: {v}")
