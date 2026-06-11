# Campus Grievance Hub - Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Campus Grievance Hub to production environments.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Local Production Build](#local-production-build)
3. [Docker Deployment](#docker-deployment)
4. [Cloud Deployment](#cloud-deployment)
5. [Security Checklist](#security-checklist)
6. [Monitoring & Logs](#monitoring--logs)
7. [Troubleshooting](#troubleshooting)

---

## Prerequisites

- Docker & Docker Compose installed
- Python 3.11+ (for local builds)
- Git for version control
- OpenSSL for certificate generation
- Valid domain name with DNS configured
- SSL/TLS certificate (from Let's Encrypt, AWS ACM, etc.)

---

## Local Production Build

### 1. Clone & Setup

```bash
git clone <repository-url>
cd Campus-Grievance-Hub
cd flask-app
```

### 2. Create Environment File

```bash
cp .env.production .env
# Edit .env with your production values
nano .env
```

**Required changes in .env:**
- `SECRET_KEY` - Generate: `python -c "import secrets; print(secrets.token_hex(32))"`
- `JWT_SECRET_KEY` - Generate new secret
- `CMS_DATABASE_URL` - Set to your MySQL connection string
- `MYSQL_PASSWORD` - Set secure password
- `MAIL_USERNAME` & `MAIL_PASSWORD` - Configure email service
- `CORS_ORIGINS` - Set to your production domain

### 3. Install Dependencies

```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 4. Initialize Database

```bash
# Create tables and seed initial data
export FLASK_ENV=production
python -c "from app import create_app, db; app = create_app('production'); \
    with app.app_context(): db.create_all(); print('Database initialized!')"
```

### 5. Run with Gunicorn

```bash
gunicorn --bind 0.0.0.0:5000 \
         --workers 4 \
         --worker-class sync \
         --timeout 120 \
         --access-logfile - \
         --error-logfile - \
         "wsgi:application"
```

---

## Docker Deployment

### 1. Build Docker Images

```bash
cd flask-app
docker build -t campus-grievance-hub:latest .
```

### 2. Setup Environment

```bash
cp .env.production .env.production.local
# Edit with your production secrets
nano .env.production.local
```

### 3. Deploy with Docker Compose

```bash
# Using specific environment file
docker-compose --env-file .env.production.local up -d

# Or with explicit variables
export $(cat .env.production.local | grep -v '^#' | xargs)
docker-compose up -d
```

### 4. Verify Deployment

```bash
# Check services
docker-compose ps

# View logs
docker-compose logs -f app

# Test health endpoint
curl http://localhost:5000/api/meta
```

### 5. Database Migrations (if needed)

```bash
# Create tables in MySQL
docker-compose exec app python -c "from app import create_app, db; \
    app = create_app('production'); \
    with app.app_context(): db.create_all()"
```

---

## Cloud Deployment

### AWS EC2

1. **Launch EC2 Instance**
   - AMI: Ubuntu 22.04 LTS
   - Instance Type: t3.medium or larger
   - Storage: 20GB+ EBS volume
   - Security Group: Allow 80, 443, 22

2. **Install Docker**
   ```bash
   sudo apt-get update
   sudo apt-get install -y docker.io docker-compose
   sudo systemctl start docker
   sudo usermod -aG docker $USER
   ```

3. **Deploy Application**
   ```bash
   git clone <repo>
   cd Campus-Grievance-Hub/flask-app
   cp .env.production .env
   nano .env  # Configure production values
   docker-compose up -d
   ```

4. **Setup Reverse Proxy (Nginx)**
   ```bash
   sudo apt-get install -y nginx
   # See nginx.conf example below
   ```

### Heroku

1. **Install Heroku CLI**
   ```bash
   curl https://cli.heroku.com/install.sh | sh
   heroku login
   ```

2. **Create Heroku App**
   ```bash
   heroku create campus-grievance-hub
   heroku addons:create cleardb:ignite  # Free MySQL addon
   ```

3. **Set Environment Variables**
   ```bash
   heroku config:set SECRET_KEY=<your-secret>
   heroku config:set JWT_SECRET_KEY=<your-jwt-secret>
   heroku config:set CMS_DATABASE_URL=$(heroku config:get CLEARDB_DATABASE_URL)
   ```

4. **Deploy**
   ```bash
   git push heroku main
   ```

### Google Cloud Run

1. **Build Container Image**
   ```bash
   gcloud builds submit --tag gcr.io/PROJECT_ID/campus-grievance-hub
   ```

2. **Deploy Service**
   ```bash
   gcloud run deploy campus-grievance-hub \
     --image gcr.io/PROJECT_ID/campus-grievance-hub \
     --platform managed \
     --region us-central1 \
     --set-env-vars SECRET_KEY=<secret>,CMS_DATABASE_URL=<mysql-url>
   ```

---

## Security Checklist

Before deploying to production, ensure:

### Environment & Secrets
- [ ] `SECRET_KEY` is a strong, randomly generated 32+ character string
- [ ] `JWT_SECRET_KEY` is unique and secure
- [ ] `.env` file is in `.gitignore` and never committed
- [ ] All default passwords have been changed
- [ ] Database credentials are stored securely (secrets manager, not code)

### HTTPS/TLS
- [ ] SSL/TLS certificate installed (Let's Encrypt recommended)
- [ ] Redirect HTTP to HTTPS
- [ ] HSTS header enabled (Strict-Transport-Security)
- [ ] Certificate auto-renewal configured

### Database
- [ ] MySQL database has strong root password
- [ ] `cms_user` has limited privileges (no DROP, ALTER)
- [ ] Database backups configured (daily recommended)
- [ ] Database connection uses encrypted SSL/TLS
- [ ] Regular backups stored off-server

### Application
- [ ] DEBUG mode disabled (`FLASK_DEBUG=false`)
- [ ] CORS origins restricted to your domain(s)
- [ ] Session cookies are HttpOnly and Secure
- [ ] SEED_DB set to `false` (prevents data resets)
- [ ] File upload directory outside web root
- [ ] Gunicorn running with appropriate worker count

### Infrastructure
- [ ] Firewall rules: only 80, 443, 22 (SSH) exposed
- [ ] Regular security updates installed
- [ ] Monitoring/alerting configured
- [ ] Automated backups enabled
- [ ] Log aggregation service enabled

### API Security
- [ ] JWT token expiration configured (8 hours)
- [ ] Rate limiting implemented
- [ ] Input validation on all endpoints
- [ ] SQL injection prevention verified (SQLAlchemy ORM)
- [ ] CSRF protection enabled

---

## Monitoring & Logs

### Docker Logs

```bash
# Real-time logs
docker-compose logs -f app

# Last 100 lines
docker-compose logs --tail=100 app

# Logs from specific service
docker-compose logs db
```

### Application Logs

The application writes logs to:
- **Console**: For Docker container output
- **File**: `app/app.log` (if mounted)

Configure log level via environment:
```bash
LOG_LEVEL=INFO  # DEBUG, INFO, WARNING, ERROR, CRITICAL
```

### Monitoring Stack (Optional)

Recommended for production:
- **Prometheus** - Metrics collection
- **Grafana** - Visualization
- **ELK Stack** - Log aggregation
- **Sentry** - Error tracking

Example Prometheus setup:
```yaml
# prometheus.yml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'flask-app'
    static_configs:
      - targets: ['localhost:5000']
```

---

## Database Backup & Recovery

### Automated Backups

```bash
#!/bin/bash
# backup.sh - Run daily via cron
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker-compose exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD cms_db \
    > "$BACKUP_DIR/cms_db_$TIMESTAMP.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "cms_db_*.sql" -mtime +30 -delete
```

### Manual Backup

```bash
docker-compose exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD cms_db > backup.sql
```

### Restore from Backup

```bash
docker-compose exec -T db mysql -u root -p$MYSQL_ROOT_PASSWORD cms_db < backup.sql
```

---

## Scaling

### Horizontal Scaling (Multiple Instances)

```yaml
# docker-compose.yml - Multiple Flask instances
version: '3.9'

services:
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
    depends_on:
      - app1
      - app2
      - app3

  app1:
    build: .
    environment:
      - FLASK_ENV=production
      - CMS_DATABASE_URL=mysql+pymysql://cms_user:password@db:3306/cms_db
    depends_on:
      - db

  app2:
    build: .
    environment:
      - FLASK_ENV=production
      - CMS_DATABASE_URL=mysql+pymysql://cms_user:password@db:3306/cms_db
    depends_on:
      - db

  db:
    image: mysql:8.0
    environment:
      MYSQL_DATABASE: cms_db
      MYSQL_USER: cms_user
      MYSQL_PASSWORD: password
      MYSQL_ROOT_PASSWORD: rootpassword
    volumes:
      - mysql_data:/var/lib/mysql

volumes:
  mysql_data:
```

---

## Troubleshooting

### Application won't start

```bash
# Check logs
docker-compose logs app

# Common issues:
# - Database connection failed: Check CMS_DATABASE_URL
# - Secret key missing: Ensure SECRET_KEY is set
# - Port already in use: Check PORT and firewall
```

### Database connection issues

```bash
# Test MySQL connection
docker-compose exec db mysql -h db -u cms_user -p

# Check MySQL logs
docker-compose logs db

# Recreate database
docker-compose down -v
docker-compose up -d
```

### High memory/CPU usage

```bash
# Check container resources
docker stats

# Increase workers if CPU is low but memory high
# In docker-compose.yml, update Gunicorn workers
```

### SSL Certificate issues

```bash
# Verify certificate
openssl s_client -connect yourdomain.com:443

# For Let's Encrypt, check renewal
certbot renew --dry-run
```

---

## Performance Optimization

### 1. Database Indexing

```sql
-- Add indexes for common queries
ALTER TABLE complaints ADD INDEX idx_status (status);
ALTER TABLE complaints ADD INDEX idx_user_id (user_id);
ALTER TABLE users ADD INDEX idx_email (email);
```

### 2. Caching

Implement Redis for session/caching:
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:latest
    ports:
      - "6379:6379"
```

### 3. Gunicorn Tuning

```bash
gunicorn --workers 8 \
         --worker-class sync \
         --worker-connections 100 \
         --timeout 120 \
         --keepalive 2 \
         wsgi:application
```

### 4. Database Connection Pooling

SQLAlchemy already handles this, but verify:
```python
SQLALCHEMY_ENGINE_OPTIONS = {
    'pool_size': 10,
    'pool_recycle': 3600,
    'pool_pre_ping': True,
}
```

---

## Support & Maintenance

- **Documentation**: See `/API_DOCUMENTATION.md` for API specs
- **Issues**: Report bugs on GitHub
- **Updates**: Check for security patches regularly
- **Backups**: Maintain daily database backups

---

**Last Updated**: 2026-06-11
**Version**: 1.0.0
