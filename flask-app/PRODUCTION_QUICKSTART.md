# Campus Grievance Hub - Production Deployment Quick Start

> **5-Minute Quick Start Guide** | See [DEPLOYMENT.md](DEPLOYMENT.md) for complete documentation

## Prerequisites

```bash
# Required
- Docker & Docker Compose installed
- Git repository cloned
- Domain name configured with DNS
- SSL certificate ready (use Let's Encrypt)
```

## Deployment in 5 Steps

### 1. Clone and Enter Directory

```bash
git clone <repository-url>
cd Campus-Grievance-Hub
cd flask-app
```

### 2. Generate Secure Secrets

```bash
# Generate SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: abcd1234...xyz

# Generate JWT_SECRET_KEY
python3 -c "import secrets; print(secrets.token_hex(32))"
# Output: efgh5678...uv
```

### 3. Configure Environment

```bash
# Copy production template
cp .env.production .env

# Edit with your values
nano .env
```

**Minimum required changes:**
```env
FLASK_ENV=production
FLASK_DEBUG=false
SECRET_KEY=YOUR_SECRET_FROM_STEP_2
JWT_SECRET_KEY=YOUR_JWT_SECRET_FROM_STEP_2
CMS_DATABASE_URL=mysql+pymysql://cms_user:PASSWORD@db:3306/cms_db
MYSQL_ROOT_PASSWORD=strong_root_password
MYSQL_PASSWORD=strong_cms_password
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
CORS_ORIGINS=https://yourdomain.com
SESSION_COOKIE_SECURE=true
SEED_DB=false
```

### 4. Deploy with Docker

```bash
# Build images
docker-compose -f ../docker-compose.production.yml build

# Start services
docker-compose -f ../docker-compose.production.yml up -d

# Verify
docker-compose -f ../docker-compose.production.yml ps
```

### 5. Verify Deployment

```bash
# Check logs
docker-compose -f ../docker-compose.production.yml logs -f app

# Test health
curl http://localhost:5000/api/meta

# Test login
# Visit http://localhost:5000 in browser
# Admin: admin@college.edu / admin123
# Student: student1@college.edu / student123
```

## Common Commands

```bash
# View logs
docker-compose -f ../docker-compose.production.yml logs -f app

# Restart services
docker-compose -f ../docker-compose.production.yml restart

# Backup database
docker-compose -f ../docker-compose.production.yml exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD cms_db > backup.sql

# Access MySQL
docker-compose -f ../docker-compose.production.yml exec db mysql -u root -p

# Stop services
docker-compose -f ../docker-compose.production.yml down

# View resource usage
docker stats
```

## Setup HTTPS with Nginx (Recommended)

```bash
# 1. Install Nginx
sudo apt-get install nginx certbot python3-certbot-nginx

# 2. Copy Nginx config
sudo cp ../nginx.conf.example /etc/nginx/sites-available/campus-grievance-hub
sudo nano /etc/nginx/sites-available/campus-grievance-hub

# 3. Enable site
sudo ln -s /etc/nginx/sites-available/campus-grievance-hub /etc/nginx/sites-enabled/

# 4. Get SSL certificate
sudo certbot certonly --standalone -d yourdomain.com -d www.yourdomain.com

# 5. Configure SSL in Nginx (edit config with certificate paths)
sudo nano /etc/nginx/sites-available/campus-grievance-hub

# 6. Test and reload Nginx
sudo nginx -t
sudo systemctl reload nginx
```

## SSL Certificate Auto-Renewal

```bash
# Install renewal cron job
sudo certbot renew --dry-run

# Certificate will auto-renew 30 days before expiration
# Check status: sudo certbot certificates
```

## Monitoring

### Check Application Status

```bash
# Health endpoint
curl https://yourdomain.com/api/meta

# View logs
docker logs cms_app_prod -f

# Monitor resources
docker stats
```

### Setup Automated Backups

```bash
#!/bin/bash
# backup.sh
BACKUP_DIR="/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

docker-compose -f docker-compose.production.yml exec -T db mysqldump \
  -u root -p$MYSQL_ROOT_PASSWORD cms_db > "$BACKUP_DIR/cms_db_$TIMESTAMP.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "cms_db_*.sql" -mtime +30 -delete

# Add to crontab:
# 0 2 * * * /path/to/backup.sh
```

## Troubleshooting

| Problem | Solution |
|---------|----------|
| **Application won't start** | Check logs: `docker-compose logs app` |
| **Database connection fails** | Verify CMS_DATABASE_URL in .env |
| **Port already in use** | Change PORT in .env or kill existing process |
| **SSL certificate error** | Verify certificate path in nginx.conf |
| **High memory usage** | Increase innodb_buffer_pool_size or add more instances |

## Security Checklist (Before Going Live)

- [ ] Changed all default passwords
- [ ] Generated strong SECRET_KEY and JWT_SECRET_KEY
- [ ] Disabled SEED_DB after initial setup
- [ ] Restricted CORS to production domain(s)
- [ ] Enabled HTTPS/SSL
- [ ] Configured automated backups
- [ ] Setup monitoring/alerts
- [ ] Verified database backups work
- [ ] Tested user login/authentication
- [ ] Verified email notifications work
- [ ] Setup firewall rules
- [ ] Enabled log rotation

## Support

- **Full Documentation**: See [DEPLOYMENT.md](../DEPLOYMENT.md)
- **Deployment Checklist**: See [PRODUCTION_CHECKLIST.md](../PRODUCTION_CHECKLIST.md)
- **API Documentation**: See [API_DOCUMENTATION.md](./API_DOCUMENTATION.md)
- **Issues**: Report on GitHub

## Demo Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@college.edu | admin123 |
| Student | student1@college.edu | student123 |

---

**Ready to deploy?** Start with Step 1 above! 🚀

For detailed information about production optimization, security hardening, and scaling, see [DEPLOYMENT.md](../DEPLOYMENT.md).
