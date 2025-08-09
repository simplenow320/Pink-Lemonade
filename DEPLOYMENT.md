# Pink Lemonade - Production Deployment Guide

## Phase 6: Deployment Configuration

### Prerequisites
- PostgreSQL database
- OpenAI API key
- SMTP credentials for email notifications
- Domain name (optional)

### Environment Variables

Create a `.env` file with:

```bash
# Database
DATABASE_URL=postgresql://user:password@host:port/dbname

# Security
SESSION_SECRET=your-secret-key-here
FLASK_SECRET_KEY=another-secret-key

# APIs
OPENAI_API_KEY=sk-your-openai-key

# Email (optional)
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Data Mode
APP_DATA_MODE=LIVE

# Optional API Keys
GRANTS_GOV_API_KEY=your-key
CANDID_API_KEY=your-key
```

### Database Setup

1. Create PostgreSQL database:
```sql
CREATE DATABASE pinklemonade;
```

2. Run migrations:
```bash
python -c "from app import create_app; app = create_app(); app.app_context().push()"
```

3. Create indexes for performance:
```python
from app.utils.performance import create_database_indexes
create_database_indexes()
```

### Production Configuration

1. **Gunicorn Configuration** (`gunicorn.conf.py`):
```python
bind = "0.0.0.0:5000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 50
preload_app = True
accesslog = "access.log"
errorlog = "error.log"
loglevel = "info"
```

2. **Nginx Configuration** (if using reverse proxy):
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
    
    client_max_body_size 10M;
}
```

### Monitoring Setup

1. **Health Check Endpoint**: `/api/admin/system/health`
2. **Metrics Endpoint**: `/api/admin/dashboard`
3. **Error Logs**: Check `error.log` file

### Backup Strategy

1. **Database Backups**:
```bash
# Daily backup script
pg_dump $DATABASE_URL > backup_$(date +%Y%m%d).sql
```

2. **File Backups**:
- Upload directory
- Configuration files
- Log files

### Security Checklist

- [x] Environment variables for sensitive data
- [x] HTTPS enabled (via Replit or Nginx)
- [x] SQL injection prevention (SQLAlchemy ORM)
- [x] XSS protection (template escaping)
- [x] CSRF protection (Flask-WTF)
- [x] Rate limiting on API endpoints
- [x] Secure password hashing (bcrypt)
- [x] Session security (secure cookies)

### Performance Optimization

1. **Database**:
   - Indexes created on frequently queried columns
   - Connection pooling enabled
   - Query optimization with pagination

2. **Caching**:
   - In-memory cache for API responses
   - Cache TTL: 5 minutes for grant data
   - Cache stats available in admin dashboard

3. **Frontend**:
   - Lazy loading for grant lists
   - Pagination (20 items per page)
   - Debounced search inputs

### Deployment Steps

1. **Clone repository**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

3. **Set environment variables**
4. **Initialize database**
5. **Create first admin user**:
   ```python
   from app.models.user import User
   admin = User(username='admin', email='admin@pinklemonade.com', role='admin')
   admin.set_password('secure-password')
   db.session.add(admin)
   db.session.commit()
   ```

6. **Start application**:
   ```bash
   gunicorn main:app
   ```

### Monitoring Commands

```bash
# Check system health
curl http://localhost:5000/api/admin/system/health

# View cache statistics
curl http://localhost:5000/api/admin/dashboard

# Check error logs
tail -f error.log
```

### Troubleshooting

1. **Database connection errors**: Check DATABASE_URL
2. **API failures**: Verify API keys are set
3. **Performance issues**: Check cache hit rate and slow queries
4. **Memory issues**: Adjust gunicorn workers

### Support

For issues or questions:
1. Check error logs
2. Review health endpoint
3. Monitor system metrics
4. Contact support with health report

## Deployment Complete! 🚀

Your Pink Lemonade platform is ready for production use.