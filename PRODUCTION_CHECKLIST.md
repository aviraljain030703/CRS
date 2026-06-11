# Campus Grievance Hub - Production Readiness Checklist

## Complete this checklist before deploying to production

---

## 1. Security Configuration

### Secrets Management
- [ ] Generate `SECRET_KEY` (min 32 characters): `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Generate `JWT_SECRET_KEY` (min 32 characters): `python -c "import secrets; print(secrets.token_hex(32))"`
- [ ] Store secrets in `.env` file (NOT in version control)
- [ ] Add `.env` to `.gitignore`
- [ ] Verify `.env` is never committed to Git
- [ ] Use secrets manager (AWS Secrets Manager, HashiCorp Vault) for cloud deployments
- [ ] Rotate secrets periodically (quarterly recommended)

### Database Security
- [ ] Set strong MySQL root password (min 16 characters, mixed case, numbers, symbols)
- [ ] Change default `cms_user` password (min 16 characters, strong)
- [ ] Limit database user permissions (no DROP, ALTER, or admin rights)
- [ ] Enable MySQL SSL/TLS connections
- [ ] Configure database firewall rules (allow app server IP only)
- [ ] Disable MySQL external access (bind to localhost or app network)
- [ ] Setup database backups (daily minimum)
- [ ] Test backup restoration process
- [ ] Configure binary logging for data recovery
- [ ] Remove test/demo user accounts from database

### Application Security
- [ ] Set `FLASK_DEBUG=false` in production
- [ ] Set `FLASK_ENV=production`
- [ ] Disable `SEED_DB` after initial deployment (`SEED_DB=false`)
- [ ] Update CORS origins to your domain only (not `*`)
- [ ] Enable `SESSION_COOKIE_SECURE=true`
- [ ] Verify `SESSION_COOKIE_HTTPONLY=true`
- [ ] Set `SESSION_COOKIE_SAMESITE=Strict`
- [ ] Implement rate limiting on authentication endpoints
- [ ] Enable CSRF protection on forms
- [ ] Verify input validation on all endpoints
- [ ] Check for SQL injection vulnerabilities (SQLAlchemy ORM used - ✓)
- [ ] Review file upload validation and restrictions
- [ ] Ensure file uploads are outside web root
- [ ] Implement virus scanning for uploaded files (optional but recommended)

### SSL/TLS
- [ ] Obtain SSL/TLS certificate (Let's Encrypt free option)
- [ ] Configure certificate with domain and www subdomain
- [ ] Setup certificate auto-renewal (certbot for Let's Encrypt)
- [ ] Test certificate validity: `openssl s_client -connect yourdomain.com:443`
- [ ] Configure HSTS header (max-age=31536000)
- [ ] Redirect all HTTP traffic to HTTPS
- [ ] Test SSL/TLS with: https://www.ssllabs.com/ssltest/
- [ ] Disable deprecated SSL/TLS versions (TLS 1.2 minimum)
- [ ] Use strong cipher suites

### API Security
- [ ] Verify JWT token expiration is set (currently 8 hours)
- [ ] Implement API rate limiting
- [ ] Add API authentication (JWT required for all endpoints)
- [ ] Validate all input parameters
- [ ] Implement request size limits
- [ ] Add request logging for API calls
- [ ] Consider API versioning for future updates

---

## 2. Infrastructure & Deployment

### Deployment Environment
- [ ] Provision production server/cloud instance
- [ ] Setup OS updates and security patches
- [ ] Configure firewall rules:
  - [ ] Allow SSH (22) from admin IPs only
  - [ ] Allow HTTP (80) from anywhere (for ACME challenges)
  - [ ] Allow HTTPS (443) from anywhere
  - [ ] Deny all other inbound traffic
- [ ] Configure outbound rules (SMTP, DNS, package managers)
- [ ] Setup SSH key-based authentication (disable password auth)
- [ ] Disable root SSH login
- [ ] Setup sudo for deployment user
- [ ] Configure fail2ban or similar for brute force protection

### Docker & Container Setup
- [ ] Verify Docker and Docker Compose installed
- [ ] Use latest stable versions of images (python:3.11, mysql:8.0, nginx:latest)
- [ ] Build and test Docker images locally first
- [ ] Scan images for vulnerabilities: `docker scan campus-grievance-hub:latest`
- [ ] Run containers as non-root user (currently: `cmsuser`)
- [ ] Set resource limits on containers
- [ ] Configure restart policies (`unless-stopped`)
- [ ] Setup container logging to syslog/ELK stack
- [ ] Configure Docker daemon security options
- [ ] Verify Docker socket is not exposed

### Environment Configuration
- [ ] Create `.env.production` file with all production values
- [ ] Verify all required environment variables are set
- [ ] Run validation: `./run_production.sh --validate`
- [ ] Database connection string matches production MySQL
- [ ] Email configuration correct (MAIL_SERVER, MAIL_USERNAME, MAIL_PASSWORD)
- [ ] CORS_ORIGINS set to production domain(s)
- [ ] File upload paths have sufficient disk space
- [ ] Log file paths are writable

### Database Setup
- [ ] Create production MySQL database
- [ ] Create database user with limited privileges
- [ ] Run initial database migration/schema creation
- [ ] Seed initial data (admin account, categories, etc.)
- [ ] Verify database tables created: `SHOW TABLES;`
- [ ] Check table structure: `DESCRIBE complaints;`
- [ ] Verify indexes exist on frequently queried columns
- [ ] Configure database backups (daily minimum)

---

## 3. Application Configuration

### Flask Settings
- [ ] Review and update all config settings in `app/config.py`
- [ ] Verify `MAX_CONTENT_LENGTH` is appropriate (currently 16MB)
- [ ] Configure `UPLOAD_FOLDER` with write permissions
- [ ] Set `ALLOWED_EXTENSIONS` appropriately
- [ ] Configure JWT token expiration (8 hours current)
- [ ] Review all security headers in app factory
- [ ] Verify error handlers return appropriate responses

### Logging
- [ ] Configure structured logging (not just console output)
- [ ] Set `LOG_LEVEL=INFO` (or appropriate level)
- [ ] Setup log rotation (prevent disk fill)
- [ ] Configure centralized logging (e.g., ELK stack)
- [ ] Include request IDs in logs for tracing
- [ ] Exclude sensitive data from logs (passwords, tokens)
- [ ] Monitor logs for errors and warnings

### Email Configuration
- [ ] Configure email service (Gmail, SendGrid, custom SMTP)
- [ ] Test email sending in staging environment
- [ ] Verify email templates for notifications
- [ ] Add error handling for failed email sends
- [ ] Configure email rate limiting
- [ ] Add email bounce handling

---

## 4. Reverse Proxy (Nginx)

### Setup
- [ ] Install Nginx on production server
- [ ] Create Nginx configuration from `nginx.conf.example`
- [ ] Update domain names in Nginx config
- [ ] Configure SSL certificate paths
- [ ] Setup SSL redirect (HTTP to HTTPS)
- [ ] Enable gzip compression
- [ ] Configure caching headers
- [ ] Setup rate limiting rules

### Security Headers
- [ ] Add Strict-Transport-Security header
- [ ] Add X-Frame-Options header
- [ ] Add X-Content-Type-Options header
- [ ] Add X-XSS-Protection header
- [ ] Add Content-Security-Policy header
- [ ] Add Referrer-Policy header
- [ ] Add Permissions-Policy header

### Performance
- [ ] Enable gzip compression
- [ ] Configure appropriate buffer sizes
- [ ] Setup connection timeouts
- [ ] Configure proxy caching
- [ ] Setup Nginx caching for static files
- [ ] Test Nginx configuration: `nginx -t`

---

## 5. Monitoring & Alerting

### Application Monitoring
- [ ] Setup application monitoring (New Relic, DataDog, or open-source)
- [ ] Monitor CPU, memory, disk usage
- [ ] Setup uptime monitoring
- [ ] Configure alerts for errors and exceptions
- [ ] Monitor database performance
- [ ] Setup request/response time monitoring
- [ ] Track API endpoint performance

### Log Monitoring
- [ ] Setup log aggregation (ELK, Splunk, CloudWatch)
- [ ] Create dashboards for key metrics
- [ ] Setup alerts for critical errors
- [ ] Monitor login attempts
- [ ] Track admin actions
- [ ] Setup alerts for security events

### Health Checks
- [ ] Configure health check endpoint: `/api/meta`
- [ ] Test health endpoint from load balancer
- [ ] Monitor database connectivity
- [ ] Monitor disk space
- [ ] Monitor SSL certificate expiration

---

## 6. Backup & Disaster Recovery

### Database Backups
- [ ] Configure automated daily database backups
- [ ] Store backups off-server (S3, Azure Storage, GCS)
- [ ] Test backup restoration regularly
- [ ] Keep backups for minimum 30 days
- [ ] Encrypt backups in transit and at rest
- [ ] Setup backup retention policy
- [ ] Test restore procedure (quarterly)

### File Backups
- [ ] Backup uploaded files to object storage
- [ ] Backup application code in version control
- [ ] Document backup schedule
- [ ] Document recovery procedures
- [ ] Test recovery procedures

### Disaster Recovery Plan
- [ ] Document complete restore procedure
- [ ] Estimate RTO (Recovery Time Objective)
- [ ] Estimate RPO (Recovery Point Objective)
- [ ] Test DR plan quarterly
- [ ] Have DNS failover configured (if multi-region)
- [ ] Document contact information for emergencies

---

## 7. Testing & Validation

### Functional Testing
- [ ] Test user registration flow
- [ ] Test complaint submission
- [ ] Test admin dashboard functionality
- [ ] Test report generation (PDF, Excel)
- [ ] Test file uploads
- [ ] Test email notifications
- [ ] Test API endpoints with JWT tokens

### Security Testing
- [ ] Run OWASP ZAP or similar for vulnerabilities
- [ ] Test SQL injection prevention
- [ ] Test XSS prevention
- [ ] Test CSRF protection
- [ ] Test authentication bypass attempts
- [ ] Test authorization/RBAC enforcement
- [ ] Test rate limiting effectiveness
- [ ] Test SSL/TLS configuration

### Performance Testing
- [ ] Load test with concurrent users (100+)
- [ ] Test database query performance
- [ ] Test file upload performance
- [ ] Test report generation under load
- [ ] Measure response times
- [ ] Identify bottlenecks

### Browser Testing
- [ ] Test on Chrome (latest)
- [ ] Test on Firefox (latest)
- [ ] Test on Safari (latest)
- [ ] Test on Edge (latest)
- [ ] Test on mobile browsers
- [ ] Test responsive design

---

## 8. Documentation

### Technical Documentation
- [ ] Update README.md with production deployment steps
- [ ] Document system architecture
- [ ] Document deployment procedure
- [ ] Document backup/recovery procedures
- [ ] Document monitoring setup
- [ ] Document troubleshooting guide
- [ ] Document API endpoints and usage

### Operational Documentation
- [ ] Document deployment checklist (this file)
- [ ] Document incident response procedures
- [ ] Document on-call procedures
- [ ] Document escalation procedures
- [ ] Document rollback procedures
- [ ] Document known issues and workarounds

### Code Documentation
- [ ] Review code comments
- [ ] Verify docstrings on functions
- [ ] Document environment variables
- [ ] Document configuration options
- [ ] Generate API documentation

---

## 9. Pre-Deployment Review

### Code Review
- [ ] Security code review completed
- [ ] Performance code review completed
- [ ] Database query optimization reviewed
- [ ] Error handling reviewed
- [ ] Logging implementation reviewed
- [ ] No hardcoded secrets in code
- [ ] No debug print statements
- [ ] All dependencies updated and patched

### Configuration Review
- [ ] All environment variables documented
- [ ] No sensitive data in config files
- [ ] Database connection tested
- [ ] Email configuration tested
- [ ] File paths accessible and writable
- [ ] Permissions correctly set

### Compliance Review
- [ ] Privacy policy reviewed and available
- [ ] Terms of service reviewed and available
- [ ] GDPR compliance verified (if applicable)
- [ ] Data retention policy documented
- [ ] User data security verified
- [ ] Encryption in transit (HTTPS) verified
- [ ] Encryption at rest considered for sensitive data

---

## 10. Deployment Day

### Pre-Deployment
- [ ] All team members notified of deployment time
- [ ] Maintenance window scheduled
- [ ] Backups completed
- [ ] Database backup verified
- [ ] Staging environment matches production
- [ ] Rollback plan documented and ready
- [ ] On-call staff available

### Deployment
- [ ] Pull latest code
- [ ] Run `.env` validation: `./run_production.sh --validate`
- [ ] Build Docker images: `docker-compose build`
- [ ] Start services: `docker-compose up -d`
- [ ] Verify all services running: `docker-compose ps`
- [ ] Monitor logs for errors: `docker-compose logs -f`
- [ ] Test application health: `curl http://localhost:5000/api/meta`
- [ ] Verify database connectivity
- [ ] Test user login
- [ ] Run smoke tests

### Post-Deployment
- [ ] Monitor application for errors (30 minutes minimum)
- [ ] Check CPU/memory usage
- [ ] Verify backups are working
- [ ] Test all critical functions
- [ ] Confirm email notifications working
- [ ] Monitor error logs
- [ ] Document deployment time and any issues
- [ ] Update deployment log

### Rollback Procedure (if needed)
- [ ] Stop current services: `docker-compose down`
- [ ] Restore from backup
- [ ] Revert code changes
- [ ] Restart services
- [ ] Verify system operational
- [ ] Document what went wrong
- [ ] Plan fix for next attempt

---

## 11. Post-Deployment

### First Week
- [ ] Monitor application closely (24/7)
- [ ] Check logs multiple times daily
- [ ] Monitor performance metrics
- [ ] Respond to user feedback
- [ ] Document any issues
- [ ] Verify automated backups running

### First Month
- [ ] Review performance metrics
- [ ] Optimize slow queries if identified
- [ ] Tune Gunicorn worker count if needed
- [ ] Review and update monitoring alerts
- [ ] Plan for scaling if needed
- [ ] Conduct security audit

### Ongoing Maintenance
- [ ] Review logs daily
- [ ] Monitor performance weekly
- [ ] Update dependencies monthly
- [ ] Review backups monthly
- [ ] Test disaster recovery quarterly
- [ ] Update documentation as needed
- [ ] Plan regular security reviews

---

## Quick Reference Commands

```bash
# Start production environment
./run_production.sh --docker

# Validate configuration
./run_production.sh --validate

# View logs
docker-compose logs -f app

# Check service status
docker-compose ps

# SSH into container
docker-compose exec app bash

# Database backup
docker-compose exec db mysqldump -u root -p$MYSQL_ROOT_PASSWORD cms_db > backup.sql

# Database restore
docker-compose exec -T db mysql -u root -p$MYSQL_ROOT_PASSWORD cms_db < backup.sql

# Stop services
docker-compose down

# View resource usage
docker stats

# Test SSL certificate
openssl s_client -connect yourdomain.com:443
```

---

## Contacts & Resources

- **Lead Developer**: [Your Name]
- **DevOps Engineer**: [Name]
- **Database Administrator**: [Name]
- **Security Team**: [Contact]

### Resources
- [DEPLOYMENT.md](DEPLOYMENT.md) - Full deployment guide
- [API_DOCUMENTATION.md](flask-app/API_DOCUMENTATION.md) - API reference
- [README.md](README.md) - Project overview
- [nginx.conf.example](nginx.conf.example) - Nginx configuration

---

**Last Updated**: 2026-06-11
**Version**: 1.0
**Status**: Ready for production deployment ✓
