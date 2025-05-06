import os
import re
import json
import logging
from datetime import datetime
import tempfile
import PyPDF2
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

def parse_grant_data(data):
    """
    Parse and validate grant data, ensuring it has the required fields
    and appropriate formats
    
    Args:
        data (dict): The raw grant data
        
    Returns:
        dict: The processed grant data
    """
    processed = {}
    
    # Required fields
    processed['title'] = data.get('title', '').strip()
    processed['funder'] = data.get('funder', '').strip()
    
    # Optional fields with defaults
    processed['description'] = data.get('description', '').strip()
    processed['eligibility'] = data.get('eligibility', '').strip()
    processed['website'] = data.get('website', '').strip()
    processed['status'] = data.get('status', 'Not Started')
    processed['notes'] = data.get('notes', '').strip()
    processed['contact_info'] = data.get('contact_info', '').strip()
    
    # Process due date
    due_date = data.get('due_date')
    if due_date:
        try:
            if isinstance(due_date, str):
                # Try to parse the date string
                processed['due_date'] = datetime.strptime(due_date, '%Y-%m-%d').date()
            elif isinstance(due_date, datetime):
                processed['due_date'] = due_date.date()
            else:
                processed['due_date'] = None
        except (ValueError, TypeError):
            processed['due_date'] = None
    else:
        processed['due_date'] = None
    
    # Process amount
    amount = data.get('amount')
    if amount:
        try:
            if isinstance(amount, str):
                # Remove currency symbols and commas
                amount = re.sub(r'[$,£€]', '', amount)
                processed['amount'] = float(amount)
            elif isinstance(amount, (int, float)):
                processed['amount'] = float(amount)
            else:
                processed['amount'] = None
        except (ValueError, TypeError):
            processed['amount'] = None
    else:
        processed['amount'] = None
    
    # Process focus areas
    focus_areas = data.get('focus_areas', [])
    if isinstance(focus_areas, str):
        # Split by commas if it's a string
        processed['focus_areas'] = [area.strip() for area in focus_areas.split(',')]
    elif isinstance(focus_areas, list):
        processed['focus_areas'] = focus_areas
    else:
        processed['focus_areas'] = []
    
    # Process match score
    match_score = data.get('match_score')
    if match_score is not None:
        try:
            processed['match_score'] = float(match_score)
        except (ValueError, TypeError):
            processed['match_score'] = 0
    else:
        processed['match_score'] = 0
    
    return processed

def extract_text_from_pdf(pdf_bytes):
    """
    Extract text from a PDF file
    
    Args:
        pdf_bytes (bytes): The PDF file content
        
    Returns:
        str: The extracted text
    """
    try:
        with tempfile.NamedTemporaryFile(delete=False) as temp:
            temp.write(pdf_bytes)
            temp_path = temp.name
        
        text = ""
        with open(temp_path, 'rb') as f:
            pdf_reader = PyPDF2.PdfReader(f)
            for page_num in range(len(pdf_reader.pages)):
                page = pdf_reader.pages[page_num]
                text += page.extract_text() + "\n\n"
        
        # Clean up
        os.unlink(temp_path)
        
        return text
    
    except Exception as e:
        logger.error(f"Error extracting text from PDF: {str(e)}")
        return ""

def format_currency(amount):
    """
    Format a number as currency
    
    Args:
        amount (float): The amount to format
        
    Returns:
        str: The formatted currency string
    """
    if amount is None:
        return "N/A"
    
    return f"${amount:,.2f}"

def format_date(date_obj):
    """
    Format a date object as a readable string
    
    Args:
        date_obj (date): The date to format
        
    Returns:
        str: The formatted date string
    """
    if date_obj is None:
        return "N/A"
    
    return date_obj.strftime("%B %d, %Y")

def get_date_status(due_date):
    """
    Get the status of a date relative to today
    
    Args:
        due_date (date): The date to check
        
    Returns:
        str: 'past', 'soon', or 'future'
    """
    if due_date is None:
        return "unknown"
    
    today = datetime.now().date()
    
    if due_date < today:
        return "past"
    elif (due_date - today).days <= 14:
        return "soon"
    else:
        return "future"

def is_valid_url(url):
    """
    Check if a URL is valid
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if valid, False otherwise
    """
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False
