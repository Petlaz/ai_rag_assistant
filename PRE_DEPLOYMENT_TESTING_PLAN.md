# Pre-Deployment Testing Plan
**AI RAG Assistant - Optimization Before AWS Deployment**

**Purpose**: Complete comprehensive testing and optimization before deploying to AWS to ensure optimal performance and cost efficiency.

**Timeline**: 8 weeks of testing and optimization → AWS Ultra-Budget Deployment

---

## Phase 1: Baseline & Scale Testing (Week 1-2)

### 1.1 Establish Current Baseline Performance
**Objective**: Document current system performance as reference point

```bash
# Create evaluation environment
mkdir -p data/evaluation results
cd /Users/peter/Desktop/ai_rag_assistant

# Run baseline evaluation with existing script
python scripts/eval_retrieval.py \
  data/samples/queries.jsonl \
  --top-k 10 \
  --output results/baseline_performance.json \
  --detailed-metrics

# Document current metrics
echo "Current Baseline (March 2026):" >> results/baseline_performance.txt
echo "- Precision@5: 0.72" >> results/baseline_performance.txt
echo "- MRR: 0.80" >> results/baseline_performance.txt
echo "- Test Date: $(date)" >> results/baseline_performance.txt
```

**Success Criteria**:
- Baseline metrics documented
- Evaluation framework working correctly
- Test environment fully functional

### 1.2 Scale Testing: 50-100 Query Dataset
**Objective**: Validate performance consistency on larger sample

**Implementation**:
```bash
# Expand test dataset (memory-conscious for M1 Mac)
python scripts/generate_test_queries.py \
  --count 75 \
  --batch-size 10 \
  --domains "general,academic" \
  --output data/evaluation/scale_test_set.jsonl

# Run scale evaluation in batches (8GB RAM optimization)
python scripts/eval_retrieval.py \
  data/evaluation/scale_test_set.jsonl \
  --top-k 10 \
  --batch-size 5 \
  --memory-limit 6GB \
  --output results/scale_test_results.json

# Statistical analysis
python scripts/analyze_eval_results.py \
  results/scale_test_results.json \
  --confidence-interval 0.95 \
  --variance-analysis \
  --compare-baseline results/baseline_performance.json
```

**Success Criteria**:
- Precision@5 maintains ≥ 0.65 (vs 0.72 baseline)
- MRR stays ≥ 0.75 (vs 0.80 baseline) 
- Performance variance < 10%
- No memory issues on M1 Mac

### 1.3 Domain-Specific Testing
**Objective**: Ensure robust cross-domain performance

**Test Domains** (25 queries each):
- Computer Science & AI
- Life Sciences & Medicine
- Physics & Engineering  
- Social Sciences

**Implementation**:
```bash
# Create domain-specific test sets
python scripts/create_domain_queries.py \
  --domains "cs_ai,life_sciences,physics,social_sciences" \
  --queries-per-domain 25 \
  --difficulty-levels "basic,intermediate,advanced" \
  --output-dir data/evaluation/domains/

# Evaluate each domain
for domain in cs_ai life_sciences physics social_sciences; do
    echo "Testing domain: $domain"
    python scripts/eval_retrieval.py \
      data/evaluation/domains/${domain}_queries.jsonl \
      --domain $domain \
      --output results/domain_${domain}_results.json
done

# Cross-domain performance analysis
python scripts/domain_performance_analysis.py \
  results/domain_*.json \
  --output results/domain_comparison_report.html
```

**Success Criteria**:
- All domains achieve Precision@5 > 0.60
- No single domain drops below 0.50 MRR
- Identify domain-specific patterns
- Total testing cost < $5 (using local models when possible)

---

## Phase 2: Model Optimization (Week 3-4)

### 2.1 Embedding Model Comparison
**Current**: `all-MiniLM-L6-v2` (384 dimensions)

**M1 Mac Optimized Candidates**:
- `all-mpnet-base-v2` (768 dims) - Better quality, good M1 performance
- `e5-small-v2` (384 dims) - Latest generation, memory efficient
- `gte-small` (384 dims) - ARM64 optimized for local inference

**Implementation**:
```bash
# Model comparison framework (sequential to avoid memory issues)
python scripts/embedding_model_comparison.py \
  --models "all-MiniLM-L6-v2,all-mpnet-base-v2,e5-small-v2" \
  --test-set data/evaluation/scale_test_set.jsonl \
  --batch-size 8 \
  --max-memory-gb 6 \
  --metrics "precision,recall,mrr,inference_speed" \
  --output results/embedding_comparison.json

# Performance vs cost analysis
python scripts/analyze_embedding_tradeoffs.py \
  results/embedding_comparison.json \
  --include-memory-usage \
  --include-inference-speed \
  --m1-optimized \
  --output results/embedding_recommendations.json
```

**Success Criteria**:
- Identify best performance/cost ratio
- Inference speed < 100ms per query on M1
- Memory usage < 4GB during embedding generation
- Document size vs quality trade-offs

### 2.2 Re-ranking Strategy Optimization
**Current**: PassThroughReranker (no re-ranking)

**Test Strategies** (local-first to minimize costs):
- Cross-encoder re-ranking (ms-marco-MiniLM-L-6-v2)
- LLM-based re-ranking (local Ollama models)
- Hybrid scoring (BM25 + semantic + relevance)

**Implementation**:
```bash
# Test re-ranking strategies locally first
python scripts/reranking_evaluation.py \
  --strategies "cross_encoder,ollama_llm,hybrid_scoring" \
  --test-set data/evaluation/scale_test_set.jsonl \
  --local-models-only \
  --baseline results/baseline_performance.json \
  --output results/reranking_comparison.json

# Cost-benefit analysis
python scripts/reranking_cost_analysis.py \
  results/reranking_comparison.json \
  --latency-threshold 200ms \
  --cost-threshold 0.001 \
  --output results/reranking_recommendations.json
```

**Target Improvements**:
- Precision@5: 0.72 → 0.78+ (8% improvement)
- MRR: 0.80 → 0.85+ (6% improvement)
- Latency increase < 50ms
- Additional cost < $2/month

---

## Phase 3: Configuration A/B Testing (Week 5)

### 3.1 Retrieval Configuration Optimization

**Test Configurations**:

```yaml
# configs/retrieval_variants.yaml
baseline:
  name: "current_baseline"
  bm25_weight: 0.7
  semantic_weight: 0.3
  top_k_retrieval: 20
  reranker: "passthrough"

balanced:
  name: "balanced_hybrid"
  bm25_weight: 0.5
  semantic_weight: 0.5
  top_k_retrieval: 25
  reranker: "cross_encoder"

semantic_heavy:
  name: "semantic_focused"
  bm25_weight: 0.3
  semantic_weight: 0.7
  top_k_retrieval: 30
  reranker: "llm_based"

optimized:
  name: "best_embedding_model"
  bm25_weight: 0.6
  semantic_weight: 0.4
  embedding_model: "WINNER_FROM_PHASE_2"
  top_k_retrieval: 25
  reranker: "WINNER_FROM_PHASE_2"
```

**Implementation**:
```bash
# A/B testing framework
python scripts/ab_test_retrieval.py \
  --configs configs/retrieval_variants.yaml \
  --test-set data/evaluation/scale_test_set.jsonl \
  --metrics "precision,recall,mrr,latency,cost" \
  --statistical-tests \
  --output results/ab_test_final_results.json

# Statistical significance analysis
python scripts/statistical_analysis.py \
  results/ab_test_final_results.json \
  --alpha 0.05 \
  --bonferroni-correction \
  --report results/statistical_significance_report.pdf
```

**Success Criteria**:
- Identify statistically significant improvements
- Optimal configuration balances performance vs cost
- All tests demonstrate statistical significance (p < 0.05)

### 3.2 Statistical Analysis and Best Configuration Selection

**Statistical Significance Testing**:
```bash
# Statistical significance analysis
python scripts/statistical_analysis.py \
  results/ab_test_final_results.json \
  --alpha 0.05 \
  --bonferroni-correction \
  --report results/statistical_significance_report.pdf

# Select and document winning configuration
python scripts/select_best_config.py \
  --results results/ab_test_final_results.json \
  --criteria "performance,cost,latency" \
  --output configs/winning_configuration.yaml
```

---

## Phase 4: MLOps & CI/CD Integration (Week 6-7)

### 4.1 MLflow Experiment Tracking Setup
**Objective**: Implement professional ML experiment tracking for all optimization phases

**MLflow Integration**:
```bash
# Install MLflow
pip install mlflow>=2.10.0

# Setup MLflow tracking
mkdir -p mlruns
python scripts/setup_mlflow_tracking.py \
  --tracking-uri ./mlruns \
  --experiment-name "rag-optimization-2026" \
  --register-baseline-metrics

# Track embedding model experiments
python scripts/embedding_model_comparison.py \
  --mlflow-tracking \
  --experiment-name "embedding-models" \
  --log-artifacts \
  --log-model-performance

# Track A/B test results
python scripts/ab_test_retrieval.py \
  --mlflow-tracking \
  --experiment-name "retrieval-configs" \
  --compare-runs \
  --tag-best-model
```

**MLflow Benefits for Your Portfolio**:
- Professional experiment management
- Model versioning and comparison
- Performance metric visualization
- Reproducible ML workflows
- Industry-standard MLOps practice

### 4.2 GitHub Actions CI/CD Pipeline
**Objective**: Implement automated testing and deployment pipeline

**CI/CD Pipeline Structure**:
```yaml
# .github/workflows/ml-pipeline.yml
name: RAG System CI/CD Pipeline

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test-and-validate:
    runs-on: ubuntu-latest
    steps:
    - name: Checkout code
    - name: Setup Python environment
    - name: Install dependencies
    - name: Run unit tests
    - name: Validate model performance
    - name: Run integration tests
    - name: Generate test reports

  model-validation:
    needs: test-and-validate
    runs-on: ubuntu-latest
    steps:
    - name: Run baseline evaluation
    - name: Compare against performance thresholds
    - name: Log results to MLflow
    - name: Create performance report

  deploy-to-aws:
    needs: [test-and-validate, model-validation]
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    steps:
    - name: Deploy to AWS Lambda
    - name: Run smoke tests
    - name: Update deployment status
```

### 4.3 AWS Deployment Preparation

**Configuration Optimization for Ultra-Budget Mode**:
```bash
# Prepare optimized configuration for AWS
python scripts/prepare_aws_config.py \
  --winning-config results/winning_configuration.yaml \
  --deployment-mode ultra-budget \
  --lambda-memory-mb 1024 \
  --sqlite-optimization \
  --output configs/aws_optimized_config.yaml

# Create deployment package with optimized models
python scripts/create_deployment_package.py \
  --config configs/aws_optimized_config.yaml \
  --include-models \
  --compress \
  --output deployment/optimized_lambda_package.zip
```

## Phase 5: Final Validation & Deployment (Week 8)

### 5.1 Cost Estimation & Budget Setup

**Final Cost Analysis**:
```bash
# Estimate deployment costs with optimized configuration
python scripts/estimate_aws_costs.py \
  --config configs/aws_optimized_config.yaml \
  --usage-patterns configs/expected_usage.yaml \
  --deployment-mode ultra-budget \
  --output results/cost_estimates.json
```

### 5.2 Final Performance Validation & Deployment

**Comprehensive Final Validation**:
```bash
# Final validation with winning configuration
python scripts/comprehensive_validation.py \
  --config results/winning_configuration.yaml \
  --test-suites "scale,domain,stress,memory" \
  --duration 2hours \
  --report results/final_validation_report.pdf

# Deploy to AWS Ultra-Budget mode
./scripts/deploy-student-stack.sh \
  --mode=ultra-budget \
  --budget=20 \
  --config configs/aws_optimized_config.yaml
```

**Expected Optimized Costs**:
- Lambda (optimized): $3-8/month
- S3 storage: $1-2/month  
- DynamoDB (caching): $1-3/month
- Bedrock (reduced by optimizations): $2-5/month
- **Total**: $7-18/month (vs $8-18 baseline)

---

## Success Metrics & Final Criteria

### Performance Targets (Post-Optimization)
| Metric | Baseline | Target | Minimum |
|--------|----------|--------|---------|
| Precision@5 | 0.72 | 0.78+ | 0.74 |
| MRR | 0.80 | 0.85+ | 0.82 |
| Query Latency (p95) | TBD | <2s | <3s |
| Memory Usage (M1) | TBD | <6GB | <8GB |
| Monthly Cost | $8-18 | $7-15 | <$20 |

### Deployment Readiness Checklist
- [ ] All performance targets achieved
- [ ] Statistical significance validated
- [ ] M1 Mac compatibility confirmed
- [ ] AWS configuration optimized
- [ ] Cost estimates within budget
- [ ] Deployment package prepared
- [ ] Rollback plan documented
- [ ] Portfolio materials prepared

---

## Implementation Schedule

| Week | Focus | Key Deliverables |
|------|-------|------------------|
| Week 1 | Baseline + Scale Testing | Documented baseline, 75-query evaluation |
| Week 2 | Domain Testing | 4 domain evaluations, cross-domain analysis |
| Week 3 | Embedding Models | Model comparison, recommendations |
| Week 4 | Re-ranking Optimization | Strategy comparison, cost analysis |
| Week 5 | A/B Configuration Testing | Statistical validation, winning config |
| Week 6 | MLflow + GitHub Actions | Experiment tracking, CI/CD pipeline |
| Week 7 | Final Validation + AWS Prep | MLOps integration, deployment package |
| Week 8 | Deployment + Portfolio | AWS deployment, interview materials |

---

## Files to Create for This Plan

```bash
# Testing scripts (check if exist, create if needed)
touch scripts/generate_test_queries.py
touch scripts/analyze_eval_results.py
touch scripts/create_domain_queries.py
touch scripts/embedding_model_comparison.py
touch scripts/reranking_evaluation.py
touch scripts/ab_test_retrieval.py
touch scripts/comprehensive_validation.py
touch scripts/prepare_aws_config.py
touch scripts/estimate_aws_costs.py

# MLOps scripts (NEW - for portfolio enhancement)
touch scripts/setup_mlflow_tracking.py
touch scripts/mlflow_model_registry.py
touch scripts/performance_monitoring.py
touch scripts/automated_retraining.py

# CI/CD configuration (NEW - shows DevOps skills)
mkdir -p .github/workflows
touch .github/workflows/ml-pipeline.yml
touch .github/workflows/model-validation.yml
touch .github/workflows/deploy-aws.yml

# Configuration files
mkdir -p configs
touch configs/retrieval_variants.yaml
touch configs/expected_usage.yaml
touch configs/mlflow_config.yaml
touch configs/performance_thresholds.yaml

# Results directory
mkdir -p results mlruns
```

---

**Next Step**: Start with Week 1 baseline testing to establish current performance benchmarks, then proceed systematically through each optimization phase.

**Advantages of This MLOps-Enhanced Approach**:
- **Technical Excellence**: Maximizes performance before deployment costs begin
- **Professional MLOps**: Demonstrates industry-standard practices (MLflow + CI/CD)
- **Portfolio Strength**: Shows modern ML engineering skills employers want
- **Statistical Rigor**: Ensures validity of improvements with proper tracking
- **Deployment Ready**: Automated testing and deployment pipeline
- **Interview Material**: Rich technical discussions about MLOps choices

## Why This Approach Perfect for Your Target Roles:

### **Machine Learning Engineer**
- **MLflow**: Shows you understand ML experimentation and model lifecycle
- **A/B Testing**: Demonstrates statistical rigor in model evaluation  
- **Performance Optimization**: Shows ability to improve ML system performance
- **Automated Testing**: Validates models systematically before deployment

### **AI Engineer** 
- **RAG System**: Cutting-edge AI architecture with LLMs and vector search
- **Hybrid Retrieval**: Advanced AI technique combining sparse and dense retrieval
- **Cost Optimization**: Shows practical AI deployment considerations
- **Integration**: End-to-end AI system with multiple components

### **GenAI Engineer**
- **LLM Integration**: Ollama/Bedrock integration for generative AI
- **RAG Pipeline**: Modern GenAI architecture for knowledge-grounded generation
- **Prompt Engineering**: Research-focused prompts with safety guardrails
- **Vector Search**: Core GenAI technology for retrieval-augmented generation

### **Data Scientist**
- **Statistical Analysis**: Proper significance testing, confidence intervals
- **Experiment Design**: Systematic A/B testing methodology
- **Performance Metrics**: Precision@K, MRR, comprehensive evaluation
- **Domain Analysis**: Cross-domain performance evaluation (CS, medicine, etc.)

---

**Skills Demonstrated for Job Applications**:
- **MLOps**: MLflow experiment tracking, model versioning
- **DevOps**: GitHub Actions CI/CD, automated testing
- **Cloud Engineering**: AWS deployment with infrastructure as code
- **Data Science**: Statistical analysis, A/B testing, performance optimization
- **Software Engineering**: Clean code, testing, documentation

**Cost During Testing**: ~$5-15 total (mostly local, minimal cloud usage for validation)

---

## Executive Summary

This 8-week pre-deployment testing plan provides a systematic approach to optimizing the AI RAG Assistant before AWS deployment. The plan demonstrates modern MLOps practices essential for ML engineering roles:

**Key Phases**:
- **Weeks 1-2**: Baseline establishment and scale testing
- **Weeks 3-4**: Model optimization (embedding models, re-ranking)  
- **Week 5**: A/B testing and configuration optimization
- **Weeks 6-7**: MLOps integration (MLflow, GitHub Actions CI/CD)
- **Week 8**: Final deployment and portfolio preparation

**Professional Skills Demonstrated**:
- Statistical rigor with A/B testing and significance analysis
- MLOps practices with MLflow experiment tracking
- DevOps automation with GitHub Actions CI/CD
- Cost optimization strategies for production deployment
- Systematic performance improvement methodology

**Portfolio Value**: Creates a comprehensive case study showcasing end-to-end ML system optimization, perfect for demonstrating practical skills to potential employers in Machine Learning Engineer, AI Engineer, GenAI Engineer, and Data Scientist roles.