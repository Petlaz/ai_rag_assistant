# DEPLOYMENT PLAN

This plan provides a structured path for promoting the AI_RAG stack from local development to production-grade infrastructure on AWS. Today, the system (Ollama, OpenSearch, Gradio app, ingestion worker, and landing page) runs locally via Docker Compose; the steps below ensure the same components can be deployed repeatably and safely in the cloud.

---

## ✅ Pre-Deployment Checklist

- [ ] AWS account with IAM user and CLI configured (`aws configure`)
- [ ] Docker images built locally for all services (`rag-app`, `rag-worker`, `ollama`, `opensearch`, `landing`)
- [ ] `.env` values reviewed and production-safe (no local paths, no plaintext secrets)
- [ ] Domain or subdomain selected (optional, for HTTPS)
- [ ] Sufficient ECS/Fargate memory budget (≥ 8 GiB recommended)

---

## 🔀 Deployment Options

### Option A — AWS ECS Fargate (recommended)
- Fully managed containers with auto-scaling and managed patching
- Higher monthly cost than DIY, but resilient and low maintenance

### Option B — EC2 Instance + Docker Compose
- Single-node host with minimal setup complexity
- Manual scaling, lower redundancy, suitable for testing or low traffic

---

## 🏗️ AWS Resources to Provision (Fargate Path)

- **Amazon ECR** repositories for each container image
- **ECS Cluster** with dedicated Services/Tasks for app, worker, landing, Ollama, OpenSearch
- **Application Load Balancer** routing port 80/443 to the Gradio service (7860)
- **Route 53 hosted zone** for DNS routing
- **AWS Certificate Manager (ACM)** certificates for HTTPS termination
- **CloudWatch Logs & Metrics** for centralised observability

---

## 🚢 Deployment Steps

1. Build and tag Docker images for every service.
2. Push all images to their corresponding Amazon ECR repositories.
3. Create ECS Task Definitions (CPU/memory, env vars, secrets) per service.
4. Deploy Services via AWS CLI, AWS Copilot, Terraform, or CDK pipelines.
5. Validate task health, ALB targets, and service connectivity.
6. Confirm user access at `https://yourdomain.com` (or configured endpoint).

---

## 🔧 Post-Deployment Tasks

- Enable HTTPS using ACM certificates on the ALB.
- Configure CloudWatch metrics, dashboards, and alarms.
- Store environment variables and secrets securely within ECS Task Definitions.
- Run smoke tests to validate ingestion → retrieval → response flows.
- (Optional) Add CI/CD workflows for automated image builds and deployments.

---

## 🔒 Security & Maintenance

- Grant each component least-privilege IAM access.
- Restrict ingress to ports 80/443; block unused ports.
- Schedule weekly cleanup or ECR lifecycle policies for image pruning.
- Keep base images and dependencies patched.
- Back up persistent data (OpenSearch snapshots, analytics CSVs) on a regular cadence.

---

## 🔁 Rollback & Recovery

- Use versioned ECR tags to revert services quickly.
- Back up critical data (e.g., `data/analytics.csv`, OpenSearch indices) before upgrades.
- Document AWS CLI rollback commands inside `/infra/aws/scripts/` for repeatability.

---

## 🚀 Future Enhancements

- **Auto-Scaling & Load Balancing**  
  ECS Service Auto Scaling with ALB for dynamic traffic distribution.

- **Monitoring & Observability**  
  CloudWatch dashboards for CPU/memory/latency metrics; optional OpenTelemetry or AWS X-Ray integration.

- **Data Persistence & Backups**  
  Migrate to Amazon OpenSearch Service or S3-backed storage; automate daily backups.

- **Continuous Deployment (CI/CD)**  
  GitHub Actions or AWS CodePipeline for build/deploy, secrets in AWS Secrets Manager.

- **Serverless & Cost Optimisation**  
  Explore AWS Lambda or Bedrock for infrequent inference; cache frequent responses (S3/DynamoDB).

- **Multi-Model Orchestration**  
  Route between small (Gemma/Mistral) and large (Llama 3 70B) models as needed.

- **Security Enhancements**  
  Enforce HTTPS, tighten IAM, restrict public endpoints, leverage VPC endpoints for internal OpenSearch traffic.

- **Global Access & CDN**  
  Serve the landing page via CloudFront + S3 for worldwide low-latency access.

- **AI Logging & Explainability**  
  Capture SHAP or explainability metrics in CloudWatch for operational transparency.

- **Timeline & Ownership**  
  Track enhancements in `/docs/roadmap/` to mark planned, in-progress, and completed work.

