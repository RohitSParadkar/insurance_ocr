import os
import re
import json
import shutil
from datetime import datetime, timezone
from insertData import insert_json 
from pathlib import Path
from dotenv import load_dotenv
from pypdf import PdfReader

import google.generativeai as genai
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import Chroma
from langchain_community.embeddings import HuggingFaceEmbeddings
from extractor import  resolve_data_path
from pathlib import Path 
from Extraction_Templates.img_xml_text_extractor import extract_text_from_pdf_via_svg_all_pages
# ==================================================
# ENV SETUP
# ==================================================
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise EnvironmentError("GEMINI_API_KEY not found")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

# ==================================================
# CONFIG
# ==================================================

#

PDF_PATH = "../data/100009809000.pdf"
BASE_CHROMA_DIR = "./chroma_db"

# ==================================================
# FINAL JSON SCHEMA
# ==================================================
FINAL_SCHEMA = {
    "insurance_company": "",
    "policy_number": "",
    "policy_holder": "",
    "policy_start_date": "",
    "policy_end_date": "",
    "address": "",
    "insured_persons": [],
    "nominee_details": []
}

# ==================================================
# 1. PDF TEXT EXTRACTION
# ==================================================
def extract_text_from_pdf(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    text = ""
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    return text.strip()

# ==================================================
# 2. CHUNK TEXT
# ==================================================
def chunk_text(text: str):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=100
    )
    return splitter.split_text(text)

# ==================================================
# 3. CREATE FRESH CHROMA DIRECTORY PER DOCUMENT
# ==================================================
def create_fresh_chroma_dir(pdf_path: str, base_dir: str = BASE_CHROMA_DIR):
    pdf_name = Path(pdf_path).stem
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    chroma_dir = os.path.join(base_dir, f"{pdf_name}_{timestamp}")
    os.makedirs(base_dir, exist_ok=True)
    if os.path.exists(chroma_dir):
        shutil.rmtree(chroma_dir)
    return chroma_dir

# ==================================================
# 4. CREATE VECTOR DB
# ==================================================
def create_vector_db(chunks, chroma_dir):
    embeddings = HuggingFaceEmbeddings(
       model_name="nomic-ai/nomic-embed-text-v1.5",
       model_kwargs={"trust_remote_code": True}
    )
    vectordb = Chroma.from_texts(
        texts=chunks,
        embedding=embeddings,
        persist_directory=chroma_dir
    )
    vectordb.persist()
    return vectordb

# ==================================================
# 5. FIELD-WISE QUERIES FOR RAG
# ==================================================
FIELD_QUERIES = [
    # Policy
    "policy number policy no certificate number cover note number",

    # Insured details
    "insured name policy holder proposer name",
    "insured contact number mobile number phone number contact details",

    # Insurance company
    "insurance company name insurer underwriting company",

    # Product
    "product name plan name policy type scheme name",

    # Dates
    "policy start date commencement date inception date",
    "policy expiry date policy end date expiration date",
    "period of insurance od cover period own damage cover start date end date"

    # Financials
    "sum assured sum insured idv insured declared value",
    "net premium total premium payable final premium",

    # Vehicle (Motor policies)
    "vehicle registration number registration no rc number vehicle number",

    # POSP / Agent
    "posp name agent name intermediary name advisor name",

    # Relationship manager
    "area manager name relationship manager rm name servicing manager"
]

def retrieve_relevant_text(vectordb, k=1):
    seen = set()
    context = []
    for query in FIELD_QUERIES:
        docs = vectordb.similarity_search(query, k=k)
        for d in docs:
            if d.page_content not in seen:
                seen.add(d.page_content)
                context.append(d.page_content)
    return "\n".join(context)

# ==================================================
# 6. SAFE JSON PARSER
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
# 7. METADATA EXTRACTION FUNCTION
# ==================================================
def extract_insurance_metadata(text: str) -> dict:
    prompt = f"""
Extract insurance policy information.

Rules:
- Output ONLY valid JSON
- No markdown, no explanation
- Missing values must be empty strings or empty lists
- Do NOT guess or infer

JSON format:
{{
  "insurance_company": "",
  "policy_number": "",
  "policy_holder": "",
  "policy_start_date": "",
  "policy_end_date": "",
  "address": "",
  "insured_persons": [
    {{
      "name": "",
      "relationship": "",
      "date_of_birth": "",
      "age": "",
      "gender": "",
      "sum_insured": ""
    }}
  ],
  "nominee_details": [
    {{
      "name": "",
      "date_of_birth": "",
      "age": "",
      "gender": ""
    }}
  ]
}}

Document text:
{text}
"""
    response = model.generate_content(
        prompt,
        generation_config={"temperature": 0}
    )
    data = safe_json_parse(response.text)
    
    # Ensure schema keys
    for key in FINAL_SCHEMA:
        data.setdefault(key, FINAL_SCHEMA[key])
    # Ensure lists
    for k in ["insured_persons", "nominee_details"]:
        if not isinstance(data.get(k), list):
            data[k] = []
    # Add timestamp
    data["created_at"] = datetime.now(timezone.utc).astimezone().isoformat()
    return data

# ==================================================
# 8. MAIN PIPELINE
# ==================================================
def main():
    
    PDF_PATH = resolve_data_path("../data/motorData/TATA_6100021729-00.pdf")
    result = extract_text_from_pdf_via_svg_all_pages(PDF_PATH)
    text = result["full_text"]
    print("Total characters in PDF:", len(text))

    # Chunk text
    chunks = chunk_text(text)

    # Create fresh Chroma folder per document
    chroma_dir = create_fresh_chroma_dir(PDF_PATH)
    vectordb = create_vector_db(chunks, chroma_dir)

    # Retrieve relevant RAG chunks
    rag_text = retrieve_relevant_text(vectordb)
    print("Context",rag_text)
    print("Characters sent to LLM:", len(rag_text))
    

    # Extract structured metadata
    # result = extract_insurance_metadata(rag_text)
    # insert_json(result)

    # Print JSON
    # print(json.dumps(result, indent=2, ensure_ascii=False))

# ==================================================
# RUN
# ==================================================
if __name__ == "__main__":
    main()
