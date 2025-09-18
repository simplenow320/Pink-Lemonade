"""
Comprehensive Credential Management System for Replit Secrets
Handles API credentials with proper validation, fallback handling, and status reporting
"""

import os
import logging
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class CredentialStatus(Enum):
    """Status of a credential"""
    AVAILABLE = "available"
    MISSING = "missing"
    INVALID = "invalid"
    DEPRECATED = "deprecated"

class CredentialPriority(Enum):
    """Priority level of credentials"""
    CRITICAL = "critical"        # Essential for core functionality
    HIGH = "high"               # Important for main features
    MEDIUM = "medium"           # Nice to have features
    LOW = "low"                 # Optional/experimental features

@dataclass
class CredentialConfig:
    """Configuration for a specific credential"""
    name: str
    env_var: str
    fallback_vars: List[str]
    priority: CredentialPriority
    description: str
    service_name: str
    validation_pattern: Optional[str] = None
    min_length: Optional[int] = None
    required_prefix: Optional[str] = None
    setup_url: Optional[str] = None

class CredentialManager:
    """Manages all API credentials with validation and status reporting"""
    
    def __init__(self):
        self.credentials = self._initialize_credential_configs()
        self.status_cache = {}
        self.last_check = None
        logger.info(f"Initialized CredentialManager with {len(self.credentials)} credential configurations")
    
    def _initialize_credential_configs(self) -> Dict[str, CredentialConfig]:
        """Initialize all credential configurations"""
        return {
            # AI Services - Critical Priority
            'openai_api_key': CredentialConfig(
                name="OpenAI API Key",
                env_var="OPENAI_API_KEY",
                fallback_vars=["OPENAI_KEY", "AI_API_KEY"],
                priority=CredentialPriority.CRITICAL,
                description="OpenAI GPT API for AI-powered grant matching and writing assistance",
                service_name="OpenAI GPT",
                validation_pattern=r"^sk-[A-Za-z0-9]{48,}$",
                min_length=48,
                required_prefix="sk-",
                setup_url="https://platform.openai.com/api-keys"
            ),
            
            # Government APIs - High Priority
            'sam_gov_api_key': CredentialConfig(
                name="SAM.gov API Key",
                env_var="SAM_GOV_API_KEY",
                fallback_vars=["SAM_API_KEY", "SAMGOV_KEY", "SAM_GOV_TOKEN"],
                priority=CredentialPriority.HIGH,
                description="SAM.gov API for federal contract opportunities and entity data",
                service_name="SAM.gov",
                min_length=32,
                setup_url="https://api.sam.gov/getting-started"
            ),
            
            'grants_gov_api_key': CredentialConfig(
                name="Grants.gov API Key",
                env_var="GRANTS_GOV_API_KEY",
                fallback_vars=["GRANTS_API_KEY", "GRANTSGOW_KEY"],
                priority=CredentialPriority.MEDIUM,
                description="Grants.gov API for federal grant opportunities (optional - has public endpoints)",
                service_name="Grants.gov",
                min_length=16,
                setup_url="https://www.grants.gov/api"
            ),
            
            # Commercial APIs - High Priority
            'candid_api_key': CredentialConfig(
                name="Candid API Key",
                env_var="CANDID_API_KEY",
                fallback_vars=["CANDID_KEY", "FOUNDATION_CENTER_KEY"],
                priority=CredentialPriority.HIGH,
                description="Candid (formerly Foundation Center) API for foundation data",
                service_name="Candid Foundation Data",
                min_length=20,
                setup_url="https://candid.org/about/products-services/apis"
            ),
            
            'candid_news_key': CredentialConfig(
                name="Candid News API Key",
                env_var="CANDID_NEWS_KEY",
                fallback_vars=["CANDID_NEWS_KEYS", "PND_API_KEY"],
                priority=CredentialPriority.MEDIUM,
                description="Candid News API for philanthropy news and RFPs",
                service_name="Candid News",
                min_length=16,
                setup_url="https://candid.org/about/products-services/apis"
            ),
            
            'candid_grants_key': CredentialConfig(
                name="Candid Grants API Key",
                env_var="CANDID_GRANTS_KEY",
                fallback_vars=["CANDID_GRANTS_KEYS"],
                priority=CredentialPriority.MEDIUM,
                description="Candid Grants API for grant opportunity data",
                service_name="Candid Grants",
                min_length=16,
                setup_url="https://candid.org/about/products-services/apis"
            ),
            
            'zyte_api_key': CredentialConfig(
                name="Zyte API Key",
                env_var="ZYTE_API_KEY",
                fallback_vars=["SCRAPINGHUB_API_KEY", "ZYTE_KEY"],
                priority=CredentialPriority.MEDIUM,
                description="Zyte API for professional web scraping of grant websites",
                service_name="Zyte Web Scraping",
                min_length=32,
                setup_url="https://www.zyte.com/api/"
            ),
            
            # Foundation Directory APIs
            'fdo_api_key': CredentialConfig(
                name="Foundation Directory Online API Key",
                env_var="FDO_API_KEY",
                fallback_vars=["FOUNDATION_DIRECTORY_KEY", "FDO_KEY"],
                priority=CredentialPriority.MEDIUM,
                description="Foundation Directory Online API for comprehensive foundation data",
                service_name="Foundation Directory",
                min_length=20,
                setup_url="https://fdo.foundationcenter.org/"
            ),
            
            'grantwatch_api_key': CredentialConfig(
                name="GrantWatch API Key",
                env_var="GRANTWATCH_API_KEY",
                fallback_vars=["GRANTWATCH_KEY"],
                priority=CredentialPriority.LOW,
                description="GrantWatch API for diverse grant opportunities",
                service_name="GrantWatch",
                min_length=16,
                setup_url="https://www.grantwatch.com/api"
            ),
            
            # Communication Services - High Priority
            'sendgrid_api_key': CredentialConfig(
                name="SendGrid API Key",
                env_var="SENDGRID_API_KEY",
                fallback_vars=["SENDGRID_KEY", "EMAIL_API_KEY"],
                priority=CredentialPriority.HIGH,
                description="SendGrid API for email notifications and communications",
                service_name="SendGrid Email",
                validation_pattern=r"^SG\.[A-Za-z0-9_-]{43,}$",
                required_prefix="SG.",
                min_length=43,
                setup_url="https://sendgrid.com/docs/ui/account-and-settings/api-keys/"
            ),
            
            # Open Data APIs - Low Priority (often public)
            'michigan_socrata_key': CredentialConfig(
                name="Michigan Socrata API Key",
                env_var="MICHIGAN_SOCRATA_API_KEY",
                fallback_vars=["SOCRATA_APP_TOKEN", "MICHIGAN_API_KEY"],
                priority=CredentialPriority.LOW,
                description="Michigan.gov Socrata API for state grant data",
                service_name="Michigan Open Data",
                min_length=16,
                setup_url="https://dev.socrata.com/foundry/"
            ),
            
            # System Credentials - Critical Priority
            'session_secret': CredentialConfig(
                name="Session Secret Key",
                env_var="SESSION_SECRET",
                fallback_vars=["SECRET_KEY", "FLASK_SECRET_KEY"],
                priority=CredentialPriority.CRITICAL,
                description="Flask session security key for user authentication",
                service_name="Flask Sessions",
                min_length=24,
                setup_url=None
            )
        }
    
    def get_credential(self, credential_id: str) -> Optional[str]:
        """Get a credential value with fallback support"""
        if credential_id not in self.credentials:
            logger.warning(f"Unknown credential ID: {credential_id}")
            return None
        
        config = self.credentials[credential_id]
        
        # Try primary environment variable
        value = os.environ.get(config.env_var)
        if value and value.strip():
            return value.strip()
        
        # Try fallback variables
        for fallback_var in config.fallback_vars:
            value = os.environ.get(fallback_var)
            if value and value.strip():
                logger.info(f"Using fallback {fallback_var} for {credential_id}")
                return value.strip()
        
        return None
    
    def validate_credential(self, credential_id: str, value: Optional[str] = None) -> Tuple[CredentialStatus, str]:
        """Validate a specific credential"""
        if credential_id not in self.credentials:
            return CredentialStatus.INVALID, f"Unknown credential: {credential_id}"
        
        config = self.credentials[credential_id]
        
        if value is None:
            value = self.get_credential(credential_id)
        
        if not value:
            return CredentialStatus.MISSING, f"{config.name} is not set"
        
        # Check minimum length
        if config.min_length and len(value) < config.min_length:
            return CredentialStatus.INVALID, f"{config.name} is too short (minimum {config.min_length} characters)"
        
        # Check required prefix
        if config.required_prefix and not value.startswith(config.required_prefix):
            return CredentialStatus.INVALID, f"{config.name} must start with '{config.required_prefix}'"
        
        # Check validation pattern
        if config.validation_pattern:
            import re
            if not re.match(config.validation_pattern, value):
                return CredentialStatus.INVALID, f"{config.name} format is invalid"
        
        return CredentialStatus.AVAILABLE, f"{config.name} is valid"
    
    def check_all_credentials(self) -> Dict[str, Dict[str, Any]]:
        """Check status of all credentials"""
        results = {}
        
        for credential_id, config in self.credentials.items():
            status, message = self.validate_credential(credential_id)
            value = self.get_credential(credential_id)
            
            results[credential_id] = {
                'name': config.name,
                'status': status.value,
                'message': message,
                'priority': config.priority.value,
                'service_name': config.service_name,
                'has_value': bool(value),
                'masked_value': f"{value[:8]}...{value[-4:]}" if value and len(value) > 12 else "***" if value else None,
                'setup_url': config.setup_url,
                'env_var': config.env_var,
                'fallback_vars': config.fallback_vars,
                'description': config.description
            }
        
        self.status_cache = results
        self.last_check = datetime.now()
        return results
    
    def get_missing_credentials(self, priority_filter: Optional[CredentialPriority] = None) -> List[Dict[str, Any]]:
        """Get list of missing credentials, optionally filtered by priority"""
        all_status = self.check_all_credentials()
        missing = []
        
        for credential_id, status_info in all_status.items():
            if status_info['status'] == CredentialStatus.MISSING.value:
                if priority_filter is None or status_info['priority'] == priority_filter.value:
                    missing.append({
                        'credential_id': credential_id,
                        **status_info
                    })
        
        return missing
    
    def get_critical_missing_credentials(self) -> List[Dict[str, Any]]:
        """Get critical missing credentials that should be requested first"""
        return self.get_missing_credentials(CredentialPriority.CRITICAL)
    
    def get_high_priority_missing_credentials(self) -> List[Dict[str, Any]]:
        """Get high priority missing credentials"""
        critical = self.get_missing_credentials(CredentialPriority.CRITICAL)
        high = self.get_missing_credentials(CredentialPriority.HIGH)
        return critical + high
    
    def get_service_status_report(self) -> Dict[str, Any]:
        """Generate a comprehensive service status report"""
        all_status = self.check_all_credentials()
        
        # Group by priority
        by_priority = {
            'critical': [],
            'high': [],
            'medium': [],
            'low': []
        }
        
        # Count statuses
        status_counts = {
            'available': 0,
            'missing': 0,
            'invalid': 0
        }
        
        enabled_services = []
        disabled_services = []
        
        for credential_id, info in all_status.items():
            by_priority[info['priority']].append(info)
            
            if info['status'] in status_counts:
                status_counts[info['status']] += 1
            
            if info['status'] == 'available':
                enabled_services.append(info['service_name'])
            else:
                disabled_services.append({
                    'service': info['service_name'],
                    'reason': info['message'],
                    'setup_url': info['setup_url']
                })
        
        return {
            'summary': {
                'total_credentials': len(all_status),
                'available': status_counts['available'],
                'missing': status_counts['missing'],
                'invalid': status_counts['invalid'],
                'last_check': self.last_check.isoformat() if self.last_check else None
            },
            'by_priority': by_priority,
            'enabled_services': enabled_services,
            'disabled_services': disabled_services,
            'next_steps': self._generate_next_steps(all_status)
        }
    
    def _generate_next_steps(self, all_status: Dict[str, Dict[str, Any]]) -> List[str]:
        """Generate actionable next steps based on credential status"""
        steps = []
        
        critical_missing = [info for info in all_status.values() if info['priority'] == 'critical' and info['status'] == 'missing']
        high_missing = [info for info in all_status.values() if info['priority'] == 'high' and info['status'] == 'missing']
        
        if critical_missing:
            steps.append(f"🚨 CRITICAL: Set up {len(critical_missing)} critical credential(s) for core functionality")
            for cred in critical_missing:
                steps.append(f"   - Configure {cred['name']} ({cred['env_var']})")
        
        if high_missing:
            steps.append(f"⚠️  HIGH PRIORITY: Configure {len(high_missing)} important credential(s) for main features")
            for cred in high_missing:
                if cred['setup_url']:
                    steps.append(f"   - Get {cred['name']}: {cred['setup_url']}")
                else:
                    steps.append(f"   - Configure {cred['name']} ({cred['env_var']})")
        
        if not critical_missing and not high_missing:
            steps.append("✅ All critical and high-priority credentials are configured!")
        
        return steps
    
    def update_api_config(self, api_sources: Dict[str, Dict]) -> Dict[str, Dict]:
        """Update API source configurations with current credential status"""
        updated_sources = {}
        
        for source_id, source_config in api_sources.items():
            updated_config = source_config.copy()
            
            # Map API source to credential
            credential_mapping = {
                'sam_gov_opportunities': 'sam_gov_api_key',
                'sam_gov_entity': 'sam_gov_api_key',
                'candid': 'candid_api_key',
                'candid_news': 'candid_news_key',
                'candid_grants': 'candid_grants_key',
                'foundation_directory': 'fdo_api_key',
                'grantwatch': 'grantwatch_api_key',
                'michigan_socrata': 'michigan_socrata_key',
                'zyte_api': 'zyte_api_key'
            }
            
            if source_id in credential_mapping:
                credential_id = credential_mapping[source_id]
                credential_value = self.get_credential(credential_id)
                status, _ = self.validate_credential(credential_id, credential_value)
                
                # Update configuration
                updated_config['api_key'] = credential_value
                updated_config['enabled'] = status == CredentialStatus.AVAILABLE
                updated_config['credential_status'] = status.value
                
                logger.info(f"Updated {source_id}: enabled={updated_config['enabled']}, status={status.value}")
            
            updated_sources[source_id] = updated_config
        
        return updated_sources
    
    def get_credentials_for_replit_secrets(self) -> List[Dict[str, str]]:
        """Get credential information formatted for Replit ask_secrets"""
        high_priority_missing = self.get_high_priority_missing_credentials()
        
        secrets_to_request = []
        for cred in high_priority_missing:
            secrets_to_request.append({
                'key': cred['env_var'],
                'description': f"{cred['name']}: {cred['description']}",
                'url': cred['setup_url'] or f"Set up {cred['service_name']} API access"
            })
        
        return secrets_to_request


# Global instance
credential_manager = CredentialManager()

def get_credential_manager() -> CredentialManager:
    """Get the global credential manager instance"""
    return credential_manager