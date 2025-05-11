"""
Synchronize Manual Sources

This script synchronizes the manual funders from manual_sources.json to the database as ScraperSources.
"""

import json
import logging
import os
import sys
from app import db
from app.models.scraper import ScraperSource

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def sync_manual_sources():
    """
    Sync the manual sources from manual_sources.json to the database as ScraperSources
    """
    try:
        # Check if manual_sources.json exists
        if not os.path.exists('manual_sources.json'):
            logger.error("manual_sources.json not found")
            return False
        
        # Read the manual_sources.json file
        with open('manual_sources.json', 'r') as f:
            manual_sources = json.load(f)
        
        if not isinstance(manual_sources, list):
            logger.error("manual_sources.json does not contain an array")
            return False
        
        # Track stats
        stats = {
            'added': 0,
            'existing': 0,
            'skipped': 0
        }
        
        # Process each manual source
        for source in manual_sources:
            if not isinstance(source, dict) or 'name' not in source or 'url' not in source:
                logger.warning(f"Skipping invalid source: {source}")
                stats['skipped'] += 1
                continue
            
            # Check if this source already exists
            existing_source = ScraperSource.query.filter_by(url=source['url']).first()
            if existing_source:
                logger.info(f"Source already exists: {source['name']} ({source['url']})")
                # Update the name if needed
                if existing_source.name != source['name']:
                    existing_source.name = source['name']
                    db.session.commit()
                    logger.info(f"Updated name for: {source['name']}")
                
                stats['existing'] += 1
                continue
            
            # Create a new ScraperSource
            location = source.get('location', 'Unknown')
            # Create a name that includes the location
            name = f"{source['name']} ({location})"
            
            new_source = ScraperSource(
                name=name,
                url=source['url'],
                selector_config={},  # Empty selector config for manual sources
                is_active=True
            )
            
            db.session.add(new_source)
            logger.info(f"Added new source: {name} ({source['url']})")
            stats['added'] += 1
        
        # Commit all changes
        db.session.commit()
        
        logger.info(f"Sync complete: Added {stats['added']}, Already existing: {stats['existing']}, Skipped: {stats['skipped']}")
        return stats
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error synchronizing manual sources: {str(e)}")
        return False

def main():
    """
    Main function
    """
    from app import create_app
    app = create_app()
    
    with app.app_context():
        stats = sync_manual_sources()
        if stats:
            print(f"Manual sources synchronized successfully: Added {stats['added']}, Already existing: {stats['existing']}, Skipped: {stats['skipped']}")
            return 0
        else:
            print("Failed to synchronize manual sources")
            return 1

if __name__ == "__main__":
    sys.exit(main())