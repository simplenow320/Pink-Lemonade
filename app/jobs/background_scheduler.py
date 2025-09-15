"""
Background Job Scheduler
Automates grant discovery refresh every 6 hours
"""
import logging
import threading
import time
from datetime import datetime, timedelta
from typing import Optional

from app.services.grant_discovery_service import GrantDiscoveryService

logger = logging.getLogger(__name__)


class BackgroundScheduler:
    """
    Simple background scheduler for periodic tasks
    """
    
    def __init__(self):
        self.running = False
        self.thread = None
        self.discovery_service = GrantDiscoveryService()
        self.refresh_interval_hours = 6
        
    def start(self):
        """
        Start the background scheduler
        """
        if self.running:
            logger.info("Background scheduler already running")
            return
            
        self.running = True
        self.thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.thread.start()
        logger.info("Background scheduler started")
        
    def stop(self):
        """
        Stop the background scheduler
        """
        self.running = False
        if self.thread:
            self.thread.join(timeout=5)
        logger.info("Background scheduler stopped")
        
    def _run_scheduler(self):
        """
        Main scheduler loop
        """
        logger.info(f"Scheduler running - will refresh every {self.refresh_interval_hours} hours")
        
        while self.running:
            try:
                # Run discovery refresh
                self._refresh_all_grants()
                
                # Sleep for the interval
                for _ in range(self.refresh_interval_hours * 3600):
                    if not self.running:
                        break
                    time.sleep(1)
                    
            except Exception as e:
                logger.error(f"Error in scheduler loop: {str(e)}")
                time.sleep(60)  # Wait a minute before retrying
                
    def _refresh_all_grants(self):
        """
        Refresh grants for all organizations
        """
        try:
            logger.info("Starting scheduled grant refresh for all organizations")
            
            # Use app context for database access
            from app import create_app
            app = create_app()
            
            with app.app_context():
                results = self.discovery_service.refresh_all_organizations()
                
                logger.info(f"Grant refresh completed: {results}")
                
                # Log summary
                if results.get('successful', 0) > 0:
                    logger.info(
                        f"Successfully refreshed {results['successful']} organizations, "
                        f"discovered {results.get('total_grants_discovered', 0)} new grants"
                    )
                    
        except Exception as e:
            logger.error(f"Error in grant refresh: {str(e)}")
            
    def run_immediate_refresh(self, org_id: Optional[int] = None):
        """
        Run an immediate refresh for an organization or all
        """
        try:
            from app import create_app
            app = create_app()
            
            with app.app_context():
                if org_id:
                    # Refresh single org
                    result = self.discovery_service.discover_and_persist(org_id)
                    logger.info(f"Immediate refresh for org {org_id}: {result}")
                else:
                    # Refresh all
                    results = self.discovery_service.refresh_all_organizations()
                    logger.info(f"Immediate refresh for all orgs: {results}")
                    
        except Exception as e:
            logger.error(f"Error in immediate refresh: {str(e)}")


# Singleton instance
scheduler = BackgroundScheduler()


def init_scheduler(app):
    """
    Initialize scheduler with Flask app
    """
    # Check demo mode first
    import os
    demo_mode = os.environ.get('DEMO_MODE', 'false').lower() == 'true'
    
    if demo_mode:
        app.logger.info("🎯 DEMO MODE - background scheduler disabled to prevent API quota exhaustion")
        app.logger.info("💡 Use manual refresh buttons for demo purposes")
        return
    
    # Start scheduler in production mode
    if os.environ.get('FLASK_ENV') != 'development':
        scheduler.start()
        app.logger.info("Production background scheduler initialized")
    else:
        app.logger.info("Development mode - background scheduler not started (use manual refresh)")