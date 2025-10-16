"""
PHASE 0: Smart Onboarding Service
Dropdown-heavy design with custom field support and immediate matching
"""
from datetime import datetime
from typing import Dict, List, Optional, Any
from app.models import db, User, Organization, UserProgress, LovedGrant
from app.services.ai_service import ai_service
import logging

logger = logging.getLogger(__name__)

class Phase0OnboardingService:
    """Smart onboarding with dropdown-heavy design and custom fields"""
    
    # Dropdown Options for Onboarding
    ONBOARDING_OPTIONS = {
        'org_type': [
            '501(c)(3) Nonprofit',
            'Faith-based Organization',
            'Educational Institution',
            'Healthcare Organization',
            'Social Service Agency',
            'Arts & Culture Organization',
            'Environmental Organization',
            'Community Development Organization',
            'Other'
        ],
        
        'annual_budget': [
            'Less than $100,000',
            '$100,000 - $500,000',
            '$500,000 - $1 million',
            '$1 million - $5 million',
            '$5 million - $10 million',
            'Over $10 million'
        ],
        
        'staff_size': [
            '1-5 employees',
            '6-20 employees',
            '21-50 employees',
            '51-100 employees',
            'Over 100 employees'
        ],
        
        'years_operation': [
            '0-2 years (startup)',
            '3-5 years',
            '6-10 years',
            '11-20 years',
            'Over 20 years'
        ],
        
        'primary_focus': [
            'Education & Youth Development',
            'Health & Human Services',
            'Arts, Culture & Humanities',
            'Environment & Animals',
            'International Development',
            'Community & Economic Development',
            'Civil Rights & Advocacy',
            'Religion & Spirituality',
            'Research & Science',
            'Other'
        ],
        
        'target_population': [
            'Children & Youth (0-18)',
            'Young Adults (18-25)',
            'Adults (26-64)',
            'Seniors (65+)',
            'Families',
            'Veterans',
            'People with Disabilities',
            'Homeless Individuals',
            'Immigrants & Refugees',
            'LGBTQ+ Community',
            'Women & Girls',
            'Men & Boys',
            'General Public',
            'Other'
        ],
        
        'service_area': [
            'Local (single city/town)',
            'County-wide',
            'Multi-county',
            'State-wide',
            'Multi-state regional',
            'National',
            'International'
        ],
        
        'grant_experience': [
            'Never applied for grants',
            '1-5 grants received',
            '6-20 grants received',
            '21-50 grants received',
            'Over 50 grants received'
        ],
        
        'typical_grant_size': [
            'Less than $10,000',
            '$10,000 - $50,000',
            '$50,000 - $250,000',
            '$250,000 - $1 million',
            'Over $1 million'
        ],
        
        'grant_types': [
            'General Operating Support',
            'Program/Project Funding',
            'Capacity Building',
            'Capital/Equipment',
            'Research & Evaluation',
            'Emergency/Disaster Relief',
            'Scholarships/Fellowships',
            'Other'
        ],
        
        'funding_timeline': [
            'Immediate (within 30 days)',
            '1-3 months',
            '3-6 months',
            '6-12 months',
            'Over 12 months'
        ]
    }
    
    def create_organization_profile(self, user_id: int, profile_data: Dict) -> Dict:
        """
        Create or update organization profile with custom field support
        
        Args:
            user_id: User creating the profile
            profile_data: Profile data including custom fields
            
        Returns:
            Created/updated organization with completeness score
        """
        try:
            user = User.query.get(user_id)
            if not user:
                return {'success': False, 'error': 'User not found'}
            
            # Check if org already exists
            org = Organization.query.filter_by(created_by_user_id=user_id).first()
            if not org:
                org = Organization(created_by_user_id=user_id)
                db.session.add(org)
            
            # Process standard fields
            standard_fields = [
                'name', 'legal_name', 'ein', 'org_type', 'year_founded',
                'website', 'mission', 'vision', 'values', 'annual_budget_range',
                'staff_size', 'service_area_type', 'primary_city',
                'primary_state', 'typical_grant_size', 'grant_writing_capacity',
                'programs_services', 'key_achievements', 'unique_capabilities',
                'partnership_interests', 'funding_priorities',
                # New consultant-quality fields
                'growth_plans', 'competitive_advantage', 'community_needs',
                'market_gap', 'collaboration_approach'
            ]
            
            for field in standard_fields:
                if field in profile_data:
                    setattr(org, field, profile_data[field])
            
            # Process array/JSON fields
            array_fields = [
                'primary_focus_areas', 'target_demographics', 'preferred_grant_types',
                'keywords', 'exclusions', 'previous_funders',
                # New consultant-quality JSON fields
                'awards_recognition', 'media_coverage', 'partnerships', 'strategic_priorities'
            ]
            
            for field in array_fields:
                if field in profile_data:
                    setattr(org, field, profile_data[field])
            
            # Process custom fields (from "Other" options)
            custom_fields = {}
            for key, value in profile_data.items():
                if key.endswith('_other') or key.startswith('custom_'):
                    custom_fields[key] = value
            
            if custom_fields:
                existing_custom = org.custom_fields or {}
                existing_custom.update(custom_fields)
                org.custom_fields = existing_custom
                
                # Extract keywords from custom fields for AI matching
                self._extract_custom_keywords(org, custom_fields)
            
            # Calculate completeness
            org.profile_completeness = org.calculate_completeness()
            org.last_profile_update = datetime.utcnow()
            
            # Mark onboarding complete if over 70%
            if org.profile_completeness >= 70:
                org.onboarding_completed_at = datetime.utcnow()
                
                # Update user progress
                progress = UserProgress.query.filter_by(user_id=user_id).first()
                if progress:
                    progress.onboarding_complete = True
            
            # Link user to organization
            user.org_id = str(org.id)
            
            db.session.commit()
            
            return {
                'success': True,
                'organization': org.to_dict(),
                'completeness': org.profile_completeness,
                'ready_for_matching': org.profile_completeness >= 70
            }
            
        except Exception as e:
            logger.error(f"Error creating organization profile: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def _extract_custom_keywords(self, org: Organization, custom_fields: Dict):
        """Extract keywords from custom fields for better AI matching"""
        try:
            # Use AI to extract keywords from custom text
            custom_text = ' '.join([str(v) for v in custom_fields.values() if v])
            
            if custom_text:
                prompt = f"""Extract 5-10 important keywords from this custom organization information 
                for grant matching purposes: {custom_text}
                
                Return as a simple comma-separated list."""
                
                keywords_text = ai_service.generate_completion(prompt, max_tokens=100)
                if keywords_text:
                    new_keywords = [k.strip() for k in keywords_text.split(',')]
                    existing = org.keywords or []
                    org.keywords = list(set(existing + new_keywords))
                    
        except Exception as e:
            logger.error(f"Error extracting custom keywords: {e}")
    
    def get_onboarding_questions(self, step: str = 'basic') -> Dict:
        """
        Get onboarding questions for a specific step
        
        Args:
            step: Onboarding step (basic, focus, capacity, experience)
            
        Returns:
            Questions with dropdown options
        """
        questions = {
            'basic': {
                'title': 'Organization Basics',
                'description': 'Tell us about your organization',
                'fields': [
                    {
                        'name': 'name',
                        'label': 'Organization Name',
                        'type': 'text',
                        'required': True
                    },
                    {
                        'name': 'org_type',
                        'label': 'Organization Type',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['org_type'],
                        'allow_other': True,
                        'required': True
                    },
                    {
                        'name': 'year_founded',
                        'label': 'Years in Operation',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['years_operation'],
                        'required': True
                    },
                    {
                        'name': 'ein',
                        'label': 'EIN/Tax ID (optional)',
                        'type': 'text',
                        'required': False
                    },
                    {
                        'name': 'website',
                        'label': 'Website (optional)',
                        'type': 'url',
                        'required': False
                    }
                ]
            },
            
            'mission': {
                'title': 'Mission & Focus',
                'description': 'What does your organization do?',
                'fields': [
                    {
                        'name': 'mission',
                        'label': 'Mission Statement',
                        'type': 'textarea',
                        'placeholder': 'Our mission is to...',
                        'required': True
                    },
                    {
                        'name': 'primary_focus_areas',
                        'label': 'Primary Focus Areas',
                        'type': 'multi-select',
                        'options': self.ONBOARDING_OPTIONS['primary_focus'],
                        'allow_other': True,
                        'required': True
                    },
                    {
                        'name': 'target_demographics',
                        'label': 'Who do you serve?',
                        'type': 'multi-select',
                        'options': self.ONBOARDING_OPTIONS['target_population'],
                        'allow_other': True,
                        'required': True
                    },
                    {
                        'name': 'service_area_type',
                        'label': 'Geographic Service Area',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['service_area'],
                        'required': True
                    },
                    {
                        'name': 'primary_city',
                        'label': 'Primary City',
                        'type': 'text',
                        'required': True
                    },
                    {
                        'name': 'primary_state',
                        'label': 'Primary State',
                        'type': 'state-dropdown',
                        'required': True
                    }
                ]
            },
            
            'capacity': {
                'title': 'Organizational Capacity',
                'description': 'Help us understand your capacity',
                'fields': [
                    {
                        'name': 'annual_budget_range',
                        'label': 'Annual Budget',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['annual_budget'],
                        'required': True
                    },
                    {
                        'name': 'staff_size',
                        'label': 'Staff Size',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['staff_size'],
                        'required': True
                    },
                    {
                        'name': 'board_size',
                        'label': 'Board Size',
                        'type': 'number',
                        'min': 1,
                        'max': 100,
                        'required': False
                    },
                    {
                        'name': 'key_achievements',
                        'label': 'Key Achievements (optional)',
                        'type': 'textarea',
                        'placeholder': 'Major accomplishments, awards, or milestones',
                        'required': False
                    }
                ]
            },
            
            'grant_experience': {
                'title': 'Grant Experience',
                'description': 'Your grant funding history and needs',
                'fields': [
                    {
                        'name': 'grant_experience',
                        'label': 'Previous Grant Experience',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['grant_experience'],
                        'required': True
                    },
                    {
                        'name': 'typical_grant_size',
                        'label': 'Typical Grant Size Sought',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['typical_grant_size'],
                        'required': True
                    },
                    {
                        'name': 'preferred_grant_types',
                        'label': 'Types of Grants Needed',
                        'type': 'multi-select',
                        'options': self.ONBOARDING_OPTIONS['grant_types'],
                        'allow_other': True,
                        'required': True
                    },
                    {
                        'name': 'funding_timeline',
                        'label': 'Funding Timeline',
                        'type': 'dropdown',
                        'options': self.ONBOARDING_OPTIONS['funding_timeline'],
                        'required': True
                    },
                    {
                        'name': 'funding_priorities',
                        'label': 'Current Funding Priorities',
                        'type': 'textarea',
                        'placeholder': 'What specific programs or needs require funding?',
                        'required': False
                    }
                ]
            }
        }
        
        return questions.get(step, questions['basic'])
    
    def save_loved_grant(self, user_id: int, grant_data: Dict) -> Dict:
        """
        Save a grant to user's loved/favorites list
        
        Args:
            user_id: User ID
            grant_data: Grant or opportunity data to save
            
        Returns:
            Saved loved grant
        """
        try:
            # Check if already loved
            existing = LovedGrant.query.filter_by(
                user_id=user_id,
                grant_id=grant_data.get('grant_id')
            ).first()
            
            if existing:
                # Update existing
                existing.status = grant_data.get('status', existing.status)
                existing.notes = grant_data.get('notes', existing.notes)
            else:
                # Create new loved grant
                loved = LovedGrant(
                    user_id=user_id,
                    grant_id=grant_data.get('grant_id'),
                    opportunity_data=grant_data.get('opportunity_data'),
                    status=grant_data.get('status', 'interested'),
                    notes=grant_data.get('notes', '')
                )
                db.session.add(loved)
            
            db.session.commit()
            
            return {
                'success': True,
                'message': 'Grant saved to favorites'
            }
            
        except Exception as e:
            logger.error(f"Error saving loved grant: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_loved_grants(self, user_id: int) -> List[Dict]:
        """Get user's loved grants with status"""
        try:
            loved_grants = LovedGrant.query.filter_by(user_id=user_id).all()
            return [lg.to_dict() for lg in loved_grants]
        except Exception as e:
            logger.error(f"Error getting loved grants: {e}")
            return []

# Singleton instance
phase0_service = Phase0OnboardingService()