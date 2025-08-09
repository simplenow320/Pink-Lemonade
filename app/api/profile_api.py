"""
Profile API endpoints for user and document management
"""

from flask import Blueprint, request, jsonify, send_file
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import json
from app import db
from app.models import Organization
from app.models import Grant
import logging

logger = logging.getLogger(__name__)

bp = Blueprint('profile_api', __name__, url_prefix='/api/profile')

# Configure upload settings
UPLOAD_FOLDER = 'uploads/documents'
ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# User profile endpoints
@bp.route('/user', methods=['GET'])
def get_user_profile():
    """Get current user profile"""
    try:
        # For now, return mock user data
        # In production, this would get the authenticated user
        user_data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@nitrogennetwork.org',
            'phone': '(555) 123-4567',
            'title': 'Grant Manager'
        }
        
        return jsonify(user_data)
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/user', methods=['POST'])
def update_user_profile():
    """Update user profile"""
    try:
        data = request.json
        
        # In production, this would update the authenticated user
        # For now, just return success
        logger.info(f"User profile update: {data}")
        
        return jsonify({'message': 'User profile updated successfully'})
    except Exception as e:
        logger.error(f"Error updating user profile: {e}")
        return jsonify({'error': str(e)}), 500

# Document management endpoints
@bp.route('/documents', methods=['GET'])
def get_documents():
    """Get all uploaded documents for the organization"""
    try:
        # Get organization
        org = Organization.query.first()
        if not org:
            return jsonify([])
        
        # Get documents from org's documents field
        documents = org.documents if hasattr(org, 'documents') else []
        
        # If documents is a string, try to parse it as JSON
        if isinstance(documents, str):
            try:
                documents = json.loads(documents)
            except:
                documents = []
        
        return jsonify(documents)
    except Exception as e:
        logger.error(f"Error getting documents: {e}")
        return jsonify([])

@bp.route('/documents', methods=['POST'])
def upload_document():
    """Upload a new document"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'File type not allowed'}), 400
        
        # Check file size
        file.seek(0, os.SEEK_END)
        file_size = file.tell()
        file.seek(0)
        
        if file_size > MAX_FILE_SIZE:
            return jsonify({'error': 'File too large (max 10MB)'}), 400
        
        # Save file
        filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_filename = f"{timestamp}_{filename}"
        filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
        
        file.save(filepath)
        
        # Get organization
        org = Organization.query.first()
        if not org:
            # Create default organization if none exists
            org = Organization(
                name='My Organization',
                mission='',
                created_at=datetime.now()
            )
            db.session.add(org)
        
        # Add document to organization
        document = {
            'id': len(org.documents) + 1 if hasattr(org, 'documents') and org.documents else 1,
            'name': filename,
            'path': filepath,
            'size': file_size,
            'uploaded_at': datetime.now().isoformat(),
            'type': filename.rsplit('.', 1)[1].lower()
        }
        
        # Update documents list
        if hasattr(org, 'documents'):
            if isinstance(org.documents, str):
                try:
                    documents = json.loads(org.documents)
                except:
                    documents = []
            else:
                documents = org.documents or []
        else:
            documents = []
        
        documents.append(document)
        
        # Store as JSON string in database
        org.documents = json.dumps(documents)
        db.session.commit()
        
        logger.info(f"Document uploaded: {filename}")
        return jsonify(document)
        
    except Exception as e:
        logger.error(f"Error uploading document: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/documents/<int:doc_id>', methods=['DELETE'])
def delete_document(doc_id):
    """Delete a specific document"""
    try:
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get documents
        if hasattr(org, 'documents'):
            if isinstance(org.documents, str):
                try:
                    documents = json.loads(org.documents)
                except:
                    documents = []
            else:
                documents = org.documents or []
        else:
            documents = []
        
        # Find and remove document
        document_to_delete = None
        for doc in documents:
            if doc.get('id') == doc_id:
                document_to_delete = doc
                documents.remove(doc)
                break
        
        if not document_to_delete:
            return jsonify({'error': 'Document not found'}), 404
        
        # Delete file from filesystem
        try:
            if os.path.exists(document_to_delete['path']):
                os.remove(document_to_delete['path'])
        except Exception as e:
            logger.warning(f"Could not delete file: {e}")
        
        # Update database
        org.documents = json.dumps(documents)
        db.session.commit()
        
        logger.info(f"Document deleted: {document_to_delete['name']}")
        return jsonify({'message': 'Document deleted successfully'})
        
    except Exception as e:
        logger.error(f"Error deleting document: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/documents', methods=['DELETE'])
def clear_all_documents():
    """Delete all documents"""
    try:
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Get documents
        if hasattr(org, 'documents'):
            if isinstance(org.documents, str):
                try:
                    documents = json.loads(org.documents)
                except:
                    documents = []
            else:
                documents = org.documents or []
        else:
            documents = []
        
        # Delete all files
        for doc in documents:
            try:
                if os.path.exists(doc['path']):
                    os.remove(doc['path'])
            except Exception as e:
                logger.warning(f"Could not delete file: {e}")
        
        # Clear documents in database
        org.documents = json.dumps([])
        db.session.commit()
        
        logger.info("All documents cleared")
        return jsonify({'message': 'All documents cleared successfully'})
        
    except Exception as e:
        logger.error(f"Error clearing documents: {e}")
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/export', methods=['GET'])
def export_profile():
    """Export complete profile as JSON"""
    try:
        # Get organization
        org = Organization.query.first()
        if not org:
            return jsonify({'error': 'Organization not found'}), 404
        
        # Prepare export data
        export_data = {
            'organization': org.to_dict(),
            'user': {
                'first_name': 'John',
                'last_name': 'Doe',
                'email': 'john@nitrogennetwork.org',
                'phone': '(555) 123-4567',
                'title': 'Grant Manager'
            },
            'documents_count': len(json.loads(org.documents)) if hasattr(org, 'documents') and org.documents else 0,
            'export_date': datetime.now().isoformat()
        }
        
        # Create JSON file
        export_filename = f"profile_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        export_path = os.path.join(UPLOAD_FOLDER, export_filename)
        
        with open(export_path, 'w') as f:
            json.dump(export_data, f, indent=2, default=str)
        
        return send_file(export_path, as_attachment=True, download_name=export_filename)
        
    except Exception as e:
        logger.error(f"Error exporting profile: {e}")
        return jsonify({'error': str(e)}), 500

@bp.route('/context', methods=['GET'])
def get_ai_context():
    """Get the AI context built from profile and documents"""
    try:
        org = Organization.query.first()
        if not org:
            return jsonify({'context': 'No organization profile available'})
        
        # Build context from organization data
        context_parts = []
        
        if org.name:
            context_parts.append(f"Organization: {org.name}")
        
        if org.mission:
            context_parts.append(f"Mission: {org.mission}")
        
        if hasattr(org, 'focus_areas') and org.focus_areas:
            areas = org.focus_areas if isinstance(org.focus_areas, list) else [org.focus_areas]
            context_parts.append(f"Focus Areas: {', '.join(areas)}")
        
        if hasattr(org, 'location') and org.location:
            context_parts.append(f"Location: {org.location}")
        
        if hasattr(org, 'keywords') and org.keywords:
            keywords = org.keywords if isinstance(org.keywords, list) else [org.keywords]
            context_parts.append(f"Keywords: {', '.join(keywords)}")
        
        # Add document count
        if hasattr(org, 'documents') and org.documents:
            doc_count = len(json.loads(org.documents)) if isinstance(org.documents, str) else len(org.documents)
            context_parts.append(f"Supporting Documents: {doc_count} uploaded")
        
        context = '\n'.join(context_parts)
        
        return jsonify({
            'context': context,
            'enhanced': len(context_parts) > 3  # Consider profile enhanced if it has more than basic info
        })
        
    except Exception as e:
        logger.error(f"Error getting AI context: {e}")
        return jsonify({'error': str(e)}), 500