# Production Deployment Command Reference

## Quick Commands

### Validate Configuration
```bash
cd flask-app
./run_production.sh --validate
```

### Start Production (Docker)
```bash
cd flask-app
docker-compose -f ../docker-compose.production.yml up -d
```

### Start Production (Gunicorn)
```bash
cd flask-app
./run_production.sh --local
```

### View Logs
```bash
docker-compose -f docker-compose.production.yml logs -f app
```

### Restart Services
```bash
docker-compose -f docker-compose.production.yml restart
```

### Stop Services
```bash
docker-compose -f docker-compose.production.yml down
```

### Database Backup
```bash
docker-compose -f docker-compose.production.yml exec db mysqldump \
  -u root -p$MYSQL_ROOT_PASSWORD cms_db > backup.sql
```

### Database Restore
```bash
docker-compose -f docker-compose.production.yml exec -T db mysql \
  -u root -p$MYSQL_ROOT_PASSWORD cms_db < backup.sql
```

### Database Shell
```bash
docker-compose -f docker-compose.production.yml exec db mysql \
  -u root -p$MYSQL_ROOT_PASSWORD
```

### Application Shell
```bash
docker-compose -f docker-compose.production.yml exec app bash
```

### View Resource Usage
```bash
docker stats
```

### Check Service Status
```bash
docker-compose -f docker-compose.production.yml ps
```

### Test Health Endpoint
```bash
curl http://localhost:5000/api/meta
```

### View Network Configuration
```bash
docker network inspect cms_network
```

### Inspect Container
```bash
docker inspect cms_app_prod
```

### View Container Events
```bash
docker-compose -f docker-compose.production.yml events
```

## Environment File Management

### Copy Production Template
```bash
cp .env.production .env
```

### Generate Secure Secrets
```bash
# SECRET_KEY
python3 -c "import secrets; print('SECRET_KEY=' + secrets.token_hex(32))"

# JWT_SECRET_KEY
python3 -c "import secrets; print('JWT_SECRET_KEY=' + secrets.token_hex(32))"
```

### Validate Environment
```bash
# Check if all required vars are set
env | grep -E "SECRET|JWT|DATABASE|MYSQL|MAIL|CORS"
```

### Update Environment Variable
```bash
# Modify .env file
nano .env

# Restart services to apply changes
docker-compose -f docker-compose.production.yml restart app
```

## SSL/TLS with Let's Encrypt

### Generate Certificate
```bash
sudo certbot certonly --standalone \
  -d yourdomain.com \
  -d www.yourdomain.com
```

### Verify Certificate
```bash
openssl s_client -connect yourdomain.com:443
```

### Certificate Renewal (Manual)
```bash
sudo certbot renew --dry-run
sudo certbot renew
```

### Certificate Renewal (Automatic via Cron)
```bash
# Add to crontab (crontab -e)
0 2 * * * /usr/bin/certbot renew --quiet
```

## Nginx Setup

### Copy Configuration
```bash
sudo cp nginx.conf.example /etc/nginx/sites-available/campus-grievance-hub
```

### Update Domain
```bash
sudo nano /etc/nginx/sites-available/campus-grievance-hub
# Replace yourdomain.com with your actual domain
# Update certificate paths if needed
```

### Enable Site
```bash
sudo ln -s /etc/nginx/sites-available/campus-grievance-hub /etc/nginx/sites-enabled/
```

### Test Configuration
```bash
sudo nginx -t
```

### Reload Nginx
```bash
sudo systemctl reload nginx
```

### View Nginx Status
```bash
sudo systemctl status nginx
```

### View Nginx Logs
```bash
# Access logs
sudo tail -f /var/log/nginx/campus-grievance-hub-access.log

# Error logs
sudo tail -f /var/log/nginx/campus-grievance-hub-error.log
```

## Backup & Recovery

### Automated Daily Backup Script
```bash
#!/bin/bash
# Create backup.sh
BACKUP_DIR="/backups"
mkdir -p $BACKUP_DIR

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
docker-compose -f docker-compose.production.yml exec -T db mysqldump \
  -u root -p$MYSQL_ROOT_PASSWORD cms_db > "$BACKUP_DIR/cms_db_$TIMESTAMP.sql"

# Keep only last 30 days
find $BACKUP_DIR -name "cms_db_*.sql" -mtime +30 -delete

# Make executable
chmod +x backup.sh

# Add to crontab (runs daily at 2 AM)
# 0 2 * * * /path/to/backup.sh
```

### List Backups
```bash
ls -lh /backups/
```

### Restore from Backup
```bash
docker-compose -f docker-compose.production.yml exec -T db mysql \
  -u root -p$MYSQL_ROOT_PASSWORD cms_db < /backups/cms_db_TIMESTAMP.sql
```

### Backup Upload to Cloud (AWS S3 example)
```bash
#!/bin/bash
# Append to backup.sh
aws s3 cp "$BACKUP_DIR/cms_db_$TIMESTAMP.sql" s3://your-bucket/backups/
```

## Monitoring & Logs

### System Logs
```bash
# Docker daemon logs
journalctl -u docker -f

# System logs
tail -f /var/log/syslog
```

### Application Logs
```bash
# Real-time logs
docker logs -f cms_app_prod

# Last 100 lines
docker logs --tail=100 cms_app_prod

# With timestamps
docker logs -t cms_app_prod
```

### Database Logs
```bash
# Error logs
docker logs cms_mysql_prod

# Slow queries (inside container)
docker exec cms_mysql_prod tail -f /var/log/mysql/slow-query.log
```

### Log Aggregation (ELK Stack example)
```bash
# Start ELK with docker-compose
docker-compose -f docker-compose.elk.yml up -d

# Configure logstash to read Docker logs
# See ELK documentation for details
```

## Performance Tuning

### Monitor in Real-Time
```bash
watch docker stats
```

### Check Database Connections
```bash
docker-compose exec db mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW PROCESSLIST;"
```

### View MySQL Status
```bash
docker-compose exec db mysql -u root -p$MYSQL_ROOT_PASSWORD -e "SHOW STATUS LIKE '%connect%';"
```

### Increase Gunicorn Workers (if needed)
Edit `docker-compose.production.yml`:
```yaml
services:
  app:
    command: >
      gunicorn --bind 0.0.0.0:5000
      --workers 8
      --worker-class sync
      wsgi:application
```

### Increase Database Buffer Pool
Edit `my-prod.cnf`:
```ini
innodb_buffer_pool_size = 4G  # Increase if you have more RAM
```

## Troubleshooting

### Application Won't Start
```bash
# Check logs
docker logs cms_app_prod

# Test database connection
docker-compose exec app python3 -c "from app import create_app, db; app = create_app('production'); print('OK')"

# Check environment variables
docker-compose exec app env | grep -E "SECRET|DATABASE"
```

### Database Connection Failed
```bash
# Check MySQL is running
docker-compose ps db

# Test connection
docker-compose exec app mysql -h db -u cms_user -p -e "SELECT 1;"

# Check MySQL logs
docker logs cms_mysql_prod
```

### Port Already in Use
```bash
# Find process using port
sudo lsof -i :5000

# Change port in .env
PORT=8000

# Restart services
docker-compose restart app
```

### High Memory Usage
```bash
# Check container stats
docker stats

# Increase container memory limit in docker-compose.production.yml
# Restart container
docker-compose restart app

# Check for memory leaks
docker logs -f cms_app_prod
```

### SSL Certificate Issues
```bash
# Verify certificate
openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Check certificate expiry
echo | openssl s_client -servername yourdomain.com -connect yourdomain.com:443 2>/dev/null | openssl x509 -noout -dates

# Renewal
sudo certbot renew
```

## Scale Horizontally (Multiple Instances)

### Run Multiple App Instances
```bash
# Update docker-compose.production.yml to add app instances
services:
  app1:
    build: .
    # configuration...
  app2:
    build: .
    # configuration...
  nginx:
    # Route traffic to app1 and app2
```

### Load Balance
```bash
# Update nginx.conf
upstream flask_app {
  server app1:5000;
  server app2:5000;
  server app3:5000;
}

# Use in location block
location / {
  proxy_pass http://flask_app;
}
```

## Database Upgrade

### Backup Before Upgrade
```bash
docker-compose exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD --all-databases > full_backup.sql
```

### Upgrade MySQL
```bash
# Update docker-compose.yml with new MySQL version
# image: mysql:8.1

# Stop services
docker-compose down

# Remove old MySQL volume (backup first!)
docker volume rm cms_mysql_data

# Rebuild and start
docker-compose up -d
```

## Security Audit

### Check Container Security
```bash
# No privileged containers
docker inspect cms_app_prod | grep '"Privileged"'

# No root user
docker inspect cms_app_prod | grep '"User"'

# No mounted docker socket
docker inspect cms_app_prod | grep '/var/run/docker.sock'
```

### Scan for Vulnerabilities
```bash
docker scan campus-grievance-hub:latest
```

### Check Security Headers
```bash
curl -I https://yourdomain.com | grep -E "^[A-Z]"
```

---

**Pro Tip**: Create shell aliases for frequently used commands:

```bash
# Add to ~/.bashrc or ~/.zshrc
alias cgh-start="docker-compose -f docker-compose.production.yml up -d"
alias cgh-stop="docker-compose -f docker-compose.production.yml down"
alias cgh-logs="docker-compose -f docker-compose.production.yml logs -f app"
alias cgh-backup="docker-compose -f docker-compose.production.yml exec -T db mysqldump -u root -p\$MYSQL_ROOT_PASSWORD cms_db > backup_\$(date +%Y%m%d_%H%M%S).sql"

# Reload shell
source ~/.bashrc
```

Use them:
```bash
cgh-start
cgh-logs
cgh-backup
```
