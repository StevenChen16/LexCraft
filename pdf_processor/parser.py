import pdfplumber
from typing import Dict, Optional
import json
import os
from openai import OpenAI
import sys
from datetime import date
from jsonschema import validate

class ContractParser:
    """Parse contract PDFs and convert to structured data"""
    
    # Schema for validating AI output
    TEMPLATE_SCHEMA = {
        "type": "object",
        "required": ["title", "sections"],
        "properties": {
            "title": {"type": "string"},
            "sections": {
                "type": "array",
                "items": {
                    "type": "object",
                    "required": ["id", "title", "fields"],
                    "properties": {
                        "id": {"type": "string"},
                        "title": {"type": "string"},
                        "fields": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "required": ["name", "label", "type", "required"],
                                "properties": {
                                    "name": {"type": "string"},
                                    "label": {"type": "string"},
                                    "type": {
                                        "type": "string",
                                        "enum": ["text", "number", "date", "select", "multiselect", "checkbox"]
                                    },
                                    "required": {"type": "boolean"},
                                    "options": {
                                        "type": "array",
                                        "items": {"type": "string"}
                                    },
                                    "validation": {
                                        "type": "object",
                                        "properties": {
                                            "min": {
                                                "oneOf": [
                                                    {"type": "number"},
                                                    {"type": "string", "format": "date"}
                                                ]
                                            },
                                            "max": {
                                                "oneOf": [
                                                    {"type": "number"},
                                                    {"type": "string", "format": "date"}
                                                ]
                                            },
                                            "pattern": {"type": "string"}
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }
    
    def __init__(self, api_key: str, api_base_url: str, model: str):
        """Initialize the parser with API credentials"""
        self.client = OpenAI(
            api_key=api_key,
            base_url=api_base_url
        )
        self.model = model
        
    def parse_pdf(self, pdf_path: str) -> Dict:
        """
        Parse PDF and return structured data
        
        Args:
            pdf_path: Path to the PDF file
            
        Returns:
            Dict containing structured contract data
            
        Raises:
            FileNotFoundError: If PDF file doesn't exist
            ValueError: If PDF text extraction fails
            JSONDecodeError: If AI response parsing fails
            ValidationError: If response doesn't match schema
        """
        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f"PDF file not found: {pdf_path}")
            
        # Extract text
        text = self._extract_text(pdf_path)
        if not text.strip():
            raise ValueError("No text could be extracted from PDF")
            
        # Analyze structure using AI
        structure = self._analyze_structure(text)
        
        # Validate structure against schema
        try:
            validate(instance=structure, schema=self.TEMPLATE_SCHEMA)
        except Exception as e:
            raise ValueError(f"AI output does not match required schema: {str(e)}")
        
        # Convert to database format
        return self._convert_to_db_format(structure)

    def _extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF with error handling"""
        text_content = []
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_content.append(text)
                        
            return "\n".join(text_content)
            
        except Exception as e:
            raise ValueError(f"Failed to extract text from PDF: {str(e)}")

    def _analyze_structure(self, contract_text: str) -> Dict:
        """Use AI to analyze contract structure"""
        system_prompt = """You are a legal document parser specializing in rental agreements.
Analyze the rental agreement text and convert it to structured JSON format.
Include all mandatory sections even if some information is implicit or missing.
IMPORTANT: Return ONLY the JSON output without any additional text, explanation or markdown formatting."""

        # 注意这里改用两个独立的字符串，而不是在模板中包含合同文本
        instruction_prompt = """Please convert this rental agreement into structured JSON with the following mandatory sections:
1. Parties (landlord and tenant information)
2. Rental Unit (property details)
3. Term (start date, end date)
4. Rent (amount, payment details)
5. Security Deposit
6. Utilities and Services
7. Maintenance and Repairs
8. Rights and Responsibilities

Required structure:
{
    "title": "Contract Title",
    "sections": [
        {
            "id": "section_id",
            "title": "Section Title", 
            "fields": [
                {
                    "name": "field_name",
                    "label": "Display Label",
                    "type": "field_type",  // Must be one of: text, number, date, select, multiselect, checkbox
                    "required": true/false,
                    "validation": {
                        "min": number/date,    // For number/date fields
                        "max": number/date,    // For number/date fields
                        "pattern": "regex"     // For text fields (e.g. email, phone, postal code)
                    },
                    "options": []  // Required for select/multiselect/checkbox types
                }
            ]
        }
    ]
}

Note:
- For phone numbers, use type "text" with appropriate pattern validation
- For email addresses, use type "text" with email pattern validation
- For long text fields, use type "text" with appropriate min/max validation
- All select/multiselect/checkbox fields must have options array
- Date fields can have date string format for min/max (e.g. "2023-01-01")
"""

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": instruction_prompt},
                    {"role": "user", "content": f"Here is the contract text to analyze:\n\n{contract_text}"}
                ],
                temperature=0.1,  # Low temperature for more consistent output
                stream=False
            )
            
            response_text = response.choices[0].message.content
            print(f"AI response: {response_text}")
            
            # Clean response text - remove any markdown and surrounding text
            if '```' in response_text:
                # Extract content between the first pair of ``` markers
                start = response_text.find('```') + 3
                end = response_text.find('```', start)
                # Skip the "json" language identifier if present
                if response_text[start:start+4] == 'json':
                    start = response_text.find('\n', start) + 1
                response_text = response_text[start:end].strip()
            else:
                # Try to find JSON content directly
                start = response_text.find('{')
                end = response_text.rfind('}') + 1
                if start != -1 and end != 0:
                    response_text = response_text[start:end].strip()
            
            try:
                parsed_json = json.loads(response_text)
                
                # Move options from validation to root level for select/multiselect/checkbox fields
                for section in parsed_json.get('sections', []):
                    for field in section.get('fields', []):
                        if field.get('type') in ['select', 'multiselect', 'checkbox']:
                            # If options are in validation, move them up
                            if 'validation' in field and 'options' in field['validation']:
                                field['options'] = field['validation'].pop('options')
                            # Remove pattern validation for these types
                            if 'validation' in field and 'pattern' in field['validation']:
                                del field['validation']['pattern']
                
                return parsed_json
            except json.JSONDecodeError as e:
                raise ValueError(f"Failed to parse AI response as JSON: {str(e)}")
                
        except Exception as e:
            raise ValueError(f"AI analysis failed: {str(e)}")

    def _convert_to_db_format(self, structure: Dict) -> Dict:
        """Convert AI analysis result to database format"""
        sections = structure.get("sections", [])
        return {
            "type": "standard",
            "version": "1.0",
            "description": structure.get("title", ""),
            "sections": sections,
            "features": {},
            "property_types": ["apartment", "house", "condo"],
            "province": None  # Will be set by import_contract_template
        }

def import_contract_template(pdf_path: str, province: str, api_key: str, api_base_url: str, model: str) -> Optional[Dict]:
    """
    Import contract template to database
    
    Args:
        pdf_path: Path to PDF file
        province: Province/state name
        api_key: OpenAI API key
        api_base_url: OpenAI API base URL
        model: Model name to use
        
    Returns:
        ContractTemplate object or None if import fails
    """
    if not os.path.exists(pdf_path):
        print(f"Error: PDF file not found at {pdf_path}")
        return None
        
    parser = ContractParser(api_key, api_base_url, model)
    session = None
    
    try:
        template_data = parser.parse_pdf(pdf_path)
        template_data['province'] = province
        
        from database.orm import ContractTemplate, get_db_session
        session, _ = get_db_session()  # 忽略返回的engine
        template = ContractTemplate(**template_data)
        session.add(template)
        session.commit()
        
        print(f"Successfully imported contract template for {province}")
        return template
        
    except Exception as e:
        print(f"Error importing template: {str(e)}")
        if session:
            session.rollback()
        return None
        
    finally:
        if session:
            session.close()

if __name__ == "__main__":
    # Example usage
    import sys, os
    sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
    from config import DEEPSEEK_CONFIG, DB_CONFIG
    
    pdf_path = "data/templates/Ontario_Residential_Tenancy_Agreement.pdf"
    
    if not os.path.exists(pdf_path):
        os.makedirs("data/templates", exist_ok=True)
        print(f"Please place the contract PDF at: {pdf_path}")
    else:
        template = import_contract_template(
            pdf_path=pdf_path,
            province="Ontario",
            api_key=DEEPSEEK_CONFIG['api_key'],
            api_base_url=DEEPSEEK_CONFIG['base_url'],
            model=DEEPSEEK_CONFIG['model']
        )