"""
Credential Setup Guide Service
Provides step-by-step guidance for setting up API credentials in Replit
"""

import logging
from typing import Dict, List, Any
from app.services.credential_manager import get_credential_manager, CredentialPriority

logger = logging.getLogger(__name__)

class CredentialSetupGuide:
    """Guide for setting up API credentials in Replit environment"""
    
    def __init__(self):
        self.credential_manager = get_credential_manager()
    
    def get_setup_instructions(self) -> Dict[str, Any]:
        """Get comprehensive setup instructions for all missing credentials"""
        
        missing_credentials = self.credential_manager.get_high_priority_missing_credentials()
        
        instructions = {
            "overview": {
                "title": "API Credential Setup for Pink Lemonade Grant Platform",
                "description": "Set up essential API credentials to unlock powerful grant discovery and matching features.",
                "total_missing": len(missing_credentials),
                "estimated_time": "15-30 minutes"
            },
            "priority_order": self._get_priority_order(),
            "detailed_instructions": self._get_detailed_instructions(missing_credentials),
            "replit_setup_steps": self._get_replit_setup_steps(),
            "verification_steps": self._get_verification_steps(),
            "troubleshooting": self._get_troubleshooting_guide()
        }
        
        return instructions
    
    def _get_priority_order(self) -> List[Dict[str, Any]]:
        """Get recommended setup order by priority"""
        return [
            {
                "priority": "Critical",
                "description": "Essential for core functionality",
                "credentials": ["OPENAI_API_KEY", "SESSION_SECRET"],
                "impact": "AI-powered features, user authentication"
            },
            {
                "priority": "High Priority", 
                "description": "Important for main features",
                "credentials": ["SAM_GOV_API_KEY", "CANDID_API_KEY", "SENDGRID_API_KEY"],
                "impact": "Federal grants, foundation data, email notifications"
            },
            {
                "priority": "Medium Priority",
                "description": "Enhanced functionality",
                "credentials": ["ZYTE_API_KEY", "FDO_API_KEY", "CANDID_NEWS_KEY"],
                "impact": "Advanced scraping, comprehensive foundation data"
            },
            {
                "priority": "Low Priority",
                "description": "Optional features",
                "credentials": ["GRANTWATCH_API_KEY", "MICHIGAN_SOCRATA_API_KEY"],
                "impact": "Additional grant sources, state-specific data"
            }
        ]
    
    def _get_detailed_instructions(self, missing_credentials: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get detailed setup instructions for each missing credential"""
        
        detailed_instructions = []
        
        for cred in missing_credentials:
            instruction = {
                "credential_name": cred["name"],
                "env_var": cred["env_var"],
                "service_name": cred["service_name"],
                "priority": cred["priority"],
                "description": cred["description"],
                "setup_url": cred["setup_url"],
                "steps": self._get_service_specific_steps(cred["credential_id"]),
                "validation": self._get_validation_info(cred["credential_id"]),
                "cost_info": self._get_cost_information(cred["credential_id"])
            }
            detailed_instructions.append(instruction)
        
        return detailed_instructions
    
    def _get_service_specific_steps(self, credential_id: str) -> List[str]:
        """Get service-specific setup steps"""
        
        steps_map = {
            "sam_gov_api_key": [
                "Visit https://api.sam.gov/getting-started",
                "Create a SAM.gov account or sign in to existing account",
                "Navigate to 'API Access' in your account dashboard",
                "Generate a new API key for your application",
                "Copy the API key (starts with alphanumeric characters)",
                "Add to Replit Secrets as 'SAM_GOV_API_KEY'"
            ],
            "candid_api_key": [
                "Visit https://candid.org/about/products-services/apis",
                "Contact Candid sales team or create developer account",
                "Subscribe to appropriate API plan (varies by needs)",
                "Receive API credentials via email or dashboard",
                "Copy the API key provided",
                "Add to Replit Secrets as 'CANDID_API_KEY'"
            ],
            "zyte_api_key": [
                "Visit https://www.zyte.com/api/",
                "Create a Zyte account",
                "Choose appropriate pricing plan",
                "Navigate to API credentials in dashboard",
                "Copy your API key",
                "Add to Replit Secrets as 'ZYTE_API_KEY'"
            ],
            "sendgrid_api_key": [
                "Visit https://sendgrid.com/",
                "Create SendGrid account",
                "Navigate to Settings > API Keys",
                "Click 'Create API Key'",
                "Choose 'Full Access' or configure specific permissions",
                "Copy the API key (starts with 'SG.')",
                "Add to Replit Secrets as 'SENDGRID_API_KEY'"
            ]
        }
        
        return steps_map.get(credential_id, [
            f"Visit the service website",
            "Create an account or sign in",
            "Navigate to API settings or developer section",
            "Generate a new API key",
            "Copy the provided API key",
            f"Add to Replit Secrets with the appropriate variable name"
        ])
    
    def _get_validation_info(self, credential_id: str) -> Dict[str, Any]:
        """Get validation information for a credential"""
        
        config = self.credential_manager.credentials.get(credential_id)
        
        validation = {
            "format_requirements": [],
            "testing_endpoint": None,
            "common_errors": []
        }
        
        # Only access config attributes if config exists and is a CredentialConfig object
        if config is not None:
            # Check for required prefix in credential config
            if hasattr(config, 'required_prefix') and config.required_prefix:
                validation["format_requirements"].append(f"Must start with '{config.required_prefix}'")
            
            # Check for minimum length requirement in credential config
            if hasattr(config, 'min_length') and config.min_length:
                validation["format_requirements"].append(f"Minimum length: {config.min_length} characters")
        
        # Add service-specific validation info
        validation_map = {
            "sam_gov_api_key": {
                "testing_endpoint": "https://api.sam.gov/entity-information/v3/entities?api_key=YOUR_KEY&limit=1",
                "common_errors": [
                    "401 Unauthorized: Invalid API key",
                    "403 Forbidden: Key lacks required permissions",
                    "429 Too Many Requests: Rate limit exceeded"
                ]
            },
            "sendgrid_api_key": {
                "testing_endpoint": "Use SendGrid's API key validation endpoint",
                "common_errors": [
                    "401 Unauthorized: Invalid API key format",
                    "403 Forbidden: Insufficient permissions"
                ]
            }
        }
        
        if credential_id in validation_map:
            validation.update(validation_map[credential_id])
        
        return validation
    
    def _get_cost_information(self, credential_id: str) -> Dict[str, Any]:
        """Get cost information for a service"""
        
        cost_info_map = {
            "openai_api_key": {
                "pricing_model": "Pay-per-use",
                "typical_cost": "$0.002 per 1K tokens (GPT-3.5)",
                "free_tier": "$5 free credits for new accounts",
                "notes": "Costs vary by model used (GPT-3.5, GPT-4, etc.)"
            },
            "sam_gov_api_key": {
                "pricing_model": "Free",
                "typical_cost": "Free for most endpoints",
                "free_tier": "10,000 requests per day",
                "notes": "Government data - publicly available"
            },
            "candid_api_key": {
                "pricing_model": "Subscription-based",
                "typical_cost": "Varies by plan ($100-$1000+ per month)",
                "free_tier": "Limited trial available",
                "notes": "Contact Candid for pricing details"
            },
            "sendgrid_api_key": {
                "pricing_model": "Freemium",
                "typical_cost": "Free up to 100 emails/day",
                "free_tier": "100 emails per day permanently free",
                "notes": "Paid plans start at $19.95/month"
            },
            "zyte_api_key": {
                "pricing_model": "Pay-per-request",
                "typical_cost": "$0.005-$0.10 per request",
                "free_tier": "1,000 free requests for trial",
                "notes": "Professional web scraping service"
            }
        }
        
        return cost_info_map.get(credential_id, {
            "pricing_model": "Varies",
            "typical_cost": "Check service website for current pricing",
            "free_tier": "May be available",
            "notes": "Contact the service provider for details"
        })
    
    def _get_replit_setup_steps(self) -> List[str]:
        """Get Replit-specific setup steps"""
        
        return [
            "1. Open your Replit project",
            "2. Click on the 'Secrets' tab in the left sidebar (🔒 icon)",
            "3. Click 'New Secret' button",
            "4. Enter the exact environment variable name (e.g., 'SAM_GOV_API_KEY')",
            "5. Paste your API key in the value field",
            "6. Click 'Add Secret' to save",
            "7. Restart your application to load the new secret",
            "8. Verify the credential is working using the status API"
        ]
    
    def _get_verification_steps(self) -> List[Dict[str, Any]]:
        """Get verification steps for confirming credentials work"""
        
        return [
            {
                "step": "Check Credential Status API",
                "endpoint": "/api/credentials/status",
                "description": "Visit this endpoint to see all credential statuses"
            },
            {
                "step": "Test Specific Service",
                "endpoint": "/api/credentials/validate/{credential_id}",
                "description": "Test individual credentials for proper validation"
            },
            {
                "step": "View Enabled Services",
                "endpoint": "/api/credentials/services/enabled",
                "description": "See which services are now enabled with your credentials"
            },
            {
                "step": "Check Application Logs",
                "description": "Monitor the application logs for any credential-related errors"
            }
        ]
    
    def _get_troubleshooting_guide(self) -> Dict[str, List[str]]:
        """Get troubleshooting guide for common credential issues"""
        
        return {
            "Invalid API Key Format": [
                "Double-check you copied the entire API key",
                "Verify there are no extra spaces or characters",
                "Check if the key has a required prefix (e.g., 'sk-', 'SG.')",
                "Ensure you're using the correct environment variable name"
            ],
            "Authentication Errors (401/403)": [
                "Verify the API key is active and not expired",
                "Check if your account has proper permissions",
                "Ensure you're using the production API key, not a test key",
                "Contact the service provider if the key should be working"
            ],
            "Rate Limiting (429 Errors)": [
                "Check your API usage limits with the provider",
                "Consider upgrading to a higher tier plan",
                "Implement request throttling in your application",
                "Monitor your API usage patterns"
            ],
            "Secret Not Loading in Replit": [
                "Ensure the secret name exactly matches the expected variable name",
                "Restart your Replit application after adding secrets",
                "Check the Secrets tab to confirm the secret was saved",
                "Verify your application is reading from environment variables"
            ]
        }
    
    def generate_credential_report(self) -> str:
        """Generate a formatted credential setup report"""
        
        report = self.credential_manager.get_service_status_report()
        
        report_lines = [
            "=" * 60,
            "CREDENTIAL MANAGEMENT SETUP REPORT",
            "=" * 60,
            "",
            f"📊 SUMMARY:",
            f"   Total Credentials: {report['summary']['total_credentials']}",
            f"   ✅ Available: {report['summary']['available']}",
            f"   ❌ Missing: {report['summary']['missing']}",
            f"   ⚠️  Invalid: {report['summary']['invalid']}",
            "",
            f"🚀 ENABLED SERVICES ({len(report['enabled_services'])}):",
        ]
        
        for service in report['enabled_services']:
            report_lines.append(f"   ✅ {service}")
        
        report_lines.extend([
            "",
            f"⚠️  DISABLED SERVICES ({len(report['disabled_services'])}):",
        ])
        
        for service_info in report['disabled_services']:
            report_lines.append(f"   ❌ {service_info['service']}: {service_info['reason']}")
        
        report_lines.extend([
            "",
            "📋 NEXT STEPS:",
        ])
        
        for step in report['next_steps']:
            report_lines.append(f"   {step}")
        
        report_lines.extend([
            "",
            "🔗 SETUP ENDPOINTS:",
            "   • Status Check: /api/credentials/status",
            "   • Setup Guide: /api/credentials/setup-guide",
            "   • Missing Credentials: /api/credentials/missing?priority=high",
            "",
            "=" * 60
        ])
        
        return "\n".join(report_lines)


# Global instance
credential_setup_guide = CredentialSetupGuide()

def get_credential_setup_guide() -> CredentialSetupGuide:
    """Get the global credential setup guide instance"""
    return credential_setup_guide