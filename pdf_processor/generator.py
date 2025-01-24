from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph
import json

class ContractPDFGenerator:
    def __init__(self, template_data):
        self.template_data = template_data
        self.styles = getSampleStyleSheet()
    
    def create_pdf(self, output_path, form_data):
        """Create a filled PDF contract"""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            rightMargin=72,
            leftMargin=72,
            topMargin=72,
            bottomMargin=72
        )
        
        # Parse template JSON
        template = json.loads(self.template_data['template_json'])
        
        # Build content
        story = []
        
        # Add title
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=16,
            spaceAfter=30
        )
        story.append(Paragraph(template['title'], title_style))
        
        # Add sections
        for section in template['sections']:
            story.append(Paragraph(section['title'], self.styles['Heading2']))
            
            for field in section['fields']:
                field_id = field['id']
                if field_id in form_data:
                    label = field['label']
                    value = form_data[field_id]
                    text = f"{label}: {value}"
                    story.append(Paragraph(text, self.styles['Normal']))
        
        # Build PDF
        doc.build(story)
