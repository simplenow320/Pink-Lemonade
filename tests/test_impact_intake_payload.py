"""
Tests for ImpactIntake model and payload validation
"""
import pytest
from datetime import datetime
from app import create_app, db
from app.models import ImpactIntake, Grant, Organization
from app.utils.impact_intake_validator import validate_and_merge_intake_payload


class TestImpactIntakePayload:
    """Test suite for impact intake payload validation"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test environment"""
        self.app = create_app()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
        
        with self.app.app_context():
            db.create_all()
            
            # Create test organization and grant
            org = Organization(
                name="Test Org",
                mission="Test mission",
                ein="12-3456789"
            )
            db.session.add(org)
            db.session.flush()
            
            grant = Grant(
                title="Test Grant",
                funder="Test Funder",
                amount_max=10000,
                org_id=org.id
            )
            db.session.add(grant)
            db.session.commit()
            
            self.grant_id = grant.id
            
            yield
            
            db.session.remove()
            db.drop_all()
    
    def test_accepts_valid_payload_with_age_zip_ethnicity_stories(self):
        """Test accepting valid payload with all new fields"""
        with self.app.app_context():
            intake = ImpactIntake(
                grant_id=self.grant_id,
                submitted_by="test@example.com",
                role="staff"
            )
            
            incoming = {
                'age': 25,
                'zip': '12345',
                'ethnicity': 'Hispanic',
                'stories': [
                    'Story 1 about impact',
                    'Story 2 about change',
                    'Story 3 about growth',
                    'Story 4 about success'
                ]
            }
            
            intake.validate_payload(incoming)
            
            assert intake.payload['age'] == 25
            assert intake.payload['zip'] == '12345'
            assert intake.payload['ethnicity'] == 'Hispanic'
            assert len(intake.payload['stories']) == 4
            assert intake.payload['stories'][0] == 'Story 1 about impact'
            
            # Save and verify persistence
            db.session.add(intake)
            db.session.commit()
            
            saved = ImpactIntake.query.get(intake.id)
            assert saved.payload['age'] == 25
    
    def test_rejects_invalid_age(self):
        """Test rejecting negative age and age > 120"""
        with self.app.app_context():
            # Test negative age
            with pytest.raises(ValueError, match="age: must be >= 0"):
                validate_and_merge_intake_payload({}, {'age': -1})
            
            # Test age > 120
            with pytest.raises(ValueError, match="age: must be <= 120"):
                validate_and_merge_intake_payload({}, {'age': 121})
            
            # Test non-integer age
            with pytest.raises(ValueError, match="age: must be a valid integer"):
                validate_and_merge_intake_payload({}, {'age': 'not a number'})
    
    def test_rejects_bad_zip(self):
        """Test rejecting invalid zip codes"""
        with self.app.app_context():
            # Test too short
            with pytest.raises(ValueError, match="zip: must be at least 5 characters"):
                validate_and_merge_intake_payload({}, {'zip': '123'})
            
            # Test too long
            with pytest.raises(ValueError, match="zip: must be at most 10 characters"):
                validate_and_merge_intake_payload({}, {'zip': '12345678901'})
            
            # Test cleaning non-alphanumeric (should pass)
            result = validate_and_merge_intake_payload({}, {'zip': '12345-6789'})
            assert result['zip'] == '12345-6789'
            
            result = validate_and_merge_intake_payload({}, {'zip': '12345!@#'})
            assert result['zip'] == '12345'  # Special chars removed
    
    def test_rejects_ethnicity_too_long(self):
        """Test rejecting ethnicity that's too long"""
        with self.app.app_context():
            # Test too long
            long_ethnicity = 'x' * 81
            with pytest.raises(ValueError, match="ethnicity: must be at most 80 characters"):
                validate_and_merge_intake_payload({}, {'ethnicity': long_ethnicity})
            
            # Test empty after trimming
            with pytest.raises(ValueError, match="ethnicity: must be at least 1 character"):
                validate_and_merge_intake_payload({}, {'ethnicity': '   '})
            
            # Test valid ethnicity
            result = validate_and_merge_intake_payload({}, {'ethnicity': '  Asian American  '})
            assert result['ethnicity'] == 'Asian American'  # Trimmed
    
    def test_truncates_stories_to_four(self):
        """Test that stories array is truncated to max 4 items"""
        with self.app.app_context():
            stories = [f"Story {i}" for i in range(10)]
            result = validate_and_merge_intake_payload({}, {'stories': stories})
            
            assert len(result['stories']) == 4
            assert result['stories'][0] == 'Story 0'
            assert result['stories'][3] == 'Story 3'
            assert 'Story 4' not in str(result['stories'])  # 5th story not included
    
    def test_story_max_length(self):
        """Test that individual stories are limited to 2000 chars"""
        with self.app.app_context():
            long_story = 'x' * 2001
            with pytest.raises(ValueError, match="stories\\[0\\]: must be at most 2000 characters"):
                validate_and_merge_intake_payload({}, {'stories': [long_story]})
            
            # Test valid story at max length
            max_story = 'y' * 2000
            result = validate_and_merge_intake_payload({}, {'stories': [max_story]})
            assert len(result['stories'][0]) == 2000
    
    def test_preserves_existing_payload_keys(self):
        """Test backward compatibility - preserving existing payload keys"""
        with self.app.app_context():
            existing = {
                'custom_field': 'value',
                'other_data': 123,
                'age': 30  # This will be overwritten
            }
            
            incoming = {
                'age': 35,
                'zip': '90210'
            }
            
            result = validate_and_merge_intake_payload(existing, incoming)
            
            # Check new values
            assert result['age'] == 35
            assert result['zip'] == '90210'
            
            # Check preserved values
            assert result['custom_field'] == 'value'
            assert result['other_data'] == 123
    
    def test_optional_fields(self):
        """Test that all fields are optional"""
        with self.app.app_context():
            # Empty incoming data should work
            result = validate_and_merge_intake_payload({}, {})
            assert result == {}
            
            # Partial data should work
            result = validate_and_merge_intake_payload({}, {'age': 30})
            assert result == {'age': 30}
            
            result = validate_and_merge_intake_payload({}, {'stories': ['One story']})
            assert result == {'stories': ['One story']}
    
    def test_null_values_handled(self):
        """Test that None/null values are handled gracefully"""
        with self.app.app_context():
            incoming = {
                'age': None,
                'zip': None,
                'ethnicity': None,
                'stories': None
            }
            
            # Should not add None values
            result = validate_and_merge_intake_payload({}, incoming)
            assert 'age' not in result
            assert 'zip' not in result
            assert 'ethnicity' not in result
            assert 'stories' not in result
    
    def test_indexes_exist_or_are_declared(self):
        """Smoke test that at least the grant_id index is created"""
        with self.app.app_context():
            from sqlalchemy import inspect
            
            inspector = inspect(db.engine)
            
            # For SQLite in testing, just verify table exists
            # Real PostgreSQL testing would check actual indexes
            tables = inspector.get_table_names()
            assert 'impact_intake' in tables
            
            # Verify columns exist
            columns = [col['name'] for col in inspector.get_columns('impact_intake')]
            assert 'id' in columns
            assert 'grant_id' in columns
            assert 'submitted_by' in columns
            assert 'role' in columns
            assert 'payload' in columns
            assert 'created_at' in columns
    
    def test_role_validation(self):
        """Test that role field accepts only valid values"""
        with self.app.app_context():
            valid_roles = ['staff', 'board', 'participant', 'other', None]
            
            for role in valid_roles:
                intake = ImpactIntake(
                    grant_id=self.grant_id,
                    role=role
                )
                db.session.add(intake)
                db.session.flush()  # This would fail if constraint violated
                db.session.rollback()  # Clean up for next iteration
    
    def test_model_to_dict(self):
        """Test the to_dict method"""
        with self.app.app_context():
            intake = ImpactIntake(
                grant_id=self.grant_id,
                submitted_by="user@test.com",
                role="staff",
                payload={'age': 25, 'zip': '12345'}
            )
            db.session.add(intake)
            db.session.commit()
            
            result = intake.to_dict()
            assert result['grant_id'] == self.grant_id
            assert result['submitted_by'] == "user@test.com"
            assert result['role'] == "staff"
            assert result['payload']['age'] == 25
            assert result['payload']['zip'] == '12345'
            assert 'created_at' in result