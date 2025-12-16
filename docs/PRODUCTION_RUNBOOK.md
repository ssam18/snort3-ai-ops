# Production Runbook - Snort3-AI-Ops

## 📖 Table of Contents
1. [System Overview](#system-overview)
2. [Deployment](#deployment)
3. [Operations](#operations)
4. [Monitoring](#monitoring)
5. [Troubleshooting](#troubleshooting)
6. [Incident Response](#incident-response)
7. [Maintenance](#maintenance)
8. [Disaster Recovery](#disaster-recovery)

---

## System Overview

### Architecture Components
- **Snort3 IPS**: Network traffic analysis and alert generation
- **AI-Ops Engine**: Multi-agent AI processing pipeline
- **ZeroMQ**: Event streaming between Snort3 and AI-Ops
- **Database**: SQLite (dev) or PostgreSQL (prod)
- **SIEM**: Splunk/ELK integration
- **Firewall**: Palo Alto/FortiGate integration

### Service Dependencies
```
Snort3 → ZeroMQ → AI-Ops Engine → {SIEM, Firewall, Database}
```

---

## Deployment

### Initial Deployment

#### 1. Install Snort3
```bash
sudo ./scripts/install_snort3.sh
```

Verify:
```bash
snort --version
snort -c /etc/snort/snort.lua -T
```

#### 2. Build AI Event Exporter Plugin
```bash
cd snort3-plugins/event_exporter
make
sudo make install
```

Verify:
```bash
snort --plugin-path /usr/local/lib/snort/plugins --list-plugins | grep ai_event
```

#### 3. Deploy AI-Ops Engine
```bash
sudo ./scripts/deploy_production.sh
```

#### 4. Configure API Keys
```bash
sudo nano /opt/snort3-ai-ops/.env
```

Required keys:
- VIRUSTOTAL_API_KEY
- ABUSEIPDB_API_KEY
- SIEM credentials
- Firewall API keys

#### 5. Start Services
```bash
sudo systemctl start snort3
sudo systemctl start snort3-ai-ops
```

### Deployment Verification Checklist

- [ ] Snort3 is running: `systemctl status snort3`
- [ ] AI-Ops engine is running: `systemctl status snort3-ai-ops`
- [ ] Events are flowing: `journalctl -u snort3-ai-ops -f`
- [ ] API is accessible: `curl http://localhost:8000/health`
- [ ] Metrics are available: `curl http://localhost:9090/metrics`
- [ ] SIEM integration working: Check SIEM for new events
- [ ] Firewall integration working: Test with `python main.py test-agent -a response`

---

## Operations

### Starting the System

```bash
# Start in order
sudo systemctl start snort3
sudo systemctl start snort3-ai-ops

# Verify
sudo systemctl status snort3
sudo systemctl status snort3-ai-ops
```

### Stopping the System

```bash
# Stop in reverse order
sudo systemctl stop snort3-ai-ops
sudo systemctl stop snort3
```

### Restarting Services

```bash
# Restart AI-Ops (preserves Snort3)
sudo systemctl restart snort3-ai-ops

# Restart both
sudo systemctl restart snort3
sudo systemctl restart snort3-ai-ops
```

### Checking Logs

```bash
# Real-time logs
journalctl -u snort3-ai-ops -f

# Recent logs
journalctl -u snort3-ai-ops --since "1 hour ago"

# Snort3 logs
journalctl -u snort3 -f

# Application logs
tail -f /opt/snort3-ai-ops/logs/aiops.log
```

### Configuration Changes

1. Edit configuration:
   ```bash
   sudo nano /opt/snort3-ai-ops/config/config.yaml
   ```

2. Validate:
   ```bash
   cd /opt/snort3-ai-ops
   source venv/bin/activate
   python main.py validate
   ```

3. Reload:
   ```bash
   sudo systemctl reload snort3-ai-ops
   ```

---

## Monitoring

### Health Checks

#### System Health
```bash
# API health endpoint
curl http://localhost:8000/health

# Metrics endpoint
curl http://localhost:9090/metrics
```

#### Service Status
```bash
systemctl status snort3
systemctl status snort3-ai-ops
```

### Key Metrics to Monitor

#### Prometheus Queries

**Event Processing Rate**:
```promql
rate(snort3_ai_ops_events_processed_total[5m])
```

**Agent Task Success Rate**:
```promql
rate(snort3_ai_ops_agent_tasks_total{status="success"}[5m]) /
rate(snort3_ai_ops_agent_tasks_total[5m])
```

**Threat Detection Rate**:
```promql
rate(snort3_ai_ops_threats_detected_total[5m])
```

**Error Rate**:
```promql
rate(snort3_ai_ops_errors_total[5m])
```

**Response Time (p95)**:
```promql
histogram_quantile(0.95, rate(snort3_ai_ops_event_processing_duration_seconds_bucket[5m]))
```

### Alerting Rules

Create alerts for:
- Event processing rate drops below threshold
- Error rate exceeds threshold
- High p95 latency
- System resource exhaustion
- Service unavailability

### Dashboards

Access Grafana dashboards:
- System Overview: http://localhost:3000/d/snort3-overview
- Agent Performance: http://localhost:3000/d/agent-performance
- Threat Detection: http://localhost:3000/d/threat-detection

---

## Troubleshooting

### Common Issues

#### 1. AI-Ops Engine Not Starting

**Symptoms**: Service fails to start

**Diagnosis**:
```bash
journalctl -u snort3-ai-ops -n 100 --no-pager
```

**Common Causes**:
- Missing API keys in .env
- Configuration errors
- Python dependencies not installed
- Port already in use

**Resolution**:
```bash
# Check configuration
cd /opt/snort3-ai-ops
source venv/bin/activate
python main.py validate

# Check .env file
sudo nano /opt/snort3-ai-ops/.env

# Reinstall dependencies
sudo -u aiops /opt/snort3-ai-ops/venv/bin/pip install -r requirements.txt

# Check ports
sudo netstat -tlnp | grep -E '8000|8080|9090'
```

#### 2. No Events Being Processed

**Symptoms**: Event queue empty, no metrics

**Diagnosis**:
```bash
# Check Snort3 is running
systemctl status snort3

# Check ZeroMQ connection
sudo netstat -an | grep 5555

# Check Snort3 logs
journalctl -u snort3 -n 100
```

**Resolution**:
```bash
# Verify Snort3 plugin loaded
snort --plugin-path /usr/local/lib/snort/plugins --list-plugins | grep ai_event

# Restart Snort3
sudo systemctl restart snort3

# Test with simulator
cd /opt/snort3-ai-ops
source venv/bin/activate
python tests/snort3_simulator.py --duration 30 --rate 5.0
```

#### 3. High Memory Usage

**Symptoms**: System running out of memory

**Diagnosis**:
```bash
# Check memory usage
free -h
ps aux --sort=-%mem | head -20

# Check AI-Ops memory
systemctl status snort3-ai-ops
```

**Resolution**:
```bash
# Adjust buffer sizes in config
sudo nano /opt/snort3-ai-ops/config/config.yaml

# Restart service
sudo systemctl restart snort3-ai-ops

# Add memory limits to systemd
sudo systemctl edit snort3-ai-ops
# Add: MemoryLimit=2G
sudo systemctl daemon-reload
sudo systemctl restart snort3-ai-ops
```

#### 4. SIEM Integration Failing

**Symptoms**: Events not appearing in SIEM

**Diagnosis**:
```bash
# Check logs for SIEM errors
journalctl -u snort3-ai-ops | grep -i siem

# Test SIEM connectivity
curl -k https://splunk.example.com:8088/services/collector/health
```

**Resolution**:
```bash
# Verify SIEM credentials
sudo nano /opt/snort3-ai-ops/.env

# Test SIEM integration
cd /opt/snort3-ai-ops
source venv/bin/activate
python -c "
from integrations.siem_connectors import create_siem_connector
config = {'host': 'https://splunk:8088', 'token': 'YOUR_TOKEN', 'index': 'security'}
siem = create_siem_connector('splunk', config)
import asyncio
asyncio.run(siem.send_event({'test': 'event'}))
"
```

#### 5. Agent Tasks Timing Out

**Symptoms**: Slow processing, timeout errors

**Diagnosis**:
```bash
# Check agent metrics
curl http://localhost:9090/metrics | grep agent_task_duration

# Check for blocked tasks
journalctl -u snort3-ai-ops | grep -i timeout
```

**Resolution**:
```bash
# Increase timeouts in config
sudo nano /opt/snort3-ai-ops/config/config.yaml

# Reduce concurrent tasks
# In config.yaml, set: max_concurrent_tasks: 5

# Restart service
sudo systemctl restart snort3-ai-ops
```

---

## Incident Response

### Security Incident Detected

#### Immediate Actions
1. Verify the alert is legitimate
2. Check threat score and confidence
3. Review automated responses taken
4. Escalate if necessary

#### Investigation Steps
```bash
# Get incident details
curl http://localhost:8000/api/v1/incidents/<incident_id>

# Investigate IP
cd /opt/snort3-ai-ops
source venv/bin/activate
python main.py investigate --ip <IP_ADDRESS>

# Check SIEM for correlated events
# (Use your SIEM interface)

# Review Snort3 PCAP if available
sudo tcpdump -r /var/log/snort/pcap/<file> | less
```

### System Compromise

If the AI-Ops system itself is compromised:

1. **Isolate**: Disconnect from network
2. **Preserve**: Take memory dump, disk snapshot
3. **Investigate**: Review logs, check for unauthorized access
4. **Remediate**: Rebuild from known-good backup
5. **Harden**: Review and strengthen security posture

---

## Maintenance

### Daily Tasks
- [ ] Review dashboards for anomalies
- [ ] Check error logs
- [ ] Verify SIEM integration
- [ ] Monitor disk space

### Weekly Tasks
- [ ] Review threat detection accuracy
- [ ] Update threat intelligence feeds
- [ ] Check for software updates
- [ ] Review blocked IP list
- [ ] Test backup restoration

### Monthly Tasks
- [ ] Analyze false positive rate
- [ ] Review and tune rules
- [ ] Update documentation
- [ ] Security audit
- [ ] Performance optimization review

### Updating the System

```bash
# Backup first
sudo /usr/local/bin/backup-snort3-ai-ops

# Pull updates
cd /opt/snort3-ai-ops
sudo git pull

# Update dependencies
sudo -u aiops /opt/snort3-ai-ops/venv/bin/pip install -r requirements.txt --upgrade

# Run tests
sudo -u aiops /opt/snort3-ai-ops/venv/bin/pytest tests/

# Restart service
sudo systemctl restart snort3-ai-ops
```

---

## Disaster Recovery

### Backup Procedures

#### Automated Backups
Backups run daily at 2 AM via cron:
```bash
/usr/local/bin/backup-snort3-ai-ops
```

Backup location: `/opt/snort3-ai-ops/backups/`

#### Manual Backup
```bash
sudo /usr/local/bin/backup-snort3-ai-ops
```

#### What's Backed Up
- Configuration files
- Database
- Environment variables
- Custom rules
- Reports (last 30 days)

### Restoration Procedures

#### Full System Restore

1. **Install prerequisites**:
   ```bash
   sudo ./scripts/install_snort3.sh
   ```

2. **Deploy AI-Ops**:
   ```bash
   sudo ./scripts/deploy_production.sh
   ```

3. **Restore from backup**:
   ```bash
   cd /opt/snort3-ai-ops/backups
   LATEST=$(ls -t backup_*.tar.gz | head -1)
   sudo tar -xzf $LATEST -C /
   ```

4. **Restart services**:
   ```bash
   sudo systemctl start snort3
   sudo systemctl start snort3-ai-ops
   ```

5. **Verify**:
   ```bash
   sudo systemctl status snort3-ai-ops
   curl http://localhost:8000/health
   ```

### Business Continuity

#### RTO (Recovery Time Objective): 1 hour
#### RPO (Recovery Point Objective): 24 hours

#### Failover Procedures
1. Deploy standby system using backup
2. Update DNS/load balancer
3. Verify event flow
4. Monitor for 15 minutes
5. Decommission failed system

---

## Contact Information

### Emergency Contacts
- **Primary On-Call**: [Phone/Slack]
- **Secondary On-Call**: [Phone/Slack]
- **Security Team**: security@example.com
- **Infrastructure Team**: infrastructure@example.com

### Escalation Path
1. Level 1: On-call engineer
2. Level 2: Senior security engineer
3. Level 3: Security architect
4. Level 4: CISO

### Vendor Support
- **Snort**: https://www.snort.org/support
- **SIEM Vendor**: [Support contact]
- **Firewall Vendor**: [Support contact]

---

## Appendices

### Appendix A: Port Reference
- 5555: ZeroMQ event stream
- 8000: AI-Ops API
- 8080: Web dashboard
- 9090: Prometheus metrics

### Appendix B: File Locations
- Configuration: `/opt/snort3-ai-ops/config/`
- Logs: `/opt/snort3-ai-ops/logs/`
- Data: `/opt/snort3-ai-ops/data/`
- Reports: `/opt/snort3-ai-ops/reports/`
- Backups: `/opt/snort3-ai-ops/backups/`

### Appendix C: Useful Commands
```bash
# View real-time events
journalctl -u snort3-ai-ops -f | grep "Event enriched"

# Check threat detection rate
journalctl -u snort3-ai-ops --since "1 hour ago" | grep "Threats Detected"

# List blocked IPs
curl http://localhost:8000/api/v1/firewall/blocked-ips

# Test agent
python main.py test-agent -a threat_intel

# Generate status report
python main.py status
```

---

**Document Version**: 1.0  
**Last Updated**: December 11, 2025  
**Maintained By**: Security Operations Team
