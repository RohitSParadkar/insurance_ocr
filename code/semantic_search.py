import os
import re
import json
from datetime import datetime, timezone
from pathlib import Path
from dotenv import load_dotenv
import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from extractor import resolve_data_path
from Extraction_Templates.img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages

# ==================================================
# ENV
# ==================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("models/gemini-2.0-flash-lite")

# ==================================================
# CONFIG
# ==================================================
BASE_CHROMA_DIR = "./chroma_db"
CHUNK_SIZE = 250
CHUNK_OVERLAP = 40
TOP_K = 1

# ==================================================
# FINAL SCHEMA
# ==================================================
FINAL_SCHEMA = {
    "insurance_company_name": "",
    "policy_number": "",
    "insured_name": "",
    "insured_contact_no": "",
    "product_name": "",
    "policy_start_date": "",
    "policy_expiry_date": "",
    "sum_assured_idv": "",
    "net_premium": "",
    "vehicle_registration_no": "",
    "posp_name": "",
    "area_manager_rm_name": "",
    "business_retention_type": "",
    "created_at": ""
}

# ==================================================
# SEMANTIC MEANINGS (NOT KEYWORDS)
# ==================================================
FIELD_MEANINGS = {
    "insurance_company_name": "insurance company name insurer underwriting company",
    "policy_number": "policy number certificate number cover note number",
    "insured_name": "insured name policy holder proposer name",
    "insured_contact_no": "insured contact number mobile phone",
    "product_name": "product name plan name policy type",
    "policy_start_date": "policy start date commencement inception",
    "policy_expiry_date": "policy expiry date end date expiration",
    "sum_assured_idv": "sum insured idv insured declared value",
    "net_premium": "net premium total premium payable",
    "vehicle_registration_no": "vehicle registration number rc number",
    "posp_name": "posp name agent advisor intermediary",
    "area_manager_rm_name": "area manager relationship manager rm name",
    "business_retention_type": "business retention new renewal rollover"
}

# ==================================================
# CLEAN TEXT
# ==================================================
def clean_text(text: str) -> str:
    patterns = [
        r"Page\s+\d+\s+of\s+\d+",
        r"Digitally signed by.*",
        r"CIN:\s*[A-Z0-9]+",
        r"IRDAI.*",
        r"Terms and Conditions.*"
    ]
    for p in patterns:
        text = re.sub(p, "", text, flags=re.I)
    return re.sub(r"\n{2,}", "\n", text).strip()

# ==================================================
# CHUNK TEXT
# ==================================================
def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP
    )
    return splitter.split_text(text)

# ==================================================
# CREATE VECTOR DB (LOCAL NOMIС)
# ==================================================
def create_vector_db(chunks, persist_dir):
    embeddings = HuggingFaceEmbeddings(
        model_name="nomic-ai/nomic-embed-text-v1.5",
        model_kwargs={"trust_remote_code": True}
    )
#     embeddings = HuggingFaceEmbeddings(
#     model_name="BAAI/bge-small-en-v1.5",
#     model_kwargs={
#         "device": "cpu"
#     },
#     encode_kwargs={
#         "normalize_embeddings": True
#     }
# )

    vectordb = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=persist_dir
    )
    vectordb.persist()
    return vectordb

# ==================================================
# SEMANTIC RETRIEVAL PER FIELD
# ==================================================
def retrieve_field_context(vectordb, k=TOP_K):
    context = {}
    for field, meaning in FIELD_MEANINGS.items():
        docs = vectordb.similarity_search(meaning, k=k)
        seen = set()
        merged = []
        for d in docs:
            if d.page_content not in seen:
                seen.add(d.page_content)
                merged.append(d.page_content)
        context[field] = "\n".join(merged)
    return context

# ==================================================
# SAFE JSON PARSER
# ==================================================
def safe_json_parse(raw: str):
    raw = raw.replace("```json", "").replace("```", "").strip()
    match = re.search(r"\{[\s\S]*\}", raw)
    if not match:
        return FINAL_SCHEMA.copy()
    try:
        return json.loads(match.group())
    except json.JSONDecodeError:
        return FINAL_SCHEMA.copy()

# ==================================================
# GEMINI EXTRACTION (MINIMAL TOKENS)
# ==================================================
def extract_insurance_metadata(field_context: dict) -> dict:
    compact_text = "\n\n".join(
        f"{k.upper()}:\n{v}" for k, v in field_context.items() if v
    )

    prompt = f"""
Extract insurance policy information.

Rules:
- Output ONLY valid JSON
- No markdown
- Do NOT guess values
- Empty string if missing

JSON schema:
{json.dumps(FINAL_SCHEMA, indent=2)}

Text:
{compact_text}
"""

    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )

    data = safe_json_parse(response.text)

    for key in FINAL_SCHEMA:
        data.setdefault(key, "")

    data["created_at"] = datetime.now(timezone.utc).isoformat()
    return data

def save_field_context(field_context: dict, output_dir="debug"):
    os.makedirs(output_dir, exist_ok=True)

    # -------- TXT FILE (Readable) --------
    txt_path = os.path.join(output_dir, "semantic_context.txt")
    with open(txt_path, "w", encoding="utf-8") as f:
        f.write("SEMANTIC FIELD CONTEXT\n")
        f.write("=" * 80 + "\n\n")

        for field, text in field_context.items():
            f.write(f"[{field.upper()}]\n")
            if text:
                f.write(text.strip() + "\n")
                f.write(f"\n--- chars: {len(text)} ---\n\n")
            else:
                f.write("[EMPTY]\n\n")

    # -------- JSON FILE (Structured) --------
    json_path = os.path.join(output_dir, "semantic_context.json")
    with open(json_path, "w", encoding="utf-8") as jf:
        json.dump(
            {
                "total_fields": len(field_context),
                "total_characters": sum(len(v) for v in field_context.values()),
                "fields": field_context
            },
            jf,
            ensure_ascii=False,
            indent=2
        )

    return txt_path, json_path

# ==================================================
# MAIN
# ==================================================
def main():
    pdf_path = resolve_data_path(
        "../data/motorData/Go_Digital/DG_4W_SCHEDULESC_D169759143_1736159709682.pdf"
    )

    result = extract_text_from_pdf_via_svg_all_pages(pdf_path)
    text = clean_text(result["full_text"])

    print("Total characters in document:", len(text))

    chunks = chunk_text(text)

    chroma_dir = os.path.join(
        BASE_CHROMA_DIR,
        f"{Path(pdf_path).stem}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    )
    os.makedirs(chroma_dir, exist_ok=True)

    vectordb = create_vector_db(chunks, chroma_dir)

    field_context = retrieve_field_context(vectordb)
    print("Characters sent to LLM:", sum(len(v) for v in field_context.values()))
    txt_path, json_path = save_field_context(field_context)

    print("Semantic context saved:")
    print("TXT :", txt_path)
    print("JSON:", json_path)

    final_data = extract_insurance_metadata(field_context)
    print(json.dumps(final_data, ensure_ascii=False, indent=2))

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    main()
