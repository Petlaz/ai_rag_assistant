# Phase 5: Production Monitoring & Alerting

This directory contains the complete implementation of Phase 5 production monitoring and alerting infrastructure for the RAG Assistant system. This phase provides comprehensive observability, real-time monitoring, intelligent alerting, and log analysis capabilities for production deployments.

## Overview

Phase 5 implements enterprise-grade monitoring and alerting infrastructure including:

- **Production Monitoring**: Real-time system health, performance, and cost monitoring
- **Intelligent Alerting**: Multi-channel alerting with escalation policies and noise reduction  
- **Log Analysis**: Comprehensive log processing, anomaly detection, and pattern analysis
- **Dashboard Integration**: CloudWatch dashboards for real-time observability
- **Cost Monitoring**: Budget tracking and cost anomaly detection

## Structure

```
scripts/monitoring/
├── production_monitoring.py    # Main production monitoring system
├── alerting_system.py         # Intelligent alerting framework
└── log_analysis.py           # Log analysis and monitoring

configs/
├── monitoring.yaml           # Production monitoring configuration
├── alerting.yaml            # Alerting system configuration
└── log_analysis.yaml        # Log analysis configuration
```

## Quick Start

### 1. Setup Production Monitoring

```bash
# Setup monitoring infrastructure
python scripts/monitoring/production_monitoring.py \
    --mode setup \
    --setup-dashboards \
    --cloudwatch-enabled

# Start continuous monitoring
python scripts/monitoring/production_monitoring.py \
    --mode continuous \
    --monitoring-interval 60 \
    --enable-alerts
```

### 2. Configure Alerting System

```bash
# Setup alerting infrastructure
python scripts/monitoring/alerting_system.py \
    --mode setup \
    --setup-alerts \
    --enable-channels slack,email

# Start alerting daemon
python scripts/monitoring/alerting_system.py \
    --mode daemon \
    --monitoring-interval 30 \
    --enable-escalation
```

### 3. Enable Log Analysis

```bash
# Setup log analysis pipeline
python scripts/monitoring/log_analysis.py \
    --mode setup \
    --setup-pipeline

# Start real-time log monitoring
python scripts/monitoring/log_analysis.py \
    --mode monitor \
    --watch-logs logs/application \
    --generate-report
```

## Production Monitoring

### Features

- **System Health Monitoring**: CPU, memory, disk, network metrics
- **Application Performance**: Response times, error rates, availability
- **ML Model Performance**: Precision, recall, inference latency
- **Cost Tracking**: AWS service costs, budget alerts, cost anomalies
- **CloudWatch Integration**: Custom dashboards and metrics

### Configuration

Edit [configs/monitoring.yaml](configs/monitoring.yaml) to configure:

```yaml
monitoring:
  thresholds:
    cpu_usage_warning: 70.0
    cpu_usage_critical: 90.0
    response_time_warning: 2000
    response_time_critical: 5000

cloudwatch:
  enabled: true
  region: "us-east-1"
  namespace: "RAGAssistant"
```

### Usage Examples

```bash
# Run single monitoring check
python scripts/monitoring/production_monitoring.py \
    --mode single-check

# Generate monitoring report
python scripts/monitoring/production_monitoring.py \
    --mode report \
    --timeframe 24hours

# Continuous monitoring with custom interval
python scripts/monitoring/production_monitoring.py \
    --mode continuous \
    --monitoring-interval 30 \
    --duration-minutes 120
```

## Intelligent Alerting

### Features

- **Multi-Channel Alerts**: Email, Slack, CloudWatch, webhooks
- **Alert Aggregation**: Deduplication and noise reduction
- **Escalation Policies**: Severity-based routing and escalation
- **Context Enrichment**: Alert details with system context
- **Maintenance Windows**: Alert suppression during maintenance

### Configuration

Edit [configs/alerting.yaml](configs/alerting.yaml) to configure:

```yaml
channels:
  email:
    enabled: true
    smtp_server: "smtp.gmail.com"
    to_emails: ["alerts@example.com"]
  
  slack:
    enabled: true
    webhook_url: "https://hooks.slack.com/..."
    channel: "#rag-alerts"

escalation:
  enabled: true
  escalation_delay_minutes: 15
  max_escalations: 2
```

### Usage Examples

```bash
# Test alert channels
python scripts/monitoring/alerting_system.py \
    --mode test \
    --test-alerts

# Generate alerting report
python scripts/monitoring/alerting_system.py \
    --mode report

# Custom alerting configuration
python scripts/monitoring/alerting_system.py \
    --config-path configs/custom_alerting.yaml
```

## Log Analysis

### Features

- **Real-Time Monitoring**: Watch log files for changes
- **Pattern Recognition**: Error classification and pattern detection
- **Anomaly Detection**: Statistical analysis for unusual log patterns
- **Performance Extraction**: Extract metrics from log messages
- **Multi-Format Support**: JSON, syslog, Apache, custom formats

### Configuration

Edit [configs/log_analysis.yaml](configs/log_analysis.yaml) to configure:

```yaml
monitoring:
  log_paths:
    - "logs/application"
    - "logs/monitoring"
  real_time:
    enabled: true
    polling_interval_seconds: 5

anomaly_detection:
  enabled: true
  window_size: 100
  threshold_multiplier: 3.0
```

### Usage Examples

```bash
# Analyze historical logs
python scripts/monitoring/log_analysis.py \
    --mode analyze \
    --log-files logs/application/*.log \
    --timeframe 24hours \
    --generate-report

# Monitor specific log paths
python scripts/monitoring/log_analysis.py \
    --mode monitor \
    --watch-logs /var/log/rag-assistant logs/application

# Setup log aggregation pipeline
python scripts/monitoring/log_analysis.py \
    --setup-pipeline \
    --elastic-host localhost:9200
```

## Configuration Reference

### Monitoring Thresholds

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | 70% | 90% |
| Memory Usage | 75% | 90% |
| Disk Usage | 80% | 95% |
| Response Time | 2000ms | 5000ms |
| Error Rate | 5% | 15% |

### Alert Severity Levels

- **Critical**: Immediate attention required (page on-call)
- **High**: Important issues (notify within 5 minutes)
- **Medium**: Notable events (notify within 15 minutes)
- **Low**: Informational (batch notifications)

### Log Analysis Patterns

- **Connection Errors**: Network and connectivity issues
- **Authentication Errors**: Auth failures and security events
- **Resource Errors**: Memory, disk, and resource exhaustion
- **Database Errors**: Database connectivity and query issues
- **API Errors**: HTTP errors and API failures
- **ML Model Errors**: Model inference and performance issues

## Dashboard Integration

### CloudWatch Dashboards

The monitoring system automatically creates CloudWatch dashboards:

1. **RAGAssistant-Production**: Main system overview
   - Query performance metrics
   - System health indicators
   - Error rates and availability
   - Usage statistics

2. **RAGAssistant-Costs**: Cost monitoring
   - Service-specific costs
   - Budget tracking
   - Cost trends and projections

### Custom Metrics

Custom CloudWatch metrics include:

- `RAGAssistant/Performance/QueryResponseTime`
- `RAGAssistant/Performance/PrecisionAt5`
- `RAGAssistant/System/ErrorRate`
- `RAGAssistant/Costs/TotalCostPerQuery`

## Security & Privacy

### Data Protection

- **Log Masking**: Automatic PII and sensitive data masking
- **Access Control**: Role-based access to monitoring data
- **Encryption**: Encrypted storage and transmission
- **Compliance**: GDPR and SOC2 compliance features

### Sensitive Data Patterns

Automatically masked patterns include:
- API keys and tokens
- Email addresses
- IP addresses
- Credit card numbers
- Social security numbers

## Production Deployment

### Prerequisites

1. **AWS Credentials**: Configure AWS CLI with appropriate IAM permissions
2. **CloudWatch Permissions**: Permissions for metrics, dashboards, and alarms
3. **Log Access**: Read permissions for application log files
4. **Network Access**: Connectivity to monitoring endpoints

### Required AWS Permissions

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "cloudwatch:PutMetricData",
        "cloudwatch:PutDashboard",
        "cloudwatch:GetMetricStatistics",
        "logs:DescribeLogGroups",
        "logs:DescribeLogStreams",
        "logs:GetLogEvents"
      ],
      "Resource": "*"
    }
  ]
}
```

### Deployment Checklist

- [ ] Configure monitoring thresholds in `configs/monitoring.yaml`
- [ ] Setup alert channels in `configs/alerting.yaml`
- [ ] Configure log paths in `configs/log_analysis.yaml`
- [ ] Test alert channels and escalation policies
- [ ] Create CloudWatch dashboards
- [ ] Setup automated reporting
- [ ] Configure maintenance windows
- [ ] Test end-to-end monitoring flow

## Performance Impact

### Resource Usage

| Component | CPU Impact | Memory Usage | Network |
|-----------|------------|--------------|---------|
| Production Monitoring | <1% | ~50MB | Low |
| Alerting System | <0.5% | ~30MB | Minimal |
| Log Analysis | <2% | ~100MB | Medium |

### Recommended Sizing

- **Small Deployment**: 1 CPU core, 512MB RAM
- **Medium Deployment**: 2 CPU cores, 1GB RAM  
- **Large Deployment**: 4 CPU cores, 2GB RAM

## Troubleshooting

### Common Issues

**CloudWatch Connection Issues**
```bash
# Check AWS credentials
aws cloudwatch list-metrics --namespace RAGAssistant

# Verify region configuration
aws configure get region
```

**Alert Channel Failures**
```bash
# Test email configuration
python scripts/monitoring/alerting_system.py --test-alerts --channels email

# Test Slack webhook
curl -X POST -H 'Content-type: application/json' \
    --data '{"text":"Test message"}' YOUR_WEBHOOK_URL
```

**Log File Access Issues**
```bash
# Check file permissions
ls -la logs/application/

# Test log file watching
python scripts/monitoring/log_analysis.py --mode monitor --watch-logs logs/
```

### Debug Mode

Enable debug logging in any script:

```bash
# Add debug logging
export LOG_LEVEL=DEBUG
python scripts/monitoring/production_monitoring.py --mode continuous
```

## Additional Resources

- [CloudWatch Documentation](https://docs.aws.amazon.com/cloudwatch/)
- [Grafana Integration Guide](docs/grafana-integration.md)
- [ELK Stack Setup](docs/elk-stack-setup.md)
- [Custom Metric Development](docs/custom-metrics.md)
- [Alert Runbooks](docs/alert-runbooks.md)

## Contributing

To add new monitoring capabilities:

1. Create feature branch: `git checkout -b monitoring/new-feature`
2. Implement monitoring logic in appropriate script
3. Add configuration options to YAML files
4. Update documentation and examples
5. Test with sample data and edge cases
6. Submit pull request with test results

## License

This monitoring infrastructure is part of the RAG Assistant project and follows the same licensing terms. See the main project LICENSE file for details.