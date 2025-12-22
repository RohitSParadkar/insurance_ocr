import pdfplumber



def extract_text_from_pdf(file_path):
    text = ""
    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text += page.extract_text() or ""
    return text

path = "../data/NivaBupa/35091132202500.pdf"
data = extract_text_from_pdf(path)
print("extractedData",data)