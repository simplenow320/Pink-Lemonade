from __future__ import annotations
from typing import Optional
import os, io, tempfile
from flask import send_file, Response
from app.services.text_utils import md_to_plain

# Try to import optional dependencies
try:
    from docx import Document
    HAS_DOCX = True
except ImportError:
    HAS_DOCX = False

try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.units import inch
    HAS_REPORTLAB = True
except ImportError:
    HAS_REPORTLAB = False

def export_docx(md_text: str, download_name: str = "document.docx"):
    if not HAS_DOCX:
        # Fallback: return plain text as .txt file
        plain = md_to_plain(md_text) or "Empty document"
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt")
        tmp.write(plain)
        tmp.flush()
        txt_name = download_name.replace('.docx', '.txt')
        return send_file(tmp.name, as_attachment=True, download_name=txt_name, mimetype="text/plain")
    
    plain = md_to_plain(md_text) or "Empty document"
    doc = Document()
    for line in plain.splitlines():
        doc.add_paragraph(line)
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".docx")
    doc.save(tmp.name)
    tmp.flush()
    return send_file(tmp.name, as_attachment=True, download_name=download_name, mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

def export_pdf(md_text: str, download_name: str = "document.pdf"):
    if not HAS_REPORTLAB:
        # Fallback: return plain text as .txt file
        plain = md_to_plain(md_text) or "Empty document"
        tmp = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix=".txt")
        tmp.write(plain)
        tmp.flush()
        txt_name = download_name.replace('.pdf', '.txt')
        return send_file(tmp.name, as_attachment=True, download_name=txt_name, mimetype="text/plain")
    
    plain = md_to_plain(md_text) or "Empty document"
    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".pdf")
    c = canvas.Canvas(tmp.name, pagesize=letter)
    width, height = letter
    left = 1.0 * inch
    top = height - 1.0 * inch
    max_width = width - 2.0 * inch
    y = top
    for paragraph in plain.splitlines():
        # simple wrap: split very long lines
        words = paragraph.split(' ')
        line = ""
        for w in words:
            test = (line + " " + w).strip()
            if c.stringWidth(test, "Times-Roman", 11) > max_width:
                c.drawString(left, y, line)
                y -= 14
                line = w
                if y < 1.0 * inch:
                    c.showPage()
                    y = top
            else:
                line = test
        if line:
            c.drawString(left, y, line)
            y -= 14
            if y < 1.0 * inch:
                c.showPage()
                y = top
        # paragraph spacing
        y -= 6
        if y < 1.0 * inch:
            c.showPage()
            y = top
    c.save()
    return send_file(tmp.name, as_attachment=True, download_name=download_name, mimetype="application/pdf")

def export_content(md_text: str, fmt: str, base_name: str):
    fmt = (fmt or "").lower()
    base = base_name.replace(" ", "_")
    if fmt == "pdf":
        return export_pdf(md_text, f"{base}.pdf")
    elif fmt in ("docx","doc"):
        return export_docx(md_text, f"{base}.docx")
    else:
        # default to docx
        return export_docx(md_text, f"{base}.docx")