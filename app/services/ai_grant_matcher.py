"""
AI Grant Matching Service with REACTO Implementation
"""
import json
import logging
from typing import Dict, List, Optional
from datetime import datetime
from app.services.ai_service import AIService
from app.services.reacto_prompts import ReactoPrompts
from app.models import Grant, Organization, db

logger = logging.getLogger(__name__)

class AIGrantMatcher:
    """AI-powered grant matching using REACTO structure"""
    
    def __init__(self):
        self.ai_service = AIService()
        self.prompts = ReactoPrompts()
        
    def match_grants_for_organization(self, org_id: int, limit: int = 20) -> List[Dict]:
        """
        Match grants for an organization using AI scoring
        
        Args:
            org_id: Organization ID
            limit: Maximum number of grants to return
            
        Returns:
            List of grants with AI match scores and explanations
        """
        try:
            # Get organization context
            org = Organization.query.get(org_id)
            if not org:
                logger.error(f"Organization {org_id} not found")
                return []
            
            org_context = org.to_ai_context()
            
            # Get grants relevant to this organization (recently created)
            grants = Grant.query.order_by(Grant.created_at.desc()).limit(limit * 2).all()
            
            # Filter by deadline if available
            if any(grant.deadline for grant in grants):
                grants = [g for g in grants if not g.deadline or g.deadline >= datetime.utcnow().date()]
            
            # Limit to reasonable number for processing
            grants = grants[:limit * 2]
            
            matched_grants = []
            
            for grant in grants:
                try:
                    # Generate REACTO prompt for this grant
                    prompt = self.prompts.grant_matching_prompt(
                        org_context=org_context,
                        grant_data=grant.to_dict()
                    )
                    
                    # Get AI match analysis
                    response = self.ai_service.generate_json_response(prompt)
                    
                    if response and 'match_score' in response:
                        # Add match data to grant
                        grant_dict = grant.to_dict()
                        grant_dict.update({
                            'match_score': response['match_score'],
                            'match_percentage': response.get('match_percentage', response['match_score'] * 20),
                            'match_verdict': response.get('verdict', 'Not Evaluated'),
                            'match_reason': response.get('recommendation', ''),
                            'key_alignments': response.get('key_alignments', []),
                            'potential_challenges': response.get('potential_challenges', []),
                            'next_steps': response.get('next_steps', []),
                            'application_tips': response.get('application_tips', '')
                        })
                        
                        # Update grant in database
                        grant.match_score = response['match_score']
                        grant.match_reason = response.get('recommendation', '')
                        grant.ai_summary = json.dumps({
                            'verdict': response.get('verdict'),
                            'alignments': response.get('key_alignments'),
                            'challenges': response.get('potential_challenges'),
                            'tips': response.get('application_tips')
                        })
                        grant.last_intelligence_update = datetime.utcnow()
                        
                        matched_grants.append(grant_dict)
                        
                except Exception as e:
                    logger.error(f"Error matching grant {grant.id}: {str(e)}")
                    # Add grant without AI scoring
                    grant_dict = grant.to_dict()
                    grant_dict['match_score'] = 0
                    grant_dict['match_reason'] = 'Scoring unavailable'
                    matched_grants.append(grant_dict)
            
            # Commit all updates
            try:
                db.session.commit()
            except Exception as e:
                logger.error(f"Error saving match scores: {str(e)}")
                db.session.rollback()
            
            # Sort by match score and return top matches
            matched_grants.sort(key=lambda x: x.get('match_score', 0), reverse=True)
            return matched_grants[:limit]
            
        except Exception as e:
            logger.error(f"Error in match_grants_for_organization: {str(e)}")
            return []
    
    def analyze_single_grant(self, grant_id: int, org_id: int) -> Dict:
        """
        Perform detailed AI analysis of a single grant for an organization
        
        Args:
            grant_id: Grant ID
            org_id: Organization ID
            
        Returns:
            Detailed match analysis
        """
        try:
            grant = Grant.query.get(grant_id)
            org = Organization.query.get(org_id)
            
            if not grant or not org:
                return {'error': 'Grant or organization not found'}
            
            # Generate comprehensive analysis
            prompt = self.prompts.grant_matching_prompt(
                org_context=org.to_ai_context(),
                grant_data=grant.to_dict()
            )
            
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Extract grant intelligence
                intelligence_prompt = self.prompts.grant_intelligence_prompt(
                    grant_text=f"{grant.title}\n{grant.eligibility or ''}\n{grant.ai_summary or ''}"
                )
                intelligence = self.ai_service.generate_json_response(intelligence_prompt)
                
                # Combine match analysis with intelligence
                analysis = {
                    'grant': grant.to_dict(),
                    'match_analysis': response,
                    'intelligence': intelligence or {},
                    'recommended_action': self._determine_action(response.get('match_score', 0)),
                    'analysis_timestamp': datetime.utcnow().isoformat()
                }
                
                # Update grant record
                grant.match_score = response.get('match_score', 0)
                grant.match_reason = response.get('recommendation', '')
                grant.requirements_summary = json.dumps(intelligence) if intelligence else None
                grant.last_intelligence_update = datetime.utcnow()
                db.session.commit()
                
                return analysis
            
            return {'error': 'Analysis failed'}
            
        except Exception as e:
            logger.error(f"Error analyzing grant {grant_id}: {str(e)}")
            return {'error': str(e)}
    
    def generate_narrative(self, grant_id: int, org_id: int, section: str = 'executive_summary') -> Dict:
        """
        Generate grant narrative section using REACTO
        
        Args:
            grant_id: Grant ID
            org_id: Organization ID
            section: Narrative section to generate
            
        Returns:
            Generated narrative with metadata
        """
        try:
            grant = Grant.query.get(grant_id)
            org = Organization.query.get(org_id)
            
            if not grant or not org:
                return {'error': 'Grant or organization not found'}
            
            # Generate narrative using REACTO prompt
            prompt = self.prompts.narrative_generation_prompt(
                org_context=org.to_ai_context(),
                grant_data=grant.to_dict(),
                section=section
            )
            
            response = self.ai_service.generate_json_response(prompt)
            
            if response:
                # Save narrative to database
                from app.models import Narrative
                narrative = Narrative()
                narrative.grant_id = grant_id
                narrative.section = section
                narrative.content = response.get('narrative_text', '')
                narrative.ai_generated = True
                narrative.created_at = datetime.utcnow()
                db.session.add(narrative)
                db.session.commit()
                
                return {
                    'success': True,
                    'narrative': response,
                    'narrative_id': narrative.id
                }
            
            return {'error': 'Narrative generation failed'}
            
        except Exception as e:
            logger.error(f"Error generating narrative: {str(e)}")
            return {'error': str(e)}
    
    def _determine_action(self, match_score: int) -> str:
        """Determine recommended action based on match score"""
        if match_score >= 4:
            return "Apply Immediately - Excellent match"
        elif match_score == 3:
            return "Consider Applying - Good potential"
        elif match_score == 2:
            return "Review Carefully - Some alignment"
        else:
            return "Skip - Poor match"
    
    def bulk_score_grants(self, org_id: int) -> Dict:
        """
        Score all available grants for an organization
        
        Args:
            org_id: Organization ID
            
        Returns:
            Summary of scoring operation
        """
        try:
            org = Organization.query.get(org_id)
            if not org:
                return {'error': 'Organization not found'}
            
            # Get all grants
            grants = Grant.query.all()
            
            # Filter by deadline if available
            if any(grant.deadline for grant in grants):
                grants = [g for g in grants if not g.deadline or g.deadline >= datetime.utcnow().date()]
            
            scored = 0
            failed = 0
            
            for grant in grants:
                try:
                    # Quick scoring without full analysis
                    prompt = self.prompts.grant_matching_prompt(
                        org_context=org.to_ai_context(),
                        grant_data=grant.to_dict()
                    )
                    
                    response = self.ai_service.generate_json_response(prompt)
                    
                    if response and 'match_score' in response:
                        grant.match_score = response['match_score']
                        grant.match_reason = response.get('recommendation', '')[:500]
                        grant.last_intelligence_update = datetime.utcnow()
                        scored += 1
                    else:
                        failed += 1
                        
                except Exception as e:
                    logger.error(f"Error scoring grant {grant.id}: {str(e)}")
                    failed += 1
            
            # Commit all updates
            db.session.commit()
            
            return {
                'success': True,
                'total_grants': len(grants),
                'scored': scored,
                'failed': failed,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error in bulk scoring: {str(e)}")
            return {'error': str(e)}