#!/usr/bin/env python3
"""
Test Script for A/B Testing Framework

This script creates sample test data and validates the A/B testing
framework implementation for Phase 3 pre-deployment testing.
"""

import json
import numpy as np
from pathlib import Path
import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def create_sample_test_data():
    """Create sample test data for A/B testing validation"""
    
    # Create test directory
    test_dir = Path("results/ab_testing/test")
    test_dir.mkdir(parents=True, exist_ok=True)
    
    # Sample queries with ground truth
    sample_queries = []
    for i in range(50):
        sample_queries.append({
            "query": f"sample query {i}",
            "expected_documents": [f"doc_{i}_1", f"doc_{i}_2"]
        })
    
    # Save sample queries
    with open(test_dir / "sample_queries.jsonl", 'w') as f:
        for query in sample_queries:
            f.write(json.dumps(query) + "\n")
    
    # Create mock A/B test results
    mock_results = {
        "experiment_metadata": {
            "start_time": "2024-01-20T10:00:00",
            "end_time": "2024-01-20T12:00:00", 
            "num_configurations": 3,
            "configuration_names": ["baseline", "optimized", "ultra_budget"],
            "num_queries": 50,
            "test_type": "multi_variant_ab_test"
        },
        "configuration_results": {
            "baseline": {
                "config_name": "baseline",
                "config": {
                    "name": "baseline", 
                    "embedding_model": "all-MiniLM-L6-v2",
                    "reranker": "passthrough",
                    "top_k_final": 5,
                    "bm25_weight": 0.7,
                    "semantic_weight": 0.3
                },
                "query_results": [],
                "aggregated_metrics": {
                    "precision_at_5_mean": 0.72,
                    "precision_at_5_std": 0.15,
                    "precision_at_5_count": 50,
                    "mrr_mean": 0.68,
                    "mrr_std": 0.18,
                    "recall_at_10_mean": 0.65,
                    "latency_ms_mean": 180,
                    "latency_ms_p95": 400
                }
            },
            "optimized": {
                "config_name": "optimized",
                "config": {
                    "name": "optimized",
                    "embedding_model": "all-mpnet-base-v2", 
                    "reranker": "cross_encoder",
                    "top_k_final": 5,
                    "bm25_weight": 0.6,
                    "semantic_weight": 0.4
                },
                "query_results": [],
                "aggregated_metrics": {
                    "precision_at_5_mean": 0.78,
                    "precision_at_5_std": 0.12,
                    "precision_at_5_count": 50,
                    "mrr_mean": 0.75,
                    "mrr_std": 0.14,
                    "recall_at_10_mean": 0.71,
                    "latency_ms_mean": 350,
                    "latency_ms_p95": 850
                }
            },
            "ultra_budget": {
                "config_name": "ultra_budget",
                "config": {
                    "name": "ultra_budget",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "reranker": "passthrough", 
                    "top_k_final": 3,
                    "bm25_weight": 0.8,
                    "semantic_weight": 0.2
                },
                "query_results": [],
                "aggregated_metrics": {
                    "precision_at_5_mean": 0.69,
                    "precision_at_5_std": 0.17,
                    "precision_at_5_count": 50,
                    "mrr_mean": 0.64,
                    "mrr_std": 0.19,
                    "recall_at_10_mean": 0.58,
                    "latency_ms_mean": 120,
                    "latency_ms_p95": 280
                }
            }
        },
        "statistical_analysis": {
            "pairwise_comparisons": {
                "optimized": {
                    "vs_baseline": "baseline",
                    "improvements": {
                        "precision_at_5_mean": 8.3,
                        "mrr_mean": 10.3,
                        "recall_at_10_mean": 9.2
                    }
                }
            }
        },
        "recommendations": {
            "recommended_configuration": "optimized",
            "deployment_decision": {
                "deploy_recommended": True,
                "criteria_check": {
                    "precision_threshold": True,
                    "mrr_threshold": True, 
                    "latency_threshold": True,
                    "improvement_significant": True
                }
            }
        }
    }
    
    # Add individual query results for statistical analysis
    np.random.seed(42)
    for config_name, config_data in mock_results["configuration_results"].items():
        query_results = []
        metrics = config_data["aggregated_metrics"]
        
        # Generate synthetic results based on aggregated metrics
        precision_mean = metrics["precision_at_5_mean"]
        precision_std = metrics["precision_at_5_std"] 
        mrr_mean = metrics["mrr_mean"]
        latency_mean = metrics["latency_ms_mean"]
        
        for i in range(50):
            # Add some variance
            precision = max(0, min(1, np.random.normal(precision_mean, precision_std)))
            mrr = max(0, min(1, np.random.normal(mrr_mean, 0.1)))
            latency = max(50, np.random.normal(latency_mean, latency_mean * 0.3))
            
            query_results.append({
                "query": f"sample query {i}",
                "retrieved_count": 5,
                "latency_ms": latency,
                "precision_at_5": precision,
                "mrr": mrr,
                "recall_at_10": precision * 0.9  # Approximate
            })
        
        config_data["query_results"] = query_results
    
    # Save mock results
    with open(test_dir / "sample_ab_results.json", 'w') as f:
        json.dump(mock_results, f, indent=2)
    
    return test_dir


def test_ab_testing_pipeline():
    """Test the complete A/B testing pipeline"""
    print("Testing A/B Testing Framework")
    print("=" * 50)
    
    # Create test data
    test_dir = create_sample_test_data()
    print(f"[PASS] Created test data in {test_dir}")
    
    try:
        # Test statistical analysis
        print("\nTesting Statistical Analysis...")
        from statistical_analysis import StatisticalAnalyzer
        
        analyzer = StatisticalAnalyzer()
        stats_results = analyzer.analyze_ab_test_results(
            str(test_dir / "sample_ab_results.json")
        )
        
        stats_output = test_dir / "test_statistical_analysis.json"
        analyzer.save_analysis(str(stats_output))
        print(f"[PASS] Statistical analysis completed: {stats_output}")
        
        # Test configuration selection  
        print("\nTesting Configuration Selection...")
        from select_best_config import ConfigurationSelector
        
        selector = ConfigurationSelector()
        selection_results = selector.run_configuration_selection(
            str(test_dir / "sample_ab_results.json")
        )
        
        selection_output = test_dir / "test_config_selection.json"
        selector.save_selection_results(str(selection_output))
        print(f"[PASS] Configuration selection completed: {selection_output}")
        
        # Print results summary
        winner = selection_results['final_selection']['winner']
        print(f"\nTest Results Summary:")
        print(f"   Selected Config: {winner['config_name']}")
        print(f"   Precision@5: {winner['precision_at_5']:.3f}")
        print(f"   Weighted Score: {winner['weighted_score']:.3f}")
        
        deployment = selection_results['deployment_recommendations']
        if deployment['deploy_immediate']:
            print(f"   Deployment: [READY]")
        elif deployment['deploy_conditional']:
            print(f"   Deployment: [WARNING]")
        else:
            print(f"   Deployment: [REVIEW]")
        
        print(f"\nTest artifacts saved to: {test_dir}")
        print("[PASS] A/B Testing Framework validation complete!")
        
        return True
        
    except Exception as e:
        print(f"[ERROR] Testing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_ab_testing_pipeline()
    
    if success:
        print("\n[SUCCESS] All tests passed! A/B testing framework is ready.")
    else:
        print("\n[FAILED] Tests failed. Check implementation.")
        sys.exit(1)