# Scripts Directory Organization

This directory contains all project scripts organized by development phases for better maintainability and scalability.

## Directory Structure

```
scripts/
├── README.md                    # This file - Project-wide script organization guide
├── eval_retrieval.py           # Core retrieval evaluation functionality
├── ingest_watch.py              # Document ingestion monitoring and automation
├── run_ingestion.py             # Document ingestion pipeline orchestration  
├── smoke_test.py                # Quick system validation and health checks
├── ab_testing/experiment_pipeline.py # A/B testing & parameter optimization
├── m1_optimization.py           # M1/M2 Mac hardware optimization
├── optimization/performance_cost_analysis.py # Performance vs cost trade-off analysis
│
├── evaluation/                  # Phase 1: Baseline & Scale Testing
│   ├── generate_test_queries.py # Query expansion & synthetic datasets
│   ├── analyze_eval_results.py  # Statistical analysis & confidence intervals
│   ├── create_domain_queries.py # Domain-specific query generation
│   ├── domain_performance_analysis.py # Cross-domain analysis framework
│   ├── baseline_evaluation.py  # Core RAG evaluation with statistics
│   └── run_baseline_evaluation.py # Baseline evaluation master orchestration script
│
├── optimization/                # Phase 2: Model Optimization
│   ├── embedding_model_comparison.py # Embedding model performance comparison
│   ├── analyze_embedding_tradeoffs.py # Performance vs cost trade-off analysis
│   ├── reranking_evaluation.py     # Re-ranking strategy evaluation
│   ├── reranking_cost_analysis.py  # Cost-benefit analysis framework
│   └── run_model_optimization.py  # Model optimization master orchestration script
│
├── ab_testing/                  # A/B Testing Framework
│   ├── ab_test_retrieval.py     # A/B testing framework with statistical validation
│   ├── statistical_analysis.py  # Statistical significance and confidence intervals
│   └── select_best_config.py    # Intelligent configuration selection
│
├── mlops/                       # MLOps Infrastructure
│   ├── setup_mlops_pipeline.py  # MLOps pipeline setup and configuration
│   ├── model_monitoring.py      # Model performance monitoring and drift detection
│   └── automated_retraining.py  # Automated retraining pipeline
│
├── monitoring/                  # Production Monitoring
│   ├── production_monitoring.py # Production monitoring dashboard setup
│   ├── alerting_system.py       # Automated alert configuration and management
│   └── log_analysis.py          # Comprehensive log analysis framework
│
└── deployment/                  # Production Deployment
    ├── blue_green_deploy.py     # Blue-green deployment with zero downtime
    ├── rollback_system.py       # Automated rollback and recovery system
    └── production_validation.py # Production validation and health checks
```

## Phase-Based Development Approach

### Core Scripts (Root Level)
- **Core Functionality**: Essential scripts for basic operations remain in the root `scripts/` directory
- **Immediate Use**: Scripts that are immediately usable in the current development cycle
- **Examples**: Ingestion scripts, evaluation tools, smoke tests

### Advanced Scripts (Organized by Feature)
- **Specialized Functionality**: Advanced capabilities organized by feature area
- **Clean Organization**: Direct folder names without arbitrary phase prefixes
- **Professional Structure**: Enterprise-ready organization for production systems

### Phase 3-6 Scripts (Organized by Feature)
- **Advanced Features**: Sophisticated functionality organized by capability area
- **Future-Ready**: Scripts prepared for advanced testing, MLOps, monitoring, and deployment
- **Scalable Structure**: Clean organization prevents script directory clutter

## Usage Guidelines

### Running Core Scripts (Phase 1-2)
```bash
# Phase 1: Run baseline evaluation
python scripts/evaluation/run_baseline_evaluation.py

# Phase 1: Generate domain-specific test queries
python scripts/evaluation/create_domain_queries.py --domains "cs_ai,life_sciences"

# Phase 1: Analyze evaluation results
python scripts/evaluation/analyze_eval_results.py results/baseline_performance.json

# Phase 2: Run model optimization
python scripts/optimization/run_model_optimization.py --quick-test

# Phase 2: Compare embedding models
python scripts/optimization/embedding_model_comparison.py --models "all-MiniLM-L6-v2,all-mpnet-base-v2"

# Phase 2: Evaluate reranking strategies
python scripts/optimization/reranking_evaluation.py --strategies "cross_encoder,hybrid_scoring"
```

### Running Feature-Based Scripts
```bash
# A/B Testing
python scripts/ab_testing/ab_test_retrieval.py --config-a baseline.yaml --config-b optimized.yaml

# MLOps Setup
python scripts/mlops/setup_mlops_pipeline.py --environment production

# Production Monitoring
python scripts/monitoring/production_monitoring.py --dashboard grafana

# Blue-Green Deployment
python scripts/deployment/blue_green_deploy.py --target production
```

## Implementation Status

### ✅ Implemented and Ready
- Core evaluation scripts (`eval_retrieval.py`, `smoke_test.py`)
- Document ingestion pipeline (`run_ingestion.py`, `ingest_watch.py`)
- **Phase 1 evaluation framework**: Complete with 6 comprehensive scripts
- **Phase 2 optimization framework**: Complete with 5 optimization scripts
- Advanced script templates with comprehensive docstrings

### 🚧 Implementation Required
- **Phase 3-6 Frameworks**: Full implementation of advanced features (currently documented with TODO markers)

## Development Best Practices

### Adding New Scripts
1. **Feature Alignment**: Place scripts in appropriate directories based on functionality and complexity
2. **Documentation**: Include comprehensive docstrings with features, usage examples, and parameter descriptions
3. **Naming Convention**: Use descriptive names that clearly indicate script functionality
4. **Dependencies**: Document any additional dependencies or setup requirements

### Script Organization Principles
- **Separation of Concerns**: Each directory focuses on specific system capabilities
- **Logical Grouping**: Scripts grouped by functionality rather than arbitrary phases
- **Maintainability**: Clear organization reduces cognitive load and improves team collaboration
- **Scalability**: Structure supports adding new scripts without directory clutter

## Dependencies by Feature Area

### A/B Testing
- Statistical analysis libraries (scipy, numpy)
- Configuration management frameworks
- Experiment tracking capabilities

### MLOps
- MLflow or similar model tracking
- Container orchestration tools
- CI/CD pipeline integration

### Monitoring
- Monitoring stack (Prometheus, Grafana)
- Log aggregation tools (ELK stack)
- Alerting systems (PagerDuty, Slack)

### Deployment
- Cloud deployment tools (AWS CLI, kubectl)
- Load balancing configuration
- Health check frameworks

## Reference Documentation

- **[Pre-Deployment Testing Plan](../PRE_DEPLOYMENT_TESTING_PLAN.md)**: Comprehensive 8-week optimization methodology
- **[System Design](../docs/system_design.md)**: Overall architecture and component relationships
- **[Operations Runbook](../docs/ops_runbook.md)**: Production operations and troubleshooting guide