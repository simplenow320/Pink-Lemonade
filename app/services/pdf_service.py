"""
PDF Generation Service
Professional PDF export for grants, reports, and documents
"""

import io
import os
from datetime import datetime
from typing import Dict, List, Optional
import logging

logger = logging.getLogger(__name__)

# Try to import reportlab, fall back to basic PDF generation if not available
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import letter, A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch
    from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
    from reportlab.platypus import Image as RLImage
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False
    logger.warning("ReportLab not available - using basic PDF generation")

class PDFService:
    """Generate professional PDFs for Pink Lemonade platform"""
    
    def __init__(self):
        self.styles = None
        if REPORTLAB_AVAILABLE:
            self.styles = getSampleStyleSheet()
            self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom styles for Pink Lemonade branding"""
        if not REPORTLAB_AVAILABLE:
            return
            
        # Title style
        self.styles.add(ParagraphStyle(
            name='PinkLemonadeTitle',
            parent=self.styles['Title'],
            fontSize=24,
            textColor=colors.HexColor('#EC4899'),  # Pink
            spaceAfter=30,
            alignment=TA_CENTER
        ))
        
        # Heading style
        self.styles.add(ParagraphStyle(
            name='PinkLemonadeHeading',
            parent=self.styles['Heading1'],
            fontSize=16,
            textColor=colors.HexColor('#EC4899'),
            spaceAfter=12,
            spaceBefore=12
        ))
        
        # Body style
        self.styles.add(ParagraphStyle(
            name='PinkLemonadeBody',
            parent=self.styles['BodyText'],
            fontSize=11,
            alignment=TA_JUSTIFY,
            spaceAfter=12
        ))
    
    def generate_grant_report_pdf(self, grants: List[Dict], org_name: str = "Organization") -> bytes:
        """Generate PDF report of grant matches"""
        if not REPORTLAB_AVAILABLE:
            return self._generate_basic_pdf(f"Grant Report for {org_name}", grants)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(f"Grant Opportunities Report", self.styles['PinkLemonadeTitle'])
        story.append(title)
        
        subtitle = Paragraph(f"<b>{org_name}</b><br/>Generated: {datetime.now().strftime('%B %d, %Y')}", 
                           self.styles['Normal'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Summary
        story.append(Paragraph(f"<b>Total Opportunities Found: {len(grants)}</b>", 
                             self.styles['PinkLemonadeHeading']))
        story.append(Spacer(1, 0.2*inch))
        
        # Grants table
        if grants:
            data = [['Grant Title', 'Funder', 'Amount', 'Deadline', 'Match Score']]
            
            for grant in grants[:50]:  # Limit to 50 for PDF size
                data.append([
                    grant.get('title', 'N/A')[:40],
                    grant.get('funder', 'N/A')[:30],
                    f"${grant.get('amount', 'N/A'):,}" if isinstance(grant.get('amount'), (int, float)) else 'N/A',
                    grant.get('deadline', 'N/A')[:10] if grant.get('deadline') else 'N/A',
                    f"{grant.get('match_score', 0):.0f}%" if grant.get('match_score') else 'N/A'
                ])
            
            table = Table(data, colWidths=[2.5*inch, 2*inch, 1*inch, 1*inch, 1*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EC4899')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
        
        # Build PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def generate_narrative_pdf(self, narrative_data: Dict, org_name: str = "Organization") -> bytes:
        """Generate PDF of grant narrative/pitch"""
        if not REPORTLAB_AVAILABLE:
            return self._generate_basic_pdf(f"Grant Narrative - {org_name}", narrative_data)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph(narrative_data.get('title', 'Grant Narrative'), 
                        self.styles['PinkLemonadeTitle'])
        story.append(title)
        
        # Organization and date
        subtitle = Paragraph(f"<b>{org_name}</b><br/>Generated: {datetime.now().strftime('%B %d, %Y')}", 
                           self.styles['Normal'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Content sections
        sections = narrative_data.get('sections', {})
        for section_name, content in sections.items():
            if content:
                # Section heading
                story.append(Paragraph(section_name.replace('_', ' ').title(), 
                                     self.styles['PinkLemonadeHeading']))
                
                # Section content
                # Handle different content types
                if isinstance(content, str):
                    paragraphs = content.split('\n\n')
                    for para in paragraphs:
                        if para.strip():
                            story.append(Paragraph(para, self.styles['PinkLemonadeBody']))
                elif isinstance(content, list):
                    for item in content:
                        story.append(Paragraph(f"• {item}", self.styles['PinkLemonadeBody']))
                elif isinstance(content, dict):
                    for key, value in content.items():
                        story.append(Paragraph(f"<b>{key}:</b> {value}", 
                                             self.styles['PinkLemonadeBody']))
                
                story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def generate_impact_report_pdf(self, report_data: Dict, org_name: str = "Organization") -> bytes:
        """Generate PDF of impact report"""
        if not REPORTLAB_AVAILABLE:
            return self._generate_basic_pdf(f"Impact Report - {org_name}", report_data)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph("Impact Report", self.styles['PinkLemonadeTitle'])
        story.append(title)
        
        # Organization and period
        period = report_data.get('period', {})
        subtitle = Paragraph(
            f"<b>{org_name}</b><br/>"
            f"Reporting Period: {period.get('start', 'N/A')} to {period.get('end', 'N/A')}<br/>"
            f"Generated: {datetime.now().strftime('%B %d, %Y')}", 
            self.styles['Normal']
        )
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Executive Summary
        if report_data.get('executive_summary'):
            story.append(Paragraph("Executive Summary", self.styles['PinkLemonadeHeading']))
            story.append(Paragraph(report_data['executive_summary'], self.styles['PinkLemonadeBody']))
            story.append(Spacer(1, 0.3*inch))
        
        # Key Metrics
        metrics = report_data.get('metrics', {})
        if metrics:
            story.append(Paragraph("Key Performance Metrics", self.styles['PinkLemonadeHeading']))
            
            # Create metrics table
            data = [['Metric', 'Value']]
            for key, value in metrics.items():
                data.append([key.replace('_', ' ').title(), str(value)])
            
            table = Table(data, colWidths=[3*inch, 2*inch])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#EC4899')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(table)
            story.append(Spacer(1, 0.3*inch))
        
        # Success Stories
        stories_list = report_data.get('success_stories', [])
        if stories_list:
            story.append(Paragraph("Success Stories", self.styles['PinkLemonadeHeading']))
            for idx, success_story in enumerate(stories_list[:5], 1):
                story.append(Paragraph(f"<b>Story {idx}:</b> {success_story}", 
                                     self.styles['PinkLemonadeBody']))
            story.append(Spacer(1, 0.3*inch))
        
        # Recommendations
        recommendations = report_data.get('recommendations', [])
        if recommendations:
            story.append(Paragraph("Recommendations", self.styles['PinkLemonadeHeading']))
            for rec in recommendations:
                story.append(Paragraph(f"• {rec}", self.styles['PinkLemonadeBody']))
        
        # Build PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def generate_case_support_pdf(self, case_data: Dict, org_name: str = "Organization") -> bytes:
        """Generate PDF of case for support"""
        if not REPORTLAB_AVAILABLE:
            return self._generate_basic_pdf(f"Case for Support - {org_name}", case_data)
        
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        
        # Title
        title = Paragraph("Case for Support", self.styles['PinkLemonadeTitle'])
        story.append(title)
        
        # Organization
        subtitle = Paragraph(f"<b>{org_name}</b><br/>Generated: {datetime.now().strftime('%B %d, %Y')}", 
                           self.styles['Normal'])
        story.append(subtitle)
        story.append(Spacer(1, 0.5*inch))
        
        # Campaign details
        campaign = case_data.get('campaign_details', {})
        if campaign:
            story.append(Paragraph("Campaign Overview", self.styles['PinkLemonadeHeading']))
            story.append(Paragraph(f"<b>Goal:</b> ${campaign.get('goal', 0):,}", 
                                 self.styles['PinkLemonadeBody']))
            story.append(Paragraph(f"<b>Purpose:</b> {campaign.get('purpose', 'N/A')}", 
                                 self.styles['PinkLemonadeBody']))
            story.append(Paragraph(f"<b>Timeline:</b> {campaign.get('timeline', 'N/A')}", 
                                 self.styles['PinkLemonadeBody']))
            story.append(Spacer(1, 0.3*inch))
        
        # Case sections
        for section in ['need_statement', 'solution', 'impact', 'call_to_action']:
            if case_data.get(section):
                heading = section.replace('_', ' ').title()
                story.append(Paragraph(heading, self.styles['PinkLemonadeHeading']))
                story.append(Paragraph(case_data[section], self.styles['PinkLemonadeBody']))
                story.append(Spacer(1, 0.2*inch))
        
        # Build PDF
        doc.build(story)
        pdf = buffer.getvalue()
        buffer.close()
        return pdf
    
    def _generate_basic_pdf(self, title: str, content: any) -> bytes:
        """Generate basic PDF without ReportLab"""
        # Create a simple text-based PDF
        pdf_content = f"""
%PDF-1.4
1 0 obj
<< /Type /Catalog /Pages 2 0 R >>
endobj
2 0 obj
<< /Type /Pages /Kids [3 0 R] /Count 1 >>
endobj
3 0 obj
<< /Type /Page /Parent 2 0 R /Resources 4 0 R /MediaBox [0 0 612 792] /Contents 5 0 R >>
endobj
4 0 obj
<< /Font << /F1 << /Type /Font /Subtype /Type1 /BaseFont /Helvetica >> >> >>
endobj
5 0 obj
<< /Length 200 >>
stream
BT
/F1 20 Tf
50 750 Td
({title}) Tj
0 -30 Td
/F1 12 Tf
(Content: {str(content)[:100]}...) Tj
ET
endstream
endobj
xref
0 6
0000000000 65535 f
0000000009 00000 n
0000000058 00000 n
0000000115 00000 n
0000000229 00000 n
0000000327 00000 n
trailer
<< /Size 6 /Root 1 0 R >>
startxref
565
%%EOF
"""
        return pdf_content.encode('utf-8')
    
    def export_to_html(self, content: Dict, title: str = "Export") -> str:
        """Export content as formatted HTML"""
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                h1 {{ color: #EC4899; }}
                h2 {{ color: #EC4899; margin-top: 30px; }}
                .header {{ text-align: center; margin-bottom: 40px; }}
                .content {{ line-height: 1.6; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #EC4899; color: white; }}
                .metric {{ background-color: #f9f9f9; padding: 10px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>{title}</h1>
                <p>Generated: {datetime.now().strftime('%B %d, %Y at %I:%M %p')}</p>
            </div>
            <div class="content">
        """
        
        # Add content based on type
        if isinstance(content, dict):
            for key, value in content.items():
                if value:
                    html += f"<h2>{key.replace('_', ' ').title()}</h2>"
                    if isinstance(value, str):
                        html += f"<p>{value}</p>"
                    elif isinstance(value, list):
                        html += "<ul>"
                        for item in value:
                            html += f"<li>{item}</li>"
                        html += "</ul>"
                    elif isinstance(value, dict):
                        html += '<div class="metric">'
                        for k, v in value.items():
                            html += f"<strong>{k}:</strong> {v}<br>"
                        html += "</div>"
        else:
            html += f"<p>{str(content)}</p>"
        
        html += """
            </div>
        </body>
        </html>
        """
        
        return html

# Singleton instance
_pdf_service = None

def get_pdf_service():
    """Get singleton PDF service"""
    global _pdf_service
    if _pdf_service is None:
        _pdf_service = PDFService()
    return _pdf_service