from PyPDF2 import PdfReader
import os
import pdfplumber
from typing import List, Dict, Any
import pytesseract
from PIL import Image

import json


# reader = PdfReader("../../data/healthData/2800000000547300_policy.pdf")
# number_of_pages = len(reader.pages)
# page = reader.pages[0]
# text = page.extract_text()



# # Ensure output directory exists
# os.makedirs("assets/images", exist_ok=True)

# # Load PDF
# pdf = PdfDocument.FromFile("../../data/healthData/2800000000547300_policy.pdf")

# # Rasterize pages to images
# pdf.RasterizeToImageFiles(
#     "assets/images/page_{page}.png",
#     DPI=96
# )


PDF_PATH = "../../data/healthData/2800000000547300_policy.pdf"
from pdf2image import convert_from_path

# incase of Linux we don't have to provide the popper_path parameter
images = convert_from_path(
	PDF_PATH, poppler_path=r"../../external_resource/poppler-25.12.0/Library/bin")

for i in range(len(images)):
	# Save pages as images in the pdf
    images[i].save(f'image_{i+1}.png', 'PNG')
    

def pdf_page_to_image(
    pdf_path: str,
    page_number: int,
    dpi: int = 300,
    output_path: str | None = None
) -> Image.Image:
    """
    Convert a specific PDF page to an image.

    :param pdf_path: Path to PDF file
    :param page_number: Page number (1-based index)
    :param dpi: Image DPI (default 300)
    :param output_path: Optional path to save image
    :return: PIL Image object
    """

    images = convert_from_path(
        pdf_path,
        dpi=dpi,
        first_page=page_number,
        last_page=page_number
    )

    if not images:
        raise ValueError(f"No page found for page number {page_number}")

    page_img = images[0]

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        page_img.save(output_path)

    return page_img
def extract_tables_raw_json(pdf_path: str) -> List[Dict[str, Any]]:
    """
    Extract tables from PDF and return raw JSON output
    """

    output = []

    with pdfplumber.open(pdf_path) as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            tables = page.extract_tables()
            if not tables:
                continue

            for table_index, table in enumerate(tables, start=1):
                output.append({
                    "page": page_number,
                    "table_index": table_index,
                    "rows": table
                })

    return output

def extract_text_from_image(image_path: str) -> str:
    """
    Extract text from an image using OCR
    """
    img = Image.open(image_path)
    text = pytesseract.image_to_string(img, config="--psm 6")
    return text.strip()

pdf_path = "../../data/healthData/2800000000547300_policy.pdf"
# pdf_page_to_image(pdf_path,2)
# tables_json = extract_tables_raw_json(pdf_path)
# print(json.dumps(tables_json, indent=2))
img_text = extract_text_from_image("../Extraction_Templates/image_3.png")
print("Text OCR \n",img_text)
