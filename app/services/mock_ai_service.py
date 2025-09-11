"""
Mock AI Service for testing and fallback
Returns realistic mock responses when AI service is unavailable
"""

import logging
import random
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class MockAIService:
    """Provides mock AI responses for testing and fallback scenarios"""
    
    @staticmethod
    def get_mock_grant_match() -> Dict:
        """Return a realistic mock grant match response"""
        scores = [2, 3, 3, 4, 4, 5]  # Weighted towards moderate-good matches
        score = random.choice(scores)
        
        match_responses = {
            5: {
                "match_score": 5,
                "verdict": "Excellent Match",
                "match_percentage": 95,
                "recommendation": "This grant is an excellent fit for your organization's mission and capabilities.",
                "key_alignments": [
                    "Mission directly aligns with funder priorities",
                    "Geographic location matches perfectly",
                    "Budget size within funder's typical range"
                ],
                "potential_challenges": [
                    "High competition expected",
                    "Comprehensive documentation required"
                ],
                "next_steps": [
                    "Begin application immediately",
                    "Gather all required documents",
                    "Contact program officer for questions"
                ],
                "application_tips": "Emphasize your track record and unique approach. Include strong metrics and testimonials."
            },
            4: {
                "match_score": 4,
                "verdict": "Strong Match",
                "match_percentage": 80,
                "recommendation": "This grant aligns well with your organization. Worth pursuing with careful preparation.",
                "key_alignments": [
                    "Program focus matches grant priorities",
                    "Organization size appropriate",
                    "Past experience relevant"
                ],
                "potential_challenges": [
                    "May need to strengthen evaluation plan",
                    "Budget justification needs detail"
                ],
                "next_steps": [
                    "Review all requirements carefully",
                    "Strengthen weak areas before applying",
                    "Seek feedback on draft application"
                ],
                "application_tips": "Focus on demonstrating impact and sustainability. Be specific about outcomes."
            },
            3: {
                "match_score": 3,
                "verdict": "Moderate Match",
                "match_percentage": 60,
                "recommendation": "This grant has potential but requires careful consideration of alignment.",
                "key_alignments": [
                    "Some mission overlap",
                    "Eligible organization type"
                ],
                "potential_challenges": [
                    "Geographic scope may be limiting",
                    "Competition from larger organizations",
                    "Partial program alignment"
                ],
                "next_steps": [
                    "Assess capacity to meet requirements",
                    "Consider partnering with other organizations",
                    "Contact funder for clarification"
                ],
                "application_tips": "Clearly articulate how you'll adapt to meet funder priorities. Consider collaboration."
            },
            2: {
                "match_score": 2,
                "verdict": "Weak Match",
                "match_percentage": 40,
                "recommendation": "Limited alignment. Consider if effort is worth potential low success rate.",
                "key_alignments": [
                    "Basic eligibility met"
                ],
                "potential_challenges": [
                    "Mission alignment unclear",
                    "Geographic restrictions",
                    "Size/scope mismatch",
                    "Limited relevant experience"
                ],
                "next_steps": [
                    "Explore other funding opportunities",
                    "Build relationships for future",
                    "Focus on better-aligned grants"
                ],
                "application_tips": "If pursuing, need exceptional narrative to overcome alignment gaps."
            }
        }
        
        return match_responses.get(score, match_responses[3])
    
    @staticmethod
    def get_mock_pitch(pitch_type: str = "elevator") -> Dict:
        """Return a mock grant pitch"""
        pitches = {
            "elevator": {
                "pitch_text": "We're Tech for Good Foundation, transforming communities through innovative technology solutions. Last year, we helped 500 low-income families access digital literacy training, resulting in 200 new jobs. With your support, we can expand to serve 2,000 families across three new cities, bridging the digital divide and creating lasting economic opportunity.",
                "hook": "What if technology could lift entire communities out of poverty?",
                "problem_statement": "500,000 families in our region lack basic digital skills needed for today's jobs.",
                "solution_overview": "Comprehensive digital literacy program with job placement support.",
                "impact_evidence": "200 job placements, $3M in new wages generated.",
                "key_points": [
                    "Proven model ready to scale",
                    "Strong community partnerships",
                    "Measurable economic impact"
                ],
                "call_to_action": "Partner with us to transform 2,000 more lives.",
                "funding_request": "$100,000 to expand program to three cities",
                "word_count": 76,
                "speaking_time": "60 seconds",
                "delivery_tips": [
                    "Start with the hook question",
                    "Pause after key statistics",
                    "End with clear ask"
                ]
            },
            "executive": {
                "pitch_text": "Tech for Good Foundation addresses the critical digital divide affecting 500,000 families in our region. These families cannot access 80% of today's jobs due to lack of digital skills. Our comprehensive Digital Bridges program provides intensive training, equipment access, and job placement support. We've demonstrated success with 200 job placements generating $3M in new wages. Our three-pronged approach includes: basic digital literacy, industry-specific training, and employer partnerships. With proven results and scalable model, we're ready to expand. Your investment of $100,000 will enable us to serve 2,000 families across three new cities, generating an estimated $12M in economic impact over three years.",
                "word_count": 106,
                "speaking_time": "2 minutes"
            },
            "detailed": {
                "pitch_text": "Tech for Good Foundation requests $100,000 to expand our award-winning Digital Bridges program. [Full detailed pitch would be here...]",
                "word_count": 500,
                "speaking_time": "5 minutes"
            }
        }
        
        base_response = pitches.get(pitch_type, pitches["elevator"])
        return {
            "success": True,
            "pitch_type": pitch_type,
            **base_response,
            "funder_connection": "Aligns with your foundation's focus on economic empowerment.",
            "follow_up_strategy": "Send impact report within 48 hours of meeting.",
            "competitive_advantages": [
                "Only program with job guarantee",
                "Lowest cost per placement in region",
                "Highest completion rate (85%)"
            ]
        }
    
    @staticmethod
    def get_mock_impact_report() -> Dict:
        """Return a mock impact report"""
        return {
            "success": True,
            "report_sections": {
                "executive_summary": "This year, Tech for Good Foundation made significant strides in bridging the digital divide...",
                "key_metrics": {
                    "beneficiaries_served": 500,
                    "programs_delivered": 5,
                    "volunteer_hours": 2000,
                    "total_impact_value": "$3,000,000"
                },
                "success_stories": [
                    {
                        "title": "From Unemployed to Tech Professional",
                        "story": "Maria, a single mother of two, transformed her life through our program..."
                    }
                ],
                "challenges_learned": "Adapted to remote learning during pandemic restrictions...",
                "future_outlook": "Expanding to three new cities in 2025..."
            },
            "visualizations": ["Impact dashboard recommended", "Success metrics chart suggested"],
            "word_count": 1500
        }
    
    @staticmethod
    def get_mock_case_support() -> Dict:
        """Return a mock case for support"""
        return {
            "success": True,
            "case_sections": {
                "compelling_need": "Our community faces a critical challenge that demands immediate action...",
                "proposed_solution": "Our evidence-based approach addresses root causes...",
                "organizational_capacity": "With 10 years of experience and proven results...",
                "expected_outcomes": "We project serving 2,000 families with 80% success rate...",
                "sustainability_plan": "Three-year path to self-sufficiency through earned revenue...",
                "call_to_action": "Your investment will transform lives and strengthen our community..."
            },
            "campaign_messaging": "Together, we can bridge the digital divide",
            "donor_benefits": ["Naming opportunities", "Impact reports", "Site visits"],
            "word_count": 2000
        }