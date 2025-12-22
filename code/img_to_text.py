# import pdfplumber
# from PIL import Image
# import pytesseract
# import io


# def extract_text_from_scanned_pdf(pdf_path):
#     """
#     Extracts text from a scanned PDF by performing OCR on each page.

#     Args:
#         pdf_path (str): The file path to the scanned PDF.

#     Returns:
#         str: The combined extracted text from all pages.
#     """
#     all_text = ""

#     # Open the PDF file
#     with pdfplumber.open(pdf_path) as pdf:
#         # Iterate through each page
#         for page_num, page in enumerate(pdf.pages, start=1):
#             print(f"Processing page {page_num}...")

#             # Extract the page as an image
#             page_image = page.to_image(resolution=300)  # Higher resolution for better OCR

#             # Convert the pdfplumber image to a PIL Image
#             pil_image = page_image.original

#             # Perform OCR on the PIL Image
#             text = pytesseract.image_to_string(pil_image, lang='eng')

#             # Append the text from this page
#             all_text += f"\n--- Page {page_num} ---\n{text}"

#     return all_text

# # Example usage
# if __name__ == "__main__":
#     pdf_file = "../data/motorData/TATA_6100021729-00.pdf"
#     extracted_text = extract_text_from_scanned_pdf(pdf_file)

#     # Print the extracted text
#     print(extracted_text)

#     # Optionally, save the text to a file
#     with open("extracted_text.txt", "w", encoding="utf-8") as text_file:
#         text_file.write(extracted_text)
#     print("\nText has been saved to 'extracted_text.txt'")

import fitz  # PyMuPDF

def extract_pdf_drawings_as_svg(pdf_path, output_svg_path, page_num=0):
    """
    Extracts vector graphics from a specific page of a PDF and saves as an SVG.
    
    Args:
        pdf_path (str): The path to the input PDF file.
        output_svg_path (str): The path to save the output SVG file.
        page_num (int): The page number (0-indexed) to extract from.
    """
    doc = fitz.open(pdf_path)
    if page_num >= doc.page_count:
        print(f"Error: Page number {page_num} is out of range.")
        doc.close()
        return

    page = doc[page_num]
    
    # Get all drawings (vector paths) on the page
    # Using text_as_path=0 ensures text is included as text elements in SVG, not drawing commands
    svg_content = page.get_svg_image(matrix=fitz.Matrix(1, 1), text_as_path=0) 

    with open(output_svg_path, "w", encoding="utf-8") as f:
        f.write(svg_content)

    doc.close()
    print(f"Successfully extracted drawings from page {page_num + 1} to {output_svg_path}")

# Example Usage:
input_pdf = "../data/motorData/TATA_6100021729-00.pdf"
output_svg = "extracted_graphics.svg"
extract_pdf_drawings_as_svg(input_pdf, output_svg, page_num=1) 