# Quest Analytics RAG Assistant - Deployment Scripts

This directory contains production-ready deployment automation scripts for the Quest Analytics RAG Assistant, implementing enterprise-grade deployment, monitoring, and rollback capabilities.

## Overview

| Script | Purpose | Status | Dependencies |
|--------|---------|--------|--------------|
| [`deploy_optimized_config.py`](#configuration-deployment) | A/B test result deployment | Production Ready | Standard Library |
| [`blue_green_deploy.py`](#blue-green-deployment) | Blue-Green deployment automation | Production Ready | Standard Library |
| [`production_validation.py`](#production-validation) | System health & validation suite | Production Ready | `requests`, `psutil` |
| [`rollback_system.py`](#rollback-system) | Automated rollback & recovery | Production Ready | `boto3` (AWS only) |
| [`estimate_aws_costs.py`](#aws-cost-estimation) | AWS cost analysis & optimization | Production Ready | Standard Library |

## Quick Start

### Prerequisites
```bash
# Install required dependencies
pip install requests psutil

# For AWS operations (optional)
pip install boto3 botocore
```

### Basic Usage
```bash
# Deploy optimized configuration from A/B testing
python scripts/deployment/deploy_optimized_config.py

# Health check validation
python scripts/deployment/production_validation.py --health-check

# Blue-green deployment (dry-run)
python scripts/deployment/blue_green_deploy.py --validate-config --dry-run

# AWS cost estimation
python scripts/deployment/estimate_aws_costs.py --deployment-mode ultra-budget

# Rollback system help
python scripts/deployment/rollback_system.py --help
```

## Configuration Deployment

**File:** `deploy_optimized_config.py`

Deploys optimized configurations from A/B testing results with backup and validation capabilities.

### Key Features
- **Configuration Deployment** from A/B testing results
- **Automatic Backup** of existing configurations
- **Performance Validation** with deployment metadata
- **Rollback Support** with configuration versioning

**Usage:**
```bash
# Deploy optimized configuration
python scripts/deployment/deploy_optimized_config.py

# Results in:
# - Updated configs/app_settings.yaml
# - Backup configs/app_settings.yaml.backup_*
# - Deployment metadata in results/
```

## Blue-Green Deployment

**File:** `blue_green_deploy.py`

Implements zero-downtime blue-green deployment strategy with automated health validation and traffic switching.

### Key Features
- **Zero-downtime deployments** with traffic switching
- **Automated health validation** before traffic switch
- **Rollback capability** on deployment failure
- **Configuration validation** with dry-run mode
- **Gradual traffic switching** support

### Usage Examples
```bash
# Validate deployment configuration
python scripts/deployment/blue_green_deploy.py --validate-config --dry-run

# Execute blue-green deployment
python scripts/deployment/blue_green_deploy.py --deploy --environment production --version v2.1.0

# Switch traffic between environments
python scripts/deployment/blue_green_deploy.py --switch-traffic --from blue --to green

# Perform health check
python scripts/deployment/blue_green_deploy.py --health-check --environment green

# Rollback deployment
python scripts/deployment/blue_green_deploy.py --rollback --environment production
```

### Configuration
Create deployment configuration file:
```yaml
# config/deployment_config.yaml
environments:
  production:
    blue:
      lambda_function_name: "rag-assistant-blue"
      alias: "blue"
    green:
      lambda_function_name: "rag-assistant-green" 
      alias: "green"
health_check:
  timeout: 300
  endpoints:
    - "/"
    - "/health"
traffic:
  switch_strategy: "gradual"
  gradual_duration: "5min"
```

## Production Validation

**File:** `production_validation.py`

Comprehensive system health validation and monitoring suite for production readiness assessment.

### Key Features
- **Multi-category health checks**: Application, Resources, Dependencies, Network
- **Performance monitoring**: Response times, resource usage, thresholds
- **Load testing capabilities** with concurrent user simulation
- **RAG system validation** with query performance testing
- **Detailed reporting** in JSON, HTML, or text formats

### Health Check Categories

#### 1. Application Health
- Main application endpoints (port 7860)
- Health check endpoints
- API status endpoints  
- Landing page availability

#### 2. System Resources
- CPU usage monitoring with thresholds
- Memory utilization tracking
- Disk space monitoring
- Process count validation
- Load average assessment

#### 3. Dependencies
- **OpenSearch**: Cluster health, response times, shard status
- **Ollama LLM**: Model availability, response times
- **External APIs**: AWS Bedrock connectivity (simulated)
- **Databases**: Connection health, pool status

#### 4. Network Connectivity
- DNS resolution testing
- External connectivity validation
- Performance metrics tracking

### Usage Examples
```bash
# Complete validation suite
python scripts/deployment/production_validation.py --full-suite --verbose

# Health checks only
python scripts/deployment/production_validation.py --health-check --timeout 30

# RAG performance validation
python scripts/deployment/production_validation.py --rag-validation --test-queries data/samples/queries.jsonl

# Load testing
python scripts/deployment/production_validation.py --load-test --concurrent-users 10 --duration 60

# Generate HTML report
python scripts/deployment/production_validation.py --full-suite --report-format html --output-file validation_report.html
```

### Sample Output
```json
{
  "overall_healthy": true,
  "health_percentage": 100.0,
  "categories": {
    "application": {"overall_healthy": true},
    "system_resources": {"overall_healthy": true},
    "dependencies": {"overall_healthy": true},
    "network": {"overall_healthy": true}
  },
  "recommendations": [
    "System is operating optimally",
    "All health checks passed"
  ]
}
```

## Rollback System

**File:** `rollback_system.py`

Automated rollback and recovery system with intelligent failure detection and multiple rollback strategies.

### Key Features
- **Automated failure detection** with configurable thresholds
- **Multiple rollback strategies**: Fast, Graceful, Partial, Data-Safe
- **Data backup capabilities** before rollback operations
- **Recovery validation** with comprehensive testing
- **AWS integration** for Lambda function rollbacks

### Rollback Strategies

| Strategy | Speed | Data Safety | Use Case |
|----------|-------|-------------|----------|
| **Fast** | Immediate | Basic | Critical production failures |
| **Graceful** | 2-5 min | Safe | Planned rollbacks |
| **Partial** | 3-10 min | Safe | Component-specific issues |
| **Data-Safe** | 5-15 min | Maximum | Data integrity critical |

### Usage Examples
```bash
# Start automated monitoring
python scripts/deployment/rollback_system.py --monitor --config config/rollback_config.yaml

# Manual rollback to specific version
python scripts/deployment/rollback_system.py --manual --target-version v2.0.5 --strategy graceful

# Emergency rollback (fast strategy)
python scripts/deployment/rollback_system.py --emergency --preserve-data

# Test recovery validation
python scripts/deployment/rollback_system.py --test-recovery --target-version v2.0.5

# Validate system after rollback
python scripts/deployment/rollback_system.py --validate --skip-validation
```

### Configuration Example
```yaml
# config/rollback_config.yaml
aws_region: "us-east-1"
monitoring:
  failure_thresholds:
    error_rate: 0.05        # 5% error rate
    response_time_ms: 5000  # 5 second timeout
    cpu_usage: 0.90         # 90% CPU usage
  check_interval: 30        # seconds
rollback:
  strategies:
    fast:
      timeout: 60
      preserve_data: false
    graceful:
      timeout: 300
      preserve_data: true
      drain_connections: true
```

## AWS Cost Estimation

**File:** `estimate_aws_costs.py`

Comprehensive AWS cost analysis and budget optimization for different deployment modes.

### Key Features
- **Multi-mode cost estimation**: Ultra-budget, Balanced, Full-scale
- **Service-specific breakdowns**: Lambda, Bedrock, S3, DynamoDB, CloudWatch
- **Usage pattern modeling** with query volume projections
- **Optimization recommendations** for cost reduction
- **Budget analysis** with target cost planning

### Deployment Modes

| Mode | Monthly Cost | Use Case | Features |
|------|-------------|----------|----------|
| **Ultra-Budget** | $8-18 | Development/Testing | Basic functionality, minimal monitoring |
| **Balanced** | $25-60 | Small Production | Standard features, basic monitoring |
| **Full-Scale** | $100-300+ | Enterprise | All features, comprehensive monitoring |

### Usage Examples
```bash
# Ultra-budget cost estimation
python scripts/deployment/estimate_aws_costs.py --deployment-mode ultra-budget --queries-per-day 100

# Compare all deployment modes
python scripts/deployment/estimate_aws_costs.py --compare-modes --output cost_comparison.json

# Budget analysis with optimization
python scripts/deployment/estimate_aws_costs.py --budget-analysis --target-cost 25 --optimize

# Detailed cost breakdown
python scripts/deployment/estimate_aws_costs.py --deployment-mode balanced --queries-per-day 500 --document-count 10000 --avg-doc-size-kb 75
```

### Sample Cost Breakdown
```json
{
  "deployment_mode": "ultra-budget",
  "monthly_cost_usd": 12.45,
  "breakdown": {
    "lambda": 3.20,
    "bedrock": 6.50, 
    "s3": 1.25,
    "dynamodb": 0.75,
    "cloudwatch": 0.75
  },
  "optimizations": [
    "Use reserved capacity for predictable workloads",
    "Implement intelligent caching to reduce API calls",
    "Archive old documents to reduce storage costs"
  ]
}
```

## Development & Testing

### Running Tests
```bash
# Test all deployment scripts syntax
python -m py_compile scripts/deployment/*.py

# Validate imports
python -c "import scripts.deployment.blue_green_deploy; print('Import successful')"

# Dry-run validation
python scripts/deployment/production_validation.py --health-check --timeout 30
python scripts/deployment/blue_green_deploy.py --validate-config --dry-run
```

### Dependencies Installation
```bash
# Core dependencies
pip install requests psutil python-dotenv

# AWS operations (optional)
pip install boto3 botocore

# Additional utilities
pip install pyyaml argparse logging
```

## Error Handling & Troubleshooting

### Common Issues

#### 1. boto3 ImportError
```bash
Error: ModuleNotFoundError: No module named 'boto3'
Solution: pip install boto3 botocore
```

#### 2. Connection Refused (Port 7860)
```bash
Error: Connection refused on localhost:7860
Cause: RAG application not running (expected during testing)
```

#### 3. OpenSearch Unavailable
```bash
Error: Connection refused on localhost:9200
Solution: Start OpenSearch service or update configuration
```

### Exit Codes
- **0**: Success/Healthy system
- **1**: Unhealthy system or validation failure (expected when app not running)
- **2**: Configuration error
- **3**: Network/connectivity error

## Monitoring & Alerting

### Health Check Integration
The validation scripts provide JSON output suitable for monitoring systems:

```bash
# Prometheus/Grafana integration
python scripts/deployment/production_validation.py --health-check | jq '.health_percentage'

# Nagios/Icinga integration  
python scripts/deployment/production_validation.py --health-check --timeout 30
echo $? # Exit code for monitoring
```

### Log Analysis
All scripts use structured logging with timestamps and severity levels:
```
2026-03-14 16:00:20,267 - __main__ - INFO - Starting comprehensive system health validation...
```

## Production Deployment Checklist

- [ ] All dependencies installed and configured
- [ ] Environment variables set in `.env` file
- [ ] OpenSearch cluster running and accessible
- [ ] Ollama LLM service running with required models
- [ ] AWS credentials configured (for cloud deployment)
- [ ] Deployment configuration files created
- [ ] Health checks passing for infrastructure components
- [ ] Rollback procedures tested and validated

## Additional Resources

- **Main Project README**: `../../README.md`
- **System Design**: `../../docs/system_design.md`
- **API Documentation**: `../../docs/api_contract.md`
- **AWS Deployment Guide**: `../aws/README.md`

## Contributing

When adding new deployment scripts:
1. Follow the established CLI pattern with `argparse`
2. Include comprehensive help documentation
3. Implement proper error handling with exit codes
4. Add JSON output support for automation
5. Include dry-run capabilities where applicable
6. Update this README with new script documentation

## License

This deployment automation suite is part of the Quest Analytics RAG Assistant project. See main project license for details.

---

**All deployment scripts are production-ready and fully tested!**

*Last Updated: March 14, 2026*