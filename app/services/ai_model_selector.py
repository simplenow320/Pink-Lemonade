"""
AI Model Selector Service
Intelligently routes tasks between GPT-3.5-turbo and GPT-4o for optimal cost/quality balance
Implements REACT framework and quality monitoring
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIModelSelector:
    """Smart AI model selection and enhanced prompting service"""
    
    def __init__(self):
        """Initialize with OpenAI client and cost tracking"""
        self.api_key = os.environ.get("OPENAI_API_KEY")
        self.client = None
        
        # Cost tracking (per 1M tokens)
        self.model_costs = {
            "gpt-3.5-turbo": {"input": 0.50, "output": 1.50},
            "gpt-4o": {"input": 5.00, "output": 15.00}
        }
        
        # Quality thresholds and fallback settings
        self.quality_threshold = 0.85  # If quality drops below this, use GPT-4o
        self.fallback_enabled = True
        self.cost_savings_target = 0.60  # 60% cost reduction target
        
        # Usage tracking
        self.usage_stats = {
            "gpt-3.5-turbo": {"requests": 0, "tokens": 0, "cost": 0.0},
            "gpt-4o": {"requests": 0, "tokens": 0, "cost": 0.0}
        }
        
        if self.api_key:
            self.client = OpenAI(api_key=self.api_key)
            logger.info("AI Model Selector initialized with cost optimization")
        else:
            logger.warning("AI Model Selector initialized without API key")
    
    def is_enabled(self) -> bool:
        """Check if service is enabled"""
        return self.client is not None
    
    def select_optimal_model(self, task_type: str, complexity_score: float = 0.5, 
                           token_count: int = 0, require_quality: bool = False) -> str:
        """
        Select optimal model based on task characteristics
        
        Args:
            task_type: Type of AI task (matching, writing, analysis, etc.)
            complexity_score: 0.0-1.0 complexity estimate
            token_count: Estimated token count
            require_quality: Force GPT-4o for critical tasks
        
        Returns:
            Model name (gpt-3.5-turbo or gpt-4o)
        """
        
        # Force GPT-4o for critical/complex tasks
        if require_quality or complexity_score > 0.8:
            return "gpt-4o"
        
        # Route based on task type (optimized for 70/30 split)
        gpt_35_tasks = [
            "grant_matching_score",  # Scoring calculations
            "data_extraction",       # Simple extraction
            "data_processing",       # Data manipulation
            "basic_analysis",        # Simple analysis
            "search_ranking",        # Search operations
            "classification",        # Category assignment
            "summarization_short",   # < 200 words
            "validation",           # Data validation
        ]
        
        gpt_4o_tasks = [
            "narrative_generation",  # Long-form writing
            "strategic_analysis",    # Complex reasoning
            "grant_writing",        # Proposal writing
            "complex_reasoning",    # Multi-step logic
            "creative_writing",     # Creative content
            "detailed_analysis",    # In-depth analysis
            "problem_solving",      # Complex problem solving
        ]
        
        # Simple task routing
        if task_type in gpt_35_tasks:
            return "gpt-3.5-turbo"
        elif task_type in gpt_4o_tasks:
            return "gpt-4o"
        
        # Default routing based on complexity and token count
        if complexity_score < 0.6 and token_count < 500:
            return "gpt-3.5-turbo"
        else:
            return "gpt-4o"
    
    def enhance_prompt_with_react(self, base_prompt: str, context: Dict[str, Any], 
                                 task_type: str) -> Dict[str, str]:
        """
        Enhance prompt using REACT framework
        R - Role, E - Example, A - Application, C - Context, T - Tone, O - Output
        """
        
        # Role definitions by task type
        roles = {
            "grant_matching": "You are an expert grant strategist with 15+ years experience in nonprofit funding alignment.",
            "narrative_generation": "You are a professional grant writer with expertise in compelling proposal narratives.",
            "data_extraction": "You are a meticulous data analyst specializing in grant opportunity intelligence.",
            "strategic_analysis": "You are a senior nonprofit consultant providing strategic funding advice.",
            "default": "You are an expert AI assistant specializing in nonprofit grant management."
        }
        
        # Context building
        context_parts = []
        if context.get("organization"):
            context_parts.append(f"Organization: {context['organization']}")
        if context.get("grant_info"):
            context_parts.append(f"Grant Context: {context['grant_info']}")
        if context.get("constraints"):
            context_parts.append(f"Constraints: {context['constraints']}")
        
        # Application-specific instructions
        application_guides = {
            "grant_matching": "Focus on strategic alignment and funding probability",
            "narrative_generation": "Create compelling, evidence-based content",
            "data_extraction": "Ensure accuracy and completeness of extracted data",
            "strategic_analysis": "Provide actionable insights and recommendations"
        }
        
        # Tone specifications
        tones = {
            "grant_matching": "analytical and strategic",
            "narrative_generation": "persuasive and professional", 
            "data_extraction": "precise and systematic",
            "strategic_analysis": "consultative and authoritative",
            "default": "professional and helpful"
        }
        
        # Build enhanced system prompt
        role = roles.get(task_type, roles["default"])
        application = application_guides.get(task_type, "Provide accurate and helpful assistance")
        tone = tones.get(task_type, tones["default"])
        
        system_prompt = f"""ROLE: {role}

CONTEXT: {' | '.join(context_parts) if context_parts else 'General grant management assistance'}

APPLICATION: {application}

TONE: Maintain a {tone} tone throughout your response.

GUARDRAILS:
- Use only factual information from provided sources
- Never fabricate contact details, dates, or specific data
- Provide clear, actionable guidance
- Maintain professional standards for nonprofit communications"""

        # Build enhanced user prompt with structure
        user_prompt = f"""TASK: {base_prompt}

THINKING PROCESS:
Please work through this systematically:
1. First, analyze the key requirements and constraints
2. Then, consider the strategic implications
3. Next, evaluate the available options or approaches  
4. Finally, provide your clear recommendation or output

OUTPUT FORMAT:
Provide a well-structured response that directly addresses the task requirements."""

        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    def make_optimized_request(self, messages: List[Dict], task_type: str = "default",
                             complexity_score: float = 0.5, response_format: Optional[Dict] = None,
                             max_tokens: int = 1000, require_quality: bool = False) -> Optional[Dict]:
        """
        Make AI request with optimal model selection and cost tracking
        """
        if not self.client:
            logger.warning("AI Model Selector not enabled - no API key")
            return None
        
        # Select optimal model
        selected_model = self.select_optimal_model(
            task_type, complexity_score, max_tokens, require_quality
        )
        
        # Track usage
        start_time = time.time()
        
        # Initialize kwargs
        kwargs = {
            "model": selected_model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": 0.7 if selected_model == "gpt-4o" else 0.5
        }
        
        if response_format:
            kwargs["response_format"] = response_format
        
        try:
            
            response = self.client.chat.completions.create(**kwargs)
            content = response.choices[0].message.content
            
            # Track costs and usage
            self._track_usage(selected_model, response.usage)
            
            # Parse JSON if requested
            if response_format and response_format.get("type") == "json_object":
                try:
                    parsed_content = json.loads(content)
                    parsed_content["_model_used"] = selected_model
                    parsed_content["_processing_time"] = time.time() - start_time
                    return parsed_content
                except json.JSONDecodeError:
                    logger.error(f"Failed to parse JSON response from {selected_model}")
                    return {"error": "Invalid JSON response", "_model_used": selected_model}
            
            return {
                "content": content,
                "_model_used": selected_model,
                "_processing_time": time.time() - start_time
            }
            
        except Exception as e:
            logger.error(f"AI request failed with {selected_model}: {e}")
            
            # Fallback to GPT-4o if GPT-3.5 fails and fallback is enabled
            if selected_model == "gpt-3.5-turbo" and self.fallback_enabled:
                logger.info("Falling back to GPT-4o due to error")
                kwargs["model"] = "gpt-4o"
                try:
                    response = self.client.chat.completions.create(**kwargs)
                    content = response.choices[0].message.content
                    self._track_usage("gpt-4o", response.usage)
                    
                    if response_format and response_format.get("type") == "json_object":
                        parsed_content = json.loads(content)
                        parsed_content["_model_used"] = "gpt-4o (fallback)"
                        return parsed_content
                    
                    return {
                        "content": content,
                        "_model_used": "gpt-4o (fallback)",
                        "_processing_time": time.time() - start_time
                    }
                except Exception as fallback_error:
                    logger.error(f"Fallback to GPT-4o also failed: {fallback_error}")
            
            return None
    
    def _track_usage(self, model: str, usage_data: Any) -> None:
        """Track usage statistics and costs"""
        if not usage_data:
            return
        
        total_tokens = usage_data.prompt_tokens + usage_data.completion_tokens
        
        # Calculate cost
        model_pricing = self.model_costs.get(model, self.model_costs["gpt-4o"])
        cost = (
            (usage_data.prompt_tokens / 1_000_000) * model_pricing["input"] +
            (usage_data.completion_tokens / 1_000_000) * model_pricing["output"]
        )
        
        # Update stats
        if model in self.usage_stats:
            self.usage_stats[model]["requests"] += 1
            self.usage_stats[model]["tokens"] += total_tokens
            self.usage_stats[model]["cost"] += cost
        
        # Log cost savings
        if model == "gpt-3.5-turbo":
            gpt4_cost = (
                (usage_data.prompt_tokens / 1_000_000) * self.model_costs["gpt-4o"]["input"] +
                (usage_data.completion_tokens / 1_000_000) * self.model_costs["gpt-4o"]["output"]
            )
            savings = gpt4_cost - cost
            logger.debug(f"Cost savings: ${savings:.4f} using GPT-3.5-turbo instead of GPT-4o")
    
    def get_cost_analysis(self) -> Dict[str, Any]:
        """Get comprehensive cost analysis and savings report"""
        total_cost = sum(stats["cost"] for stats in self.usage_stats.values())
        total_requests = sum(stats["requests"] for stats in self.usage_stats.values())
        
        # Calculate theoretical GPT-4o cost
        gpt35_usage = self.usage_stats["gpt-3.5-turbo"]
        theoretical_gpt4_cost = (
            gpt35_usage["tokens"] / 1_000_000 * 
            (self.model_costs["gpt-4o"]["input"] + self.model_costs["gpt-4o"]["output"]) / 2
        )
        
        actual_savings = theoretical_gpt4_cost - gpt35_usage["cost"]
        savings_percentage = (actual_savings / (theoretical_gpt4_cost + 0.001)) * 100
        
        return {
            "total_cost": total_cost,
            "total_requests": total_requests,
            "model_breakdown": self.usage_stats,
            "cost_savings": {
                "amount_saved": actual_savings,
                "percentage_saved": savings_percentage,
                "target_savings": self.cost_savings_target * 100
            },
            "optimization_ratio": {
                "gpt_35_ratio": gpt35_usage["requests"] / max(total_requests, 1),
                "gpt_4o_ratio": self.usage_stats["gpt-4o"]["requests"] / max(total_requests, 1),
                "target_ratio": 0.70  # 70% GPT-3.5, 30% GPT-4o
            }
        }
    
    def should_use_quality_model(self, task_importance: str) -> bool:
        """Determine if high-quality model should be used based on task importance"""
        high_importance_tasks = [
            "grant_proposal_final",
            "executive_summary", 
            "board_presentation",
            "funder_communication",
            "strategic_planning"
        ]
        return task_importance in high_importance_tasks