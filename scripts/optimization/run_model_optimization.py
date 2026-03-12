#!/usr/bin/env python3
"""
Phase 2 Orchestration Script - Model Optimization
=================================================

Orchestrates the complete Phase 2 model optimization pipeline including:
1. Embedding model comparison
2. Re-ranking strategy evaluation  
3. Combined optimization testing
4. A/B testing framework
5. Performance vs cost analysis

Usage:
    python scripts/optimization/run_model_optimization.py
    python scripts/optimization/run_model_optimization.py --quick-test --max-queries 25
    python scripts/optimization/run_model_optimization.py --embedding-models "all-mpnet-base-v2,e5-small-v2"

Author: AI RAG Assistant Team
Date: March 2026  
Phase: 2 - Model Optimization
"""

import argparse
import json
import logging
import subprocess
import time
import traceback
from pathlib import Path
from typing import Dict, List, Optional
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ModelOptimizationOrchestrator:
    """Orchestrates Phase 2 model optimization pipeline."""
    
    def __init__(self, config_path: Optional[Path] = None, quick_test: bool = False):
        self.quick_test = quick_test
        self.config_path = config_path or Path("configs/optimization_config.yaml")
        self.config = self.load_configuration()
        self.results = {}
        
        # Setup directories
        self.results_dir = Path("results/optimization")
        self.results_dir.mkdir(parents=True, exist_ok=True)
        
    def load_configuration(self) -> Dict:
        """Load Phase 2 configuration."""
        try:
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            logger.info(f"Loaded configuration from {self.config_path}")
            return config
        except FileNotFoundError:
            logger.warning(f"Configuration file not found: {self.config_path}")
            return self._get_default_config()
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {e}")
            return self._get_default_config()
            
    def _get_default_config(self) -> Dict:
        """Get default configuration for Phase 2."""
        return {
            'embedding_models': {
                'baseline': {'name': 'all-MiniLM-L6-v2'},
                'quality_focused': {'name': 'all-mpnet-base-v2'},
                'efficient_modern': {'name': 'e5-small-v2'},
                'm1_optimized': {'name': 'gte-small'}
            },
            'reranking_strategies': {
                'cross_encoder': {'name': 'cross_encoder'},
                'ollama_llm': {'name': 'ollama_llm'},
                'hybrid_scoring': {'name': 'hybrid_scoring'}
            },
            'evaluation': {
                'test_datasets': {
                    'scale_test': {'path': 'data/evaluation/scale_test_set.jsonl'}
                }
            },
            'hardware': {
                'max_memory_gb': 6.0,
                'batch_size': 8
            }
        }
        
    def create_test_dataset(self, max_queries: Optional[int] = None) -> Path:
        """Create or verify test dataset for Phase 2."""
        test_set_path = Path("data/evaluation/scale_test_set.jsonl")
        
        if test_set_path.exists():
            logger.info(f"Test dataset already exists: {test_set_path}")
            return test_set_path
            
        logger.info("Creating test dataset for Phase 2...")
        
        # Create test dataset using generate_test_queries.py
        cmd = [
            "python", "scripts/evaluation/generate_test_queries.py",
            "--count", str(max_queries or 75),
            "--domains", "general,academic,technical,medical",
            "--difficulty-mix", "basic:0.3,intermediate:0.5,advanced:0.2",
            "--output", str(test_set_path)
        ]
        
        if self.quick_test:
            cmd[3] = "25"  # Reduce count for quick test
            
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            logger.info("Test dataset created successfully")
            return test_set_path
        except subprocess.CalledProcessError as e:
            logger.error(f"Failed to create test dataset: {e}")
            logger.error(f"STDERR: {e.stderr}")
            raise
            
    def run_embedding_comparison(self, models: Optional[List[str]] = None) -> Dict:
        """Run embedding model comparison."""
        logger.info("\\n" + "="*60)
        logger.info("PHASE 2.1: EMBEDDING MODEL COMPARISON")
        logger.info("="*60)
        
        # Get models to test
        if models:
            model_list = models
        else:
            model_configs = self.config.get('embedding_models', {})
            model_list = [config['name'] for config in model_configs.values()]
            
        if self.quick_test:
            # Test only baseline and one alternative for quick test
            model_list = model_list[:2]
            
        logger.info(f"Testing embedding models: {model_list}")
        
        # Setup paths
        test_set_path = self.create_test_dataset()
        output_path = self.results_dir / "embedding_comparison.json"
        
        # Run embedding comparison
        cmd = [
            "python", "scripts/optimization/embedding_model_comparison.py",
            "--models", ",".join(model_list),
            "--test-set", str(test_set_path),
            "--batch-size", str(self.config.get('hardware', {}).get('batch_size', 8)),
            "--max-memory-gb", str(self.config.get('hardware', {}).get('max_memory_gb', 6.0)),
            "--output", str(output_path)
        ]
        
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Embedding comparison completed successfully")
            
            # Load and store results
            with open(output_path, 'r') as f:
                comparison_results = json.load(f)
                
            self.results['embedding_comparison'] = comparison_results
            
            # Log summary
            if 'recommendations' in comparison_results:
                rec = comparison_results['recommendations']
                if 'best_overall' in rec:
                    logger.info(f"Best overall model: {rec['best_overall']['model']}")
                    
            return comparison_results
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Embedding comparison failed: {e}")
            logger.error(f"STDERR: {e.stderr}")
            raise
            
    def run_reranking_evaluation(self, strategies: Optional[List[str]] = None) -> Dict:
        """Run re-ranking strategy evaluation."""
        logger.info("\\n" + "="*60)
        logger.info("PHASE 2.2: RE-RANKING STRATEGY EVALUATION") 
        logger.info("="*60)
        
        # Get strategies to test
        if strategies:
            strategy_list = strategies
        else:
            strategy_configs = self.config.get('reranking_strategies', {})
            strategy_list = [config['name'] for config in strategy_configs.values()]
            
        if self.quick_test:
            # Test only hybrid_scoring and cross_encoder for quick test
            strategy_list = [s for s in strategy_list if s in ['hybrid_scoring', 'cross_encoder']]
            
        logger.info(f"Testing re-ranking strategies: {strategy_list}")
        
        # Setup paths
        test_set_path = self.create_test_dataset()
        output_path = self.results_dir / "reranking_evaluation.json"
        baseline_path = self.results_dir / "embedding_comparison.json" if 'embedding_comparison' in self.results else None
        
        # Run re-ranking evaluation
        cmd = [
            "python", "scripts/optimization/reranking_evaluation.py",
            "--strategies", ",".join(strategy_list),
            "--test-set", str(test_set_path),
            "--output", str(output_path),
            "--local-models-only"
        ]
        
        if baseline_path:
            cmd.extend(["--baseline", str(baseline_path)])
            
        try:
            logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)
            
            logger.info("Re-ranking evaluation completed successfully")
            
            # Load and store results
            with open(output_path, 'r') as f:
                reranking_results = json.load(f)
                
            self.results['reranking_evaluation'] = reranking_results
            
            # Log summary
            if 'recommendations' in reranking_results:
                rec = reranking_results['recommendations']
                if 'best_quality' in rec:
                    logger.info(f"Best quality strategy: {rec['best_quality']['strategy']}")
                if 'best_cost_benefit' in rec:
                    logger.info(f"Best cost-benefit: {rec['best_cost_benefit']['strategy']}")
                    
            return reranking_results
            
        except subprocess.CalledProcessError as e:
            logger.error(f"Re-ranking evaluation failed: {e}")
            logger.error(f"STDERR: {e.stderr}")
            raise
            
    def analyze_combined_results(self) -> Dict:
        """Analyze combined results and generate recommendations."""
        logger.info("\\n" + "="*60)
        logger.info("PHASE 2.3: COMBINED ANALYSIS")
        logger.info("="*60)
        
        if 'embedding_comparison' not in self.results or 'reranking_evaluation' not in self.results:
            logger.warning("Cannot perform combined analysis - missing results")
            return {}
            
        embedding_results = self.results['embedding_comparison']
        reranking_results = self.results['reranking_evaluation']
        
        # Extract best performers
        best_embedding = None
        if 'recommendations' in embedding_results and 'best_overall' in embedding_results['recommendations']:
            best_embedding = embedding_results['recommendations']['best_overall']['model']
            
        best_reranker = None  
        if 'recommendations' in reranking_results and 'best_cost_benefit' in reranking_results['recommendations']:
            best_reranker = reranking_results['recommendations']['best_cost_benefit']['strategy']
            
        # Calculate combined performance estimates
        combined_analysis = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'best_embedding_model': best_embedding,
            'best_reranking_strategy': best_reranker,
            'performance_estimates': {},
            'cost_analysis': {},
            'implementation_recommendation': {}
        }
        
        # Performance estimates
        if best_embedding and best_reranker:
            # Find performance data for best models
            embedding_metrics = None
            for model_result in embedding_results.get('model_performance', []):
                if model_result['model_name'] == best_embedding:
                    embedding_metrics = model_result
                    break
                    
            reranking_metrics = None
            for strategy_result in reranking_results.get('strategy_performance', []):
                if strategy_result['strategy_name'] == best_reranker:
                    reranking_metrics = strategy_result
                    break
                    
            if embedding_metrics and reranking_metrics:
                # Estimate combined performance
                combined_analysis['performance_estimates'] = {
                    'estimated_precision_at_5': min(
                        embedding_metrics['precision_at_5'] + reranking_metrics['quality_improvement'] / 100,
                        0.95
                    ),
                    'estimated_mrr': min(
                        embedding_metrics.get('mrr', 0.8) * (1 + reranking_metrics['quality_improvement'] / 100),
                        0.95
                    ),
                    'estimated_latency_ms': (
                        embedding_metrics['inference_time_ms'] + 
                        reranking_metrics['avg_rerank_time_ms']
                    ),
                    'estimated_memory_mb': (
                        embedding_metrics['memory_usage_mb'] + 
                        reranking_metrics['memory_usage_mb']
                    )
                }
                
                # Cost analysis
                combined_analysis['cost_analysis'] = {
                    'embedding_cost_per_query': 0.0001 if 'mpnet' in best_embedding else 0.00005,
                    'reranking_cost_per_query': reranking_metrics['cost_per_query'],
                    'total_cost_per_query': (
                        (0.0001 if 'mpnet' in best_embedding else 0.00005) +
                        reranking_metrics['cost_per_query']
                    ),
                    'monthly_cost_estimate': (
                        ((0.0001 if 'mpnet' in best_embedding else 0.00005) +
                         reranking_metrics['cost_per_query']) * 10000  # 10k queries/month
                    )
                }
                
        # Implementation recommendation
        combined_analysis['implementation_recommendation'] = {
            'recommended_configuration': {
                'embedding_model': best_embedding,
                'reranking_strategy': best_reranker,
                'bm25_weight': 0.6,
                'semantic_weight': 0.4,
                'top_k_retrieval': 25
            },
            'deployment_priority': 'high' if combined_analysis['performance_estimates'].get('estimated_precision_at_5', 0) > 0.78 else 'medium',
            'risk_assessment': 'low' if combined_analysis['cost_analysis'].get('monthly_cost_estimate', 100) < 5 else 'medium'
        }
        
        self.results['combined_analysis'] = combined_analysis
        
        # Save combined analysis
        output_path = self.results_dir / "combined_analysis.json"
        with open(output_path, 'w') as f:
            json.dump(combined_analysis, f, indent=2)
            
        logger.info("Combined analysis completed")
        logger.info(f"Best embedding model: {best_embedding}")
        logger.info(f"Best re-ranking strategy: {best_reranker}")
        
        return combined_analysis
        
    def generate_optimization_summary(self) -> Dict:
        """Generate comprehensive Phase 2 summary report."""
        logger.info("\\n" + "="*60)
        logger.info("PHASE 2 SUMMARY REPORT")
        logger.info("="*60)
        
        summary = {
            'phase': 'Phase 2 - Model Optimization',
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'evaluation_framework': 'MLOps Testing Pipeline',
            'quick_test_mode': self.quick_test,
            'results_summary': {},
            'key_findings': {},
            'recommendations': {},
            'next_steps': {}
        }
        
        # Results summary
        summary['results_summary'] = {
            'embedding_models_tested': len(self.results.get('embedding_comparison', {}).get('model_performance', [])),
            'reranking_strategies_tested': len(self.results.get('reranking_evaluation', {}).get('strategy_performance', [])),
            'total_experiments': 2,
            'total_test_queries': 75 if not self.quick_test else 25
        }
        
        # Key findings
        key_findings = []
        
        if 'embedding_comparison' in self.results:
            embedding_rec = self.results['embedding_comparison'].get('recommendations', {})
            if 'best_overall' in embedding_rec:
                key_findings.append(f"Best embedding model: {embedding_rec['best_overall']['model']}")
                
        if 'reranking_evaluation' in self.results:
            reranking_rec = self.results['reranking_evaluation'].get('recommendations', {})
            if 'best_cost_benefit' in reranking_rec:
                key_findings.append(f"Best re-ranking strategy: {reranking_rec['best_cost_benefit']['strategy']}")
                
        if 'combined_analysis' in self.results:
            combined = self.results['combined_analysis']
            if 'performance_estimates' in combined:
                est_precision = combined['performance_estimates'].get('estimated_precision_at_5', 0)
                if est_precision > 0:
                    improvement = ((est_precision - 0.72) / 0.72) * 100
                    key_findings.append(f"Estimated performance improvement: {improvement:.1f}%")
                    
        summary['key_findings'] = key_findings
        
        # Recommendations
        if 'combined_analysis' in self.results:
            combined = self.results['combined_analysis']
            summary['recommendations'] = combined.get('implementation_recommendation', {})
        else:
            summary['recommendations'] = {
                'status': 'Incomplete - run full Phase 2 pipeline for recommendations'
            }
            
        # Next steps
        summary['next_steps'] = {
            'immediate': [
                "Review Phase 2 detailed results",
                "Validate winning configuration with A/B testing",
                "Prepare Phase 3 production deployment plan"
            ],
            'phase_3_preparation': [
                "Setup monitoring and alerting infrastructure", 
                "Design gradual rollout strategy",
                "Establish production performance baselines"
            ]
        }
        
        # Save summary report
        output_path = self.results_dir / "optimization_summary_report.json"
        with open(output_path, 'w') as f:
            json.dump(summary, f, indent=2)
            
        # Print summary
        print("\\n" + "="*80)
        print("PHASE 2 OPTIMIZATION SUMMARY")
        print("="*80)
        print(f"Completion Time: {summary['timestamp']}")
        print(f"Quick Test Mode: {summary['quick_test_mode']}")
        print("\\nKey Findings:")
        for finding in key_findings:
            print(f"  • {finding}")
            
        if 'recommended_configuration' in summary['recommendations']:
            rec_config = summary['recommendations']['recommended_configuration']
            print("\\nRecommended Configuration:")
            print(f"  • Embedding Model: {rec_config.get('embedding_model', 'N/A')}")
            print(f"  • Re-ranking Strategy: {rec_config.get('reranking_strategy', 'N/A')}")
            print(f"  • BM25 Weight: {rec_config.get('bm25_weight', 'N/A')}")
            print(f"  • Semantic Weight: {rec_config.get('semantic_weight', 'N/A')}")
            
        print("\\nNext Steps:")
        for step in summary['next_steps']['immediate']:
            print(f"  1. {step}")
            
        print("\\n" + "="*80)
        
        return summary
        
    def run_full_optimization(self, embedding_models: Optional[List[str]] = None,
                       reranking_strategies: Optional[List[str]] = None) -> Dict:
        """Run complete Phase 2 optimization pipeline."""
        logger.info("\\n" + "="*80)
        logger.info("STARTING PHASE 2 MODEL OPTIMIZATION")
        logger.info("="*80)
        logger.info(f"Quick test mode: {self.quick_test}")
        
        start_time = time.time()
        
        try:
            # Step 1: Embedding model comparison
            self.run_embedding_comparison(embedding_models)
            
            # Step 2: Re-ranking strategy evaluation
            self.run_reranking_evaluation(reranking_strategies)
            
            # Step 3: Combined analysis
            self.analyze_combined_results()
            
            # Step 4: Generate summary
            summary = self.generate_optimization_summary()
            
            duration = time.time() - start_time
            logger.info(f"\\nPhase 2 optimization completed in {duration:.1f} seconds")
            
            return summary
            
        except Exception as e:
            logger.error(f"Phase 2 optimization failed: {e}")
            logger.error(traceback.format_exc())
            raise


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Run Model optimization pipeline",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run full model optimization
  python scripts/optimization/run_model_optimization.py
  
  # Quick test with limited models
  python scripts/optimization/run_model_optimization.py --quick-test
  
  # Test specific embedding models
  python scripts/optimization/run_model_optimization.py --embedding-models "all-mpnet-base-v2,e5-small-v2"
  
  # Test specific re-ranking strategies
  python scripts/optimization/run_model_optimization.py --reranking-strategies "cross_encoder,hybrid_scoring"
        """
    )
    
    parser.add_argument(
        '--config',
        type=Path,
        help='Path to optimization configuration file'
    )
    
    parser.add_argument(
        '--quick-test',
        action='store_true',
        help='Run quick test with reduced dataset and models'
    )
    
    parser.add_argument(
        '--embedding-models',
        type=str,
        help='Comma-separated list of embedding models to test'
    )
    
    parser.add_argument(
        '--reranking-strategies', 
        type=str,
        help='Comma-separated list of re-ranking strategies to test'
    )
    
    parser.add_argument(
        '--max-queries',
        type=int,
        help='Maximum number of test queries to generate'
    )
    
    args = parser.parse_args()
    
    # Parse model and strategy lists
    embedding_models = None
    if args.embedding_models:
        embedding_models = [model.strip() for model in args.embedding_models.split(',')]
        
    reranking_strategies = None  
    if args.reranking_strategies:
        reranking_strategies = [strategy.strip() for strategy in args.reranking_strategies.split(',')]
        
    # Create orchestrator
    orchestrator = ModelOptimizationOrchestrator(
        config_path=args.config,
        quick_test=args.quick_test
    )
    
    try:
        # Run Phase 2 optimization
        summary = orchestrator.run_full_optimization(
            embedding_models=embedding_models,
            reranking_strategies=reranking_strategies
        )
        
        print("\\n✅ Phase 2 optimization completed successfully!")
        print(f"📊 Results saved to: {orchestrator.results_dir}/")
        print(f"📋 Summary report: {orchestrator.results_dir}/optimization_summary_report.json")
        
        return 0
        
    except Exception as e:
        logger.error(f"Phase 2 optimization failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())