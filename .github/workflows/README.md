# CI/CD Pipeline Documentation

## Overview

This project implements a comprehensive CI/CD pipeline using GitHub Actions workflows, designed for enterprise-grade ML/AI applications with automated testing, model validation, and AWS deployment.

## Workflows

### 1. ML Pipeline (`ml-pipeline.yml`)

**Triggered on:**
- Push to `main` or `develop` branches
- Pull requests to `main`
- Changes to RAG pipeline, LLM client, or dependencies

**Features:**
- **Code Quality**: Black formatting, isort imports, flake8 linting, mypy type checking
- **Unit Testing**: Comprehensive test suite with coverage reporting
- **Integration Testing**: Full RAG pipeline end-to-end validation
- **Performance Benchmarking**: Automated performance regression detection
- **Service Dependencies**: OpenSearch and Ollama integration for realistic testing

**Stages:**
1. `lint-and-format` - Code quality validation
2. `unit-tests` - Fast feedback with isolated tests
3. `integration-tests` - Full system validation
4. `performance-benchmark` - Performance tracking

### 2. Model Validation (`model-validation.yml`)

**Triggered on:**
- Push to `main` (model changes)
- Daily schedule (drift detection)
- Manual workflow dispatch

**Features:**
- **RAGAS Evaluation**: Advanced RAG assessment using industry-standard metrics
- **Quality Gates**: Automated quality thresholds with failure detection
- **Model Drift Detection**: Continuous monitoring for performance degradation
- **MLflow Integration**: Experiment tracking and metric logging
- **Multi-Model Support**: Evaluation across different LLM configurations

**Metrics Tracked:**
- **Retrieval**: Precision, recall, relevancy
- **Response Quality**: Answer relevancy, faithfulness, context precision/recall
- **Performance Drift**: Historical comparison and trend analysis

### 3. AWS Deployment (`deploy-aws.yml`)

**Triggered on:**
- Push to `main`
- Version tags (`v*.*.*`)
- Manual deployment with environment selection

**Features:**
- **Multi-Environment**: Staging and production deployment paths
- **Cost Estimation**: Automated AWS cost analysis and reporting
- **Blue-Green Deployment**: Zero-downtime deployments with automatic rollback
- **Security Scanning**: Container vulnerability assessment with Trivy
- **Infrastructure as Code**: Terraform-managed AWS resources
- **Production Validation**: Comprehensive health checks and smoke tests

**Deployment Modes:**
- `ultra-budget` - Cost-optimized ($8-18/month)
- `balanced` - Production-ready ($25-60/month)
- `full-scale` - Enterprise grade ($100-300+/month)

## Setup Requirements

### 1. Repository Secrets

Configure the following secrets in your GitHub repository (`Settings > Secrets and variables > Actions`):

```bash
# AWS Configuration
AWS_ACCESS_KEY_ID              # AWS access key for deployment
AWS_SECRET_ACCESS_KEY          # AWS secret key for deployment
TERRAFORM_STATE_BUCKET         # S3 bucket for Terraform state

# Optional: External Services
CODECOV_TOKEN                  # For coverage reporting
SLACK_WEBHOOK_URL             # For deployment notifications
```

### 2. Environment Setup

**Development:**
```bash
# Install dependencies
pip install -r requirements.txt
pip install pytest pytest-cov black isort flake8 mypy

# Setup pre-commit hooks (recommended)
pre-commit install
```

**Production:**
- AWS account with appropriate IAM permissions
- ECR repository for container images
- Terraform state bucket configuration

### 3. AWS Permissions

Required IAM permissions for deployment:
```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "ecs:*",
        "ecr:*",
        "ec2:*",
        "iam:*",
        "logs:*",
        "application-autoscaling:*",
        "elasticloadbalancing:*"
      ],
      "Resource": "*"
    }
  ]
}
```

## Workflow Configuration

### Environment Variables

Key configuration variables used across workflows:

```yaml
PYTHON_VERSION: '3.11'
AWS_REGION: 'us-east-1'
CONTAINER_REGISTRY: 'public.ecr.aws'
OLLAMA_HOST: 'http://localhost:11434'
MLFLOW_TRACKING_URI: 'sqlite:///mlflow.db'
```

### Quality Gates

**Code Quality Thresholds:**
- Black formatting compliance (required)
- Import sorting with isort (required)
- Flake8 linting (E9, F63, F7, F82 errors fail)
- Test coverage reporting (no minimum enforced)

**Model Quality Thresholds:**
```python
{
    'retrieval_precision': 0.7,
    'retrieval_recall': 0.6,
    'ragas_answer_relevancy': 0.7,
    'ragas_faithfulness': 0.8,
    'ragas_context_precision': 0.7,
    'ragas_context_recall': 0.6
}
```

**Security Thresholds:**
- Container vulnerability scanning (HIGH/CRITICAL severity fails)
- Dependency security audit
- Secret detection

## Monitoring and Alerting

### Automated Notifications

**Pull Request Comments:**
- Model evaluation results
- Deployment status and URLs
- Cost estimation reports

**Issue Creation:**
- Deployment failures (automatic)
- Quality gate failures
- Security vulnerabilities

### Performance Tracking

**Benchmarking:**
- Automatic performance regression detection (200% alert threshold)
- Historical trend analysis
- MLflow experiment tracking

**Drift Detection:**
- Daily model performance monitoring
- 10% degradation threshold
- Automated alerts and recommendations

## Usage Examples

### Manual Deployment

```bash
# Deploy to staging with ultra-budget mode
gh workflow run deploy-aws.yml \
  -f environment=staging \
  -f deployment_mode=ultra-budget

# Force production deployment (skip validation)
gh workflow run deploy-aws.yml \
  -f environment=production \
  -f deployment_mode=balanced \
  -f force_deploy=true
```

### Model Evaluation

```bash
# Run comprehensive model evaluation
gh workflow run model-validation.yml \
  -f evaluation_mode=comprehensive \
  -f model_version=v1.2.0

# Trigger drift detection
gh workflow run model-validation.yml \
  -f evaluation_mode=drift-detection
```

## Troubleshooting

### Common Issues

**Test Failures:**
```bash
# Run tests locally
pytest tests/ -v --cov=rag_pipeline

# Check OpenSearch connection
curl -X GET "localhost:9200/_cluster/health"
```

**Deployment Issues:**
```bash
# Check AWS credentials
aws sts get-caller-identity

# Validate Terraform configuration
cd infra/terraform && terraform validate

# Test Docker builds locally
docker build -f deployment/aws/docker/Dockerfile.app .
```

**Model Validation Errors:**
```bash
# Test Ollama connection
curl http://localhost:11434/api/generate \
  -d '{"model": "llama3.2:1b", "prompt": "test"}'

# Check MLflow server
mlflow server --backend-store-uri sqlite:///mlflow.db
```

### Debug Mode

Enable verbose logging in workflows:
```yaml
env:
  ACTIONS_STEP_DEBUG: true
  ACTIONS_RUNNER_DEBUG: true
```

### Performance Optimization

**Caching Strategy:**
- Python dependencies cached by requirements.txt hash
- Docker layer caching for faster builds
- Terraform state and module caching

**Parallel Execution:**
- Independent jobs run in parallel
- Test suites organized by execution time
- Multi-platform Docker builds

## Best Practices

### Development Workflow

1. **Feature Development:**
   - Create feature branch from `develop`
   - ML Pipeline runs automatically on push
   - Code quality gates prevent merge

2. **Model Updates:**
   - Model validation runs on merge to `main`
   - Quality gates ensure no regression
   - Automatic drift monitoring

3. **Deployment Process:**
   - Staging deployment on merge to `main`
   - Production deployment on version tags
   - Automatic rollback on failure

### Security Considerations

- Container image scanning before deployment
- Secrets management through GitHub Secrets
- Network security groups and IAM least privilege
- Encrypted data in transit and at rest

### Cost Management

- Automatic cost estimation before deployment
- Resource tagging for cost tracking
- Auto-scaling groups for efficient utilization
- Development environment auto-shutdown

## Maintenance

### Regular Tasks

**Weekly:**
- Review performance benchmark trends
- Check for dependency updates
- Monitor AWS cost reports

**Monthly:**
- Update base Docker images
- Review and rotate AWS credentials
- Analyze workflow performance metrics

**Quarterly:**
- Security audit of IAM permissions
- Review and update quality thresholds
- Performance optimization review

### Updating Workflows

When modifying workflows:
1. Test changes in feature branch
2. Validate workflow syntax with `act` (local GitHub Actions runner)
3. Monitor first production run carefully
4. Update documentation as needed

---

For additional support, refer to the [deployment documentation](../deployment/aws/README.md) or create an issue with the `ci-cd` label.