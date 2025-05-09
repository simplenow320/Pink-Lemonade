"""
Unit tests for the scheduler module.

These tests verify the behavior of the scheduler component, including job scheduling,
thread management, and error handling.
"""

import pytest
import threading
import time
from unittest.mock import patch, MagicMock, call
from datetime import datetime, timedelta
import schedule
from app.utils.scheduler import (
    initialize_scheduler,
    scheduler_loop,
    scheduled_scraping_job,
    get_next_scheduled_run,
    stop_scheduler,
    scheduler_running,
    scheduler_thread
)


class TestScheduler:
    """Test suite for the scheduler module."""

    def setup_method(self):
        """Set up the test environment before each test."""
        # Clear all scheduled jobs
        schedule.clear()
        
        # Ensure the scheduler is stopped
        if scheduler_running:
            stop_scheduler()
            
        # Reset module state if needed
        import app.utils.scheduler
        app.utils.scheduler.scheduler_running = False
        app.utils.scheduler.scheduler_thread = None

    def teardown_method(self):
        """Clean up after each test."""
        # Ensure the scheduler is stopped
        if scheduler_running:
            stop_scheduler()
        
        # Clear all scheduled jobs
        schedule.clear()

    @patch('app.utils.scheduler.schedule')
    def test_initialize_scheduler_success(self, mock_schedule):
        """Test successful scheduler initialization."""
        # Set up mocks
        mock_schedule.next_run.return_value = datetime.now() + timedelta(hours=1)
        
        # Call the function
        result = initialize_scheduler()
        
        # Verify the result
        assert result['status'] == 'success'
        assert 'next_run' in result
        
        # Verify that the scheduler was set up correctly
        mock_schedule.clear.assert_called_once()
        mock_schedule.every.assert_called_once()
        
        # Verify that the scheduler thread was started
        assert scheduler_running is True
        assert scheduler_thread is not None
        assert scheduler_thread.is_alive() is True
        
        # Clean up
        stop_scheduler()

    @patch('app.utils.scheduler.schedule')
    def test_initialize_scheduler_with_existing_thread(self, mock_schedule):
        """Test initializing the scheduler when a thread is already running."""
        # Set up mocks
        mock_schedule.next_run.return_value = datetime.now() + timedelta(hours=1)
        
        # Start a first scheduler
        initialize_scheduler()
        first_thread = scheduler_thread
        
        # Start a second scheduler
        result = initialize_scheduler()
        second_thread = scheduler_thread
        
        # Verify the result
        assert result['status'] == 'success'
        
        # Verify that we have a new thread
        assert first_thread is not second_thread
        
        # Clean up
        stop_scheduler()

    @patch('app.utils.scheduler.schedule')
    def test_initialize_scheduler_error(self, mock_schedule):
        """Test handling errors during scheduler initialization."""
        # Set up mocks to raise an exception
        mock_schedule.every.side_effect = Exception("Test exception")
        
        # Call the function
        result = initialize_scheduler()
        
        # Verify the result
        assert result['status'] == 'error'
        assert 'error' in result
        assert 'Test exception' in result['error']
        
        # Verify that the scheduler thread was not started
        assert scheduler_running is False or scheduler_thread is None

    @patch('app.utils.scheduler.schedule')
    @patch('app.utils.scheduler.time')
    def test_scheduler_loop(self, mock_time, mock_schedule):
        """Test the scheduler loop function."""
        # Set up mocks
        mock_time.sleep.side_effect = [None, Exception("Stop test")]
        mock_schedule.get_jobs.return_value = ["job1", "job2"]
        
        # Set up global variables
        import app.utils.scheduler
        app.utils.scheduler.scheduler_running = True
        
        # Call the function (it will exit after the second iteration due to our side effect)
        with pytest.raises(Exception, match="Stop test"):
            scheduler_loop()
        
        # Verify that the schedule was checked
        assert mock_schedule.run_pending.call_count >= 1
        assert mock_time.sleep.call_count >= 1

    @patch('app.utils.scheduler.time')
    def test_scheduler_loop_handles_exceptions(self, mock_time):
        """Test that the scheduler loop handles exceptions properly."""
        # Set up mocks to raise exceptions for the first two iterations, then stop the test
        side_effects = [
            Exception("First error"),  # First iteration throws an error
            Exception("Second error"),  # Second iteration throws an error
            Exception("Stop test")     # Third iteration stops the test
        ]
        mock_time.sleep.side_effect = side_effects
        
        # Set up a mock for schedule.run_pending that raises an exception
        with patch('app.utils.scheduler.schedule.run_pending', side_effect=Exception("Job error")):
            # Set up global variables
            import app.utils.scheduler
            app.utils.scheduler.scheduler_running = True
            
            # Call the function (it will exit after the third iteration due to our side effect)
            with pytest.raises(Exception, match="Stop test"):
                scheduler_loop()
            
            # Verify the sleep was called for each iteration (indicates the loop continued)
            assert mock_time.sleep.call_count == 3

    @patch('app.utils.scheduler.create_app')
    @patch('app.utils.scheduler.run_scraping_job')
    @patch('app.utils.scheduler.db')
    def test_scheduled_scraping_job_success(self, mock_db, mock_run_scraping, mock_create_app):
        """Test successful execution of a scheduled scraping job."""
        # Set up mocks
        mock_app = MagicMock()
        mock_app_context = MagicMock()
        mock_app.app_context.return_value = mock_app_context
        mock_create_app.return_value = mock_app
        
        # Mock successful scraping result
        mock_result = {
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(minutes=5),
            'sources_scraped': 10,
            'grants_found': 25,
            'grants_added': 15,
            'status': 'completed'
        }
        mock_run_scraping.return_value = mock_result
        
        # Call the function
        result = scheduled_scraping_job()
        
        # Verify that the function created an app context
        mock_create_app.assert_called_once()
        mock_app.app_context.assert_called_once()
        
        # Verify that the scraping job was run
        mock_run_scraping.assert_called_once()
        
        # Verify that the history was recorded in the database
        assert mock_db.session.add.call_count == 1
        assert mock_db.session.commit.call_count == 1
        
        # Verify the result
        assert result == mock_result

    @patch('app.utils.scheduler.create_app')
    @patch('app.utils.scheduler.run_scraping_job')
    @patch('app.utils.scheduler.db')
    def test_scheduled_scraping_job_db_error(self, mock_db, mock_run_scraping, mock_create_app):
        """Test handling database errors in the scheduled scraping job."""
        # Set up mocks
        mock_app = MagicMock()
        mock_app_context = MagicMock()
        mock_app.app_context.return_value = mock_app_context
        mock_create_app.return_value = mock_app
        
        # Mock successful scraping result
        mock_result = {
            'start_time': datetime.now(),
            'end_time': datetime.now() + timedelta(minutes=5),
            'sources_scraped': 10,
            'grants_found': 25,
            'grants_added': 15,
            'status': 'completed'
        }
        mock_run_scraping.return_value = mock_result
        
        # Mock a database error
        mock_db.session.commit.side_effect = Exception("Database error")
        mock_db.session.is_active = True
        
        # Call the function
        result = scheduled_scraping_job()
        
        # Verify that the scraping job was run
        mock_run_scraping.assert_called_once()
        
        # Verify that a rollback was performed
        mock_db.session.rollback.assert_called_once()
        
        # Verify the result still contains the scraping job outcome
        assert result == mock_result

    @patch('app.utils.scheduler.create_app')
    @patch('app.utils.scheduler.run_scraping_job')
    def test_scheduled_scraping_job_scraping_error(self, mock_run_scraping, mock_create_app):
        """Test handling errors in the scraping job itself."""
        # Set up mocks
        mock_app = MagicMock()
        mock_app_context = MagicMock()
        mock_app.app_context.return_value = mock_app_context
        mock_create_app.return_value = mock_app
        
        # Mock a scraping job error
        mock_run_scraping.side_effect = Exception("Scraping error")
        
        # Call the function
        result = scheduled_scraping_job()
        
        # Verify the result contains the error information
        assert result['status'] == 'failed'
        assert result['error_message'] == 'Scraping error'
        assert result['grants_added'] == 0
        assert result['grants_found'] == 0
        assert result['sources_scraped'] == 0

    @patch('app.utils.scheduler.schedule')
    def test_get_next_scheduled_run_with_runs(self, mock_schedule):
        """Test getting the next scheduled run when runs are scheduled."""
        # Set up mocks
        next_run_time = datetime.now() + timedelta(hours=1)
        mock_schedule.next_run.return_value = next_run_time
        
        # Call the function
        result = get_next_scheduled_run()
        
        # Verify the result
        assert next_run_time.strftime("%Y-%m-%d") in result
        assert "UTC" in result

    @patch('app.utils.scheduler.schedule')
    def test_get_next_scheduled_run_without_runs(self, mock_schedule):
        """Test getting the next scheduled run when no runs are scheduled."""
        # Set up mocks
        mock_schedule.next_run.return_value = None
        
        # Call the function
        result = get_next_scheduled_run()
        
        # Verify the result
        assert result == "No scheduled runs"

    @patch('app.utils.scheduler.schedule')
    def test_get_next_scheduled_run_error(self, mock_schedule):
        """Test handling errors when getting the next scheduled run."""
        # Set up mocks
        mock_schedule.next_run.side_effect = Exception("Test exception")
        
        # Call the function
        result = get_next_scheduled_run()
        
        # Verify the result
        assert "Error" in result

    def test_stop_scheduler_when_running(self):
        """Test stopping the scheduler when it's running."""
        # Start the scheduler
        initialize_scheduler()
        
        # Verify the scheduler is running
        assert scheduler_running is True
        assert scheduler_thread is not None
        assert scheduler_thread.is_alive() is True
        
        # Stop the scheduler
        result = stop_scheduler()
        
        # Verify the result
        assert result['status'] == 'success'
        
        # Verify the scheduler was stopped
        assert scheduler_running is False
        assert scheduler_thread is not None  # Thread object still exists
        assert scheduler_thread.is_alive() is False  # But thread is not alive

    def test_stop_scheduler_when_not_running(self):
        """Test stopping the scheduler when it's not running."""
        # Make sure the scheduler is not running
        import app.utils.scheduler
        app.utils.scheduler.scheduler_running = False
        app.utils.scheduler.scheduler_thread = None
        
        # Stop the scheduler
        result = stop_scheduler()
        
        # Verify the result
        assert result['status'] == 'warning'
        assert "not running" in result['message']

    @patch('app.utils.scheduler.threading')
    def test_stop_scheduler_error(self, mock_threading):
        """Test handling errors when stopping the scheduler."""
        # Set up mocks
        thread_mock = MagicMock()
        thread_mock.is_alive.return_value = True
        thread_mock.join.side_effect = Exception("Thread error")
        
        # Set up global variables
        import app.utils.scheduler
        app.utils.scheduler.scheduler_running = True
        app.utils.scheduler.scheduler_thread = thread_mock
        
        # Stop the scheduler
        result = stop_scheduler()
        
        # Verify the result
        assert result['status'] == 'error'
        assert 'Thread error' in result['error']