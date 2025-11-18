# AUPAT Production Deployment Guide

**Version:** 1.0.0
**Last Updated:** 2025-11-18
**For AUPAT Version:** 0.1.4+

This guide covers production deployment of AUPAT on Linux servers with security hardening, monitoring, and high availability considerations.

---

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Security Hardening](#security-hardening)
3. [Environment Configuration](#environment-configuration)
4. [Database Setup](#database-setup)
5. [Application Deployment](#application-deployment)
6. [Reverse Proxy (nginx)](#reverse-proxy-nginx)
7. [SSL/TLS Certificates](#ssltls-certificates)
8. [Systemd Services](#systemd-services)
9. [Firewall Configuration](#firewall-configuration)
10. [Backup Automation](#backup-automation)
11. [Log Management](#log-management)
12. [Monitoring & Alerts](#monitoring--alerts)
13. [Performance Tuning](#performance-tuning)
14. [Scaling Considerations](#scaling-considerations)
15. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### Minimum Requirements

- **OS:** Ubuntu 22.04 LTS / Debian 12 / RHEL 9 (or equivalent)
- **CPU:** 2 cores
- **RAM:** 4GB minimum, 8GB recommended
- **Disk:** 50GB minimum (SSD recommended)
- **Python:** 3.11+
- **Node.js:** 18+ (if running desktop app)

### Required Software

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y \
    python3.11 python3.11-venv python3-pip \
    nginx \
    certbot python3-certbot-nginx \
    exiftool \
    ffmpeg \
    git \
    logrotate \
    ufw \
    fail2ban

# RHEL/CentOS
sudo dnf install -y \
    python311 python311-pip \
    nginx \
    certbot python3-certbot-nginx \
    perl-Image-ExifTool \
    ffmpeg \
    git \
    logrotate \
    firewalld \
    fail2ban
```

---

## Security Hardening

### Security Checklist

- [ ] Create dedicated `aupat` user (no sudo access)
- [ ] Disable root SSH login
- [ ] Configure firewall (only ports 80, 443, 22 open)
- [ ] Set up fail2ban for brute force protection
- [ ] Enable SSL/TLS with Let's Encrypt
- [ ] Set secure file permissions (600 for secrets, 644 for code)
- [ ] Use environment variables for secrets (no hardcoded credentials)
- [ ] Enable Flask secret key rotation
- [ ] Configure CORS properly (restrict origins in production)
- [ ] Disable Flask debug mode
- [ ] Set up log monitoring for security events
- [ ] Regular security updates (unattended-upgrades)

### Create Dedicated User

```bash
# Create aupat user
sudo useradd -m -s /bin/bash aupat

# Add to necessary groups
sudo usermod -aG www-data aupat

# Switch to aupat user for deployment
sudo -u aupat -i
```

### Disable Root SSH

```bash
# Edit SSH config
sudo nano /etc/ssh/sshd_config

# Set these values:
PermitRootLogin no
PasswordAuthentication no
PubkeyAuthentication yes

# Restart SSH
sudo systemctl restart sshd
```

### Configure fail2ban

```bash
# Create jail for nginx
sudo nano /etc/fail2ban/jail.d/aupat.conf
```

```ini
[aupat-nginx]
enabled = true
port = http,https
filter = nginx-http-auth
logpath = /var/log/nginx/aupat-error.log
maxretry = 5
bantime = 3600
findtime = 600
```

```bash
sudo systemctl restart fail2ban
sudo fail2ban-client status
```

---

## Environment Configuration

### Directory Structure

```bash
/opt/aupat/                  # Application root
├── app.py
├── scripts/
├── venv/                    # Python virtual environment
├── data/                    # Database and user data
│   ├── aupat.db
│   └── archive/             # Media archive
├── logs/                    # Application logs
├── backups/                 # Database backups
└── user/
    └── user.json            # User configuration
```

### Create Directory Structure

```bash
sudo mkdir -p /opt/aupat/{data,logs,backups,user}
sudo chown -R aupat:aupat /opt/aupat
sudo chmod 755 /opt/aupat
sudo chmod 700 /opt/aupat/user
```

### Environment Variables

Create `/opt/aupat/.env`:

```bash
# Flask Configuration
FLASK_ENV=production
FLASK_DEBUG=0
FLASK_SECRET_KEY=<generate-with-openssl-rand-hex-32>

# Database
DB_PATH=/opt/aupat/data/aupat.db

# Logging
LOG_LEVEL=INFO
LOG_FORMAT=json

# External Services (optional)
IMMICH_URL=https://immich.example.com
IMMICH_API_KEY=<your-immich-api-key>
ARCHIVEBOX_URL=http://localhost:8001

# Security
ALLOWED_ORIGINS=https://aupat.example.com

# Performance
WORKERS=4
TIMEOUT=60
```

Generate secret key:
```bash
openssl rand -hex 32
```

### Set Permissions

```bash
sudo chmod 600 /opt/aupat/.env
sudo chown aupat:aupat /opt/aupat/.env
```

---

## Database Setup

### Initialize Database

```bash
cd /opt/aupat
source venv/bin/activate

# Run migrations
python scripts/migrate.py --status
python scripts/migrate.py --upgrade

# Verify
sqlite3 data/aupat.db "SELECT * FROM versions;"
```

### Database Permissions

```bash
sudo chmod 644 /opt/aupat/data/aupat.db
sudo chown aupat:aupat /opt/aupat/data/aupat.db
```

### WAL Mode for Performance

```bash
sqlite3 /opt/aupat/data/aupat.db "PRAGMA journal_mode=WAL;"
```

---

## Application Deployment

### Clone and Install

```bash
# As aupat user
cd /opt/aupat
git clone https://github.com/bizzlechizzle/aupat.git .

# Create virtual environment
python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install --upgrade pip
pip install -r requirements.txt

# Verify installation
python scripts/migrate.py --list
```

### Production Configuration

Create `/opt/aupat/user/user.json`:

```json
{
  "db_name": "aupat",
  "db_loc": "/opt/aupat/data/aupat.db",
  "db_backup": "/opt/aupat/backups",
  "archive_path": "/opt/aupat/data/archive",
  "staging_path": "/opt/aupat/data/staging",
  "import_author": "admin"
}
```

Set permissions:
```bash
sudo chmod 600 /opt/aupat/user/user.json
sudo chown aupat:aupat /opt/aupat/user/user.json
```

---

## Reverse Proxy (nginx)

### nginx Configuration

Create `/etc/nginx/sites-available/aupat`:

```nginx
# Rate limiting
limit_req_zone $binary_remote_addr zone=aupat_api:10m rate=10r/s;
limit_conn_zone $binary_remote_addr zone=aupat_conn:10m;

# Upstream Flask application
upstream aupat_backend {
    server 127.0.0.1:5002 fail_timeout=0;
}

server {
    listen 80;
    listen [::]:80;
    server_name aupat.example.com;

    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    listen [::]:443 ssl http2;
    server_name aupat.example.com;

    # SSL certificates (Let's Encrypt)
    ssl_certificate /etc/letsencrypt/live/aupat.example.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/aupat.example.com/privkey.pem;
    ssl_trusted_certificate /etc/letsencrypt/live/aupat.example.com/chain.pem;

    # SSL configuration (Mozilla Intermediate)
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-ECDSA-AES128-GCM-SHA256:ECDHE-RSA-AES128-GCM-SHA256:ECDHE-ECDSA-AES256-GCM-SHA384:ECDHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 1d;
    ssl_stapling on;
    ssl_stapling_verify on;

    # Security headers
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload" always;
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/aupat-access.log;
    error_log /var/log/nginx/aupat-error.log warn;

    # Max upload size for media files
    client_max_body_size 100M;
    client_body_timeout 300s;

    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/x-javascript application/xml+rss application/json;

    # API rate limiting
    location /api/ {
        limit_req zone=aupat_api burst=20 nodelay;
        limit_conn aupat_conn 10;

        proxy_pass http://aupat_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Timeouts for long-running operations
        proxy_connect_timeout 60s;
        proxy_send_timeout 300s;
        proxy_read_timeout 300s;

        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

    # Health check endpoint (no rate limit)
    location /api/health {
        proxy_pass http://aupat_backend;
        proxy_set_header Host $host;
        access_log off;
    }

    # Static files (if serving directly)
    location /static/ {
        alias /opt/aupat/static/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Deny access to sensitive files
    location ~ /\. {
        deny all;
        access_log off;
        log_not_found off;
    }

    location ~ /(user\.json|\.env|\.git) {
        deny all;
        access_log off;
        log_not_found off;
    }
}
```

### Enable Site

```bash
sudo ln -s /etc/nginx/sites-available/aupat /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

---

## SSL/TLS Certificates

### Let's Encrypt with Certbot

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Generate certificate
sudo certbot --nginx -d aupat.example.com

# Verify auto-renewal
sudo certbot renew --dry-run

# Auto-renewal is handled by systemd timer
sudo systemctl status certbot.timer
```

### Manual Certificate Renewal

```bash
sudo certbot renew
sudo systemctl reload nginx
```

---

## Systemd Services

### AUPAT API Service

Create `/etc/systemd/system/aupat-api.service`:

```ini
[Unit]
Description=AUPAT API Server
After=network.target

[Service]
Type=simple
User=aupat
Group=aupat
WorkingDirectory=/opt/aupat
Environment="PATH=/opt/aupat/venv/bin"
EnvironmentFile=/opt/aupat/.env

# Use gunicorn for production
ExecStart=/opt/aupat/venv/bin/gunicorn \
    --bind 127.0.0.1:5002 \
    --workers 4 \
    --timeout 60 \
    --access-logfile /opt/aupat/logs/access.log \
    --error-logfile /opt/aupat/logs/error.log \
    --log-level info \
    app:app

# Restart policy
Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ProtectHome=true
ReadWritePaths=/opt/aupat/data /opt/aupat/logs /opt/aupat/backups

[Install]
WantedBy=multi-user.target
```

### Archive Worker Service

Create `/etc/systemd/system/aupat-worker.service`:

```ini
[Unit]
Description=AUPAT Archive Worker
After=network.target aupat-api.service

[Service]
Type=simple
User=aupat
Group=aupat
WorkingDirectory=/opt/aupat
Environment="PATH=/opt/aupat/venv/bin"
EnvironmentFile=/opt/aupat/.env

ExecStart=/opt/aupat/venv/bin/python scripts/archive_worker.py

Restart=always
RestartSec=10

# Security hardening
NoNewPrivileges=true
PrivateTmp=true
ProtectSystem=strict
ReadWritePaths=/opt/aupat/data /opt/aupat/logs

[Install]
WantedBy=multi-user.target
```

### Enable and Start Services

```bash
# Install gunicorn
/opt/aupat/venv/bin/pip install gunicorn

# Reload systemd
sudo systemctl daemon-reload

# Enable services
sudo systemctl enable aupat-api
sudo systemctl enable aupat-worker

# Start services
sudo systemctl start aupat-api
sudo systemctl start aupat-worker

# Check status
sudo systemctl status aupat-api
sudo systemctl status aupat-worker

# View logs
sudo journalctl -u aupat-api -f
sudo journalctl -u aupat-worker -f
```

---

## Firewall Configuration

### UFW (Ubuntu/Debian)

```bash
# Reset firewall
sudo ufw --force reset

# Default policies
sudo ufw default deny incoming
sudo ufw default allow outgoing

# Allow SSH (change port if using non-standard)
sudo ufw allow 22/tcp

# Allow HTTP/HTTPS
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp

# Enable firewall
sudo ufw enable

# Verify
sudo ufw status verbose
```

### firewalld (RHEL/CentOS)

```bash
# Enable firewall
sudo systemctl enable firewalld
sudo systemctl start firewalld

# Allow services
sudo firewall-cmd --permanent --add-service=ssh
sudo firewall-cmd --permanent --add-service=http
sudo firewall-cmd --permanent --add-service=https

# Reload
sudo firewall-cmd --reload

# Verify
sudo firewall-cmd --list-all
```

---

## Backup Automation

### Database Backup Script

Create `/opt/aupat/scripts/production_backup.sh`:

```bash
#!/bin/bash
set -e

# Configuration
BACKUP_DIR="/opt/aupat/backups"
DB_PATH="/opt/aupat/data/aupat.db"
RETENTION_DAYS=30
LOG_FILE="/opt/aupat/logs/backup.log"

# Create backup with timestamp
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="$BACKUP_DIR/aupat_backup_$TIMESTAMP.db"

echo "[$(date)] Starting backup..." >> "$LOG_FILE"

# SQLite backup (online backup)
sqlite3 "$DB_PATH" ".backup '$BACKUP_FILE'"

# Compress backup
gzip "$BACKUP_FILE"
BACKUP_FILE="$BACKUP_FILE.gz"

echo "[$(date)] Backup created: $BACKUP_FILE" >> "$LOG_FILE"

# Calculate size
SIZE=$(du -h "$BACKUP_FILE" | cut -f1)
echo "[$(date)] Backup size: $SIZE" >> "$LOG_FILE"

# Delete old backups
find "$BACKUP_DIR" -name "aupat_backup_*.db.gz" -mtime +$RETENTION_DAYS -delete
echo "[$(date)] Cleaned up backups older than $RETENTION_DAYS days" >> "$LOG_FILE"

# Verify backup
if [ -f "$BACKUP_FILE" ]; then
    echo "[$(date)] Backup successful" >> "$LOG_FILE"
    exit 0
else
    echo "[$(date)] Backup failed!" >> "$LOG_FILE"
    exit 1
fi
```

Make executable:
```bash
sudo chmod +x /opt/aupat/scripts/production_backup.sh
sudo chown aupat:aupat /opt/aupat/scripts/production_backup.sh
```

### Cron Job for Automated Backups

```bash
# Edit aupat user's crontab
sudo -u aupat crontab -e

# Add daily backup at 2 AM
0 2 * * * /opt/aupat/scripts/production_backup.sh

# Verify cron job
sudo -u aupat crontab -l
```

### Offsite Backup (rsync to remote server)

```bash
# Add to backup script or separate cron job
rsync -avz --delete \
    /opt/aupat/backups/ \
    backup-user@backup-server:/backups/aupat/
```

---

## Log Management

### Log Rotation

Create `/etc/logrotate.d/aupat`:

```
/opt/aupat/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 aupat aupat
    sharedscripts
    postrotate
        systemctl reload aupat-api > /dev/null 2>&1 || true
    endscript
}

/var/log/nginx/aupat-*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 www-data adm
    sharedscripts
    postrotate
        nginx -s reload > /dev/null 2>&1 || true
    endscript
}
```

Test log rotation:
```bash
sudo logrotate -d /etc/logrotate.d/aupat
sudo logrotate -f /etc/logrotate.d/aupat
```

### Structured Logging

Enable JSON logging for easier parsing:

```bash
# In /opt/aupat/.env
LOG_FORMAT=json
LOG_LEVEL=INFO
```

### Centralized Logging (Optional)

For production environments, consider:
- **ELK Stack** (Elasticsearch, Logstash, Kibana)
- **Loki + Grafana**
- **Datadog**
- **CloudWatch Logs** (AWS)

Example filebeat configuration for ELK:

```yaml
filebeat.inputs:
- type: log
  enabled: true
  paths:
    - /opt/aupat/logs/*.log
  json.keys_under_root: true
  json.add_error_key: true

output.elasticsearch:
  hosts: ["localhost:9200"]
  index: "aupat-%{+yyyy.MM.dd}"
```

---

## Monitoring & Alerts

### Health Check Monitoring

Use external monitoring service to ping `/api/health`:

```bash
# Example with curl (for cron-based monitoring)
*/5 * * * * curl -f http://localhost:5002/api/health || echo "AUPAT API is down!" | mail -s "AUPAT Alert" admin@example.com
```

### System Monitoring

Install monitoring tools:

```bash
# Install Netdata (real-time monitoring)
bash <(curl -Ss https://my-netdata.io/kickstart.sh)

# Or Prometheus + Node Exporter
sudo apt-get install prometheus prometheus-node-exporter

# Or use cloud-based: Datadog, New Relic, etc.
```

### Application Metrics

Add Prometheus metrics to Flask app:

```bash
# Install prometheus-flask-exporter
/opt/aupat/venv/bin/pip install prometheus-flask-exporter
```

Add to `app.py`:
```python
from prometheus_flask_exporter import PrometheusMetrics

metrics = PrometheusMetrics(app)
```

Metrics available at `/metrics` endpoint.

### Alert Rules

Example Prometheus alert rules:

```yaml
groups:
  - name: aupat
    rules:
      - alert: AupatAPIDown
        expr: up{job="aupat-api"} == 0
        for: 5m
        annotations:
          summary: "AUPAT API is down"

      - alert: HighErrorRate
        expr: rate(flask_http_request_total{status=~"5.."}[5m]) > 0.1
        annotations:
          summary: "High error rate detected"
```

---

## Performance Tuning

### Gunicorn Workers

Calculate optimal workers:
```
workers = (2 * CPU_cores) + 1
```

For 4-core server:
```
--workers 9
```

### Database Optimization

```sql
-- Enable WAL mode
PRAGMA journal_mode=WAL;

-- Increase cache size (64MB)
PRAGMA cache_size=-64000;

-- Analyze query plans
ANALYZE;

-- Vacuum database periodically
VACUUM;
```

Add to cron:
```bash
# Monthly vacuum
0 3 1 * * sqlite3 /opt/aupat/data/aupat.db "VACUUM; ANALYZE;"
```

### nginx Optimization

```nginx
# In nginx.conf
worker_processes auto;
worker_rlimit_nofile 100000;

events {
    worker_connections 4000;
    use epoll;
    multi_accept on;
}

http {
    # Enable sendfile
    sendfile on;
    tcp_nopush on;
    tcp_nodelay on;

    # Keepalive
    keepalive_timeout 65;
    keepalive_requests 100;

    # Buffer sizes
    client_body_buffer_size 128k;
    client_max_body_size 100m;
    client_header_buffer_size 1k;
    large_client_header_buffers 4 16k;
}
```

### System Limits

```bash
# Edit /etc/security/limits.conf
aupat soft nofile 65536
aupat hard nofile 65536

# Edit /etc/sysctl.conf
net.core.somaxconn = 1024
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.ip_local_port_range = 10000 65000
```

---

## Scaling Considerations

### Horizontal Scaling

For high traffic:

1. **Multiple API servers** behind load balancer
2. **Shared database** (SQLite not ideal - migrate to PostgreSQL)
3. **Shared file storage** (NFS or S3 for media files)
4. **Redis** for session management
5. **Message queue** (RabbitMQ) for worker tasks

### Database Migration (SQLite → PostgreSQL)

When scaling beyond single server:

```bash
# Export SQLite data
sqlite3 aupat.db .dump > aupat_dump.sql

# Import to PostgreSQL
psql -U aupat -d aupat_production -f aupat_dump.sql
```

Update connection strings in code.

### CDN for Static Assets

Use CloudFlare or AWS CloudFront for media delivery:

```nginx
location /media/ {
    # Redirect to CDN
    return 302 https://cdn.example.com$request_uri;
}
```

---

## Troubleshooting

### Common Issues

**Issue:** API returns 502 Bad Gateway

```bash
# Check if service is running
sudo systemctl status aupat-api

# Check logs
sudo journalctl -u aupat-api -n 100

# Check if port is listening
sudo netstat -tulpn | grep 5002

# Restart service
sudo systemctl restart aupat-api
```

**Issue:** Database locked errors

```bash
# Check if WAL mode is enabled
sqlite3 /opt/aupat/data/aupat.db "PRAGMA journal_mode;"

# Should return "wal", if not:
sqlite3 /opt/aupat/data/aupat.db "PRAGMA journal_mode=WAL;"
```

**Issue:** High CPU usage

```bash
# Check running processes
top -u aupat

# Check worker count
ps aux | grep gunicorn | wc -l

# Reduce workers if needed
sudo nano /etc/systemd/system/aupat-api.service
sudo systemctl daemon-reload
sudo systemctl restart aupat-api
```

**Issue:** Disk space full

```bash
# Check disk usage
df -h

# Find large files
sudo du -sh /opt/aupat/* | sort -h

# Clean up old logs
find /opt/aupat/logs -name "*.log" -mtime +30 -delete

# Clean up old backups
find /opt/aupat/backups -name "*.gz" -mtime +30 -delete
```

### Debug Mode (Temporary)

**NEVER enable in production permanently!**

```bash
# Temporary debug mode
sudo nano /opt/aupat/.env
# Set: FLASK_DEBUG=1, LOG_LEVEL=DEBUG

sudo systemctl restart aupat-api

# Check logs
sudo journalctl -u aupat-api -f

# IMPORTANT: Disable debug mode after troubleshooting!
# Set: FLASK_DEBUG=0, LOG_LEVEL=INFO
```

---

## Post-Deployment Checklist

After deployment, verify:

- [ ] All services running: `sudo systemctl status aupat-*`
- [ ] API accessible: `curl https://aupat.example.com/api/health`
- [ ] SSL certificate valid: `curl -I https://aupat.example.com`
- [ ] Firewall configured: `sudo ufw status`
- [ ] Logs rotating: Check `/var/log/logrotate.log`
- [ ] Backups working: Check `/opt/aupat/backups/`
- [ ] Database migrations applied: `python scripts/migrate.py --status`
- [ ] External tools available: `exiftool -ver && ffmpeg -version`
- [ ] Monitoring active: Check monitoring dashboard
- [ ] Security headers present: `curl -I https://aupat.example.com | grep -i "x-"`
- [ ] Rate limiting working: Test with rapid requests
- [ ] Health checks passing: Monitor endpoint
- [ ] Environment variables set: `cat /opt/aupat/.env` (verify no secrets exposed)

---

## Maintenance Schedule

**Daily:**
- Monitor logs for errors
- Check disk space
- Verify backup success

**Weekly:**
- Review security logs
- Check for application updates
- Test restore procedure

**Monthly:**
- Security updates: `sudo apt-get update && sudo apt-get upgrade`
- Database vacuum: `sqlite3 aupat.db "VACUUM; ANALYZE;"`
- Review and rotate SSL certificates
- Performance review

**Quarterly:**
- Full disaster recovery test
- Security audit
- Dependency updates: `pip list --outdated`

---

## Support & Resources

- **Documentation:** https://github.com/bizzlechizzle/aupat
- **Issues:** https://github.com/bizzlechizzle/aupat/issues
- **Security:** Report to security@example.com
- **Migration Guide:** docs/MIGRATION_GUIDE.md
- **API Documentation:** docs/techguide.md

---

**Last Updated:** 2025-11-18
**Maintained By:** AUPAT Project Team
