"""
Smart Templates Service for Phase 5
Handles AI-powered document generation and template management
"""

import os
import json
from datetime import datetime
from typing import Dict, List, Optional, Any
import openai
from sqlalchemy import func
from app import db
from app.models_templates import (
    SmartTemplate, GeneratedDocument, TemplateCategory,
    DocumentComment, ContentLibrary
)

class TemplateService:
    """Service for managing smart templates and document generation"""
    
    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            openai.api_key = self.api_key
    
    def get_templates(self, category_id: Optional[int] = None) -> List[Dict]:
        """Get all available templates"""
        query = SmartTemplate.query.filter_by(is_active=True)
        
        if category_id:
            query = query.filter_by(category_id=category_id)
        
        templates = query.order_by(SmartTemplate.times_used.desc()).all()
        
        return [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'category': t.category.name if t.category else None,
            'type': t.template_type,
            'typical_length': t.typical_length,
            'time_to_complete': t.time_to_complete,
            'difficulty_level': t.difficulty_level,
            'times_used': t.times_used,
            'success_rate': t.success_rate,
            'avg_rating': t.avg_rating,
            'is_premium': t.is_premium
        } for t in templates]
    
    def generate_document(self, template_id: int, user_id: int, 
                         organization_id: int, grant_id: Optional[int] = None,
                         custom_data: Optional[Dict] = None) -> Dict:
        """Generate a new document from a template"""
        
        template = SmartTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Get organization data for auto-filling
        from app.models import Organization
        org = Organization.query.get(organization_id)
        if not org:
            raise ValueError("Organization not found")
        
        # Get grant data if applicable
        grant_data = {}
        if grant_id:
            from app.models import Grant
            grant = Grant.query.get(grant_id)
            if grant:
                grant_data = {
                    'grant_name': grant.name,
                    'funder': grant.funder_name,
                    'amount': grant.amount,
                    'deadline': grant.deadline.strftime('%B %d, %Y') if grant.deadline else None
                }
        
        # Prepare document structure
        document_content = self._prepare_document_structure(
            template, org, grant_data, custom_data
        )
        
        # Generate AI content for each section
        if self.api_key:
            document_content = self._enhance_with_ai(
                template, document_content, org, grant_data
            )
        
        # Create the document record
        doc = GeneratedDocument(
            template_id=template_id,
            user_id=user_id,
            organization_id=organization_id,
            grant_id=grant_id,
            title=f"{template.name} - {datetime.now().strftime('%B %d, %Y')}",
            content=document_content,
            word_count=self._count_words(document_content),
            ai_enhanced=bool(self.api_key),
            completion_percentage=self._calculate_completion(document_content),
            status='draft'
        )
        
        db.session.add(doc)
        
        # Update template usage stats
        template.times_used += 1
        
        db.session.commit()
        
        return {
            'id': doc.id,
            'title': doc.title,
            'content': doc.content,
            'word_count': doc.word_count,
            'completion_percentage': doc.completion_percentage,
            'status': doc.status,
            'ai_enhanced': doc.ai_enhanced
        }
    
    def _prepare_document_structure(self, template: SmartTemplate, 
                                   org: Any, grant_data: Dict,
                                   custom_data: Optional[Dict]) -> Dict:
        """Prepare the initial document structure with auto-filled data"""
        
        structure = template.structure or {}
        default_content = template.default_content or {}
        
        # Auto-fill organization data
        org_data = {
            'organization_name': org.name,
            'mission_statement': org.mission_statement,
            'description': org.description,
            'website': org.website,
            'ein': getattr(org, 'ein', ''),
            'annual_budget': getattr(org, 'annual_budget', ''),
            'staff_size': getattr(org, 'staff_size', ''),
            'year_founded': getattr(org, 'year_founded', '')
        }
        
        # Merge all data sources
        data = {**org_data, **grant_data, **(custom_data or {})}
        
        # Build document sections
        document = {}
        for section_key, section_config in structure.items():
            section = {
                'title': section_config.get('title', ''),
                'required': section_config.get('required', False),
                'max_words': section_config.get('max_words'),
                'content': ''
            }
            
            # Add default content if available
            if section_key in default_content:
                section['content'] = self._fill_template_vars(
                    default_content[section_key], data
                )
            
            document[section_key] = section
        
        return document
    
    def _enhance_with_ai(self, template: SmartTemplate, document: Dict,
                        org: Any, grant_data: Dict) -> Dict:
        """Use AI to generate or enhance document content"""
        
        if not self.api_key:
            return document
        
        ai_prompts = template.ai_prompts or {}
        
        for section_key, section in document.items():
            if section_key in ai_prompts and not section.get('content'):
                try:
                    # Generate content using AI
                    prompt = self._build_ai_prompt(
                        ai_prompts[section_key],
                        org, grant_data, section
                    )
                    
                    response = openai.ChatCompletion.create(
                        model="gpt-4o",
                        messages=[
                            {"role": "system", "content": "You are an expert grant writer creating compelling, professional content for nonprofit organizations."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=section.get('max_words', 500) * 2  # Approximate tokens
                    )
                    
                    section['content'] = response.choices[0].message['content'].strip()
                    section['ai_generated'] = True
                    
                except Exception as e:
                    print(f"AI generation error for section {section_key}: {e}")
                    section['ai_error'] = str(e)
        
        return document
    
    def _build_ai_prompt(self, prompt_template: str, org: Any, 
                        grant_data: Dict, section: Dict) -> str:
        """Build AI prompt with context"""
        
        context = f"""
        Organization: {org.name}
        Mission: {org.mission_statement}
        Description: {org.description}
        """
        
        if grant_data:
            context += f"""
            Grant: {grant_data.get('grant_name', 'N/A')}
            Funder: {grant_data.get('funder', 'N/A')}
            Amount: ${grant_data.get('amount', 'N/A')}
            """
        
        if section.get('max_words'):
            context += f"\nMaximum length: {section['max_words']} words"
        
        return f"{context}\n\n{prompt_template}"
    
    def _fill_template_vars(self, text: str, data: Dict) -> str:
        """Replace template variables with actual data"""
        for key, value in data.items():
            text = text.replace(f"{{{{{key}}}}}", str(value) if value else '')
        return text
    
    def _count_words(self, document: Dict) -> int:
        """Count total words in document"""
        total = 0
        for section in document.values():
            if isinstance(section, dict) and 'content' in section:
                total += len(section['content'].split())
        return total
    
    def _calculate_completion(self, document: Dict) -> float:
        """Calculate document completion percentage"""
        total_sections = 0
        completed_sections = 0
        
        for section in document.values():
            if isinstance(section, dict):
                total_sections += 1
                if section.get('content'):
                    completed_sections += 1
        
        return (completed_sections / total_sections * 100) if total_sections > 0 else 0
    
    def update_document(self, document_id: int, updates: Dict, user_id: int, organization_id: int) -> Dict:
        """Update an existing document with organization validation"""
        
        doc = GeneratedDocument.query.get(document_id)
        if not doc:
            raise ValueError("Document not found or access denied")
        
        # Validate organization ownership
        if doc.organization_id != organization_id:
            # Check if user is admin
            from app.models import User
            user = User.query.get(user_id)
            if not user or not (hasattr(user, 'role') and user.role == 'admin'):
                raise ValueError("Document not found or access denied")
        
        # Update content
        if 'content' in updates:
            doc.content = updates['content']
            doc.word_count = self._count_words(updates['content'])
            doc.completion_percentage = self._calculate_completion(updates['content'])
        
        # Update metadata
        if 'title' in updates:
            doc.title = updates['title']
        if 'status' in updates:
            doc.status = updates['status']
            if updates['status'] == 'submitted':
                doc.submitted_at = datetime.utcnow()
        
        doc.last_edited_by = user_id
        doc.updated_at = datetime.utcnow()
        
        # Increment version if major change
        if updates.get('create_version'):
            new_version = GeneratedDocument(
                template_id=doc.template_id,
                user_id=user_id,
                grant_id=doc.grant_id,
                organization_id=doc.organization_id,
                title=doc.title,
                content=doc.content,
                version=doc.version + 1,
                parent_document_id=doc.id,
                status=doc.status
            )
            db.session.add(new_version)
        
        db.session.commit()
        
        return {
            'id': doc.id,
            'title': doc.title,
            'content': doc.content,
            'word_count': doc.word_count,
            'completion_percentage': doc.completion_percentage,
            'status': doc.status,
            'updated_at': doc.updated_at.isoformat()
        }
    
    def get_document(self, document_id: int, user_id: int, organization_id: int) -> Dict:
        """Get a specific document with organization validation"""
        
        doc = GeneratedDocument.query.get(document_id)
        if not doc:
            raise ValueError("Document not found or access denied")
        
        # Validate organization ownership
        if doc.organization_id != organization_id:
            # Check if user is admin
            from app.models import User
            user = User.query.get(user_id)
            if not user or not (hasattr(user, 'role') and user.role == 'admin'):
                raise ValueError("Document not found or access denied")
        
        return {
            'id': doc.id,
            'template_id': doc.template_id,
            'template_name': doc.template.name if doc.template else None,
            'title': doc.title,
            'content': doc.content,
            'word_count': doc.word_count,
            'completion_percentage': doc.completion_percentage,
            'status': doc.status,
            'ai_enhanced': doc.ai_enhanced,
            'created_at': doc.created_at.isoformat(),
            'updated_at': doc.updated_at.isoformat(),
            'versions': len(doc.versions),
            'comments': doc.comments.count(),
            'organization_id': doc.organization_id
        }
    
    def get_user_documents(self, user_id: int, status: Optional[str] = None) -> List[Dict]:
        """Get all documents for a user"""
        
        query = GeneratedDocument.query.filter_by(user_id=user_id)
        
        if status:
            query = query.filter_by(status=status)
        
        documents = query.order_by(GeneratedDocument.updated_at.desc()).all()
        
        return [{
            'id': doc.id,
            'title': doc.title,
            'template_name': doc.template.name if doc.template else None,
            'grant_name': doc.grant.name if doc.grant else None,
            'status': doc.status,
            'completion_percentage': doc.completion_percentage,
            'word_count': doc.word_count,
            'updated_at': doc.updated_at.isoformat()
        } for doc in documents]
    
    def add_content_to_library(self, organization_id: int, title: str,
                              content_type: str, content: str,
                              tags: Optional[List[str]] = None) -> Dict:
        """Add reusable content to library"""
        
        library_item = ContentLibrary(
            organization_id=organization_id,
            title=title,
            content_type=content_type,
            content=content,
            tags=tags or []
        )
        
        db.session.add(library_item)
        db.session.commit()
        
        return {
            'id': library_item.id,
            'title': library_item.title,
            'content_type': library_item.content_type,
            'content': library_item.content,
            'tags': library_item.tags
        }
    
    def get_library_content(self, organization_id: int, 
                           content_type: Optional[str] = None) -> List[Dict]:
        """Get content from library"""
        
        query = ContentLibrary.query.filter_by(organization_id=organization_id)
        
        if content_type:
            query = query.filter_by(content_type=content_type)
        
        items = query.order_by(ContentLibrary.times_used.desc()).all()
        
        return [{
            'id': item.id,
            'title': item.title,
            'content_type': item.content_type,
            'content': item.content,
            'tags': item.tags,
            'times_used': item.times_used,
            'is_favorite': item.is_favorite
        } for item in items]
    
    # ============= SMART TOOLS TEMPLATE METHODS =============
    
    def save_smart_tools_template(self, tool_type: str, name: str, description: str,
                                  generated_content: str, input_parameters: Dict,
                                  organization_id: int, user_id: int,
                                  tags: List[str] = None, focus_areas: List[str] = None,
                                  funder_types: List[str] = None, is_shared: bool = False) -> Dict:
        """Save Smart Tools generated content as a template"""
        
        template = SmartTemplate(
            name=name,
            description=description,
            template_type=tool_type,  # For backwards compatibility
            tool_type=tool_type,      # Smart Tools specific field
            generated_content=generated_content,
            input_parameters=input_parameters,
            organization_id=organization_id,
            created_by_user_id=user_id,
            tags=tags or [],
            focus_areas=focus_areas or [],
            funder_types=funder_types or [],
            is_shared=is_shared,
            is_active=True,
            times_used=0,
            success_rate=0.0,
            avg_rating=0.0
        )
        
        db.session.add(template)
        db.session.commit()
        
        return {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'tool_type': template.tool_type,
            'tags': template.tags,
            'focus_areas': template.focus_areas,
            'funder_types': template.funder_types,
            'times_used': template.times_used,
            'created_at': template.created_at.isoformat(),
            'is_shared': template.is_shared
        }
    
    def get_smart_tools_templates(self, organization_id: int, tool_type: str = None,
                                  tags: List[str] = None, focus_areas: List[str] = None,
                                  funder_types: List[str] = None) -> List[Dict]:
        """Get templates filtered for Smart Tools"""
        
        # Start with templates for this organization or shared templates
        query = SmartTemplate.query.filter(
            db.or_(
                SmartTemplate.organization_id == organization_id,
                SmartTemplate.is_shared == True
            )
        ).filter_by(is_active=True)
        
        # Filter by tool type if specified
        if tool_type:
            query = query.filter_by(tool_type=tool_type)
        
        # Filter by tags if specified
        if tags:
            for tag in tags:
                query = query.filter(SmartTemplate.tags.contains([tag]))
        
        # Filter by focus areas if specified  
        if focus_areas:
            for area in focus_areas:
                query = query.filter(SmartTemplate.focus_areas.contains([area]))
        
        # Filter by funder types if specified
        if funder_types:
            for funder_type in funder_types:
                query = query.filter(SmartTemplate.funder_types.contains([funder_type]))
        
        templates = query.order_by(SmartTemplate.times_used.desc(), SmartTemplate.created_at.desc()).all()
        
        return [{
            'id': t.id,
            'name': t.name,
            'description': t.description,
            'tool_type': t.tool_type,
            'tags': t.tags or [],
            'focus_areas': t.focus_areas or [],
            'funder_types': t.funder_types or [],
            'times_used': t.times_used,
            'success_rate': t.success_rate,
            'avg_rating': t.avg_rating,
            'created_at': t.created_at.isoformat(),
            'last_used_at': t.last_used_at.isoformat() if t.last_used_at else None,
            'is_shared': t.is_shared,
            'created_by_same_org': t.organization_id == organization_id,
            'preview': t.generated_content[:200] + '...' if t.generated_content and len(t.generated_content) > 200 else t.generated_content
        } for t in templates]
    
    def get_template_parameters(self, template_id: int) -> Dict:
        """Get input parameters from a template for prefilling Smart Tools forms"""
        
        template = SmartTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        return {
            'id': template.id,
            'name': template.name,
            'description': template.description,
            'tool_type': template.tool_type,
            'input_parameters': template.input_parameters or {},
            'tags': template.tags or [],
            'focus_areas': template.focus_areas or [],
            'funder_types': template.funder_types or [],
            'generated_content': template.generated_content
        }
    
    def delete_smart_tools_template(self, template_id: int, user_id: int):
        """Delete a Smart Tools template (only if user created it)"""
        
        template = SmartTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        # Check if user has permission to delete (created by user or admin)
        if template.created_by_user_id != user_id:
            raise ValueError("Permission denied - can only delete your own templates")
        
        # Soft delete by setting is_active to False
        template.is_active = False
        db.session.commit()
    
    def mark_template_used(self, template_id: int):
        """Mark template as used and update usage statistics"""
        
        template = SmartTemplate.query.get(template_id)
        if not template:
            raise ValueError("Template not found")
        
        template.times_used += 1
        template.last_used_at = datetime.utcnow()
        
        # Update success rate (could be calculated based on feedback later)
        # For now, just maintain the existing rate
        
        db.session.commit()