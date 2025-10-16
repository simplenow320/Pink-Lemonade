"""
Template Engine for Smart Tools
Reduces AI dependency by using smart templates with data-driven personalization
"""

import json
import re
from datetime import datetime
from typing import Dict, Any, Optional, List
import random

class TemplateEngine:
    """Handles template selection, filling, and component assembly"""
    
    def __init__(self):
        self.templates = self._load_templates()
        self.components = self._load_components()
    
    def _load_templates(self) -> Dict[str, Dict]:
        """Load all templates for different tools"""
        return {
            'thank_you': {
                'formal': {
                    'template': """Dear {donor_name},

On behalf of {org_name}, I want to express our heartfelt gratitude for your generous {donation_type} of {amount} to support {purpose}.

{impact_statement}

Your contribution directly enables us to {specific_use}. In the past year alone, we have {achievement_metric}, and your support ensures we can continue this vital work.

{personal_touch}

{closing_statement}

With sincere appreciation,

{signatory_name}
{signatory_title}
{org_name}""",
                    'tone': 'formal',
                    'length': 'standard'
                },
                'warm': {
                    'template': """Dear {donor_name},

Thank you! Your {donation_type} of {amount} to {org_name} means more than words can express.

{impact_statement}

Because of supporters like you, we can {specific_use}. {personal_touch}

{achievement_metric} - and that's just the beginning of what your generosity makes possible.

{closing_statement}

Gratefully,

{signatory_name}
{signatory_title}""",
                    'tone': 'warm',
                    'length': 'concise'
                }
            },
            'social_media': {
                'twitter': {
                    'announcement': "{hook} {main_message} {call_to_action} {hashtags}",
                    'impact': "📊 {impact_metric}! Thanks to your support, {org_name} {achievement}. {call_to_action} {hashtags}",
                    'gratitude': "🙏 Thank you to everyone who {action}! Together we're {mission_verb}. {impact_snippet} {hashtags}",
                    'event': "📅 Join us {event_date} for {event_name}! {event_description} {registration_cta} {hashtags}"
                },
                'linkedin': {
                    'professional': """{headline}

{context_paragraph}

Key achievements:
{bullet_points}

{call_to_action}

{hashtags}""",
                    'thought_leadership': """{question_hook}

At {org_name}, we've learned that {insight}.

{supporting_data}

{conclusion}

What's your experience with {topic}? Let's discuss in the comments.

{hashtags}"""
                }
            },
            'grant_pitch': {
                'elevator': {
                    'template': "{org_name} {impact_verb} {beneficiary_count} {beneficiaries} in {service_area} through {primary_programs}. With {years_active} years of proven impact and a {budget_size} annual budget, we seek {amount} to {specific_goal}. This investment will {expected_outcome}, directly aligning with {funder_priority}.",
                    'duration': '30_seconds'
                },
                'executive': {
                    'template': """{org_name} requests {amount} to {project_title}.

**The Need:** {problem_statement}

**Our Solution:** {solution_approach}

**Impact:** {impact_projection}

**Alignment:** {alignment_statement}

**Sustainability:** {sustainability_plan}""",
                    'duration': '2_minutes'
                }
            }
        }
    
    def _load_components(self) -> Dict[str, List[str]]:
        """Load reusable content components"""
        return {
            'impact_statements': [
                "Your support transforms lives in our community",
                "Your generosity creates lasting change",
                "Your investment empowers those we serve",
                "Your partnership makes our mission possible",
                "Your contribution drives meaningful impact"
            ],
            'achievement_metrics': [
                "served {count} individuals with essential services",
                "provided {hours} hours of direct support",
                "delivered {programs} vital programs to our community",
                "reached {percent}% more people than last year",
                "achieved a {percent}% success rate in our programs"
            ],
            'closing_statements': [
                "Together, we're building a stronger community",
                "Your partnership makes all the difference",
                "Thank you for believing in our mission",
                "We're honored to have you as a supporter",
                "Your trust in our work inspires us daily"
            ],
            'social_hooks': [
                "🎉 Big news!",
                "📢 Exciting update:",
                "💪 Together we're stronger:",
                "🌟 Making a difference:",
                "❤️ Community love:",
                "🚀 Moving forward:",
                "✨ Celebrating impact:"
            ],
            'call_to_actions': [
                "Learn more at {website}",
                "Join us: {website}",
                "Be part of the change: {website}",
                "Support our mission: {website}",
                "Get involved today: {website}"
            ],
            'hashtag_sets': {
                'general': ['#NonProfit', '#CommunityImpact', '#MakeADifference'],
                'fundraising': ['#Fundraising', '#Donate', '#SupportOurCause'],
                'gratitude': ['#ThankYou', '#Grateful', '#CommunitySupport'],
                'impact': ['#Impact', '#ChangeMakers', '#SocialGood']
            }
        }
    
    def fill_template(self, tool: str, template_type: str, data: Dict[str, Any]) -> str:
        """Fill a template with provided data"""
        if tool not in self.templates:
            raise ValueError(f"Tool {tool} not found in templates")
        
        if template_type not in self.templates[tool]:
            # Use first available template as fallback
            template_type = list(self.templates[tool].keys())[0]
        
        template_data = self.templates[tool][template_type]
        
        # Handle nested template structure
        if isinstance(template_data, dict) and 'template' in template_data:
            template = template_data['template']
        else:
            template = template_data
        
        # Fill basic placeholders
        filled = template
        for key, value in data.items():
            placeholder = f"{{{key}}}"
            if placeholder in filled:
                filled = filled.replace(placeholder, str(value))
        
        # Handle any remaining placeholders with defaults
        filled = self._fill_missing_placeholders(filled)
        
        return filled
    
    def _fill_missing_placeholders(self, template: str) -> str:
        """Fill any remaining placeholders with sensible defaults"""
        # Find all remaining placeholders
        placeholders = re.findall(r'\{([^}]+)\}', template)
        
        for placeholder in placeholders:
            if placeholder in ['website', 'url']:
                template = template.replace(f'{{{placeholder}}}', '[website]')
            elif placeholder in ['amount', 'donation_amount']:
                template = template.replace(f'{{{placeholder}}}', '[amount]')
            elif placeholder in ['date', 'event_date']:
                template = template.replace(f'{{{placeholder}}}', '[date]')
            else:
                # Remove unfilled placeholders
                template = template.replace(f'{{{placeholder}}}', '')
        
        return template.strip()
    
    def get_component(self, component_type: str, specific: Optional[str] = None) -> str:
        """Get a random or specific component"""
        if component_type not in self.components:
            return ""
        
        component_list = self.components[component_type]
        
        if specific and specific in component_list:
            return specific
        elif isinstance(component_list, list):
            return random.choice(component_list)
        elif isinstance(component_list, dict) and specific in component_list:
            items = component_list[specific]
            return ' '.join(items) if isinstance(items, list) else items
        
        return ""
    
    def build_structured_content(self, sections: Dict[str, str]) -> str:
        """Assemble content from multiple sections"""
        content_parts = []
        for section_name, section_content in sections.items():
            if section_content:
                content_parts.append(section_content)
        
        return "\n\n".join(content_parts)
    
    def personalize_with_data(self, template: str, org_data: Dict) -> str:
        """Add personalization using organization data without AI"""
        # Calculate derived fields
        personalized_data = {
            'years_active': self._calculate_years_active(org_data.get('founded')),
            'beneficiary_count': self._format_number(org_data.get('beneficiaries_served', 'many')),
            'budget_size': self._get_budget_descriptor(org_data.get('annual_budget_range')),
            'impact_verb': self._get_impact_verb(org_data.get('org_type')),
            'mission_verb': self._extract_mission_verb(org_data.get('mission', ''))
        }
        
        # Merge with original data
        personalized_data.update(org_data)
        
        # Fill template with personalized data
        return self.fill_template('grant_pitch', 'elevator', personalized_data)
    
    def _calculate_years_active(self, founded: Optional[str]) -> str:
        """Calculate years of operation"""
        if not founded:
            return "several"
        
        try:
            founded_year = int(founded)
            current_year = datetime.now().year
            years = current_year - founded_year
            if years < 1:
                return "less than 1"
            elif years == 1:
                return "1"
            else:
                return str(years)
        except:
            return "many"
    
    def _format_number(self, number: Any) -> str:
        """Format number for display"""
        if isinstance(number, (int, float)):
            if number >= 1000000:
                return f"{number/1000000:.1f}M"
            elif number >= 1000:
                return f"{number/1000:.0f}K"
            else:
                return str(int(number))
        return str(number) if number else "numerous"
    
    def _get_budget_descriptor(self, budget_range: Optional[str]) -> str:
        """Get descriptive term for budget size"""
        if not budget_range:
            return "sustainable"
        
        budget_descriptors = {
            "Under $50,000": "lean",
            "$50,000-$250,000": "modest",
            "$250,000-$1M": "substantial",
            "$1M-$5M": "significant",
            "$5M-$10M": "major",
            "Over $10M": "extensive"
        }
        
        return budget_descriptors.get(budget_range, "appropriate")
    
    def _get_impact_verb(self, org_type: Optional[str]) -> str:
        """Get appropriate action verb based on org type"""
        if not org_type:
            return "serves"
        
        impact_verbs = {
            "501(c)(3)": "serves",
            "Foundation": "supports",
            "Religious": "ministers to",
            "Educational": "educates",
            "Healthcare": "cares for",
            "Social Services": "assists",
            "Environmental": "protects",
            "Arts/Culture": "enriches"
        }
        
        return impact_verbs.get(org_type, "serves")
    
    def _extract_mission_verb(self, mission: str) -> str:
        """Extract action verb from mission statement"""
        if not mission:
            return "making a difference"
        
        # Common mission verbs to look for
        action_verbs = [
            "empowering", "serving", "building", "creating", "supporting",
            "providing", "helping", "advancing", "improving", "transforming"
        ]
        
        mission_lower = mission.lower()
        for verb in action_verbs:
            if verb in mission_lower:
                return verb
        
        return "fulfilling our mission"
    
    def generate_hashtags(self, focus_areas: List[str], location: Optional[str] = None) -> str:
        """Generate relevant hashtags based on focus areas and location"""
        hashtags = []
        
        # Add general nonprofit hashtags
        hashtags.extend(self.components['hashtag_sets']['general'])
        
        # Add focus area hashtags
        for area in focus_areas[:3]:  # Limit to 3 focus areas
            # Convert to hashtag format
            hashtag = '#' + ''.join(area.title().split())
            hashtags.append(hashtag)
        
        # Add location if provided
        if location:
            location_parts = location.split(',')
            if location_parts:
                city = location_parts[0].strip().replace(' ', '')
                hashtags.append(f'#{city}')
        
        # Add nonprofit tag
        hashtags.append('#NonProfit')
        
        # Return unique hashtags, limited to 7
        unique_hashtags = []
        seen = set()
        for tag in hashtags:
            if tag.lower() not in seen:
                unique_hashtags.append(tag)
                seen.add(tag.lower())
        
        return ' '.join(unique_hashtags[:7])