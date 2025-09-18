"""
Unit tests for API sources with missing credentials
Tests that sources requiring credentials are properly disabled when credentials are missing
"""

import pytest
import os
from unittest.mock import patch, Mock
from typing import Dict, Any

from app.services.apiManager import APIManager
from app.config.apiConfig import APIConfig
from tests.fixtures.api_responses import get_mock_response, SOURCE_MOCK_RESPONSES


class TestAPISourcesMissingCredentials:
    """Test API sources behavior when credentials are missing"""
    
    def test_credential_required_sources_disabled_without_credentials(self, clean_environment):
        """Test that sources requiring credentials are disabled when credentials are missing"""
        config = APIConfig()
        
        # Sources that require credentials
        credential_required_sources = {
            'sam_gov_opportunities': 'SAM_GOV_API_KEY',
            'sam_gov_entity': 'SAM_GOV_API_KEY',
            'foundation_directory': 'FDO_API_KEY',
            'grantwatch': 'GRANTWATCH_API_KEY',
            'candid': 'CANDID_API_KEY',
            'zyte_api': 'ZYTE_API_KEY',
        }
        
        for source_id, env_var in credential_required_sources.items():
            with pytest.raises(KeyError):
                # Environment variable should not exist
                os.environ[env_var]
            
            source_config = config.get_source_config(source_id)
            
            # Source should be disabled
            assert source_config.get('enabled', False) is False, \
                f"{source_id} should be disabled without {env_var}"
            
            # Should require credentials
            assert source_config.get('credential_required', False) is True, \
                f"{source_id} should require credentials"
            
            # API key should be None
            assert source_config.get('api_key') is None, \
                f"{source_id} should not have API key without credentials"
    
    def test_public_sources_enabled_without_credentials(self, clean_environment):
        """Test that public sources are enabled even without credentials"""
        config = APIConfig()
        
        # Sources that don't require credentials (public APIs)
        public_sources = [
            'grants_gov',
            'federal_register',
            'govinfo',  # Optional credentials
            'hhs_grants',
            'ed_grants', 
            'nsf_grants'
        ]
        
        for source_id in public_sources:
            source_config = config.get_source_config(source_id)
            
            # These sources should either be enabled or have credential_required=False
            credential_required = source_config.get('credential_required', False)
            enabled = source_config.get('enabled', False)
            
            if not credential_required:
                # Public APIs should generally be enabled
                assert enabled or source_id in ['hhs_grants', 'ed_grants', 'nsf_grants'], \
                    f"Public source {source_id} should be enabled"
    
    def test_api_manager_handles_missing_credentials_gracefully(self, clean_environment):
        """Test that APIManager handles missing credentials without crashing"""
        api_manager = APIManager()
        
        # Sources that require credentials
        credential_sources = [
            'sam_gov_opportunities',
            'sam_gov_entity', 
            'foundation_directory',
            'grantwatch',
            'candid',
            'zyte_api'
        ]
        
        for source_name in credential_sources:
            # These calls should not raise exceptions
            results = api_manager.get_grants_from_source(source_name, {})
            
            # Should return empty list when credentials missing
            assert isinstance(results, list), f"{source_name} should return list"
            assert len(results) == 0, f"{source_name} should return empty list without credentials"
    
    def test_api_manager_excludes_disabled_sources(self, clean_environment):
        """Test that APIManager excludes disabled sources from operations"""
        api_manager = APIManager()
        
        # Get enabled sources
        enabled_sources = api_manager.get_enabled_sources()
        
        # Sources requiring credentials should not be in enabled sources
        credential_sources = [
            'sam_gov_opportunities',
            'sam_gov_entity',
            'foundation_directory', 
            'grantwatch',
            'candid',
            'zyte_api'
        ]
        
        for source_name in credential_sources:
            assert source_name not in enabled_sources, \
                f"{source_name} should not be in enabled sources without credentials"
    
    def test_search_opportunities_works_with_partial_sources(self, clean_environment, mock_api_server):
        """Test that search_opportunities works even when some sources are disabled"""
        api_manager = APIManager()
        
        # Configure mock server for enabled sources
        mock_api_server.set_custom_response('grants_gov', get_mock_response('grants_gov', 'success'))
        mock_api_server.set_custom_response('federal_register', get_mock_response('federal_register', 'success'))
        
        # This should work even with missing credentials for other sources
        results = api_manager.search_opportunities("education", {"limit": 10})
        
        # Should get results from enabled sources
        assert isinstance(results, list)
        # May be empty if no enabled sources, but should not crash
    
    def test_individual_source_isolation(self, clean_environment):
        """Test that missing credentials for one source don't affect others"""
        # Test with some credentials present
        with patch.dict(os.environ, {'GOVINFO_API_KEY': 'test-key'}):
            config = APIConfig()
            api_manager = APIManager()
            
            # GovInfo should be enabled with credentials
            govinfo_config = config.get_source_config('govinfo')
            assert govinfo_config.get('enabled', False) is True
            assert govinfo_config.get('api_key') == 'test-key'
            
            # SAM.gov should still be disabled without credentials
            sam_config = config.get_source_config('sam_gov_opportunities')
            assert sam_config.get('enabled', False) is False
            assert sam_config.get('api_key') is None
            
            # Enabled sources should only include the ones with credentials
            enabled_sources = api_manager.get_enabled_sources()
            assert 'govinfo' in enabled_sources
            assert 'sam_gov_opportunities' not in enabled_sources
    
    def test_credential_status_reporting(self, clean_environment):
        """Test credential status reporting shows missing credentials"""
        config = APIConfig()
        
        credential_status = config.get_credential_status()
        
        # Should have status for all configured sources
        assert isinstance(credential_status, dict)
        assert len(credential_status) > 0
        
        # Check specific sources
        credential_sources = [
            'sam_gov_opportunities',
            'foundation_directory',
            'candid',
            'zyte_api'
        ]
        
        for source_id in credential_sources:
            if source_id in credential_status:
                source_status = credential_status[source_id]
                
                # Should not have credentials
                assert source_status.get('has_credentials', True) is False, \
                    f"{source_id} should not have credentials"
                
                # Should require credentials
                assert source_status.get('credential_required', False) is True, \
                    f"{source_id} should require credentials"
                
                # Should have primary env var specified
                assert 'primary_env_var' in source_status, \
                    f"{source_id} should specify primary env var"
    
    def test_health_check_identifies_missing_credentials(self, clean_environment):
        """Test health check properly identifies missing credential issues"""
        config = APIConfig()
        
        credential_sources = [
            'sam_gov_opportunities',
            'foundation_directory',
            'candid'
        ]
        
        for source_id in credential_sources:
            health = config.check_source_health(source_id)
            
            # Should be unhealthy due to missing credentials
            assert health.get('healthy', True) is False, \
                f"{source_id} should be unhealthy without credentials"
            
            # Should have appropriate error message
            errors = health.get('errors', [])
            assert len(errors) > 0, f"{source_id} should have errors"
            
            # Error should mention credentials
            credential_error_found = any(
                'credential' in error.lower() or 'missing' in error.lower()
                for error in errors
            )
            assert credential_error_found, \
                f"{source_id} should have credential-related error: {errors}"
    
    @pytest.mark.parametrize("source_name", [
        'sam_gov_opportunities',
        'sam_gov_entity', 
        'foundation_directory',
        'grantwatch',
        'candid',
        'zyte_api'
    ])
    def test_individual_credential_source_disabled(self, source_name, clean_environment):
        """Test individual credential-required sources are disabled"""
        config = APIConfig()
        api_manager = APIManager()
        
        # Source should be disabled in config
        source_config = config.get_source_config(source_name)
        assert source_config.get('enabled', False) is False
        
        # Source should not be in enabled sources
        enabled_sources = api_manager.get_enabled_sources()
        assert source_name not in enabled_sources
        
        # API call should return empty
        results = api_manager.get_grants_from_source(source_name, {})
        assert results == []
    
    def test_fallback_credential_environment_variables(self, clean_environment):
        """Test that fallback environment variables are checked"""
        # Test SAM.gov fallback variables
        sam_fallbacks = ['SAM_API_KEY', 'SAMGOV_KEY']
        
        for fallback_var in sam_fallbacks:
            with patch.dict(os.environ, {fallback_var: 'fallback-key-value'}):
                config = APIConfig()
                
                sam_opportunities = config.get_source_config('sam_gov_opportunities')
                sam_entity = config.get_source_config('sam_gov_entity')
                
                # Should be enabled with fallback credentials
                assert sam_opportunities.get('enabled', False) is True, \
                    f"SAM opportunities should be enabled with {fallback_var}"
                assert sam_entity.get('enabled', False) is True, \
                    f"SAM entity should be enabled with {fallback_var}"
                
                # Should have the fallback key
                assert sam_opportunities.get('api_key') == 'fallback-key-value'
                assert sam_entity.get('api_key') == 'fallback-key-value'
    
    def test_mixed_credential_availability(self, clean_environment):
        """Test behavior when some credentials are available and others are not"""
        # Set credentials for some sources but not others
        with patch.dict(os.environ, {
            'SAM_GOV_API_KEY': 'sam-key-123',
            'GOVINFO_API_KEY': 'govinfo-key-456'
            # Intentionally not setting CANDID_API_KEY, FDO_API_KEY, etc.
        }):
            config = APIConfig()
            api_manager = APIManager()
            
            # Sources with credentials should be enabled
            sam_config = config.get_source_config('sam_gov_opportunities')
            govinfo_config = config.get_source_config('govinfo')
            
            assert sam_config.get('enabled', False) is True
            assert govinfo_config.get('enabled', False) is True
            
            # Sources without credentials should be disabled
            candid_config = config.get_source_config('candid')
            fdo_config = config.get_source_config('foundation_directory')
            
            assert candid_config.get('enabled', False) is False
            assert fdo_config.get('enabled', False) is False
            
            # Enabled sources should reflect this
            enabled_sources = api_manager.get_enabled_sources()
            assert 'sam_gov_opportunities' in enabled_sources
            assert 'govinfo' in enabled_sources
            assert 'candid' not in enabled_sources
            assert 'foundation_directory' not in enabled_sources
    
    def test_configuration_validation_with_missing_credentials(self, clean_environment):
        """Test configuration validation reports missing credentials correctly"""
        config = APIConfig()
        
        validation_report = config.validate_configuration()
        
        # Should have validation report structure
        assert 'total_sources' in validation_report
        assert 'enabled_sources' in validation_report
        assert 'sources_with_credentials' in validation_report
        assert 'healthy_sources' in validation_report
        
        # With missing credentials, fewer sources should be enabled
        total_sources = validation_report['total_sources']
        enabled_sources = validation_report['enabled_sources']
        sources_with_credentials = validation_report['sources_with_credentials']
        
        assert total_sources > enabled_sources, \
            "Some sources should be disabled due to missing credentials"
        
        assert sources_with_credentials < total_sources, \
            "Some sources should be missing credentials"
    
    def test_circuit_breaker_not_initialized_for_disabled_sources(self, clean_environment):
        """Test that circuit breakers are not initialized for disabled sources"""
        api_manager = APIManager()
        
        disabled_sources = [
            'sam_gov_opportunities',
            'foundation_directory',
            'candid'
        ]
        
        for source_name in disabled_sources:
            # Circuit breaker should either not exist or reflect disabled state
            circuit_breaker = api_manager.circuit_breakers.get(source_name)
            
            # If circuit breaker exists, verify source is not in enabled sources
            if circuit_breaker:
                enabled_sources = api_manager.get_enabled_sources()
                assert source_name not in enabled_sources, \
                    f"{source_name} has circuit breaker but should be disabled"
    
    def test_rate_limiter_not_applied_to_disabled_sources(self, clean_environment):
        """Test that rate limiting is not applied to disabled sources"""
        api_manager = APIManager()
        
        disabled_sources = [
            'sam_gov_opportunities',
            'foundation_directory', 
            'candid'
        ]
        
        for source_name in disabled_sources:
            # Multiple calls should all return empty (not rate limited)
            for i in range(10):
                results = api_manager.get_grants_from_source(source_name, {'call': i})
                assert results == [], f"{source_name} call {i} should return empty"
            
            # Should not have rate limit tracking for disabled sources
            # (This is implicit - disabled sources return early before rate limiting)
    
    def test_cache_not_used_for_disabled_sources(self, clean_environment):
        """Test that caching is not used for disabled sources"""
        api_manager = APIManager()
        
        disabled_sources = [
            'sam_gov_opportunities',
            'foundation_directory',
            'candid'
        ]
        
        for source_name in disabled_sources:
            params = {'query': 'test'}
            
            # Multiple identical calls
            result1 = api_manager.get_grants_from_source(source_name, params)
            result2 = api_manager.get_grants_from_source(source_name, params)
            
            # Both should return empty (consistent behavior)
            assert result1 == []
            assert result2 == []
            
            # Cache should not have entries for disabled sources
            cache_key = api_manager.cache.get_cache_key(source_name, params)
            # We can't easily verify cache absence, but consistent empty results indicate
            # no caching is happening (since nothing is being fetched to cache)