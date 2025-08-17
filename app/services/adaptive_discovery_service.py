"""
Adaptive Grant Discovery Service
Dynamic questioning system that adapts based on user answers
Prioritizes high-impact questions and skips irrelevant ones
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from enum import Enum
from app.services.ai_optimizer_service import ai_optimizer

logger = logging.getLogger(__name__)

class QuestionPriority(Enum):
    """Priority levels for adaptive questions"""
    CRITICAL = 1      # Must ask (mission, org type)
    HIGH = 2          # Very important (budget, location)
    MEDIUM = 3        # Important but flexible (programs, demographics)
    LOW = 4           # Nice to have (previous funders, success rate)
    CONDITIONAL = 5   # Only ask based on previous answers

class AdaptiveDiscoveryService:
    """
    Intelligent grant discovery that adapts questions based on context
    Saves time by asking only relevant questions in priority order
    """
    
    def __init__(self):
        self.optimizer = ai_optimizer
        self.session_data = {}
        
        # Question bank with priorities and conditions
        self.questions = {
            # CRITICAL Questions (always ask first)
            "org_name": {
                "priority": QuestionPriority.CRITICAL,
                "question": "What's your organization's name?",
                "type": "text",
                "required": True,
                "default": None,
                "follow_up": None
            },
            "mission": {
                "priority": QuestionPriority.CRITICAL,
                "question": "In 1-2 sentences, what's your organization's mission?",
                "type": "text",
                "required": True,
                "default": None,
                "follow_up": "focus_areas"
            },
            "org_type": {
                "priority": QuestionPriority.CRITICAL,
                "question": "What type of organization are you?",
                "type": "select",
                "options": ["501(c)(3) Nonprofit", "Faith-based", "Educational Institution", 
                           "Healthcare", "Arts/Culture", "Environmental", "Social Services", "Other"],
                "required": True,
                "default": "501(c)(3) Nonprofit",
                "follow_up": None
            },
            
            # HIGH Priority Questions
            "annual_budget": {
                "priority": QuestionPriority.HIGH,
                "question": "What's your annual operating budget?",
                "type": "select",
                "options": ["Under $100K", "$100K-$500K", "$500K-$1M", "$1M-$5M", "Over $5M"],
                "required": False,
                "default": "$100K-$500K",
                "follow_up": "grant_size_needed"
            },
            "location": {
                "priority": QuestionPriority.HIGH,
                "question": "Where is your organization based? (City, State)",
                "type": "text",
                "required": True,
                "default": None,
                "follow_up": "service_area"
            },
            "urgency": {
                "priority": QuestionPriority.HIGH,
                "question": "When do you need funding?",
                "type": "select",
                "options": ["Immediately (1-3 months)", "Soon (3-6 months)", 
                           "This year (6-12 months)", "Next year", "Ongoing"],
                "required": False,
                "default": "This year (6-12 months)",
                "follow_up": None
            },
            
            # MEDIUM Priority Questions
            "focus_areas": {
                "priority": QuestionPriority.MEDIUM,
                "question": "Select your top 3 focus areas:",
                "type": "multiselect",
                "options": ["Education", "Health", "Youth Development", "Community Development",
                           "Arts & Culture", "Environment", "Housing", "Employment", 
                           "Food Security", "Mental Health", "Senior Services", "Veterans"],
                "required": False,
                "max_selections": 3,
                "default": ["Community Development"],
                "follow_up": "target_population"
            },
            "target_population": {
                "priority": QuestionPriority.MEDIUM,
                "question": "Who do you primarily serve?",
                "type": "multiselect",
                "options": ["Children (0-12)", "Youth (13-18)", "Young Adults (19-25)",
                           "Adults", "Seniors (65+)", "Families", "Veterans", 
                           "People with Disabilities", "Homeless", "Low-income"],
                "required": False,
                "max_selections": 3,
                "default": ["Families"],
                "follow_up": None
            },
            
            # CONDITIONAL Questions (asked based on previous answers)
            "faith_denomination": {
                "priority": QuestionPriority.CONDITIONAL,
                "condition": lambda answers: answers.get("org_type") == "Faith-based",
                "question": "What's your religious affiliation/denomination?",
                "type": "select",
                "options": ["Christian - Protestant", "Christian - Catholic", "Jewish", 
                           "Muslim", "Buddhist", "Hindu", "Interfaith", "Other"],
                "required": False,
                "default": "Christian - Protestant",
                "follow_up": None
            },
            "grant_size_needed": {
                "priority": QuestionPriority.CONDITIONAL,
                "condition": lambda answers: answers.get("annual_budget") in ["Under $100K", "$100K-$500K"],
                "question": "What size grant are you seeking?",
                "type": "select",
                "options": ["Under $10K", "$10K-$25K", "$25K-$50K", "$50K-$100K", "Over $100K"],
                "required": False,
                "default": "$10K-$25K",
                "follow_up": None
            },
            "service_area": {
                "priority": QuestionPriority.CONDITIONAL,
                "condition": lambda answers: bool(answers.get("location")),
                "question": "What's your service area?",
                "type": "select",
                "options": ["Neighborhood", "City", "County", "Multi-county", "Statewide", "National"],
                "required": False,
                "default": "City",
                "follow_up": None
            },
            
            # LOW Priority Questions (ask if time permits)
            "previous_grants": {
                "priority": QuestionPriority.LOW,
                "question": "Have you received grants before?",
                "type": "select",
                "options": ["Never", "1-2 grants", "3-5 grants", "6-10 grants", "Many (10+)"],
                "required": False,
                "default": "1-2 grants",
                "follow_up": "grant_experience"
            },
            "grant_writer": {
                "priority": QuestionPriority.LOW,
                "question": "Who will write your grant applications?",
                "type": "select",
                "options": ["Myself", "Staff member", "Volunteer", "Consultant", "Not sure"],
                "required": False,
                "default": "Myself",
                "follow_up": None
            }
        }
        
    def start_discovery(self, initial_data: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Start adaptive discovery session
        Returns first question based on priority
        """
        self.session_data = initial_data or {}
        next_question = self.get_next_question()
        
        return {
            "session_id": self._generate_session_id(),
            "question": next_question,
            "progress": self.calculate_progress(),
            "estimated_questions_remaining": self.estimate_remaining_questions()
        }
    
    def get_next_question(self) -> Optional[Dict[str, Any]]:
        """
        Get the next most important question based on:
        1. Priority level
        2. Whether conditions are met
        3. What's already been answered
        """
        unanswered = []
        
        for key, q_data in self.questions.items():
            # Skip if already answered
            if key in self.session_data:
                continue
                
            # Check conditional questions
            if q_data["priority"] == QuestionPriority.CONDITIONAL:
                condition = q_data.get("condition")
                if condition and not condition(self.session_data):
                    continue
            
            unanswered.append((key, q_data))
        
        # Sort by priority (lower number = higher priority)
        unanswered.sort(key=lambda x: x[1]["priority"].value)
        
        if unanswered:
            key, question = unanswered[0]
            return {
                "key": key,
                "question": question["question"],
                "type": question["type"],
                "options": question.get("options"),
                "required": question.get("required", False),
                "default": question.get("default"),
                "max_selections": question.get("max_selections")
            }
        
        return None
    
    def process_answer(self, question_key: str, answer: Any) -> Dict[str, Any]:
        """
        Process user's answer and determine next question
        Adapts based on the answer provided
        """
        # Store answer
        self.session_data[question_key] = answer
        
        # Check for follow-up questions
        question_data = self.questions.get(question_key, {})
        follow_up_key = question_data.get("follow_up")
        
        # Adapt based on specific answers
        self._adapt_questions_based_on_answer(question_key, answer)
        
        # Get next question
        next_question = None
        if follow_up_key and follow_up_key not in self.session_data:
            # Priority follow-up
            next_question = self._format_question(follow_up_key, self.questions[follow_up_key])
        else:
            next_question = self.get_next_question()
        
        # Check if we have enough for basic matching
        can_match = self._has_minimum_data()
        
        return {
            "next_question": next_question,
            "progress": self.calculate_progress(),
            "can_start_matching": can_match,
            "estimated_questions_remaining": self.estimate_remaining_questions(),
            "session_data": self.session_data
        }
    
    def _adapt_questions_based_on_answer(self, key: str, answer: Any):
        """
        Dynamically adjust question priorities based on answers
        Makes the system truly adaptive
        """
        # If organization is faith-based, increase priority of denomination question
        if key == "org_type" and answer == "Faith-based":
            if "faith_denomination" in self.questions:
                self.questions["faith_denomination"]["priority"] = QuestionPriority.HIGH
        
        # If budget is small, skip complex grant questions
        if key == "annual_budget" and answer in ["Under $100K"]:
            # Lower priority of complex questions
            if "grant_writer" in self.questions:
                self.questions["grant_writer"]["priority"] = QuestionPriority.LOW
        
        # If urgency is immediate, skip low-priority questions
        if key == "urgency" and answer == "Immediately (1-3 months)":
            # Mark all LOW priority as CONDITIONAL (skip unless needed)
            for q_key, q_data in self.questions.items():
                if q_data["priority"] == QuestionPriority.LOW:
                    q_data["priority"] = QuestionPriority.CONDITIONAL
                    q_data["condition"] = lambda x: False  # Skip
    
    def _has_minimum_data(self) -> bool:
        """Check if we have enough data to start grant matching"""
        required_fields = ["org_name", "mission", "org_type"]
        return all(field in self.session_data for field in required_fields)
    
    def calculate_progress(self) -> Dict[str, Any]:
        """Calculate discovery progress"""
        # Count answered questions by priority
        critical_answered = sum(1 for k, v in self.questions.items() 
                               if v["priority"] == QuestionPriority.CRITICAL 
                               and k in self.session_data)
        critical_total = sum(1 for v in self.questions.values() 
                           if v["priority"] == QuestionPriority.CRITICAL)
        
        high_answered = sum(1 for k, v in self.questions.items() 
                          if v["priority"] == QuestionPriority.HIGH 
                          and k in self.session_data)
        high_total = sum(1 for v in self.questions.values() 
                       if v["priority"] == QuestionPriority.HIGH)
        
        total_answered = len(self.session_data)
        
        # Calculate percentage (weight critical questions more)
        if critical_total > 0:
            critical_progress = (critical_answered / critical_total) * 50
        else:
            critical_progress = 0
            
        if high_total > 0:
            high_progress = (high_answered / high_total) * 30
        else:
            high_progress = 0
        
        other_progress = min(20, (total_answered - critical_answered - high_answered) * 4)
        
        overall_progress = critical_progress + high_progress + other_progress
        
        return {
            "percentage": min(100, int(overall_progress)),
            "answered": total_answered,
            "critical_complete": critical_answered == critical_total,
            "status": self._get_progress_status(overall_progress)
        }
    
    def _get_progress_status(self, progress: float) -> str:
        """Get human-readable progress status"""
        if progress < 30:
            return "Just getting started"
        elif progress < 50:
            return "Building your profile"
        elif progress < 75:
            return "Almost ready for matching"
        elif progress < 100:
            return "Finalizing details"
        else:
            return "Ready for grant matching!"
    
    def estimate_remaining_questions(self) -> int:
        """Estimate how many more questions to ask"""
        # Only count CRITICAL and HIGH priority unanswered questions
        remaining = 0
        for key, q_data in self.questions.items():
            if key in self.session_data:
                continue
            if q_data["priority"] in [QuestionPriority.CRITICAL, QuestionPriority.HIGH]:
                remaining += 1
            elif q_data["priority"] == QuestionPriority.CONDITIONAL:
                # Check if condition is met
                condition = q_data.get("condition")
                if condition and condition(self.session_data):
                    remaining += 1
        
        return remaining
    
    def _format_question(self, key: str, question_data: Dict) -> Dict:
        """Format question for API response"""
        return {
            "key": key,
            "question": question_data["question"],
            "type": question_data["type"],
            "options": question_data.get("options"),
            "required": question_data.get("required", False),
            "default": question_data.get("default"),
            "max_selections": question_data.get("max_selections")
        }
    
    def _generate_session_id(self) -> str:
        """Generate unique session ID"""
        import uuid
        return str(uuid.uuid4())
    
    def get_discovery_summary(self) -> Dict[str, Any]:
        """
        Get summary of discovery session with recommendations
        Uses AI to generate personalized grant strategy
        """
        if not self._has_minimum_data():
            return {
                "error": "Insufficient data for summary",
                "required_fields": ["org_name", "mission", "org_type"]
            }
        
        # Build context for AI
        context = {
            "organization": self.session_data,
            "profile_completeness": self.calculate_progress()["percentage"],
            "data_quality": self._assess_data_quality()
        }
        
        # Generate REACTO-based strategy using optimizer
        prompt = f"""Based on this nonprofit profile, provide a grant discovery strategy:
        
Organization: {self.session_data.get('org_name')}
Mission: {self.session_data.get('mission')}
Type: {self.session_data.get('org_type')}
Budget: {self.session_data.get('annual_budget', 'Not specified')}
Location: {self.session_data.get('location', 'Not specified')}
Focus Areas: {', '.join(self.session_data.get('focus_areas', []))}
Urgency: {self.session_data.get('urgency', 'Not specified')}

Provide a JSON response with:
1. "grant_readiness_score": 1-5 (based on profile completeness)
2. "recommended_grant_types": List of 3-5 grant types to pursue
3. "estimated_success_rate": Percentage based on profile strength
4. "immediate_actions": List of 3 actions to take now
5. "profile_gaps": List of missing information that would help
6. "strategy_summary": 2-3 sentence personalized strategy"""

        result = self.optimizer.optimize_request(
            task_type="analyze_grant_fit",  # Uses GPT-4o for critical analysis
            prompt=prompt,
            context={"json_output": True, "max_tokens": 500}
        )
        
        if result.get("success"):
            return {
                "success": True,
                "profile": self.session_data,
                "analysis": result.get("content"),
                "model_used": result.get("model_used"),
                "cost_info": result.get("estimated_cost")
            }
        else:
            return {
                "success": False,
                "error": "Failed to generate strategy",
                "profile": self.session_data
            }
    
    def _assess_data_quality(self) -> str:
        """Assess quality of collected data"""
        score = 0
        max_score = 10
        
        # Check for critical fields
        if self.session_data.get("mission"):
            score += 2
        if self.session_data.get("org_type"):
            score += 2
        if self.session_data.get("location"):
            score += 1
        if self.session_data.get("annual_budget"):
            score += 1
        if self.session_data.get("focus_areas"):
            score += 2
        if self.session_data.get("target_population"):
            score += 1
        if self.session_data.get("urgency"):
            score += 1
        
        quality_percentage = (score / max_score) * 100
        
        if quality_percentage >= 80:
            return "Excellent"
        elif quality_percentage >= 60:
            return "Good"
        elif quality_percentage >= 40:
            return "Fair"
        else:
            return "Needs Improvement"

# Global instance
adaptive_discovery = AdaptiveDiscoveryService()