"""
Document Upload System for Grant Applications
Handles file uploads, storage, and retrieval
"""
from flask import Blueprint, jsonify, request, send_file
from werkzeug.utils import secure_filename
import os
import uuid
from datetime import datetime
from app import db
from app.models import GrantDocument
import logging

logger = logging.getLogger(__name__)
bp = Blueprint('document_uploads', __name__)

# Configure upload settings
UPLOAD_FOLDER = 'uploads/grant_documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt', 'xls', 'xlsx', 'png', 'jpg', 'jpeg'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@bp.route('/api/documents/upload', methods=['POST'])
def upload_document():
    """
    Upload a document for a grant application
    """
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        grant_id = request.form.get('grant_id', type=int)
        document_type = request.form.get('document_type', 'general')
        description = request.form.get('description', '')
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': f'File type not allowed. Allowed types: {", ".join(ALLOWED_EXTENSIONS)}'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size: {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Generate unique filename
        original_filename = secure_filename(file.filename)
        unique_id = str(uuid.uuid4())[:8]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{timestamp}_{unique_id}_{original_filename}"
        
        # Create grant-specific folder
        if grant_id:
            grant_folder = os.path.join(UPLOAD_FOLDER, f"grant_{grant_id}")
            os.makedirs(grant_folder, exist_ok=True)
            file_path = os.path.join(grant_folder, filename)
        else:
            file_path = os.path.join(UPLOAD_FOLDER, filename)
        
        # Save file
        file.save(file_path)
        
        # Save to database
        doc = GrantDocument(
            grant_id=grant_id,
            filename=original_filename,
            file_path=file_path,
            file_size=file_size,
            document_type=document_type,
            description=description,
            uploaded_by=1  # Default user ID
        )
        db.session.add(doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'document_id': doc.id,
            'filename': original_filename,
            'size': file_size,
            'type': document_type,
            'uploaded_at': doc.uploaded_at.isoformat() if doc.uploaded_at else None
        })
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/documents/grant/<int:grant_id>', methods=['GET'])
def get_grant_documents(grant_id):
    """
    Get all documents for a specific grant
    """
    try:
        documents = GrantDocument.query.filter_by(grant_id=grant_id).all()
        
        return jsonify({
            'success': True,
            'documents': [doc.to_dict() for doc in documents],
            'total': len(documents)
        })
        
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """
    Delete a document
    """
    try:
        doc = GrantDocument.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete file from filesystem
        if os.path.exists(doc.file_path):
            os.remove(doc.file_path)
        
        # Delete from database
        db.session.delete(doc)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': 'Document deleted successfully'
        })
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/api/documents/<int:doc_id>/download', methods=['GET'])
def download_document(doc_id):
    """
    Download a document
    """
    try:
        doc = GrantDocument.query.get(doc_id)
        if not doc:
            return jsonify({'error': 'Document not found'}), 404
        
        if not os.path.exists(doc.file_path):
            return jsonify({'error': 'File not found on server'}), 404
        
        return send_file(
            doc.file_path,
            as_attachment=True,
            download_name=doc.filename
        )
        
    except Exception as e:
        logger.error(f"Error downloading document: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/api/documents/types', methods=['GET'])
def get_document_types():
    """
    Get available document types
    """
    return jsonify({
        'types': [
            {'value': 'proposal', 'label': 'Grant Proposal'},
            {'value': 'budget', 'label': 'Budget Document'},
            {'value': 'letter_of_support', 'label': 'Letter of Support'},
            {'value': 'financial_statement', 'label': 'Financial Statement'},
            {'value': '501c3', 'label': '501(c)(3) Certificate'},
            {'value': 'board_list', 'label': 'Board Member List'},
            {'value': 'audit', 'label': 'Audit Report'},
            {'value': 'other', 'label': 'Other Document'}
        ]
    })