# Technology Stack Reference Guide
**Essential Technologies for ML/AI Engineering Roles**

This guide explains key technologies commonly used in modern ML/AI engineering and how they work together in production systems.

---

## Docker

### **What is Docker?**
- **Definition**: A containerization platform that packages applications and their dependencies into lightweight, portable containers
- **Purpose**: Ensures applications run consistently across different environments (development, staging, production)
- **Key Concept**: "Build once, run anywhere"

### **Core Functions**:
1. **Application Packaging**: Bundles code, runtime, libraries, and dependencies
2. **Environment Isolation**: Each container runs independently without conflicts
3. **Consistency**: Same behavior across different machines and environments
4. **Scalability**: Easy to scale applications up or down
5. **Portability**: Move containers between development, testing, and production

### **In Your RAG Project**:
```dockerfile
# Example: Dockerfile for RAG Assistant
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
EXPOSE 7860
CMD ["python", "deployment/app_gradio.py"]
```

### **Why Important for ML/AI Jobs**:
- **Model Deployment**: Package ML models with exact dependencies
- **Reproducibility**: Ensure model works same way everywhere
- **Microservices**: Break ML systems into manageable components
- **Cloud Deployment**: Standard way to deploy to AWS, GCP, Azure

---

## FastAPI

### **What is FastAPI?**
- **Definition**: A modern, fast Python web framework for building APIs
- **Purpose**: Create RESTful APIs with automatic documentation and validation
- **Key Features**: High performance, automatic OpenAPI docs, type hints

### **Core Functions**:
1. **API Creation**: Build REST endpoints for web applications
2. **Data Validation**: Automatic request/response validation using Python types
3. **Documentation**: Auto-generates interactive API docs (Swagger UI)
4. **Performance**: One of the fastest Python frameworks
5. **Async Support**: Handle concurrent requests efficiently

### **In Your RAG Project**:
```python
# Example: FastAPI endpoint for RAG queries
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI(title="RAG Assistant API")

class QueryRequest(BaseModel):
    question: str
    document_ids: list[str] = None

class QueryResponse(BaseModel):
    answer: str
    sources: list[str]
    confidence: float

@app.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    # Process RAG query
    result = await rag_pipeline.process_query(request.question)
    return QueryResponse(
        answer=result.answer,
        sources=result.sources,
        confidence=result.confidence
    )
```

### **Why Important for ML/AI Jobs**:
- **Model Serving**: Expose ML models as web APIs
- **Integration**: Connect ML backends with frontend applications
- **Microservices**: Create modular ML services
- **Production APIs**: Professional way to deploy ML systems

---

## CI/CD (Continuous Integration/Continuous Deployment)

### **What is CI/CD?**
- **Definition**: A methodology for automating software development, testing, and deployment
- **CI (Continuous Integration)**: Automatically test and integrate code changes
- **CD (Continuous Deployment)**: Automatically deploy tested code to production
- **Purpose**: Reduce manual errors, increase deployment frequency, faster feedback

### **Core Functions**:
1. **Automated Testing**: Run tests automatically on code changes
2. **Code Integration**: Merge changes from multiple developers safely
3. **Automated Deployment**: Deploy applications without manual intervention
4. **Quality Assurance**: Catch bugs early in development process
5. **Rollback Capability**: Quickly revert problematic deployments

### **Typical CI/CD Pipeline**:
```
Code Push → Automated Tests → Build → Deploy to Staging → Deploy to Production
     ↓            ↓              ↓           ↓                    ↓
   GitHub    →  Unit Tests   →  Docker   →  Test Env     →    Live System
             →  Integration  →  Package  →  Validation   →    Monitoring
```

### **In ML/AI Context**:
1. **Model Validation**: Automatically test model performance
2. **Data Pipeline Testing**: Validate data processing steps  
3. **A/B Testing**: Deploy multiple model versions safely
4. **Model Monitoring**: Track model performance in production
5. **Automated Retraining**: Retrain models when performance degrades

### **Why Important for ML/AI Jobs**:
- **MLOps**: Essential for production ML systems
- **Reliability**: Reduce deployment risks for ML models
- **Scalability**: Handle multiple model versions and experiments
- **Collaboration**: Multiple data scientists can work together safely

---

## GitHub Actions

### **What is GitHub Actions?**
- **Definition**: GitHub's built-in CI/CD platform that automates workflows
- **Purpose**: Implement CI/CD directly within GitHub repositories
- **Key Feature**: Event-driven workflows triggered by repository events

### **Core Functions**:
1. **Workflow Automation**: Run scripts on code pushes, pull requests, etc.
2. **Testing Automation**: Automatically run test suites
3. **Build Automation**: Compile/package applications automatically
4. **Deployment Automation**: Deploy to cloud platforms
5. **Integration**: Connect with external services and APIs

### **Example Workflow for ML Project**:
```yaml
# .github/workflows/ml-pipeline.yml
name: ML Model Pipeline

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test-model:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    
    - name: Set up Python
      uses: actions/setup-python@v3
      with:
        python-version: 3.11
        
    - name: Install dependencies
      run: |
        pip install -r requirements.txt
        
    - name: Run model tests
      run: |
        python -m pytest tests/test_model_performance.py
        
    - name: Validate model metrics
      run: |
        python scripts/validate_model_performance.py
        
    - name: Deploy to AWS
      if: github.ref == 'refs/heads/main'
      run: |
        ./scripts/deploy-to-aws.sh
```

### **In Your RAG Project**:
- **Model Testing**: Test embedding models and retrieval performance
- **Integration Testing**: Test full RAG pipeline end-to-end
- **Deployment**: Automatically deploy to AWS when code is merged
- **Performance Monitoring**: Track metrics and alert on degradation

### **Why Important for ML/AI Jobs**:
- **Industry Standard**: Most companies use GitHub Actions or similar
- **Automation Skills**: Shows you understand modern development practices
- **MLOps**: Essential for production ML systems
- **Efficiency**: Reduces manual work and errors

---

## MLflow

### **What is MLflow?**
- **Definition**: An open-source platform for managing machine learning lifecycle
- **Purpose**: Track experiments, version models, and manage deployments
- **Key Components**: Tracking, Projects, Models, Registry

### **Core Functions**:
1. **Experiment Tracking**: Log parameters, metrics, and artifacts
2. **Model Versioning**: Track different versions of ML models
3. **Model Registry**: Central repository for production models
4. **Reproducibility**: Recreate experiments and results
5. **Deployment**: Deploy models to various platforms

### **MLflow Components**:

#### **1. MLflow Tracking**
```python
# Track ML experiments
import mlflow
import mlflow.sklearn

with mlflow.start_run():
    # Log parameters
    mlflow.log_param("embedding_model", "all-MiniLM-L6-v2")
    mlflow.log_param("bm25_weight", 0.7)
    
    # Log metrics
    mlflow.log_metric("precision_at_5", 0.72)
    mlflow.log_metric("mrr", 0.80)
    
    # Log model
    mlflow.sklearn.log_model(retrieval_model, "rag_model")
    
    # Log artifacts
    mlflow.log_artifact("results/evaluation_report.html")
```

#### **2. MLflow Models**
```python
# Load and use tracked models
import mlflow.pyfunc

# Load production model
model = mlflow.pyfunc.load_model("models:/rag_assistant/Production")

# Make predictions
predictions = model.predict(queries)
```

#### **3. MLflow Registry**
```python
# Register model for production
from mlflow.tracking import MlflowClient

client = MlflowClient()
client.create_registered_model("rag_assistant")

# Promote model to production
client.transition_model_version_stage(
    name="rag_assistant",
    version=1,
    stage="Production"
)
```

### **In Your RAG Project**:
- **Embedding Model Comparison**: Track performance of different embedding models
- **A/B Testing**: Compare retrieval configurations systematically
- **Performance Monitoring**: Track metrics over time
- **Model Versioning**: Manage different versions of your RAG system

### **Why Important for ML/AI Jobs**:
- **Experiment Management**: Essential skill for ML engineers
- **Model Lifecycle**: Shows understanding of production ML
- **Reproducibility**: Critical for reliable ML systems
- **Collaboration**: Standard tool for ML teams

---

## A/B Testing

### **What is A/B Testing?**
- **Definition**: A statistical method for comparing two or more versions of a system to determine which performs better
- **Purpose**: Make data-driven decisions about system improvements
- **Key Concept**: Randomly divide users/traffic between different versions and measure performance differences

### **Core Functions**:
1. **Hypothesis Testing**: Scientifically test whether changes improve performance
2. **Statistical Validation**: Ensure observed differences are statistically significant
3. **Risk Mitigation**: Test changes on small groups before full deployment
4. **Performance Comparison**: Compare multiple approaches simultaneously
5. **Decision Making**: Provide quantitative evidence for business/technical decisions

### **A/B Testing Process**:
```
1. Hypothesis Formation → 2. Experiment Design → 3. Implementation → 4. Data Collection → 5. Statistical Analysis → 6. Decision
     ↓                        ↓                      ↓                 ↓                    ↓                      ↓
"Model A will           Split traffic         Deploy both         Collect metrics     Calculate p-values    Choose winner
improve precision       50/50 between        versions in         for both groups     test significance     deploy to 100%
by 10%"                Model A & B           production                                                    of traffic"
```

### **In Your RAG Project Context**:

#### **Example: Embedding Model A/B Test**
```python
# A/B test different embedding models
import mlflow
import scipy.stats as stats

# Configuration A: Current model
config_a = {
    "embedding_model": "all-MiniLM-L6-v2",
    "bm25_weight": 0.7,
    "semantic_weight": 0.3
}

# Configuration B: Better model
config_b = {
    "embedding_model": "all-mpnet-base-v2", 
    "bm25_weight": 0.6,
    "semantic_weight": 0.4
}

# Run A/B test
def run_ab_test(test_queries, config_a, config_b):
    # Split queries randomly
    import random
    random.shuffle(test_queries)
    split_point = len(test_queries) // 2
    
    queries_a = test_queries[:split_point]
    queries_b = test_queries[split_point:]
    
    # Test both configurations
    results_a = evaluate_rag_system(queries_a, config_a)
    results_b = evaluate_rag_system(queries_b, config_b)
    
    # Statistical analysis
    precision_a = results_a['precision_at_5']
    precision_b = results_b['precision_at_5']
    
    # T-test for statistical significance
    t_stat, p_value = stats.ttest_ind(precision_a, precision_b)
    
    # Log to MLflow
    with mlflow.start_run():
        mlflow.log_param("test_type", "embedding_model_ab_test")
        mlflow.log_metric("config_a_precision", np.mean(precision_a))
        mlflow.log_metric("config_b_precision", np.mean(precision_b))
        mlflow.log_metric("p_value", p_value)
        mlflow.log_metric("effect_size", np.mean(precision_b) - np.mean(precision_a))
    
    return {
        "winner": "B" if np.mean(precision_b) > np.mean(precision_a) and p_value < 0.05 else "A",
        "p_value": p_value,
        "effect_size": np.mean(precision_b) - np.mean(precision_a),
        "statistically_significant": p_value < 0.05
    }
```

#### **Multi-variant Testing (A/B/C/D)**:
```python
# Test multiple retrieval configurations simultaneously
retrieval_configs = {
    "baseline": {"bm25_weight": 0.7, "semantic_weight": 0.3, "top_k": 20},
    "balanced": {"bm25_weight": 0.5, "semantic_weight": 0.5, "top_k": 25},
    "semantic_heavy": {"bm25_weight": 0.3, "semantic_weight": 0.7, "top_k": 30},
    "optimized": {"bm25_weight": 0.6, "semantic_weight": 0.4, "top_k": 22}
}

def run_multivariant_test(test_queries, configs):
    results = {}
    
    # Randomly assign queries to different configurations
    import random
    random.shuffle(test_queries)
    queries_per_config = len(test_queries) // len(configs)
    
    for i, (config_name, config) in enumerate(configs.items()):
        start_idx = i * queries_per_config
        end_idx = start_idx + queries_per_config
        config_queries = test_queries[start_idx:end_idx]
        
        # Evaluate configuration
        config_results = evaluate_rag_system(config_queries, config)
        results[config_name] = config_results
        
        # Log to MLflow
        with mlflow.start_run():
            mlflow.log_param("config_name", config_name)
            mlflow.log_params(config)
            mlflow.log_metric("precision_at_5", np.mean(config_results['precision_at_5']))
            mlflow.log_metric("mrr", np.mean(config_results['mrr']))
    
    # Statistical comparison using ANOVA
    from scipy.stats import f_oneway
    precision_scores = [results[config]['precision_at_5'] for config in configs]
    f_stat, p_value = f_oneway(*precision_scores)
    
    return results, p_value
```

### **A/B Testing Best Practices**:

#### **1. Statistical Rigor**:
```python
# Calculate required sample size
from scipy.stats import norm

def calculate_sample_size(baseline_rate, minimum_detectable_effect, alpha=0.05, power=0.8):
    """Calculate minimum sample size for A/B test"""
    z_alpha = norm.ppf(1 - alpha/2)  # Two-tailed test
    z_beta = norm.ppf(power)
    
    p1 = baseline_rate
    p2 = baseline_rate + minimum_detectable_effect
    p_pooled = (p1 + p2) / 2
    
    sample_size = (2 * p_pooled * (1 - p_pooled) * (z_alpha + z_beta)**2) / (p2 - p1)**2
    return int(sample_size)

# Example: Need to detect 5% improvement in precision
baseline_precision = 0.72
min_effect = 0.05  # Want to detect 5% improvement
required_samples = calculate_sample_size(baseline_precision, min_effect)
print(f"Need {required_samples} samples per group")
```

#### **2. Randomization and Controls**:
```python
# Proper randomization
import hashlib

def assign_to_group(user_id, test_name):
    """Consistent assignment of users to A/B test groups"""
    hash_input = f"{test_name}_{user_id}".encode()
    hash_value = int(hashlib.md5(hash_input).hexdigest(), 16)
    return "A" if hash_value % 2 == 0 else "B"

# Example: User always gets same experience
user_group = assign_to_group("user_123", "embedding_model_test")
```

### **Integration with MLOps Pipeline**:
```python
# A/B test as part of model deployment
def deploy_with_ab_test(new_model, current_model, traffic_split=0.1):
    """Deploy new model with A/B testing"""
    
    # Start A/B test experiment in MLflow
    with mlflow.start_run(run_name="ab_test_deployment"):
        mlflow.log_param("new_model_version", new_model.version)
        mlflow.log_param("current_model_version", current_model.version)
        mlflow.log_param("traffic_split", traffic_split)
        
        # Deploy both models
        current_model.deploy(traffic_percentage=1.0 - traffic_split)
        new_model.deploy(traffic_percentage=traffic_split)
        
        # Monitor for statistical significance
        monitor_ab_test(current_model, new_model, 
                       success_metric="precision_at_5",
                       minimum_effect=0.05)
```

### **Why A/B Testing is Critical for ML/AI Jobs**:

#### **1. Data-Driven Decision Making**:
- **Objective Evaluation**: Remove bias and prove model improvements quantitatively
- **Risk Management**: Test changes safely before full deployment
- **Resource Optimization**: Focus development on changes that actually improve performance

#### **2. Production ML Skills**:
- **Experiment Design**: Shows understanding of statistical methodology
- **Model Comparison**: Essential for choosing between ML approaches
- **Production Testing**: Real-world skill for deploying ML systems

#### **3. Business Impact**:
- **ROI Measurement**: Quantify the business value of ML improvements
- **User Experience**: Ensure model changes improve user satisfaction
- **Confidence Building**: Provide stakeholders with statistical proof of improvements

### **Common A/B Testing Metrics in RAG Systems**:

| Metric | Purpose | Statistical Test |
|--------|---------|-----------------|
| **Precision@K** | Relevance of top results | t-test, Mann-Whitney U |
| **Mean Reciprocal Rank (MRR)** | Ranking quality | t-test, Wilcoxon signed-rank |
| **Query Response Time** | Performance | t-test |
| **User Satisfaction** | User experience | Chi-square, t-test |
| **Click-Through Rate** | Result relevance | Chi-square test |

### **Interview Questions About A/B Testing**:

**Q: "How would you A/B test a new ML model?"**
**A**: "I would design a randomized experiment splitting traffic between the current and new models, define success metrics like precision@5, calculate required sample sizes for statistical significance, monitor both versions with MLflow, and use statistical tests to determine if the new model significantly outperforms the current one."

**Q: "What's the difference between A/B testing and model evaluation?"**
**A**: "Model evaluation tests performance on historical data, while A/B testing compares models in production with real users. A/B testing accounts for real-world factors like data drift, user behavior changes, and system interactions that offline evaluation might miss."

**Q: "How do you ensure A/B test validity?"**
**A**: "Key factors include proper randomization, sufficient sample sizes, controlling for confounding variables, avoiding peeking at results early, and using appropriate statistical tests. I use MLflow to track all these factors and ensure reproducible analysis."

---

## How These Technologies Work Together

### **In a Production ML System**:

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│   Source    │    │    CI/CD    │    │   Docker    │    │   FastAPI   │
│    Code     │───▶│   Pipeline  │───▶│  Container  │───▶│   Service   │
│  (GitHub)   │    │(GitHub      │    │             │    │             │
│             │    │ Actions)    │    │             │    │             │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                           │                                      │
                           ▼                                      │
                   ┌─────────────┐                               │
                   │   MLflow    │                               │
                   │  Tracking   │◄──────────────────────────────┘
                   │   Server    │
                   └─────────────┘
```

### **Example Workflow in Your RAG Project**:

1. **Development**: Write code locally, track experiments with MLflow
2. **Version Control**: Push code to GitHub
3. **CI/CD**: GitHub Actions automatically:
   - Run tests on the RAG pipeline
   - Validate model performance metrics
   - Build Docker container with optimized model
4. **Deployment**: Deploy FastAPI service in Docker container to AWS
5. **Monitoring**: MLflow tracks production metrics and model performance
6. **Iteration**: Based on monitoring data, improve and redeploy

### **For Job Interviews**:

**Common Questions and How to Answer**:

**Q: "How would you deploy an ML model to production?"**
**A**: "I would containerize the model using Docker to ensure consistency, create a FastAPI service to expose it as an API, use MLflow to track the model version and performance, and set up a CI/CD pipeline with GitHub Actions to automate testing and deployment."

**Q: "How do you manage ML experiments?"**
**A**: "I use MLflow to track all experiments, logging parameters, metrics, and model artifacts. This allows me to compare different approaches systematically and reproduce successful experiments."

**Q: "What's your experience with containerization?"**
**A**: "I use Docker to package ML applications with their dependencies, ensuring they run consistently across development, testing, and production environments. This is especially important for ML models that depend on specific library versions."

---

## Technology Comparison Summary

| Technology | Primary Purpose | Use Case in ML/AI | Key Benefit |
|------------|----------------|-------------------|-------------|
| **Docker** | Containerization | Package ML models with dependencies | Consistency across environments |
| **FastAPI** | Web API Framework | Serve ML models as APIs | High-performance model serving |
| **CI/CD** | Automation Methodology | Automate ML testing and deployment | Reliable, repeatable deployments |
| **GitHub Actions** | Automation Platform | Implement CI/CD for ML projects | Integrated with code repository |
| **MLflow** | ML Lifecycle Management | Track experiments and manage models | Reproducible ML development |

## Skills for Your Resume

Based on this knowledge, you can confidently list:

**Technical Skills**:
- **Containerization**: Docker for ML model deployment
- **API Development**: FastAPI for model serving
- **MLOps**: MLflow for experiment tracking and model management
- **DevOps**: GitHub Actions CI/CD for automated deployment
- **Cloud Deployment**: AWS integration with containerized ML services

**Project Experience**:
- "Implemented MLflow experiment tracking for systematic RAG optimization"
- "Built FastAPI service for production RAG model deployment"
- "Designed CI/CD pipeline using GitHub Actions for automated ML model testing"
- "Containerized ML applications using Docker for consistent deployment"
- "Integrated MLOps practices for reproducible model development lifecycle"

---

This comprehensive understanding of these technologies demonstrates modern ML engineering practices and will serve you well in interviews for Machine Learning Engineer, AI Engineer, GenAI Engineer, and Data Scientist positions.