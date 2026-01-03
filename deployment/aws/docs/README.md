# 📚 AWS Deployment Documentation

*Comprehensive guides for deploying your RAG Assistant to AWS with three cost-optimized deployment modes*

---

## 🎯 Choose Your Deployment Mode

We offer **three deployment modes** optimized for different budgets and use cases:

### 💰 Ultra-Budget Mode ($8-18/month)
**Perfect for:** Students, learning, demos, portfolio projects
- SQLite vector storage (no external DB costs)
- Lambda Function URLs (no API Gateway costs)  
- 24-hour aggressive caching
- Automatic document cleanup

### ⚖️ Balanced Mode ($15-35/month)
**Perfect for:** Small production apps, internship projects
- Pinecone or Chroma vector storage
- API Gateway + Lambda
- Smart caching strategy
- Intelligent cost optimization

### 🚀 Full Mode ($25-68/month)
**Perfect for:** Production apps, showcasing to employers
- OpenSearch Serverless
- Full hybrid search capabilities
- Advanced monitoring and analytics
- High availability setup

---

## 📖 Documentation Overview

This folder contains **everything you need** for a successful AWS deployment, specifically designed for **master students** doing their first cloud deployment.

### 🚀 Start Here
1. **[Infrastructure Setup](infrastructure-setup.md)** - AWS account preparation and prerequisites
2. **[Services Configuration](services-configuration.md)** - Detailed configuration for all deployment modes
3. **[Troubleshooting Guide](troubleshooting.md)** - Solutions for common deployment issues
4. **[Cost Optimization Guide](../COST_OPTIMIZATION.md)** - Student-specific cost strategies

---

## 📋 Documentation Structure

### 1. [Infrastructure Setup](infrastructure-setup.md)
**What it covers:**
- AWS account setup and student credits
- IAM user configuration
- Cost management and budgets
- Region selection and optimization
- Security best practices

**When to use:** Before starting any deployment

### 2. [Services Configuration](services-configuration.md)
**What it covers:**
- Lambda function optimization
- OpenSearch Serverless setup
- Bedrock model configuration
- DynamoDB caching strategy
- API Gateway configuration
- S3 storage optimization

**When to use:** During deployment and optimization

### 3. [Troubleshooting Guide](troubleshooting.md)
**What it covers:**
- Critical deployment failures
- Service-specific issues
- Cost-related problems
- Performance optimization
- Security fixes
- Emergency cleanup procedures

**When to use:** When things go wrong (and they will!)

---

## 🎯 Quick Reference

### Essential Commands
```bash
# Check AWS configuration
aws sts get-caller-identity
aws configure list

# Deploy the stack
./scripts/deploy-student-stack.sh

# Check deployment status
aws cloudformation describe-stacks --stack-name rag-assistant-student

# Monitor costs
aws ce get-cost-and-usage --time-period Start=2026-01-01,End=2026-01-31 --granularity MONTHLY --metrics BlendedCost
```

### Cost Monitoring (Critical for Students!)
- **Set budget alerts at $25, $40, $50**
- **Check costs daily for first week**
- **Use us-east-1 region for lowest prices**
- **Enable S3 lifecycle rules**
- **Cache responses aggressively**

### Support Resources
- **AWS Student Portal**: [AWS Educate](https://aws.amazon.com/education/awseducate/)
- **Pricing Calculator**: [AWS Calculator](https://calculator.aws/)
- **Community Support**: [AWS Forums](https://forums.aws.amazon.com/)

---

## 🎓 Learning Path

### For Your First AWS Deployment:
1. **Start with [Infrastructure Setup](infrastructure-setup.md)** 
   - Configure AWS account and credits
   - Set up billing alerts
   - Test basic service access

2. **Follow the [parent README](../README.md)** 
   - Run the one-click deployment script
   - Monitor the deployment process

3. **Reference [Services Configuration](services-configuration.md)**
   - Understand what each service does
   - Learn optimization techniques
   - Plan for scaling

4. **Keep [Troubleshooting Guide](troubleshooting.md) handy**
   - Bookmark common solutions
   - Know emergency procedures
   - Understand cost controls

### For Job Interviews:
- **Demonstrate cost consciousness**: "Optimized for $15-50/month budget"
- **Show serverless expertise**: "Used Lambda + Bedrock for 70% cost reduction"  
- **Highlight monitoring**: "Implemented comprehensive CloudWatch dashboards"
- **Discuss scalability**: "Designed for traffic growth from 100 to 10K+ requests/day"

---

## 💡 Pro Tips for Students

### Before Deployment:
- ✅ Activate AWS student credits ($100+ recommended)
- ✅ Set up billing alerts BEFORE deploying anything
- ✅ Choose us-east-1 region for lowest costs
- ✅ Read the troubleshooting guide once

### During Deployment:
- 📊 Monitor costs in real-time
- 🔍 Check CloudFormation events if deployment fails
- 📝 Document any issues for your portfolio
- ⏱️ Expect 20-30 minutes for full deployment

### After Deployment:
- 🧪 Test the system thoroughly
- 📈 Monitor performance metrics
- 💰 Review costs weekly
- 🔄 Plan optimizations

---

## 🚀 Quick Start Commands

### Deploy Ultra-Budget Mode ($8-18/month)
```bash
cd /path/to/AI_RAG  
./scripts/deploy-student-stack.sh --mode=ultra-budget --budget=20
```

### Deploy Balanced Mode ($15-35/month) 
```bash
cd /path/to/AI_RAG
./scripts/deploy-student-stack.sh --mode=balanced --budget=40
```

### Deploy Full Mode ($25-68/month)
```bash
cd /path/to/AI_RAG
./scripts/deploy-student-stack.sh --mode=full --budget=70
```

### Get Help
```bash
./scripts/deploy-student-stack.sh --help
```

---

## 🚀 Ready to Deploy?

1. **Complete prerequisite checklist** in [Infrastructure Setup](infrastructure-setup.md)
2. **Choose your deployment mode** based on your budget
3. **Run the deployment script** with your chosen mode
4. **Monitor and optimize** using these guides
5. **Showcase your cloud skills** to potential employers!

**Remember:** Every successful cloud engineer started with their first deployment. You're about to join that community! 🌟