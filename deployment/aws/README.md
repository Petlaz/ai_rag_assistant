# 🚀 AWS Cloud Deployment

**Deploy your RAG Assistant to AWS with three cost-optimized modes**

---

## 🎯 Choose Your Deployment Mode

| Mode | Monthly Cost | Best For | Setup Time |
|------|-------------|----------|------------|
| **💰 Ultra-Budget** | $8-18 | Students, Learning, Demos | 30 min |
| **⚖️ Balanced** | $15-35 | Small Production, Portfolio | 45 min |
| **🚀 Full** | $25-68 | Production, Showcasing Skills | 60 min |

---

## 🚀 Quick Start

### 1. Deploy Ultra-Budget Mode (Recommended for Students)
```bash
cd /path/to/AI_RAG
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20
```

### 2. Deploy Balanced Mode  
```bash
cd /path/to/AI_RAG
./scripts/deploy-student-stack.sh --mode=balanced --budget=40
```

### 3. Deploy Full Production Mode
```bash
cd /path/to/AI_RAG  
./scripts/deploy-student-stack.sh --mode=full --budget=70
```

### 4. Get Help
```bash
./scripts/deploy-student-stack.sh --help
```

---

## 📚 Complete Documentation

### 📋 Setup Guides
- **[Infrastructure Setup](docs/infrastructure-setup.md)** - AWS account preparation & prerequisites
- **[Services Configuration](docs/services-configuration.md)** - Detailed service configuration for all modes
- **[Troubleshooting Guide](docs/troubleshooting.md)** - Common issues and solutions

### 💰 Cost Optimization
- **[Cost Optimization Guide](COST_OPTIMIZATION.md)** - Student-specific cost strategies and monitoring
- **[Ultra-Budget Implementation](ULTRA_BUDGET_IMPLEMENTATION.md)** - Complete ultra-budget system overview
- **[Deployment Roadmap](AWS_DEPLOYMENT_ROADMAP.md)** - Strategic deployment planning

---

## 🎓 Student-Specific Features

### 💰 Ultra-Budget Mode Highlights
- ✅ **$8-18/month** - Perfect for student budgets
- ✅ **SQLite Vector Storage** - No external database costs
- ✅ **Lambda Function URLs** - No API Gateway charges
- ✅ **24-Hour Caching** - Minimize LLM API costs
- ✅ **Automatic Cleanup** - Control storage costs

### 🎯 Cost Control Features
- **Billing Alerts** - Automatic notifications at 80% budget
- **Usage Monitoring** - Daily cost tracking and optimization
- **Emergency Shutdown** - One-click resource cleanup
- **Upgrade Path** - Seamless migration between modes

---

## 🏗️ Architecture Overview

### Ultra-Budget Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Gradio    │    │   Lambda    │    │   Bedrock   │
│     UI      │───▶│  Function   │───▶│   Claude    │
│             │    │   + SQLite  │    │   Haiku     │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   
       │                   ▼                   
       │            ┌─────────────┐            
       │            │ DynamoDB    │            
       └───────────▶│  Cache      │            
                    └─────────────┘            
```

### Balanced Architecture  
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Gradio    │    │ API Gateway │    │   Bedrock   │
│     UI      │───▶│   Lambda    │───▶│   Claude    │
│             │    │             │    │    Mix      │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   
       │                   ▼                   
       │            ┌─────────────┐            
       │            │  Pinecone   │            
       └───────────▶│   Vector    │            
                    │     DB      │            
                    └─────────────┘            
```

### Full Production Architecture
```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│ CloudFront  │    │ API Gateway │    │   Bedrock   │
│   Gradio    │───▶│   Lambda    │───▶│   Claude    │
│     UI      │    │             │    │   Sonnet    │
└─────────────┘    └─────────────┘    └─────────────┘
       │                   │                   
       │                   ▼                   
       │            ┌─────────────┐            
       │            │ OpenSearch  │            
       └───────────▶│ Serverless  │            
                    └─────────────┘            
```

---

## ⚡ Prerequisites

### AWS Account Setup
- [ ] AWS account with student credits activated
- [ ] AWS CLI installed and configured
- [ ] Billing alerts configured  
- [ ] Region selected (us-east-1 recommended for lowest costs)

### Local Environment
- [ ] Python 3.11+ installed
- [ ] Required dependencies: `pip install -r requirements.txt`
- [ ] Docker running (for local development)

---

## 🔧 Advanced Configuration

### Environment Variables
```bash
# Set deployment preferences
export AWS_REGION="us-east-1"
export DEPLOYMENT_MODE="ultra-budget"
export BUDGET_LIMIT="20"

# Optional: Custom configuration
export STACK_NAME="my-rag-assistant"
export ENABLE_MONITORING="true"
```

### Custom Deployment
```bash
# Deploy with custom settings
./scripts/deploy-student-stack.sh \
  --mode=ultra-budget \
  --budget=25 \
  --region=eu-west-1 \
  --stack-name=my-custom-stack
```

---

## 📊 Cost Monitoring

### Real-Time Cost Tracking
```bash
# Check today's costs
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-%d),End=$(date -d "1 day" +%Y-%m-%d) \
  --granularity DAILY \
  --metrics BlendedCost

# Monthly cost summary
aws ce get-cost-and-usage \
  --time-period Start=$(date +%Y-%m-01),End=$(date +%Y-%m-%d) \
  --granularity MONTHLY \
  --metrics BlendedCost
```

### Set Up Billing Alerts
```bash
# Create budget with alerts
aws budgets create-budget \
  --account-id $(aws sts get-caller-identity --query Account --output text) \
  --budget file://budget-config.json
```

---

## 🆘 Emergency Procedures

### Immediate Cost Control
```bash
# Emergency shutdown (preserves data)
./scripts/emergency-shutdown.sh --preserve-data

# Complete cleanup (removes everything)
./scripts/emergency-shutdown.sh --full-cleanup
```

### Troubleshooting Commands
```bash
# Check deployment status
aws cloudformation describe-stacks --stack-name rag-assistant-ultra

# View recent logs
aws logs tail /aws/lambda/rag-assistant-ultra-query --follow

# Test function directly
aws lambda invoke --function-name rag-assistant-ultra-query test-output.json
```

---

## 🎉 Success Indicators

### ✅ Deployment Complete When You See:
- [ ] CloudFormation stack status: `CREATE_COMPLETE`
- [ ] Lambda function responding to test invocations
- [ ] Gradio UI accessible and functional
- [ ] Document upload and query working
- [ ] Costs within expected range

### 📈 Portfolio Benefits
- **Cloud Architecture Skills** - Demonstrate AWS serverless expertise
- **Cost Optimization** - Show financial awareness and efficiency
- **Monitoring & Operations** - Display production-ready practices
- **Scalability Planning** - Exhibit growth-oriented thinking

---

## 🚀 Next Steps

### After Successful Deployment
1. **Test thoroughly** - Upload documents and test queries
2. **Monitor costs daily** for the first week
3. **Document your architecture** for portfolio/interviews
4. **Plan optimizations** based on usage patterns
5. **Consider upgrades** as your needs grow

### Career Development
- Add to your **GitHub portfolio** with detailed documentation
- Include in **resume** as cloud deployment experience  
- Prepare **interview talking points** about cost optimization
- Plan **advanced features** for future implementations

---

**🎯 Start with Ultra-Budget mode and upgrade as you grow!**

Perfect for students who want to learn AWS without breaking the bank. 💰