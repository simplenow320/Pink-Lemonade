"""
Performance optimization utilities
Database indexes, query optimization, lazy loading
"""

from app import db
import logging

logger = logging.getLogger(__name__)

def create_database_indexes():
    """Create database indexes for better performance"""
    try:
        # Grant indexes
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_status ON grants(status)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_deadline ON grants(deadline)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_funder ON grants(funder)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_source_name ON grants(source_name)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_match_score ON grants(match_score DESC)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_grants_created_at ON grants(created_at DESC)')
        
        # User indexes
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_users_username ON users(username)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_users_role ON users(role)')
        
        # Organization indexes
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_organizations_name ON organizations(name)')
        
        # Watchlist indexes
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_user_id ON watchlist(user_id)')
        db.session.execute('CREATE INDEX IF NOT EXISTS idx_watchlist_type ON watchlist(type)')
        
        db.session.commit()
        logger.info("Database indexes created successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")
        db.session.rollback()
        return False

def optimize_query(query, limit=100):
    """Optimize database query with pagination and limiting"""
    return query.limit(limit).all()

def batch_insert(model_class, records, batch_size=100):
    """Batch insert records for better performance"""
    try:
        for i in range(0, len(records), batch_size):
            batch = records[i:i + batch_size]
            db.session.bulk_insert_mappings(model_class, batch)
            db.session.commit()
            logger.debug(f"Inserted batch of {len(batch)} records")
        
        logger.info(f"Batch inserted {len(records)} records")
        return True
        
    except Exception as e:
        logger.error(f"Error in batch insert: {e}")
        db.session.rollback()
        return False

def lazy_load_grants(page=1, per_page=20, filters=None):
    """Lazy load grants with pagination"""
    from app.models.grant import Grant
    
    query = Grant.query
    
    # Apply filters
    if filters:
        if filters.get('status'):
            query = query.filter_by(status=filters['status'])
        if filters.get('funder'):
            query = query.filter_by(funder=filters['funder'])
        if filters.get('min_score'):
            query = query.filter(Grant.match_score >= filters['min_score'])
    
    # Order by relevance
    query = query.order_by(Grant.match_score.desc(), Grant.created_at.desc())
    
    # Paginate
    return query.paginate(page=page, per_page=per_page, error_out=False)

def preload_related(grants):
    """Preload related data to avoid N+1 queries"""
    from sqlalchemy.orm import joinedload
    
    # Preload narratives and source relationships
    grant_ids = [g.id for g in grants]
    
    # Load all related data in one query
    from app.models.grant import Grant
    return Grant.query.filter(Grant.id.in_(grant_ids)).options(
        joinedload(Grant.narrative)
    ).all()

def analyze_slow_queries():
    """Analyze and log slow queries"""
    try:
        # Get slow queries (PostgreSQL specific)
        result = db.session.execute("""
            SELECT query, calls, mean_exec_time
            FROM pg_stat_statements
            WHERE mean_exec_time > 100
            ORDER BY mean_exec_time DESC
            LIMIT 10
        """)
        
        slow_queries = []
        for row in result:
            slow_queries.append({
                'query': row[0][:100],  # First 100 chars
                'calls': row[1],
                'avg_time_ms': row[2]
            })
        
        return slow_queries
        
    except Exception as e:
        logger.error(f"Error analyzing slow queries: {e}")
        return []