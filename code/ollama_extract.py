"""
Insurance PDF Text Extractor using Ollama
Much faster and lighter than vision-based extraction
Works with PDFs that have searchable text
"""

import ollama
import json
import csv
from pathlib import Path
import PyPDF2
import fitz  # PyMuPDF - better extraction

class InsuranceTextExtractor:
    def __init__(self, model='qwen2.5:3b'):
        """
        Initialize text-based extractor
        
        Recommended lightweight models:
        - 'qwen2.5:3b' (2GB, 4GB RAM) - ⭐ BEST for documents
        - 'phi3:mini' (2.3GB, 4GB RAM) - Good alternative
        - 'llama3.2:3b' (2GB, 4GB RAM) - Fast
        - 'gemma2:2b' (1.6GB, 3GB RAM) - Lightest
        - 'mistral:7b' (4.1GB, 8GB RAM) - More accurate
        """
        self.model = model
        print(f"Using text model: {model}")
        
    def extract_text_pypdf2(self, pdf_path):
        """
        Extract text using PyPDF2 (simpler, faster)
        """
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n\n"
        except Exception as e:
            print(f"Error with PyPDF2: {e}")
        return text
    
    def extract_text_pymupdf(self, pdf_path):
        """
        Extract text using PyMuPDF (better quality)
        Recommended method
        """
        text = ""
        try:
            doc = fitz.open(pdf_path)
            for page_num, page in enumerate(doc, 1):
                text += f"--- Page {page_num} ---\n"
                text += page.get_text() + "\n\n"
            doc.close()
        except Exception as e:
            print(f"Error with PyMuPDF: {e}")
        return text
    
    def check_if_text_pdf(self, pdf_path):
        """
        Check if PDF has extractable text
        Returns: (has_text, sample_text)
        """
        try:
            doc = fitz.open(pdf_path)
            sample = doc[0].get_text().strip()
            doc.close()
            
            has_text = len(sample) > 50  # At least 50 chars
            return has_text, sample[:200] if has_text else ""
        except:
            return False, ""
    
    def extract_data_from_text(self, text, source_file="", page_info=""):
        """
        Extract insurance data using Ollama text model
        """
        prompt = f"""Extract insurance policy information from the following document text.

Rules:
- Output ONLY valid JSON
- No markdown, no explanation, no preamble
- Missing values must be empty strings ""
- Extract ALL insured persons mentioned in the document
- Extract ALL nominees mentioned in the document
- For dates, use format from document (DD/MM/YYYY or DD-MM-YYYY)

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

Return only the JSON object:"""

        try:
            response = ollama.chat(
                model=self.model,
                messages=[{
                    'role': 'user',
                    'content': prompt
                }]
            )
            
            content = response['message']['content'].strip()
            
            # Clean JSON from markdown code blocks
            if '```json' in content:
                content = content.split('```json')[1].split('```')[0]
            elif '```' in content:
                content = content.split('```')[1].split('```')[0]
            
            content = content.strip()
            
            # Parse JSON
            data = json.loads(content)
            
            # Validate structure
            data = self._validate_and_clean_data(data)
            
            # Add metadata
            if source_file:
                data['source_file'] = source_file
            if page_info:
                data['page_info'] = page_info
                
            return data
            
        except json.JSONDecodeError as e:
            print(f"JSON parse error: {e}")
            print(f"Raw response:\n{content}")
            return None
        except Exception as e:
            print(f"Extraction error: {e}")
            return None
    
    def _validate_and_clean_data(self, data):
        """
        Validate and clean extracted data structure
        """
        # Ensure required top-level fields exist
        required_fields = [
            "insurance_company", "policy_number", "policy_holder",
            "policy_start_date", "policy_end_date", "address",
            "insured_persons", "nominee_details"
        ]
        
        for field in required_fields:
            if field not in data:
                if field in ["insured_persons", "nominee_details"]:
                    data[field] = []
                else:
                    data[field] = ""
        
        # Ensure insured_persons is a list
        if not isinstance(data["insured_persons"], list):
            data["insured_persons"] = []
        
        # Validate each insured person
        for person in data["insured_persons"]:
            required_person_fields = [
                "name", "relationship", "date_of_birth", 
                "age", "gender", "sum_insured"
            ]
            for field in required_person_fields:
                if field not in person:
                    person[field] = ""
        
        # Ensure nominee_details is a list
        if not isinstance(data["nominee_details"], list):
            data["nominee_details"] = []
        
        # Validate each nominee
        for nominee in data["nominee_details"]:
            required_nominee_fields = ["name", "date_of_birth", "age", "gender"]
            for field in required_nominee_fields:
                if field not in nominee:
                    nominee[field] = ""
        
        return data
    
    def process_pdf(self, pdf_path, method='pymupdf'):
        """
        Process PDF and extract insurance data
        
        Args:
            pdf_path: Path to PDF file
            method: 'pymupdf' (recommended) or 'pypdf2'
        
        Returns:
            Extracted data dictionary
        """
        print(f"\nProcessing: {pdf_path}")
        
        # Check if PDF has text
        has_text, sample = self.check_if_text_pdf(pdf_path)
        
        if not has_text:
            print("⚠️  WARNING: This PDF appears to be scanned (no text found)")
            print("   Consider using the vision-based extractor instead")
            return None
        
        print(f"✓ PDF has extractable text (sample: {sample[:50]}...)")
        
        # Extract text
        print(f"Extracting text using {method}...")
        if method == 'pymupdf':
            text = self.extract_text_pymupdf(pdf_path)
        else:
            text = self.extract_text_pypdf2(pdf_path)
        
        if not text or len(text) < 100:
            print("✗ Failed to extract sufficient text")
            return None
        
        print(f"✓ Extracted {len(text)} characters")
        
        # Extract data using LLM
        print(f"Analyzing with {self.model}...")
        data = self.extract_data_from_text(
            text, 
            source_file=Path(pdf_path).name
        )
        
        if data:
            print("✓ Successfully extracted data")
            return data
        else:
            print("✗ Failed to extract structured data")
            return None
    
    def process_multiple_pdfs(self, pdf_paths):
        """
        Process multiple PDFs
        """
        all_data = []
        
        for pdf_path in pdf_paths:
            data = self.process_pdf(pdf_path)
            if data:
                all_data.append(data)
        
        return all_data
    
    def save_to_csv(self, data, output_file='insurance_data.csv'):
        """
        Save to CSV (flattened structure)
        For nested data (insured_persons, nominees), creates separate rows
        """
        if not data:
            print("No data to save")
            return
        
        # Handle both single dict and list of dicts
        if isinstance(data, dict):
            data = [data]
        
        # Flatten the data for CSV
        flattened_data = []
        
        for record in data:
            # Get base policy info
            base_info = {
                'source_file': record.get('source_file', ''),
                'page_info': record.get('page_info', ''),
                'insurance_company': record.get('insurance_company', ''),
                'policy_number': record.get('policy_number', ''),
                'policy_holder': record.get('policy_holder', ''),
                'policy_start_date': record.get('policy_start_date', ''),
                'policy_end_date': record.get('policy_end_date', ''),
                'address': record.get('address', '')
            }
            
            # Add insured persons
            insured_persons = record.get('insured_persons', [])
            if insured_persons:
                for idx, person in enumerate(insured_persons, 1):
                    row = base_info.copy()
                    row.update({
                        f'insured_person_{idx}_name': person.get('name', ''),
                        f'insured_person_{idx}_relationship': person.get('relationship', ''),
                        f'insured_person_{idx}_dob': person.get('date_of_birth', ''),
                        f'insured_person_{idx}_age': person.get('age', ''),
                        f'insured_person_{idx}_gender': person.get('gender', ''),
                        f'insured_person_{idx}_sum_insured': person.get('sum_insured', '')
                    })
                    
                    # Add nominees for this row
                    nominees = record.get('nominee_details', [])
                    if nominees:
                        for nom_idx, nominee in enumerate(nominees, 1):
                            row[f'nominee_{nom_idx}_name'] = nominee.get('name', '')
                            row[f'nominee_{nom_idx}_dob'] = nominee.get('date_of_birth', '')
                            row[f'nominee_{nom_idx}_age'] = nominee.get('age', '')
                            row[f'nominee_{nom_idx}_gender'] = nominee.get('gender', '')
                    
                    flattened_data.append(row)
                    break  # One row per policy for now
            else:
                # No insured persons, just base info
                flattened_data.append(base_info)
        
        if flattened_data:
            fieldnames = list(flattened_data[0].keys())
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(flattened_data)
            
            print(f"\n✓ Saved to {output_file}")
    
    def save_to_csv_detailed(self, data, output_file='insurance_detailed.csv'):
        """
        Save to CSV with separate rows for each insured person
        Better for policies with multiple insured persons
        """
        if not data:
            print("No data to save")
            return
        
        if isinstance(data, dict):
            data = [data]
        
        rows = []
        
        for record in data:
            base_info = {
                'source_file': record.get('source_file', ''),
                'insurance_company': record.get('insurance_company', ''),
                'policy_number': record.get('policy_number', ''),
                'policy_holder': record.get('policy_holder', ''),
                'policy_start_date': record.get('policy_start_date', ''),
                'policy_end_date': record.get('policy_end_date', ''),
                'address': record.get('address', '')
            }
            
            insured_persons = record.get('insured_persons', [])
            if insured_persons:
                for person in insured_persons:
                    row = base_info.copy()
                    row.update({
                        'insured_name': person.get('name', ''),
                        'relationship': person.get('relationship', ''),
                        'date_of_birth': person.get('date_of_birth', ''),
                        'age': person.get('age', ''),
                        'gender': person.get('gender', ''),
                        'sum_insured': person.get('sum_insured', '')
                    })
                    
                    # Add first nominee (can be expanded)
                    nominees = record.get('nominee_details', [])
                    if nominees:
                        row['nominee_name'] = nominees[0].get('name', '')
                        row['nominee_dob'] = nominees[0].get('date_of_birth', '')
                        row['nominee_age'] = nominees[0].get('age', '')
                        row['nominee_gender'] = nominees[0].get('gender', '')
                    
                    rows.append(row)
            else:
                rows.append(base_info)
        
        if rows:
            fieldnames = list(rows[0].keys())
            
            with open(output_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(rows)
            
            print(f"✓ Saved detailed view to {output_file}")
    
    def save_to_json(self, data, output_file='insurance_data.json'):
        """Save to JSON"""
        if isinstance(data, dict):
            data = [data]
            
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✓ Saved to {output_file}")


def main():
    """Example usage"""
    
    # Initialize with lightweight model
    extractor = InsuranceTextExtractor(model='qwen3:0.6b')
    
    # Process single PDF
    pdf_path = '../data/100009809000.pdf'
    data = extractor.process_pdf(pdf_path)
    
    if data:
        # Display
        print("\n" + "="*60)
        print("EXTRACTED DATA")
        print("="*60)
        print(json.dumps(data, indent=2))
        
        # Save in different formats
        extractor.save_to_json(data, 'output.json')
        extractor.save_to_csv(data, 'output.csv')
        extractor.save_to_csv_detailed(data, 'output_detailed.csv')
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Policy Number: {data.get('policy_number', 'N/A')}")
        print(f"Insurance Company: {data.get('insurance_company', 'N/A')}")
        print(f"Policy Holder: {data.get('policy_holder', 'N/A')}")
        print(f"Insured Persons: {len(data.get('insured_persons', []))}")
        print(f"Nominees: {len(data.get('nominee_details', []))}")
    
    # Process multiple PDFs
    # import glob
    # pdf_files = glob.glob('insurance_pdfs/*.pdf')
    # all_data = extractor.process_multiple_pdfs(pdf_files)
    # extractor.save_to_csv_detailed(all_data, 'all_policies.csv')


if __name__ == "__main__":
    main()