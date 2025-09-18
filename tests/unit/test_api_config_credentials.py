"""
Unit tests for API configuration credential handling and isolation
Tests ensure that missing/invalid credentials don't affect other sources
"""

import unittest
from unittest.mock import patch, Mock, MagicMock
import os
from app.config.apiConfig import APIConfig, API_SOURCES
from app.services.apiManager import APIManager


class TestAPIConfigCredentials(unittest.TestCase):
    """Test API configuration credential handling"""

    def setUp(self):
        """Set up test environment"""
        # Clear environment variables to start with clean state
        self.original_env = {}
        env_vars_to_clear = [
            'SAM_GOV_API_KEY', 'SAM_API_KEY', 'SAMGOV_KEY',
            'MICHIGAN_SOCRATA_API_KEY', 'SOCRATA_APP_TOKEN', 'MICHIGAN_API_KEY',
            'ZYTE_API_KEY', 'SCRAPINGHUB_API_KEY', 'ZYTE_KEY',
            'GOVINFO_API_KEY', 'GOVINFO_KEY',
            'CANDID_API_KEY', 'FDO_API_KEY', 'GRANTWATCH_API_KEY'
        ]
        
        for var in env_vars_to_clear:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def tearDown(self):
        """Restore original environment"""
        # Restore original environment variables
        for var, value in self.original_env.items():
            os.environ[var] = value

    def test_missing_credentials_disable_required_sources(self):
        """Test that sources requiring credentials are disabled when credentials are missing"""
        config = APIConfig()
        
        # Sources that require credentials should be disabled
        required_credential_sources = [
            'sam_gov_opportunities', 'sam_gov_entity', 'zyte_api',
            'foundation_directory', 'grantwatch', 'candid'
        ]
        
        for source_id in required_credential_sources:
            with self.subTest(source=source_id):
                source_config = config.get_source_config(source_id)
                self.assertFalse(source_config.get('enabled', False),
                               f"{source_id} should be disabled without credentials")
                self.assertTrue(source_config.get('credential_required', False),
                              f"{source_id} should require credentials")
                self.assertIsNone(source_config.get('api_key'),
                                f"{source_id} should not have API key")

    def test_optional_credentials_enable_public_sources(self):
        """Test that sources with optional credentials are enabled even without them"""
        config = APIConfig()
        
        # Sources that don't require credentials should be enabled
        public_sources = [
            'grants_gov', 'federal_register', 'govinfo',
            'hhs_grants', 'ed_grants', 'nsf_grants', 'michigan_socrata'
        ]
        
        for source_id in public_sources:
            with self.subTest(source=source_id):
                source_config = config.get_source_config(source_id)
                expected_enabled = source_config.get('enabled', False)
                # These should be enabled by default or auto-enabled
                if source_id in ['grants_gov', 'federal_register', 'govinfo', 
                               'hhs_grants', 'ed_grants', 'nsf_grants']:
                    self.assertTrue(expected_enabled,
                                  f"{source_id} should be enabled (public API)")

    def test_credentials_enable_required_sources(self):
        """Test that adding credentials enables previously disabled sources"""
        # Test with SAM.gov credentials
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'test-key-123'}):
            config = APIConfig()
            
            sam_opportunities = config.get_source_config('sam_gov_opportunities')
            sam_entity = config.get_source_config('sam_gov_entity')
            
            self.assertTrue(sam_opportunities.get('enabled', False),
                          "SAM.gov opportunities should be enabled with credentials")
            self.assertTrue(sam_entity.get('enabled', False),
                          "SAM.gov entity should be enabled with credentials")
            self.assertEqual(sam_opportunities.get('api_key'), 'test-key-123')
            self.assertEqual(sam_entity.get('api_key'), 'test-key-123')

    def test_fallback_credentials_work(self):
        """Test that fallback environment variables are used when primary is missing"""
        # Test SAM.gov fallback
        with patch.dict(os.environ, {'SAM_API_KEY': 'fallback-key-456'}):
            config = APIConfig()
            
            sam_opportunities = config.get_source_config('sam_gov_opportunities')
            self.assertEqual(sam_opportunities.get('api_key'), 'fallback-key-456')
            self.assertTrue(sam_opportunities.get('enabled', False))

    def test_invalid_credentials_isolation(self):
        """Test that invalid credentials for one source don't affect others"""
        with patch.dict(os.environ, {
            'SAM_GOV_API_KEY': 'invalid-key',
            'GOVINFO_API_KEY': 'valid-key'
        }):
            config = APIConfig()
            
            # Both should be enabled despite one having invalid credentials
            sam_config = config.get_source_config('sam_gov_opportunities')
            govinfo_config = config.get_source_config('govinfo')
            
            self.assertTrue(sam_config.get('enabled', False),
                          "SAM.gov should be enabled (credential validation happens at runtime)")
            self.assertTrue(govinfo_config.get('enabled', False),
                          "GovInfo should be enabled")

    def test_health_check_detects_credential_issues(self):
        """Test that health check properly identifies credential issues"""
        config = APIConfig()
        
        # Check a source without required credentials
        health = config.check_source_health('sam_gov_opportunities')
        self.assertFalse(health['healthy'])
        self.assertIn('Missing required credentials', health['errors'])
        
        # Check a public source
        health = config.check_source_health('grants_gov')
        self.assertTrue(health['healthy'])
        self.assertEqual(len(health['errors']), 0)

    def test_credential_status_report(self):
        """Test comprehensive credential status reporting"""
        config = APIConfig()
        status = config.get_credential_status()
        
        # Should have status for all configured sources
        self.assertGreater(len(status), 10)
        
        # Check specific source status
        sam_status = status.get('sam_gov_opportunities', {})
        self.assertFalse(sam_status.get('has_credentials', True))
        self.assertTrue(sam_status.get('credential_required', False))
        self.assertEqual(sam_status.get('primary_env_var'), 'SAM_GOV_API_KEY')
        self.assertIn('SAM_API_KEY', sam_status.get('fallback_env_vars', []))

    def test_auth_type_consistency(self):
        """Test that auth_type and auth_header are properly configured"""
        config = APIConfig()
        
        auth_configs = {
            'sam_gov_opportunities': ('api_key', 'X-Api-Key'),
            'sam_gov_entity': ('api_key', 'X-Api-Key'),
            'michigan_socrata': ('app_token', 'X-App-Token'),
            'zyte_api': ('basic_auth', 'Authorization'),
            'govinfo': ('api_key', 'X-API-Key')
        }
        
        for source_id, (expected_auth_type, expected_header) in auth_configs.items():
            with self.subTest(source=source_id):
                source_config = config.get_source_config(source_id)
                self.assertEqual(source_config.get('auth_type'), expected_auth_type,
                               f"{source_id} should use {expected_auth_type} auth")
                self.assertEqual(source_config.get('auth_header'), expected_header,
                               f"{source_id} should use {expected_header} header")

    def test_configuration_validation(self):
        """Test overall configuration validation"""
        config = APIConfig()
        report = config.validate_configuration()
        
        self.assertIsInstance(report, dict)
        self.assertIn('total_sources', report)
        self.assertIn('enabled_sources', report)
        self.assertIn('sources_with_credentials', report)
        self.assertIn('healthy_sources', report)
        
        # Should have reasonable numbers
        self.assertGreater(report['total_sources'], 15)
        self.assertGreater(report['enabled_sources'], 5)


class TestAPIManagerCredentialIsolation(unittest.TestCase):
    """Test APIManager credential isolation and error handling"""

    def setUp(self):
        """Set up test environment"""
        self.original_env = {}
        # Clear credentials
        env_vars = ['SAM_GOV_API_KEY', 'ZYTE_API_KEY', 'MICHIGAN_SOCRATA_API_KEY']
        for var in env_vars:
            if var in os.environ:
                self.original_env[var] = os.environ[var]
                del os.environ[var]

    def tearDown(self):
        """Restore environment"""
        for var, value in self.original_env.items():
            os.environ[var] = value

    @patch('app.services.apiManager.requests.request')
    def test_authentication_failure_isolation(self, mock_request):
        """Test that auth failures in one source don't affect others"""
        # Mock a 401 response for authenticated source
        mock_response = Mock()
        mock_response.status_code = 401
        mock_response.text = 'Unauthorized'
        mock_request.return_value = mock_response
        
        api_manager = APIManager()
        
        # This should handle the auth failure gracefully
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'invalid-key'}):
            results = api_manager.get_grants_from_source('sam_gov_opportunities', {})
            
            # Should return empty list, not crash
            self.assertIsInstance(results, list)
            self.assertEqual(len(results), 0)

    @patch('app.services.apiManager.requests.request')
    def test_rate_limit_isolation(self, mock_request):
        """Test that rate limits in one source don't affect others"""
        # Mock a 429 response
        mock_response = Mock()
        mock_response.status_code = 429
        mock_response.text = 'Rate limit exceeded'
        mock_request.return_value = mock_response
        
        api_manager = APIManager()
        
        # Rate limit should be handled gracefully
        results = api_manager.get_grants_from_source('grants_gov', {})
        
        # Should return empty list when rate limited
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 0)

    def test_missing_credentials_dont_crash_manager(self):
        """Test that missing credentials don't crash the API manager"""
        api_manager = APIManager()
        
        # These should not raise exceptions
        sources_needing_creds = ['sam_gov_opportunities', 'zyte_api']
        
        for source in sources_needing_creds:
            with self.subTest(source=source):
                results = api_manager.get_grants_from_source(source, {})
                self.assertIsInstance(results, list)
                self.assertEqual(len(results), 0)

    def test_auth_header_preparation(self):
        """Test that auth headers are prepared correctly based on auth_type"""
        api_manager = APIManager()
        
        # Test API key auth
        with patch.dict(os.environ, {'SAM_GOV_API_KEY': 'test-key'}):
            config = api_manager._prepare_authenticated_request(
                'sam_gov_opportunities', 'https://example.com', 'GET'
            )
            self.assertEqual(config['headers']['X-Api-Key'], 'test-key')
        
        # Test app token auth
        with patch.dict(os.environ, {'MICHIGAN_SOCRATA_API_KEY': 'app-token'}):
            config = api_manager._prepare_authenticated_request(
                'michigan_socrata', 'https://example.com', 'GET'
            )
            self.assertEqual(config['headers']['X-App-Token'], 'app-token')

    def test_error_handling_configuration(self):
        """Test that error handling configuration is properly applied"""
        api_manager = APIManager()
        
        # Check that sources have proper error handling config
        sam_config = api_manager.sources.get('sam_gov_opportunities', {})
        error_config = sam_config.get('error_handling', {})
        
        self.assertIn('retry_codes', error_config)
        self.assertIn('max_retries', error_config)
        self.assertIn('backoff_factor', error_config)
        
        self.assertIn(429, error_config['retry_codes'])  # Rate limit should trigger retry
        self.assertGreater(error_config['max_retries'], 0)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)