"""
Integration tests for the scheduler module.

These tests verify the integration of the scheduler with the Flask application,
including database operations and actual job execution.
"""

import pytest
import time
from unittest.mock import patch
from datetime import datetime, timedelta
from app.utils.scheduler import initialize_scheduler, stop_scheduler, get_next_scheduled_run
from app.models.scraper import ScraperHistory


class TestSchedulerIntegration:
    """Integration test suite for the scheduler module."""

    def setup_method(self):
        """Set up the test environment before each test."""
        # Stop any running scheduler
        stop_scheduler()

    def teardown_method(self):
        """Clean up after each test."""
        # Ensure the scheduler is stopped
        stop_scheduler()

    def test_scheduler_initialization_with_app(self, app):
        """Test scheduler initialization within app context."""
        with app.app_context():
            # Initialize the scheduler
            result = initialize_scheduler()
            
            # Verify the result
            assert result['status'] == 'success'
            assert 'next_run' in result
            
            # Get the next scheduled run
            next_run = get_next_scheduled_run()
            assert isinstance(next_run, str)
            
            # Stop the scheduler
            stop_result = stop_scheduler()
            assert stop_result['status'] == 'success'

    @patch('app.services.scraper_service.run_scraping_job')
    def test_scheduled_job_creates_history_record(self, mock_run_scraping, app):
        """Test that a scheduled job creates a history record in the database."""
        # Set up the mock to return successful scraping results
        mock_run_scraping.return_value = {
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(minutes=2),
            'sources_scraped': 5,
            'grants_found': 10,
            'grants_added': 7,
            'status': 'completed'
        }
        
        with app.app_context():
            # Get initial count of history records
            initial_count = ScraperHistory.query.count()
            
            # Create a custom schedule that will run immediately for testing
            from app.utils import scheduler
            import schedule
            
            # Clear any existing schedules
            schedule.clear()
            
            # Schedule the job to run in 1 second
            schedule.every(1).seconds.do(scheduler.scheduled_scraping_job)
            
            # Initialize and start the scheduler
            initialize_scheduler()
            
            # Wait for the job to execute (give it 3 seconds)
            time.sleep(3)
            
            # Stop the scheduler
            stop_scheduler()
            
            # Check that a new history record was created
            final_count = ScraperHistory.query.count()
            assert final_count > initial_count
            
            # Get the latest record
            latest_record = ScraperHistory.query.order_by(ScraperHistory.id.desc()).first()
            
            # Verify the record contains the expected data
            assert latest_record is not None
            assert latest_record.sources_scraped == 5
            assert latest_record.grants_found == 10
            assert latest_record.grants_added == 7
            assert latest_record.status == 'completed'

    @patch('app.services.scraper_service.run_scraping_job')
    def test_scheduler_records_errors(self, mock_run_scraping, app):
        """Test that the scheduler records errors in the database."""
        # Set up the mock to raise an exception
        mock_run_scraping.side_effect = Exception("Test scraping error")
        
        with app.app_context():
            # Get initial count of history records
            initial_count = ScraperHistory.query.count()
            
            # Create a custom schedule that will run immediately for testing
            from app.utils import scheduler
            import schedule
            
            # Clear any existing schedules
            schedule.clear()
            
            # Schedule the job to run in 1 second
            schedule.every(1).seconds.do(scheduler.scheduled_scraping_job)
            
            # Initialize and start the scheduler
            initialize_scheduler()
            
            # Wait for the job to execute (give it 3 seconds)
            time.sleep(3)
            
            # Stop the scheduler
            stop_scheduler()
            
            # Check that a new history record was created
            final_count = ScraperHistory.query.count()
            assert final_count > initial_count
            
            # Get the latest record
            latest_record = ScraperHistory.query.order_by(ScraperHistory.id.desc()).first()
            
            # Verify the record contains the error information
            assert latest_record is not None
            assert latest_record.status == 'failed'
            assert "Test scraping error" in latest_record.error_message
            assert latest_record.grants_added == 0

    def test_get_next_scheduled_run_from_live_scheduler(self, app):
        """Test getting the next scheduled run from a live scheduler."""
        with app.app_context():
            # Initialize the scheduler
            initialize_scheduler()
            
            # Get the next scheduled run
            next_run = get_next_scheduled_run()
            
            # Verify the result
            assert isinstance(next_run, str)
            assert "UTC" in next_run
            
            # The next run should be at 5:00 UTC (midnight EST)
            tomorrow = datetime.now() + timedelta(days=1)
            if datetime.now().hour >= 5:
                # If current hour is 5 or later, the next run is tomorrow
                assert tomorrow.strftime("%Y-%m-%d") in next_run
            else:
                # If current hour is before 5, the next run is today
                assert datetime.now().strftime("%Y-%m-%d") in next_run
            
            # Stop the scheduler
            stop_scheduler()