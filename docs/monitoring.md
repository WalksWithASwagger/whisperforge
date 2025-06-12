# WhisperForge v2.0 Production Monitoring & SLO Runbook

## 📊 Overview

This document provides comprehensive guidance for monitoring WhisperForge v2.0 in production, including SLO definitions, alerting thresholds, and incident response procedures.

## 🎯 Service Level Objectives (SLOs)

### Primary SLOs

| Metric | Target | Measurement Window | Alert Threshold |
|--------|--------|-------------------|-----------------|
| **Error Rate (5xx)** | < 1% | 5 minutes | > 1% for 5 minutes |
| **Response Time (Median)** | < 30 seconds | 5 minutes | > 30s for 5 minutes |
| **Pipeline Success Rate** | > 95% | 1 hour | < 95% for 15 minutes |
| **System Availability** | > 99.5% | 24 hours | < 99.5% for 1 hour |

### Secondary SLOs

| Metric | Target | Measurement Window |
|--------|--------|-------------------|
| **Database Response Time** | < 500ms | 5 minutes |
| **CPU Usage** | < 80% | 5 minutes |
| **Memory Usage** | < 85% | 5 minutes |
| **Disk Space** | > 1GB free | 1 hour |

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Streamlit     │    │   Core Services │    │   External APIs │
│   Frontend      │───▶│   - Session Mgr │───▶│   - Supabase    │
│   - Monitoring  │    │   - Auth Wrapper│    │   - OpenAI      │
│   - Metrics     │    │   - Pipelines   │    │   - Anthropic   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Structured    │    │   Health Checks │    │   Metrics       │
│   Logging       │    │   - Database    │    │   Export        │
│   - JSON Format │    │   - File System │    │   - Prometheus  │
│   - Trace IDs   │    │   - AI Providers│    │   - JSON        │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📈 Monitoring Stack

### Core Components

1. **Structured Logging** (`core/monitoring.py`)
   - JSON format with trace IDs
   - User context tracking
   - Performance metrics
   - Error tracking with stack traces

2. **Health Checks** (`core/health_check.py`)
   - Database connectivity
   - External API availability
   - System resources
   - File system access

3. **Metrics Export** (`core/metrics_exporter.py`)
   - Prometheus format
   - JSON export for dashboards
   - Real-time SLO calculation

4. **Streamlit Integration** (`core/streamlit_monitoring.py`)
   - Session tracking
   - User action monitoring
   - Pipeline performance
   - Error capture

### Log Locations

- **Structured Logs**: `logs/whisperforge_structured_YYYYMMDD.jsonl`
- **Application Logs**: `streamlit.log`
- **Session Storage**: `~/.whisperforge_sessions/`

## 🚨 Alert Definitions

### Critical Alerts (Page Immediately)

#### 1. High 5xx Error Rate
```yaml
Alert: High5xxErrorRate
Condition: error_rate_5xx > 1% for 5 minutes
Severity: Critical
Response Time: < 5 minutes
```

**Runbook:**
1. Check application logs for error patterns
2. Verify database connectivity
3. Check external API status (OpenAI, Anthropic, Supabase)
4. Review recent deployments
5. Scale resources if needed

#### 2. System Unhealthy
```yaml
Alert: SystemUnhealthy
Condition: health_status == "unhealthy"
Severity: Critical
Response Time: < 5 minutes
```

**Runbook:**
1. Access health check endpoint: `/health` or Health Check page
2. Review failed health checks
3. Check environment variables
4. Verify database connection
5. Restart application if necessary

### Warning Alerts (Investigate Within 30 Minutes)

#### 3. High Response Time
```yaml
Alert: HighResponseTime
Condition: median_response_time > 30s for 5 minutes
Severity: Warning
Response Time: < 30 minutes
```

**Runbook:**
1. Check system resources (CPU, memory)
2. Review database performance
3. Analyze slow queries in logs
4. Check external API latency
5. Consider scaling or optimization

#### 4. Pipeline Failures
```yaml
Alert: PipelineFailures
Condition: pipeline_success_rate < 95% for 15 minutes
Severity: Warning
Response Time: < 30 minutes
```

**Runbook:**
1. Check pipeline logs for error patterns
2. Verify AI provider API keys and quotas
3. Review file upload issues
4. Check transcription service status
5. Validate content generation prompts

## 🔍 Troubleshooting Guide

### Common Issues

#### Database Connection Issues
```bash
# Check Supabase connectivity
curl -H "apikey: $SUPABASE_ANON_KEY" \
     "$SUPABASE_URL/rest/v1/users?select=id&limit=1"

# Verify environment variables
echo $SUPABASE_URL
echo $SUPABASE_ANON_KEY
```

#### High Memory Usage
```bash
# Check memory usage
ps aux | grep streamlit
free -h

# Check session storage
du -sh ~/.whisperforge_sessions/
find ~/.whisperforge_sessions/ -name "*.json" -mtime +7 -delete
```

#### File Upload Issues
```bash
# Check disk space
df -h

# Check logs directory
ls -la logs/
tail -f logs/whisperforge_structured_$(date +%Y%m%d).jsonl
```

#### AI Provider Issues
```bash
# Test OpenAI API
curl -H "Authorization: Bearer $OPENAI_API_KEY" \
     "https://api.openai.com/v1/models"

# Test Anthropic API
curl -H "x-api-key: $ANTHROPIC_API_KEY" \
     "https://api.anthropic.com/v1/messages" \
     -d '{"model":"claude-3-sonnet-20240229","max_tokens":10,"messages":[{"role":"user","content":"test"}]}'
```

### Performance Optimization

#### 1. Session Management
- Monitor session file count: `ls ~/.whisperforge_sessions/ | wc -l`
- Clean expired sessions: `find ~/.whisperforge_sessions/ -name "*.json" -mtime +7 -delete`
- Check session size: `du -sh ~/.whisperforge_sessions/`

#### 2. Database Optimization
- Monitor query performance in logs
- Check connection pool usage
- Verify index usage for frequent queries

#### 3. Memory Management
- Monitor Streamlit memory usage
- Check for memory leaks in long-running sessions
- Restart application if memory usage > 85%

## 📊 Dashboard Setup

### Grafana Dashboard Import

1. **Import Dashboard**:
   ```bash
   # Import the provided dashboard
   curl -X POST http://grafana:3000/api/dashboards/db \
        -H "Content-Type: application/json" \
        -d @monitoring/grafana_dashboard.json
   ```

2. **Configure Data Sources**:
   - **Prometheus**: `http://prometheus:9090`
   - **Loki**: `http://loki:3100`

3. **Set Up Alerts**:
   - Configure notification channels (Slack, email, PagerDuty)
   - Set alert rules for SLO violations
   - Test alert delivery

### Metrics Endpoints

#### Health Check
```bash
# Application health
curl http://localhost:8501/health

# Detailed health with metrics
curl http://localhost:8501/health?format=json
```

#### Prometheus Metrics
```bash
# Export Prometheus metrics
curl http://localhost:8501/metrics

# Or via application
# Navigate to Health Check page → Export Prometheus Metrics
```

## 🔧 Maintenance Procedures

### Daily Tasks
- [ ] Review SLO compliance dashboard
- [ ] Check for any alert notifications
- [ ] Monitor disk space usage
- [ ] Review error logs for patterns

### Weekly Tasks
- [ ] Clean up old log files
- [ ] Review performance trends
- [ ] Update dashboard configurations
- [ ] Test alert mechanisms

### Monthly Tasks
- [ ] Review and update SLO targets
- [ ] Analyze capacity planning metrics
- [ ] Update monitoring documentation
- [ ] Conduct incident response drills

## 🚀 Deployment Monitoring

### Pre-Deployment Checklist
- [ ] Health checks passing
- [ ] All SLOs within targets
- [ ] No active alerts
- [ ] Database migrations tested
- [ ] Rollback plan prepared

### Post-Deployment Monitoring
1. **Immediate (0-15 minutes)**:
   - Monitor error rates
   - Check health status
   - Verify key functionality

2. **Short-term (15-60 minutes)**:
   - Monitor response times
   - Check pipeline success rates
   - Review user feedback

3. **Long-term (1-24 hours)**:
   - Analyze performance trends
   - Monitor resource usage
   - Review SLO compliance

## 📞 Escalation Procedures

### Severity Levels

#### P0 - Critical (Page Immediately)
- System completely down
- Data loss or corruption
- Security breach
- SLO violations affecting > 50% of users

**Response**: Page on-call engineer immediately

#### P1 - High (Respond within 30 minutes)
- Significant feature degradation
- SLO violations affecting < 50% of users
- Performance issues

**Response**: Notify on-call engineer via Slack/email

#### P2 - Medium (Respond within 4 hours)
- Minor feature issues
- Non-critical alerts
- Performance degradation

**Response**: Create ticket for next business day

#### P3 - Low (Respond within 24 hours)
- Enhancement requests
- Documentation updates
- Non-urgent maintenance

**Response**: Add to backlog

### Contact Information

```yaml
Primary On-Call: [Your contact info]
Secondary On-Call: [Backup contact]
Engineering Manager: [Manager contact]
Product Owner: [Product contact]

Slack Channels:
  - #whisperforge-alerts
  - #engineering-oncall
  - #incidents

External Services:
  - Supabase Status: https://status.supabase.com/
  - OpenAI Status: https://status.openai.com/
  - Anthropic Status: https://status.anthropic.com/
```

## 🔐 Security Monitoring

### Key Security Metrics
- Failed authentication attempts
- Unusual user activity patterns
- API key usage anomalies
- Database access patterns

### Security Alerts
- Multiple failed login attempts
- Unusual API usage patterns
- Unauthorized access attempts
- Data export anomalies

## 📚 Additional Resources

- [WhisperForge Architecture Documentation](../SYSTEM_ANALYSIS_REPORT.md)
- [Session Management Guide](../SESSION_REFACTOR_IMPLEMENTATION.md)
- [Development Guide](../DEVELOPMENT_GUIDE.md)
- [Deployment Verification](../DEPLOYMENT_VERIFICATION_REPORT.md)

---

**Last Updated**: $(date)
**Version**: 2.0
**Maintained By**: WhisperForge Engineering Team 