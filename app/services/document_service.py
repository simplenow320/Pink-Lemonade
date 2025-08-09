"""
Document Management Service
Handles document uploads and attachments for grants
"""
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from werkzeug.utils import secure_filename
from app.models import GrantDocument
from app import db
import logging

logger = logging.getLogger(__name__)

class DocumentService:
    """Manages document uploads and attachments"""
    
    ALLOWED_EXTENSIONS = {
        'pdf', 'doc', 'docx', 'txt', 'rtf', 
        'xls', 'xlsx', 'csv',
        'png', 'jpg', 'jpeg', 'gif',
        'zip'
    }
    
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    
    def __init__(self, upload_folder: str = 'uploads/documents'):
        self.upload_folder = upload_folder
        os.makedirs(upload_folder, exist_ok=True)
    
    def allowed_file(self, filename: str) -> bool:
        """Check if file extension is allowed"""
        return '.' in filename and \
            filename.rsplit('.', 1)[1].lower() in self.ALLOWED_EXTENSIONS
    
    def generate_unique_filename(self, original_filename: str) -> str:
        """Generate a unique filename to prevent collisions"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(secure_filename(original_filename))
        random_hash = hashlib.md5(f"{timestamp}{name}".encode()).hexdigest()[:8]
        return f"{timestamp}_{random_hash}{ext}"
    
    def save_document(self, file, grant_id: int, document_type: str, 
                     description: str = None, user_id: int = None) -> Dict:
        """
        Save a document and create database record
        """
        try:
            if not file:
                return {'success': False, 'error': 'No file provided'}
            
            if not self.allowed_file(file.filename):
                return {'success': False, 'error': 'File type not allowed'}
            
            # Check file size
            file.seek(0, os.SEEK_END)
            file_size = file.tell()
            file.seek(0)
            
            if file_size > self.MAX_FILE_SIZE:
                return {'success': False, 'error': f'File size exceeds {self.MAX_FILE_SIZE/1024/1024}MB limit'}
            
            # Generate unique filename and save
            unique_filename = self.generate_unique_filename(file.filename)
            file_path = os.path.join(self.upload_folder, unique_filename)
            file.save(file_path)
            
            # Create database record
            document = GrantDocument()
            document.grant_id = grant_id
            document.filename = file.filename
            document.file_path = file_path
            document.file_size = file_size
            document.document_type = document_type
            document.description = description
            document.uploaded_by = user_id
            document.uploaded_at = datetime.now()
            
            db.session.add(document)
            db.session.commit()
            
            return {
                'success': True,
                'document_id': document.id,
                'filename': document.filename,
                'size': file_size,
                'type': document_type
            }
            
        except Exception as e:
            logger.error(f"Error saving document: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_grant_documents(self, grant_id: int) -> List[Dict]:
        """
        Get all documents for a grant
        """
        try:
            documents = GrantDocument.query.filter_by(grant_id=grant_id)\
                .order_by(GrantDocument.uploaded_at.desc()).all()
            
            doc_list = []
            for doc in documents:
                doc_list.append({
                    'id': doc.id,
                    'filename': doc.filename,
                    'document_type': doc.document_type,
                    'description': doc.description,
                    'file_size': doc.file_size,
                    'uploaded_by': doc.uploaded_by,
                    'uploaded_at': doc.uploaded_at.isoformat()
                })
            
            return doc_list
            
        except Exception as e:
            logger.error(f"Error getting documents for grant {grant_id}: {e}")
            return []
    
    def delete_document(self, document_id: int) -> Dict:
        """
        Delete a document
        """
        try:
            document = GrantDocument.query.get(document_id)
            if not document:
                return {'success': False, 'error': 'Document not found'}
            
            # Delete physical file
            if os.path.exists(document.file_path):
                os.remove(document.file_path)
            
            # Delete database record
            db.session.delete(document)
            db.session.commit()
            
            return {'success': True, 'document_id': document_id}
            
        except Exception as e:
            logger.error(f"Error deleting document {document_id}: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_document_stats(self, grant_id: int) -> Dict:
        """
        Get document statistics for a grant
        """
        try:
            documents = GrantDocument.query.filter_by(grant_id=grant_id).all()
            
            total_size = sum(doc.file_size for doc in documents)
            doc_types = {}
            
            for doc in documents:
                doc_type = doc.document_type or 'other'
                if doc_type not in doc_types:
                    doc_types[doc_type] = 0
                doc_types[doc_type] += 1
            
            return {
                'total_documents': len(documents),
                'total_size': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'document_types': doc_types
            }
            
        except Exception as e:
            logger.error(f"Error getting document stats: {e}")
            return {}

# Singleton instance
document_service = DocumentService()