#!/bin/bash
#
# Production Deployment Script
# Deploys Snort3-AI-Ops to production environment
#
# Usage: sudo ./scripts/deploy_production.sh
#

set -e

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

# Configuration
DEPLOY_DIR="/opt/snort3-ai-ops"
SERVICE_USER="aiops"
SERVICE_GROUP="aiops"

echo -e "${BLUE}╔═══════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║     Snort3-AI-Ops Production Deployment                  ║${NC}"
echo -e "${BLUE}╚═══════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo -e "${RED}Error: Please run as root (use sudo)${NC}"
    exit 1
fi

# Step 1: Create service user
echo -e "${GREEN}[1/10]${NC} Creating service user..."
if ! id -u $SERVICE_USER >/dev/null 2>&1; then
    useradd -r -s /bin/bash -d $DEPLOY_DIR -m -c "Snort3-AI-Ops Service" $SERVICE_USER
    echo -e "${GREEN}✓${NC} User created: $SERVICE_USER"
else
    echo -e "${YELLOW}→${NC} User already exists: $SERVICE_USER"
fi

# Step 2: Create deployment directory
echo -e "${GREEN}[2/10]${NC} Setting up deployment directory..."
mkdir -p $DEPLOY_DIR
cp -r . $DEPLOY_DIR/
echo -e "${GREEN}✓${NC} Files copied to $DEPLOY_DIR"

# Step 3: Create necessary directories
echo -e "${GREEN}[3/10]${NC} Creating application directories..."
mkdir -p $DEPLOY_DIR/{data,logs,reports,models,backups}
chmod 755 $DEPLOY_DIR/{data,logs,reports,models,backups}
echo -e "${GREEN}✓${NC} Directories created"

# Step 4: Setup Python virtual environment
echo -e "${GREEN}[4/10]${NC} Setting up Python virtual environment..."
cd $DEPLOY_DIR
python3 -m venv venv
chown -R $SERVICE_USER:$SERVICE_GROUP $DEPLOY_DIR
$DEPLOY_DIR/venv/bin/pip install --upgrade pip
$DEPLOY_DIR/venv/bin/pip install -r requirements.txt
echo -e "${GREEN}✓${NC} Virtual environment configured"

# Step 5: Configure environment
echo -e "${GREEN}[5/10]${NC} Configuring environment..."
if [ ! -f "$DEPLOY_DIR/.env" ]; then
    cp $DEPLOY_DIR/.env.example $DEPLOY_DIR/.env
    echo -e "${YELLOW}→${NC} Created .env file - PLEASE CONFIGURE API KEYS!"
    echo -e "${YELLOW}→${NC} Edit: $DEPLOY_DIR/.env"
else
    echo -e "${GREEN}✓${NC} .env file already exists"
fi

chown $SERVICE_USER:$SERVICE_GROUP $DEPLOY_DIR/.env
chmod 600 $DEPLOY_DIR/.env

# Step 6: Install systemd services
echo -e "${GREEN}[6/10]${NC} Installing systemd services..."
cp scripts/systemd/snort3-ai-ops.service /etc/systemd/system/
cp scripts/systemd/snort3.service /etc/systemd/system/
systemctl daemon-reload
echo -e "${GREEN}✓${NC} Systemd services installed"

# Step 7: Setup log rotation
echo -e "${GREEN}[7/10]${NC} Configuring log rotation..."
cat > /etc/logrotate.d/snort3-ai-ops << 'EOF'
/opt/snort3-ai-ops/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    notifempty
    create 0640 aiops aiops
    sharedscripts
    postrotate
        systemctl reload snort3-ai-ops >/dev/null 2>&1 || true
    endscript
}
EOF
echo -e "${GREEN}✓${NC} Log rotation configured"

# Step 8: Setup firewall rules
echo -e "${GREEN}[8/10]${NC} Configuring firewall..."
if command -v ufw >/dev/null 2>&1; then
    ufw allow 8000/tcp comment "Snort3-AI-Ops API"
    ufw allow 8080/tcp comment "Snort3-AI-Ops Dashboard"
    ufw allow 9090/tcp comment "Prometheus Metrics"
    echo -e "${GREEN}✓${NC} UFW rules added"
elif command -v firewall-cmd >/dev/null 2>&1; then
    firewall-cmd --permanent --add-port=8000/tcp
    firewall-cmd --permanent --add-port=8080/tcp
    firewall-cmd --permanent --add-port=9090/tcp
    firewall-cmd --reload
    echo -e "${GREEN}✓${NC} firewalld rules added"
else
    echo -e "${YELLOW}→${NC} No firewall detected - please configure manually"
fi

# Step 9: Create backup script
echo -e "${GREEN}[9/10]${NC} Setting up backup script..."
cat > /usr/local/bin/backup-snort3-ai-ops << 'EOF'
#!/bin/bash
BACKUP_DIR="/opt/snort3-ai-ops/backups"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
tar -czf $BACKUP_DIR/backup_$TIMESTAMP.tar.gz \
    /opt/snort3-ai-ops/config \
    /opt/snort3-ai-ops/data \
    /opt/snort3-ai-ops/.env
find $BACKUP_DIR -name "backup_*.tar.gz" -mtime +30 -delete
EOF
chmod +x /usr/local/bin/backup-snort3-ai-ops

# Add to crontab
(crontab -u $SERVICE_USER -l 2>/dev/null; echo "0 2 * * * /usr/local/bin/backup-snort3-ai-ops") | crontab -u $SERVICE_USER -
echo -e "${GREEN}✓${NC} Backup script configured (runs daily at 2 AM)"

# Step 10: Final setup
echo -e "${GREEN}[10/10]${NC} Final configuration..."

# Enable services (but don't start yet)
systemctl enable snort3-ai-ops.service
systemctl enable snort3.service

echo -e "${GREEN}✓${NC} Services enabled"

echo ""
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}✓ Production Deployment Complete!${NC}"
echo -e "${GREEN}═══════════════════════════════════════════════════════════${NC}"
echo ""
echo "Deployment Location: $DEPLOY_DIR"
echo "Service User: $SERVICE_USER"
echo ""
echo -e "${YELLOW}IMPORTANT - Next Steps:${NC}"
echo ""
echo "1. Configure API Keys:"
echo "   sudo nano $DEPLOY_DIR/.env"
echo ""
echo "2. Verify Snort3 configuration:"
echo "   sudo snort -c /etc/snort/snort.lua -T"
echo ""
echo "3. Start Snort3:"
echo "   sudo systemctl start snort3"
echo ""
echo "4. Start AI-Ops Engine:"
echo "   sudo systemctl start snort3-ai-ops"
echo ""
echo "5. Check service status:"
echo "   sudo systemctl status snort3-ai-ops"
echo "   sudo journalctl -u snort3-ai-ops -f"
echo ""
echo "6. Access the API:"
echo "   http://localhost:8000"
echo ""
echo "7. View dashboards:"
echo "   http://localhost:8080  (Web UI)"
echo "   http://localhost:9090  (Prometheus)"
echo ""
echo -e "${RED}WARNING:${NC} Make sure to:"
echo "  - Configure SSL/TLS certificates for production"
echo "  - Set strong passwords in .env file"
echo "  - Review firewall rules"
echo "  - Configure monitoring and alerting"
echo "  - Set up regular backups"
echo ""
