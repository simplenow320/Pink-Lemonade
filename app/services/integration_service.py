"""
Advanced Integration Service
Calendar, CRM, and Document Management
"""

from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
import json
import hashlib
import mimetypes

logger = logging.getLogger(__name__)

class IntegrationService:
    """
    Manages advanced integrations:
    - Calendar synchronization
    - CRM connections
    - Document management
    - Email integration
    - Cloud storage
    """
    
    # Supported integrations
    INTEGRATIONS = {
        'calendar': {
            'google_calendar': {
                'name': 'Google Calendar',
                'features': ['sync_deadlines', 'create_events', 'reminders'],
                'oauth': True
            },
            'outlook_calendar': {
                'name': 'Outlook Calendar',
                'features': ['sync_deadlines', 'create_events', 'reminders'],
                'oauth': True
            },
            'ical': {
                'name': 'iCal Feed',
                'features': ['export_feed', 'subscribe'],
                'oauth': False
            }
        },
        'crm': {
            'salesforce': {
                'name': 'Salesforce',
                'features': ['sync_contacts', 'opportunity_tracking', 'custom_fields'],
                'oauth': True
            },
            'hubspot': {
                'name': 'HubSpot',
                'features': ['sync_contacts', 'deal_pipeline', 'activity_logging'],
                'oauth': True
            },
            'pipedrive': {
                'name': 'Pipedrive',
                'features': ['sync_contacts', 'deal_tracking', 'activity_sync'],
                'oauth': True
            }
        },
        'documents': {
            'google_drive': {
                'name': 'Google Drive',
                'features': ['store_documents', 'collaborative_editing', 'version_control'],
                'oauth': True
            },
            'dropbox': {
                'name': 'Dropbox',
                'features': ['store_documents', 'file_sharing', 'backup'],
                'oauth': True
            },
            'sharepoint': {
                'name': 'SharePoint',
                'features': ['store_documents', 'team_folders', 'permissions'],
                'oauth': True
            }
        },
        'email': {
            'gmail': {
                'name': 'Gmail',
                'features': ['send_emails', 'track_conversations', 'templates'],
                'oauth': True
            },
            'outlook': {
                'name': 'Outlook',
                'features': ['send_emails', 'track_conversations', 'templates'],
                'oauth': True
            }
        }
    }
    
    def get_available_integrations(self) -> Dict:
        """Get list of available integrations"""
        try:
            integrations = []
            for category, services in self.INTEGRATIONS.items():
                for service_id, service_info in services.items():
                    integrations.append({
                        'id': service_id,
                        'category': category,
                        'name': service_info['name'],
                        'features': service_info['features'],
                        'requires_oauth': service_info['oauth'],
                        'enabled': False,  # Check if user has connected
                        'icon': self._get_service_icon(service_id)
                    })
            
            return {
                'success': True,
                'integrations': integrations,
                'categories': list(self.INTEGRATIONS.keys())
            }
            
        except Exception as e:
            logger.error(f"Error getting integrations: {e}")
            return {'success': False, 'error': str(e)}
    
    def sync_calendar_events(self, org_id: int, calendar_service: str) -> Dict:
        """Sync grant deadlines with calendar"""
        try:
            from app.models import Grant
            
            # Get upcoming grant deadlines
            grants = Grant.query.filter(
                Grant.org_id == org_id,
                Grant.deadline >= datetime.utcnow(),
                Grant.application_stage.in_(['researching', 'writing', 'review'])
            ).all()
            
            events = []
            for grant in grants:
                if grant.deadline:
                    events.append({
                        'id': f'grant_{grant.id}',
                        'title': f'Grant Deadline: {grant.title}',
                        'description': f'Amount: ${grant.amount_max:,.0f}\nFunder: {grant.funder}',
                        'start': grant.deadline.isoformat(),
                        'end': grant.deadline.isoformat(),
                        'all_day': True,
                        'color': self._get_stage_color(grant.application_stage),
                        'reminders': [
                            {'method': 'email', 'days_before': 7},
                            {'method': 'popup', 'days_before': 3},
                            {'method': 'popup', 'days_before': 1}
                        ]
                    })
            
            # Sync with calendar service
            if calendar_service == 'google_calendar':
                result = self._sync_google_calendar(events)
            elif calendar_service == 'outlook_calendar':
                result = self._sync_outlook_calendar(events)
            else:
                result = self._export_ical_feed(events)
            
            return {
                'success': True,
                'events_synced': len(events),
                'service': calendar_service,
                'next_sync': (datetime.utcnow() + timedelta(hours=1)).isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing calendar: {e}")
            return {'success': False, 'error': str(e)}
    
    def sync_crm_contacts(self, org_id: int, crm_service: str) -> Dict:
        """Sync grant contacts with CRM"""
        try:
            from app.models import Grant, ScraperSource
            
            # Get unique funders and contacts
            sources = ScraperSource.query.filter_by(org_id=org_id).all()
            
            contacts = []
            for source in sources:
                if source.contact_email:
                    contacts.append({
                        'id': f'source_{source.id}',
                        'name': source.funder_name or source.name,
                        'email': source.contact_email,
                        'phone': source.contact_phone,
                        'organization': source.funder_name,
                        'type': 'Funder',
                        'tags': ['grant_funder', source.source_type],
                        'custom_fields': {
                            'total_grants': source.grants_available,
                            'website': source.website,
                            'last_contact': source.last_scraped.isoformat() if source.last_scraped else None
                        }
                    })
            
            # Sync with CRM service
            if crm_service == 'salesforce':
                result = self._sync_salesforce(contacts)
            elif crm_service == 'hubspot':
                result = self._sync_hubspot(contacts)
            else:
                result = self._sync_pipedrive(contacts)
            
            return {
                'success': True,
                'contacts_synced': len(contacts),
                'service': crm_service,
                'sync_type': 'bidirectional',
                'last_sync': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error syncing CRM: {e}")
            return {'success': False, 'error': str(e)}
    
    def manage_documents(self, org_id: int, action: str, 
                        document_data: Dict = None) -> Dict:
        """Manage grant documents"""
        try:
            if action == 'upload':
                result = self._upload_document(org_id, document_data)
            elif action == 'list':
                result = self._list_documents(org_id)
            elif action == 'download':
                result = self._download_document(org_id, document_data.get('document_id'))
            elif action == 'delete':
                result = self._delete_document(org_id, document_data.get('document_id'))
            elif action == 'organize':
                result = self._organize_documents(org_id)
            else:
                return {'success': False, 'error': 'Invalid action'}
            
            return result
            
        except Exception as e:
            logger.error(f"Error managing documents: {e}")
            return {'success': False, 'error': str(e)}
    
    def setup_email_templates(self, org_id: int) -> Dict:
        """Setup email templates for grant communications"""
        try:
            templates = [
                {
                    'id': 'initial_inquiry',
                    'name': 'Initial Grant Inquiry',
                    'subject': 'Grant Inquiry - {{organization_name}}',
                    'body': self._get_email_template('initial_inquiry'),
                    'variables': ['organization_name', 'grant_title', 'contact_name']
                },
                {
                    'id': 'follow_up',
                    'name': 'Follow Up',
                    'subject': 'Following Up - {{grant_title}}',
                    'body': self._get_email_template('follow_up'),
                    'variables': ['grant_title', 'last_contact_date', 'next_steps']
                },
                {
                    'id': 'thank_you',
                    'name': 'Thank You',
                    'subject': 'Thank You - {{organization_name}}',
                    'body': self._get_email_template('thank_you'),
                    'variables': ['contact_name', 'grant_amount', 'impact_statement']
                },
                {
                    'id': 'submission_confirmation',
                    'name': 'Submission Confirmation',
                    'subject': 'Grant Application Submitted - {{grant_title}}',
                    'body': self._get_email_template('submission_confirmation'),
                    'variables': ['grant_title', 'submission_date', 'reference_number']
                }
            ]
            
            return {
                'success': True,
                'templates': templates,
                'total': len(templates)
            }
            
        except Exception as e:
            logger.error(f"Error setting up templates: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_integration_status(self, org_id: int) -> Dict:
        """Get status of all integrations"""
        try:
            status = {
                'calendar': {
                    'connected': False,
                    'service': None,
                    'last_sync': None,
                    'events_synced': 0
                },
                'crm': {
                    'connected': False,
                    'service': None,
                    'last_sync': None,
                    'contacts_synced': 0
                },
                'documents': {
                    'connected': False,
                    'service': None,
                    'storage_used': '0 MB',
                    'files_count': 0
                },
                'email': {
                    'connected': False,
                    'service': None,
                    'templates_configured': 4,
                    'emails_sent': 0
                }
            }
            
            # Check actual connection status (would query database)
            # This is placeholder data
            
            return {
                'success': True,
                'status': status,
                'recommendations': self._get_integration_recommendations(status)
            }
            
        except Exception as e:
            logger.error(f"Error getting status: {e}")
            return {'success': False, 'error': str(e)}
    
    def export_data(self, org_id: int, format: str = 'csv') -> Dict:
        """Export grant data to various formats"""
        try:
            from app.models import Grant
            import csv
            import io
            
            grants = Grant.query.filter_by(org_id=org_id).all()
            
            if format == 'csv':
                output = io.StringIO()
                writer = csv.writer(output)
                
                # Write headers
                writer.writerow([
                    'Title', 'Funder', 'Amount', 'Deadline', 
                    'Stage', 'Match Score', 'Created', 'Updated'
                ])
                
                # Write data
                for grant in grants:
                    writer.writerow([
                        grant.title,
                        grant.funder,
                        grant.amount_max,
                        grant.deadline.strftime('%Y-%m-%d') if grant.deadline else '',
                        grant.application_stage,
                        grant.match_score,
                        grant.created_at.strftime('%Y-%m-%d'),
                        grant.updated_at.strftime('%Y-%m-%d') if grant.updated_at else ''
                    ])
                
                export_data = output.getvalue()
                
            elif format == 'json':
                export_data = json.dumps([{
                    'id': g.id,
                    'title': g.title,
                    'funder': g.funder,
                    'amount': g.amount_max,
                    'deadline': g.deadline.isoformat() if g.deadline else None,
                    'stage': g.application_stage,
                    'match_score': g.match_score
                } for g in grants], indent=2)
                
            else:
                return {'success': False, 'error': 'Unsupported format'}
            
            # Generate download link
            file_hash = hashlib.md5(export_data.encode()).hexdigest()
            filename = f'grants_export_{datetime.utcnow().strftime("%Y%m%d")}_{file_hash[:8]}.{format}'
            
            return {
                'success': True,
                'filename': filename,
                'format': format,
                'size': len(export_data),
                'records': len(grants),
                'data': export_data[:1000] + '...' if len(export_data) > 1000 else export_data
            }
            
        except Exception as e:
            logger.error(f"Error exporting data: {e}")
            return {'success': False, 'error': str(e)}
    
    # Helper methods
    
    def _get_service_icon(self, service_id: str) -> str:
        """Get icon for service"""
        icons = {
            'google_calendar': '📅',
            'outlook_calendar': '📆',
            'salesforce': '☁️',
            'hubspot': '🎯',
            'google_drive': '📁',
            'dropbox': '📦',
            'gmail': '📧',
            'outlook': '✉️'
        }
        return icons.get(service_id, '🔗')
    
    def _get_stage_color(self, stage: str) -> str:
        """Get color for grant stage"""
        colors = {
            'discovery': '#gray',
            'researching': '#blue',
            'writing': '#yellow',
            'review': '#orange',
            'submitted': '#purple',
            'pending': '#indigo',
            'awarded': '#green',
            'declined': '#red'
        }
        return colors.get(stage, '#gray')
    
    def _sync_google_calendar(self, events: List[Dict]) -> Dict:
        """Sync with Google Calendar (placeholder)"""
        # Would use Google Calendar API
        return {'synced': len(events)}
    
    def _sync_outlook_calendar(self, events: List[Dict]) -> Dict:
        """Sync with Outlook Calendar (placeholder)"""
        # Would use Microsoft Graph API
        return {'synced': len(events)}
    
    def _export_ical_feed(self, events: List[Dict]) -> Dict:
        """Export iCal feed (placeholder)"""
        # Would generate iCal format
        return {'exported': len(events)}
    
    def _sync_salesforce(self, contacts: List[Dict]) -> Dict:
        """Sync with Salesforce (placeholder)"""
        # Would use Salesforce API
        return {'synced': len(contacts)}
    
    def _sync_hubspot(self, contacts: List[Dict]) -> Dict:
        """Sync with HubSpot (placeholder)"""
        # Would use HubSpot API
        return {'synced': len(contacts)}
    
    def _sync_pipedrive(self, contacts: List[Dict]) -> Dict:
        """Sync with Pipedrive (placeholder)"""
        # Would use Pipedrive API
        return {'synced': len(contacts)}
    
    def _upload_document(self, org_id: int, document_data: Dict) -> Dict:
        """Upload document"""
        return {
            'success': True,
            'document_id': f'doc_{org_id}_{datetime.utcnow().timestamp()}',
            'filename': document_data.get('filename'),
            'size': document_data.get('size')
        }
    
    def _list_documents(self, org_id: int) -> Dict:
        """List documents"""
        return {
            'success': True,
            'documents': [],
            'total': 0
        }
    
    def _download_document(self, org_id: int, document_id: str) -> Dict:
        """Download document"""
        return {
            'success': True,
            'document_id': document_id,
            'url': f'/documents/{document_id}'
        }
    
    def _delete_document(self, org_id: int, document_id: str) -> Dict:
        """Delete document"""
        return {
            'success': True,
            'deleted': document_id
        }
    
    def _organize_documents(self, org_id: int) -> Dict:
        """Organize documents into folders"""
        folders = {
            'proposals': [],
            'budgets': [],
            'letters_of_support': [],
            'reports': [],
            'correspondence': []
        }
        return {
            'success': True,
            'folders': folders
        }
    
    def _get_email_template(self, template_type: str) -> str:
        """Get email template content"""
        templates = {
            'initial_inquiry': """Dear {{contact_name}},

I am writing on behalf of {{organization_name}} to inquire about {{grant_title}}.

Our organization aligns closely with your foundation's mission, and we believe our work could significantly benefit from your support.

Would it be possible to schedule a brief call to discuss our proposal?

Best regards,
{{sender_name}}""",
            'follow_up': """Dear {{contact_name}},

I wanted to follow up on our grant application for {{grant_title}} submitted on {{submission_date}}.

Please let me know if you need any additional information.

Thank you for your consideration.

Best regards,
{{sender_name}}""",
            'thank_you': """Dear {{contact_name}},

Thank you so much for your generous grant of {{grant_amount}} to support our work.

{{impact_statement}}

We look forward to keeping you updated on our progress.

With gratitude,
{{sender_name}}""",
            'submission_confirmation': """Dear Team,

This confirms that our grant application for {{grant_title}} has been successfully submitted on {{submission_date}}.

Reference Number: {{reference_number}}

We will keep you updated on the progress.

Best regards,
{{sender_name}}"""
        }
        return templates.get(template_type, '')
    
    def _get_integration_recommendations(self, status: Dict) -> List[str]:
        """Get recommendations for integrations"""
        recommendations = []
        
        if not status['calendar']['connected']:
            recommendations.append('Connect calendar to never miss a deadline')
        
        if not status['crm']['connected']:
            recommendations.append('Sync CRM to manage funder relationships')
        
        if not status['documents']['connected']:
            recommendations.append('Enable cloud storage for document management')
        
        return recommendations