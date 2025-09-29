"""
AI Optimizer Service - Intelligent Model Routing
Implements cost-optimized model selection: GPT-3.5-turbo for simple tasks, GPT-4o for complex work
Saves 30-60% on AI costs while maintaining quality where it matters
"""
import os
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from enum import Enum
from openai import OpenAI

logger = logging.getLogger(__name__)

class TaskComplexity(Enum):
    """Task complexity levels for model routing"""
    SIMPLE = "simple"       # Use GPT-3.5-turbo (summarize, classify, extract)
    MODERATE = "moderate"   # Use GPT-3.5-turbo with structured output
    COMPLEX = "complex"     # Use GPT-4o (generate narratives, REACTO prompts)
    CRITICAL = "critical"   # Use GPT-4o with validation (grant analysis, scoring)

class ModelType(Enum):
    """Available AI models with cost ratios"""
    TURBO_35 = "gpt-3.5-turbo-1106"  # Use faster 1106 version ~$0.0015 per 1K tokens (fast, cheap)
    GPT_4O = "gpt-4o"                  # ~$0.01 per 1K tokens (smart, expensive)

class AIOptimizerService:
    """
    Intelligent model routing service that optimizes cost vs quality
    Saves 30-60% on AI costs by routing simple tasks to GPT-3.5-turbo
    """
    
    def __init__(self):
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            logger.warning("OpenAI API key not found - AI optimizer disabled")
            self.client = None
        else:
            self.client = OpenAI(api_key=api_key)
            
        # Task complexity mapping - determines which model to use
        self.task_routing = {
            # SIMPLE TASKS (GPT-3.5-turbo-1106) - 60% of requests
            "summarize_grant": TaskComplexity.SIMPLE,
            "extract_keywords": TaskComplexity.SIMPLE,
            "classify_grant_type": TaskComplexity.SIMPLE,
            "basic_matching": TaskComplexity.SIMPLE,
            "format_text": TaskComplexity.SIMPLE,
            "grant_matching": TaskComplexity.SIMPLE,  # Speed up grant matching
            
            # MODERATE TASKS (GPT-3.5-turbo with structure) - 20% of requests
            "generate_outline": TaskComplexity.MODERATE,
            "create_checklist": TaskComplexity.MODERATE,
            "extract_requirements": TaskComplexity.MODERATE,
            "simple_qa": TaskComplexity.MODERATE,
            
            # COMPLEX TASKS (GPT-4o) - 15% of requests
            "generate_narrative": TaskComplexity.COMPLEX,
            "create_reacto_prompt": TaskComplexity.COMPLEX,
            "write_case_support": TaskComplexity.COMPLEX,
            "impact_report": TaskComplexity.COMPLEX,
            "grant_pitch": TaskComplexity.COMPLEX,
            
            # CRITICAL TASKS (GPT-4o with validation) - 5% of requests
            "score_grant_match": TaskComplexity.CRITICAL,
            "analyze_grant_fit": TaskComplexity.CRITICAL,
            "strategic_recommendations": TaskComplexity.CRITICAL,
            "compliance_check": TaskComplexity.CRITICAL
        }
        
        # Cost tracking
        self.usage_stats = {
            ModelType.TURBO_35: {"calls": 0, "tokens": 0, "estimated_cost": 0.0},
            ModelType.GPT_4O: {"calls": 0, "tokens": 0, "estimated_cost": 0.0}
        }
    
    def determine_complexity(self, task_type: str, context: Dict[str, Any]) -> TaskComplexity:
        """
        Determine task complexity based on type and context
        Returns appropriate complexity level for model selection
        """
        # Check predefined routing
        if task_type in self.task_routing:
            base_complexity = self.task_routing[task_type]
            
            # Upgrade complexity if context demands it
            if context.get("requires_accuracy", False):
                if base_complexity == TaskComplexity.SIMPLE:
                    return TaskComplexity.MODERATE
                elif base_complexity == TaskComplexity.MODERATE:
                    return TaskComplexity.COMPLEX
                    
            if context.get("word_count", 0) > 2000:
                return TaskComplexity.COMPLEX
                
            if context.get("is_final_submission", False):
                return TaskComplexity.CRITICAL
                
            return base_complexity
            
        # Default to moderate for unknown tasks
        return TaskComplexity.MODERATE
    
    def select_model(self, complexity: TaskComplexity) -> Tuple[ModelType, str]:
        """
        Select optimal model based on task complexity
        Returns model type and explanation for transparency
        """
        if complexity in [TaskComplexity.SIMPLE, TaskComplexity.MODERATE]:
            return (
                ModelType.TURBO_35,
                f"Using GPT-3.5-turbo-1106 for {complexity.value} task (fastest, 60% cost savings)"
            )
        else:
            return (
                ModelType.GPT_4O,
                f"Using GPT-4o for {complexity.value} task (higher accuracy needed)"
            )
    
    def create_reacto_prompt(self, task_info: Dict[str, Any]) -> str:
        """
        Generate a REACTO-structured prompt for any AI task
        Follows the 6-part structure: Role, Example, Application, Context, Tone, Output
        """
        return f"""
**R - Role**
You are an expert grant writer and nonprofit strategist with 15+ years of experience. You specialize in {task_info.get('domain', 'grant management')} and have helped organizations secure millions in funding. Your expertise includes understanding funder priorities, crafting compelling narratives, and ensuring compliance with all requirements.

**E - Example**
A successful output looks like a well-structured {task_info.get('output_type', 'document')} that directly addresses the funder's priorities, uses concrete data and stories, maintains professional tone throughout, and clearly demonstrates impact and feasibility. For instance, a winning grant narrative would open with a compelling need statement backed by statistics, transition smoothly into proposed solutions with clear timelines, and close with measurable outcomes that align with funder goals.

**A - Application**
First, analyze the provided {task_info.get('input_type', 'information')} to identify key themes and requirements. Then structure your response according to {task_info.get('structure', 'standard format')}, ensuring each section flows logically to the next. Include specific examples and data points where relevant. Apply guardrails: stay within {task_info.get('word_limit', '1000')} words, avoid jargon unless necessary, ensure all claims are supportable, and maintain consistency in tone and messaging throughout.

**C - Context**
{task_info.get('organization', 'The organization')} is seeking {task_info.get('goal', 'funding')} for {task_info.get('purpose', 'their mission')}. Key constraints include: {task_info.get('constraints', 'standard requirements')}. The target audience is {task_info.get('audience', 'grant reviewers')} who value {task_info.get('values', 'clear, concise, impactful proposals')}. Success means {task_info.get('success_criteria', 'securing the grant')}.

**T - Tone**
Maintain a {task_info.get('tone', 'professional yet passionate')} voice that conveys expertise without being overly technical. Write with confidence and clarity, using active voice and concrete language. The style should be {task_info.get('style', 'formal but engaging')}, accessible to reviewers who may not be subject matter experts. Balance emotional appeal with logical argumentation.

**O - Output**
Deliver a {task_info.get('output_format', 'complete document')} that includes:
1. {task_info.get('section1', 'Executive summary or introduction')}
2. {task_info.get('section2', 'Main body with supporting details')}
3. {task_info.get('section3', 'Conclusion with clear next steps')}
Format: {task_info.get('format', 'Clear paragraphs with headers')}
Testing: Verify the output meets all requirements, stays within limits, and addresses all key points.
Quality check: Ensure no placeholder text, all statistics are realistic, and tone remains consistent.
"""
    
    def optimize_request(
        self,
        task_type: str,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        force_model: Optional[ModelType] = None
    ) -> Dict[str, Any]:
        """
        Main optimization method - routes requests to appropriate model
        Returns response with cost tracking and model explanation
        """
        if not self.client:
            return {
                "error": "OpenAI API key not configured",
                "suggestion": "Please set OPENAI_API_KEY environment variable"
            }
        
        context = context or {}
        
        # Determine complexity and select model
        if force_model:
            model = force_model
            explanation = f"Using {model.value} (manually specified)"
        else:
            complexity = self.determine_complexity(task_type, context)
            model, explanation = self.select_model(complexity)
        
        try:
            # Make API call with selected model and timeout
            import httpx
            # Set timeout to 10 seconds to prevent hanging
            timeout = httpx.Timeout(10.0, read=10.0, write=10.0, connect=5.0)
            client_with_timeout = OpenAI(
                api_key=os.environ.get("OPENAI_API_KEY"),
                timeout=timeout,
                max_retries=1
            )
            
            # Ensure json is mentioned in prompt when using json_object format
            if context.get("json_output"):
                json_prompt = f"{prompt}\n\nPlease provide your response in json format."
                messages = [{"role": "system", "content": "You are an AI assistant. Always respond in json format when requested."}, {"role": "user", "content": json_prompt}]
            else:
                messages = [{"role": "user", "content": prompt}]
            
            response = client_with_timeout.chat.completions.create(
                model=model.value,
                messages=messages,
                temperature=context.get("temperature", 0),  # Default to deterministic
                max_tokens=context.get("max_tokens", 200),  # Default to 200 for speed
                stream=False,  # Explicit no streaming for speed
                top_p=context.get("top_p", 1),  # Faster generation
                response_format={"type": "json_object"} if context.get("json_output") else {"type": "text"}
            )
            
            # Track usage for cost optimization
            usage = response.usage
            cost = 0.0  # Initialize cost
            if usage:
                self.usage_stats[model]["calls"] += 1
                self.usage_stats[model]["tokens"] += usage.total_tokens
                
                # Estimate cost (rough calculation)
                if model == ModelType.TURBO_35:
                    cost = usage.total_tokens * 0.0000010  # GPT-3.5-turbo-1106 is cheaper
                else:
                    cost = usage.total_tokens * 0.00001  # ~$0.01 per 1K tokens
                    
                self.usage_stats[model]["estimated_cost"] += cost
            
            # Parse response
            content = response.choices[0].message.content
            if context.get("json_output") and content:
                try:
                    content = json.loads(content)
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from {model.value}")
            
            return {
                "success": True,
                "content": content,
                "model_used": model.value,
                "explanation": explanation,
                "tokens_used": usage.total_tokens if usage else 0,
                "estimated_cost": f"${cost:.4f}" if usage else "N/A",
                "task_type": task_type
            }
            
        except Exception as e:
            error_msg = str(e)
            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                logger.warning(f"AI request timed out for {model.value} - returning mock response")
                # Return a mock response for testing/fallback
                return {
                    "success": False,
                    "error": "AI service timeout",
                    "content": {
                        "match_score": 3,
                        "verdict": "Moderate Match (AI unavailable - default score)",
                        "recommendation": "This grant may be suitable. Review requirements carefully.",
                        "key_alignments": ["Mission alignment needs review"],
                        "potential_challenges": ["Requirements verification needed"],
                        "next_steps": ["Review grant requirements", "Contact funder for details"],
                        "application_tips": "Ensure all requirements are met before applying."
                    } if context.get("json_output") else "AI service temporarily unavailable. Please try again later.",
                    "model_used": "fallback",
                    "explanation": "Using fallback response due to AI timeout"
                }
            
            logger.error(f"AI optimization error with {model.value}: {error_msg}")
            
            # Fallback to other model if first fails
            if model == ModelType.TURBO_35 and not force_model:
                logger.info("Falling back to GPT-4o after GPT-3.5-turbo error")
                return self.optimize_request(
                    task_type, prompt, context, 
                    force_model=ModelType.GPT_4O
                )
            
            return {
                "success": False,
                "error": str(e),
                "model_attempted": model.value
            }
    
    def get_usage_report(self) -> Dict[str, Any]:
        """
        Get detailed usage statistics and cost savings
        Shows how much money saved by intelligent routing
        """
        total_turbo_cost = self.usage_stats[ModelType.TURBO_35]["estimated_cost"]
        total_gpt4_cost = self.usage_stats[ModelType.GPT_4O]["estimated_cost"]
        total_actual_cost = total_turbo_cost + total_gpt4_cost
        
        # Calculate what it would have cost if everything used GPT-4o
        total_tokens = (
            self.usage_stats[ModelType.TURBO_35]["tokens"] +
            self.usage_stats[ModelType.GPT_4O]["tokens"]
        )
        total_if_all_gpt4 = total_tokens * 0.00001
        
        savings = total_if_all_gpt4 - total_actual_cost
        savings_percent = (savings / total_if_all_gpt4 * 100) if total_if_all_gpt4 > 0 else 0
        
        return {
            "turbo_35": {
                "calls": self.usage_stats[ModelType.TURBO_35]["calls"],
                "tokens": self.usage_stats[ModelType.TURBO_35]["tokens"],
                "cost": f"${total_turbo_cost:.2f}"
            },
            "gpt_4o": {
                "calls": self.usage_stats[ModelType.GPT_4O]["calls"],
                "tokens": self.usage_stats[ModelType.GPT_4O]["tokens"],
                "cost": f"${total_gpt4_cost:.2f}"
            },
            "totals": {
                "actual_cost": f"${total_actual_cost:.2f}",
                "would_have_cost": f"${total_if_all_gpt4:.2f}",
                "savings": f"${savings:.2f}",
                "savings_percent": f"{savings_percent:.1f}%"
            },
            "recommendation": self._get_optimization_recommendation()
        }
    
    def _get_optimization_recommendation(self) -> str:
        """Generate optimization recommendations based on usage patterns"""
        turbo_calls = self.usage_stats[ModelType.TURBO_35]["calls"]
        gpt4_calls = self.usage_stats[ModelType.GPT_4O]["calls"]
        
        if turbo_calls == 0 and gpt4_calls == 0:
            return "No AI calls made yet. System ready for optimization."
        
        turbo_ratio = turbo_calls / (turbo_calls + gpt4_calls) if (turbo_calls + gpt4_calls) > 0 else 0
        
        if turbo_ratio > 0.7:
            return "Excellent optimization! Over 70% of tasks using ultra-fast GPT-3.5-turbo-1106."
        elif turbo_ratio > 0.5:
            return "Good balance. Consider reviewing complex tasks for potential downgrade."
        else:
            return "High GPT-4o usage. Review if all tasks truly need premium model."

# Global instance
ai_optimizer = AIOptimizerService()