# Baseline Evaluation Guide

This guide covers the baseline evaluation implementation of the MLOps testing pipeline for establishing baseline RAG performance metrics.

## Overview

The baseline evaluation establishes a comprehensive evaluation framework with:
- Domain-specific query datasets (Computer Science/AI, Life Sciences, Physics, Social Sciences)
- Statistical evaluation framework with confidence intervals and variance analysis
- Automated baseline measurement and reporting
- Infrastructure for A/B testing and parameter optimization

## Quick Start

### Prerequisites
- Python environment configured (via configure_python_environment)
- RAG system components available
- OpenSearch instance running (if testing with real system)
- Ollama instance running (if testing generation)

### One-Command Baseline Evaluation

```bash
# Full baseline evaluation
python scripts/run_phase1_evaluation.py

# Quick test with limited queries
python scripts/evaluation/run_baseline_evaluation.py --max-queries 10
```

## Individual Components

### 1. Create Domain-Specific Queries

```bash
# Create queries for all domains
python scripts/create_domain_queries.py \
  --domains cs_ai,life_sciences,physics,social_sciences \
  --queries-per-domain 25 \
  --output-dir data/evaluation \
  --cross-domain

# Create queries for specific domain
python scripts/create_domain_queries.py \
  --domains cs_ai \
  --queries-per-domain 50 \
  --output-dir data/evaluation/cs_focused
```

Output files:
- `data/evaluation/cs_ai_queries.jsonl` - Computer Science/AI queries
- `data/evaluation/life_sciences_queries.jsonl` - Life Sciences queries  
- `data/evaluation/physics_queries.jsonl` - Physics queries
- `data/evaluation/social_sciences_queries.jsonl` - Social Sciences queries
- `data/evaluation/cross_domain_queries.jsonl` - Cross-domain queries

### 2. Run Baseline Evaluation

```bash
# Evaluate single domain
python scripts/baseline_evaluation.py \
  --queries data/evaluation/cs_ai_queries.jsonl \
  --config configs/baseline_config.json \
  --output results/baseline_evaluation/baseline/cs_ai_results.jsonl \\
  --use-reranking

# Quick test without reranking
python scripts/baseline_evaluation.py \
  --queries data/evaluation/cs_ai_queries.jsonl \
  --config configs/baseline_config.json \
  --output results/test_results.jsonl \
  --max-queries 5
```

### 3. Statistical Analysis

```bash
# Comprehensive baseline analysis
python scripts/analyze_eval_results.py \
  --results results/baseline_evaluation/baseline/cs_ai_results.jsonl \\
  --output-dir results/baseline_evaluation/analysis/cs_ai \\
  --analysis-type baseline \
  --confidence-level 0.95

# Compare multiple result sets
python scripts/analyze_eval_results.py \
  --results results/baseline_evaluation/baseline/cs_ai_results.jsonl \\
  --baseline-results results/baseline_evaluation/baseline/physics_results.jsonl \\
  --output-dir results/baseline_evaluation/analysis/cs_vs_physics \\
  --analysis-type comparison
```

### 4. Parameter Optimization

```bash
# Test different retrieval parameters
python scripts/experiment_pipeline.py \
  --baseline-config configs/baseline_config.json \
  --queries data/evaluation/cs_ai_queries.jsonl \
  --output-dir results/baseline_evaluation/experiments \\
  --experiment-type sweep \
  --sweep-parameter "retrieval.top_k" \
  --sweep-values "5,10,15,20" \
  --max-queries 20

# Grid search on multiple parameters
python scripts/experiment_pipeline.py \
  --baseline-config configs/baseline_config.json \
  --queries data/evaluation/cs_ai_queries.jsonl \
  --output-dir results/baseline_evaluation/experiments \\
  --experiment-type grid \
  --grid-parameters '{"retrieval.top_k": [5, 10], "reranker.top_k": [3, 5]}' \
  --max-queries 15
```

## Query Format

Each query file contains JSONL with the following structure:

```json
{
  "id": "cs_ai_001",
  "question": "How does attention mechanism work in transformers?",
  "keywords": ["attention mechanism", "transformers"],
  "expected_answer_snippet": "attention mechanism",
  "domain": "cs_ai",
  "difficulty": "intermediate",
  "question_type": "architecture",
  "created_at": "2025-01-16T...",
  "synthetic": true
}
```

## Evaluation Metrics

### Primary Metrics
- **Retrieval Accuracy**: Top-1 and Top-5 scores
- **Response Time**: Retrieval, reranking, and total time
- **Success Rate**: Percentage of successful evaluations
- **Keyword Coverage**: Presence of expected terms

### Statistical Analysis
- **Confidence Intervals**: 95% confidence bounds for all metrics
- **Variance Analysis**: Statistical significance testing
- **Distribution Analysis**: Performance across domains and difficulty
- **Baseline Comparison**: Change detection and effect sizes

## Output Structure

```
results/phase1/
├── baseline/                    # Raw evaluation results
│   ├── cs_ai_results.jsonl
│   ├── life_sciences_results.jsonl
│   └── physics_results.jsonl
├── analysis/                    # Statistical analysis reports
│   ├── cs_ai/
│   │   ├── baseline_analysis.json
│   │   ├── confidence_intervals.json
│   │   └── performance_summary.json
│   └── comparative/
└── experiments/                 # Parameter optimization results
    ├── sweep_top_k_001_config.json
    ├── sweep_top_k_001_results.jsonl
    └── batch_summary_20250116_143052.json
```

## Configuration

### Baseline Configuration (`configs/baseline_config.json`)

Key settings for baseline evaluation:
- `retrieval.top_k: 10` - Number of documents to retrieve
- `reranker.enabled: true` - Use semantic reranking
- `reranker.top_k: 5` - Rerank top 5 documents
- `generation.enabled: false` - Disable generation for speed

### Custom Configuration

Override specific parameters:
```json
{
  "retrieval": {
    "top_k": 15,
    "similarity_threshold": 0.1
  },
  "reranker": {
    "enabled": false
  }
}
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure RAG pipeline modules are in Python path
   ```bash
   export PYTHONPATH="${PYTHONPATH}:/path/to/ai_rag_assistant"
   ```

2. **OpenSearch Connection**: For mock evaluation without OpenSearch:
   - Scripts will automatically use mock data if components aren't available
   - Check baseline_evaluation.py logs for connection status

3. **Memory Issues**: Reduce batch sizes in configuration:
   - `embedding.batch_size: 16` (default: 32)
   - `reranker.batch_size: 8` (default: 16)

4. **Slow Evaluation**: Use `--max-queries` for testing:
   ```bash
   python scripts/evaluation/run_baseline_evaluation.py --max-queries 10
   ```

### Mock Mode

If RAG components are not available, scripts run in mock mode:
- Generates realistic but synthetic evaluation data
- Useful for testing the evaluation framework itself
- Look for "Running in test mode" messages in logs

## Next Steps

After baseline evaluation completion:

1. **Review Baseline Metrics**: Check analysis reports in `results/baseline_evaluation/analysis/`
2. **Identify Bottlenecks**: Look for domains/difficulties with low performance  
3. **Plan Optimization**: Use ab_testing/experiment_pipeline.py for optimization testing
4. **Scale Testing**: Increase query counts for production evaluation

## Example Workflow

```bash
# 1. Full baseline evaluation
python scripts/evaluation/run_baseline_evaluation.py

# 2. Quick parameter test
python scripts/experiment_pipeline.py \
  --baseline-config configs/baseline_config.json \
  --queries data/evaluation/cs_ai_queries.jsonl \
  --output-dir results/test_optimization \
  --experiment-type single \
  --experiment-id "test_higher_topk" \
  --experiment-name "Test Top-K=15" \
  --parameters '{"retrieval.top_k": 15}' \
  --max-queries 10

# 3. Compare results
python scripts/analyze_eval_results.py \
  --results results/test_optimization/test_higher_topk_results.jsonl \
  --baseline-results results/baseline_evaluation/baseline/cs_ai_results.jsonl \\
  --output-dir results/comparison \
  --analysis-type comparison
```

## Success Criteria

Baseline evaluation establishes performance baseline if:
- All domain queries execute successfully
- Statistical analysis shows stable confidence intervals  
- Performance metrics are realistic (Top-1 > 0.5, response time < 2s)
- Framework ready for optimization experiments

Ready for model optimization and A/B testing!