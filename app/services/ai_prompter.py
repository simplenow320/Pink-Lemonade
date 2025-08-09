"""
AI Prompter Service
Handles runtime prompt concatenation, token filling, and OpenAI API calls
"""
import os
import json
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from openai import OpenAI

logger = logging.getLogger(__name__)

class AIPrompter:
    def __init__(self, model: str = "gpt-4o"):
        """Initialize AI Prompter with OpenAI client and model"""
        api_key = os.environ.get("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.prompts_dir = Path(__file__).parent.parent / "prompts"
        
        # Load global guardrails once
        guardrails_path = self.prompts_dir / "global_guardrails.json"
        with open(guardrails_path, 'r') as f:
            self.global_guardrails = json.load(f)['system']
    
    def load_prompt_template(self, module_name: str) -> Dict[str, Any]:
        """Load a prompt template from JSON file"""
        prompt_path = self.prompts_dir / f"{module_name}.json"
        if not prompt_path.exists():
            raise FileNotFoundError(f"Prompt template not found: {module_name}.json")
        
        with open(prompt_path, 'r') as f:
            return json.load(f)
    
    def fill_tokens(self, template: Dict[str, Any], tokens: Dict[str, str]) -> Any:
        """Replace {{tokens}} in template with actual values"""
        def replace_tokens(obj):
            if isinstance(obj, str):
                for key, value in tokens.items():
                    obj = obj.replace(f"{{{{{key}}}}}", str(value))
                return obj
            elif isinstance(obj, dict):
                return {k: replace_tokens(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [replace_tokens(item) for item in obj]
            return obj
        
        return replace_tokens(template)
    
    def build_system_prompt(self, template: Dict[str, Any]) -> str:
        """Build complete system prompt with global guardrails"""
        system = template.get('system', '')
        # Replace <GLOBAL_GUARDRAILS> placeholder
        system = system.replace('<GLOBAL_GUARDRAILS>', self.global_guardrails)
        return system
    
    def build_user_prompt(self, template: Dict[str, Any], data_pack: Dict[str, Any]) -> str:
        """Build user prompt from template and data pack"""
        parts = []
        
        # Add context
        if 'context' in template:
            parts.append("Context:")
            for key, value in template['context'].items():
                parts.append(f"- {key}: {value}")
            parts.append("")
        
        # Add data pack
        if data_pack:
            parts.append("Available Data:")
            for key, value in data_pack.items():
                if value:
                    parts.append(f"\n{key.upper()}:")
                    if isinstance(value, dict):
                        parts.append(json.dumps(value, indent=2))
                    elif isinstance(value, list):
                        for item in value:
                            parts.append(f"- {item}")
                    else:
                        parts.append(str(value))
            parts.append("")
        
        # Add task instructions
        if 'task' in template and 'instructions' in template['task']:
            parts.append("Instructions:")
            for instruction in template['task']['instructions']:
                parts.append(f"- {instruction}")
            parts.append("")
        
        # Add output format requirements
        if 'output_format' in template:
            parts.append("Output Format Requirements:")
            output_format = template['output_format']
            if 'type' in output_format:
                parts.append(f"- Type: {output_format['type']}")
            if 'sections' in output_format:
                parts.append(f"- Sections: {', '.join(output_format['sections'])}")
            if 'end_with' in output_format:
                parts.append(f"- Must end with: {output_format['end_with']}")
        
        return "\n".join(parts)
    
    def run_prompt(self, module_name: str, tokens: Dict[str, str], data_pack: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a prompt with the given module, tokens, and data
        Returns: Dict with 'success', 'output', 'needs_input', and 'error' keys
        """
        try:
            # Load and prepare template
            template = self.load_prompt_template(module_name)
            template = self.fill_tokens(template, tokens)
            
            # Build prompts
            system_prompt = self.build_system_prompt(template)
            user_prompt = self.build_user_prompt(template, data_pack)
            
            # Call OpenAI API
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                max_tokens=2000
            )
            
            output = response.choices[0].message.content
            
            # Handle None output
            if output is None:
                return {
                    'success': False,
                    'output': None,
                    'needs_input': [],
                    'error': 'No output generated from AI'
                }
            
            # Check for missing info/assets
            needs_input = []
            if "Missing Info" in output or "Missing Assets" in output:
                # Extract the missing items
                lines = output.split('\n')
                in_missing_section = False
                for line in lines:
                    if "Missing Info" in line or "Missing Assets" in line:
                        in_missing_section = True
                    elif in_missing_section and line.strip().startswith('-'):
                        needs_input.append(line.strip()[1:].strip())
                    elif in_missing_section and not line.strip():
                        in_missing_section = False
            
            # Validate output based on module requirements
            validation_error = self.validate_output(module_name, template, output, data_pack)
            if validation_error:
                return {
                    'success': False,
                    'output': output,
                    'needs_input': needs_input,
                    'error': validation_error
                }
            
            return {
                'success': True if not needs_input else False,
                'output': output,
                'needs_input': needs_input,
                'error': None
            }
            
        except Exception as e:
            logger.error(f"Error running prompt for {module_name}: {str(e)}")
            return {
                'success': False,
                'output': None,
                'needs_input': [],
                'error': str(e)
            }
    
    def validate_output(self, module_name: str, template: Dict[str, Any], output: str, data_pack: Dict[str, Any]) -> Optional[str]:
        """Validate output based on module-specific rules"""
        # Check for Source Notes requirement
        output_format = template.get('output_format', {})
        if output_format.get('end_with') == 'Source Notes' and 'Source Notes' not in output:
            return "Output missing required 'Source Notes' section"
        
        # Module-specific validation
        if module_name == 'impact_report':
            # Validate budget totals if present in data_pack
            if 'budget_actuals' in data_pack and isinstance(data_pack['budget_actuals'], dict):
                stored_total = data_pack['budget_actuals'].get('total_expenses', 0)
                # This would need more sophisticated parsing of the output to extract totals
                # For now, just check if budget info is present
                if 'Financials' not in output and stored_total > 0:
                    return "Impact report missing financial section"
        
        return None

# Singleton instance
_prompter_instance = None

def get_prompter(model: str = "gpt-4o") -> AIPrompter:
    """Get or create the AI Prompter instance"""
    global _prompter_instance
    if _prompter_instance is None:
        _prompter_instance = AIPrompter(model)
    return _prompter_instance