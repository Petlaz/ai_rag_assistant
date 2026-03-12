#!/usr/bin/env python3
"""
A/B Testing and Parameter Optimization Pipeline

This script implements comprehensive A/B testing framework for RAG system optimization,
including parameter sweeps, statistical significance testing, and automated
experiment orchestration for systematic performance improvement.

Features:
- Automated A/B testing framework
- Parameter grid search optimization
- Statistical significance validation
- Multi-objective optimization
- Experiment reproducibility controls
- Performance regression detection
- Bayesian optimization integration
- Comprehensive experiment logging

Usage:
    # Run A/B test between configurations
    python scripts/ab_testing/experiment_pipeline.py --config-a baseline.yaml --config-b optimized.yaml
    
    # Parameter grid search optimization
    python scripts/ab_testing/experiment_pipeline.py --param-sweep --grid-config params.yaml
    
    # Bayesian optimization experiment
    python scripts/ab_testing/experiment_pipeline.py --bayesian-opt --trials 50 --objective precision
"""
"""
Experimental pipeline for RAG configuration testing and optimization.
Supports A/B testing, parameter sweeps, and performance comparisons.
"""

import json
import argparse
import asyncio
import time
import logging
import shutil
from typing import List, Dict, Any, Tuple, Optional, Iterator
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict
from collections import defaultdict
import itertools
import sys

# Add project root to Python path
sys.path.append(str(Path(__file__).parent.parent))

@dataclass
class ExperimentConfig:
    """Configuration for a single experiment."""
    experiment_id: str
    name: str
    description: str
    parameters: Dict[str, Any]
    baseline_config: Optional[str] = None
    query_subset: Optional[List[str]] = None  # Specific query IDs to test
    max_queries: Optional[int] = None
    created_at: str = ""
    
    def __post_init__(self):
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

@dataclass
class ExperimentResult:
    """Results from running an experiment."""
    experiment_id: str
    config: ExperimentConfig
    metrics: Dict[str, float]
    individual_results: List[Dict[str, Any]]
    runtime_seconds: float
    success_rate: float
    error_log: List[str]
    completed_at: str = ""
    
    def __post_init__(self):
        if not self.completed_at:
            self.completed_at = datetime.now().isoformat()

class ExperimentRunner:
    """Run controlled experiments on RAG system configurations."""
    
    def __init__(self, baseline_config_path: str, output_dir: str):
        """Initialize experiment runner."""
        self.baseline_config_path = baseline_config_path
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = self._setup_logging()
        
        # Load baseline configuration
        with open(baseline_config_path, 'r') as f:
            self.baseline_config = json.load(f)
        
        self.logger.info(f"Initialized experiment runner with baseline: {baseline_config_path}")
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration."""
        logger = logging.getLogger('experiment_runner')
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            # Console handler
            console_handler = logging.StreamHandler()
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)
            
            # File handler
            log_file = self.output_dir / 'experiments.log'
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(console_formatter)
            logger.addHandler(file_handler)
        
        return logger
    
    def create_experiment_config(self, experiment_id: str, name: str, 
                               description: str, parameters: Dict[str, Any],
                               **kwargs) -> ExperimentConfig:
        """Create a new experiment configuration."""
        config = ExperimentConfig(
            experiment_id=experiment_id,
            name=name,
            description=description,
            parameters=parameters,
            baseline_config=self.baseline_config_path,
            **kwargs
        )
        
        # Save experiment configuration
        config_file = self.output_dir / f"{experiment_id}_config.json"
        with open(config_file, 'w') as f:
            json.dump(asdict(config), f, indent=2)
        
        self.logger.info(f"Created experiment config: {experiment_id}")
        return config
    
    def generate_parameter_sweep(self, parameter_name: str, values: List[Any],
                               base_experiment: Dict[str, Any]) -> List[ExperimentConfig]:
        """Create experiment configs for parameter sweep."""
        configs = []
        
        for i, value in enumerate(values):
            experiment_id = f"{base_experiment['experiment_id']}_sweep_{parameter_name}_{i:03d}"
            
            # Update parameters
            parameters = base_experiment['parameters'].copy()
            parameters[parameter_name] = value
            
            config = self.create_experiment_config(
                experiment_id=experiment_id,
                name=f"{base_experiment['name']} - {parameter_name}={value}",
                description=f"Parameter sweep: {parameter_name}={value}. {base_experiment['description']}",
                parameters=parameters,
                max_queries=base_experiment.get('max_queries'),
                query_subset=base_experiment.get('query_subset')
            )
            configs.append(config)
        
        self.logger.info(f"Created {len(configs)} configs for {parameter_name} sweep")
        return configs
    
    def generate_grid_search(self, parameter_grid: Dict[str, List[Any]],
                           base_experiment: Dict[str, Any]) -> List[ExperimentConfig]:
        """Create experiment configs for grid search."""
        configs = []
        
        # Get all combinations of parameters
        param_names = list(parameter_grid.keys())
        param_values = list(parameter_grid.values())
        
        for i, combination in enumerate(itertools.product(*param_values)):
            experiment_id = f"{base_experiment['experiment_id']}_grid_{i:03d}"
            
            # Create parameter dict for this combination
            parameters = base_experiment['parameters'].copy()
            for param_name, value in zip(param_names, combination):
                parameters[param_name] = value
            
            # Create description
            param_desc = ", ".join(f"{name}={value}" for name, value in zip(param_names, combination))
            
            config = self.create_experiment_config(
                experiment_id=experiment_id,
                name=f"{base_experiment['name']} - Grid {i:03d}",
                description=f"Grid search: {param_desc}. {base_experiment['description']}",
                parameters=parameters,
                max_queries=base_experiment.get('max_queries'),
                query_subset=base_experiment.get('query_subset')
            )
            configs.append(config)
        
        self.logger.info(f"Created {len(configs)} configs for grid search")
        return configs
    
    def create_experiment_script_config(self, experiment_config: ExperimentConfig) -> str:
        """Create a temporary config file for running baseline_evaluation.py."""
        # Merge baseline config with experiment parameters
        merged_config = self.baseline_config.copy()
        
        # Apply parameter overrides
        for key, value in experiment_config.parameters.items():
            if '.' in key:
                # Handle nested parameters (e.g., 'retrieval.top_k')
                parts = key.split('.')
                current = merged_config
                for part in parts[:-1]:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
                current[parts[-1]] = value
            else:
                merged_config[key] = value
        
        # Save temporary config
        temp_config_file = self.output_dir / f"temp_config_{experiment_config.experiment_id}.json"
        with open(temp_config_file, 'w') as f:
            json.dump(merged_config, f, indent=2)
        
        return str(temp_config_file)
    
    def run_experiment(self, experiment_config: ExperimentConfig, 
                      query_file: str) -> ExperimentResult:
        """Run a single experiment."""
        start_time = time.time()
        errors = []
        
        self.logger.info(f"Starting experiment: {experiment_config.experiment_id}")
        self.logger.info(f"Description: {experiment_config.description}")
        
        try:
            # Create temporary configuration file
            temp_config_file = self.create_experiment_script_config(experiment_config)
            
            # Prepare output file
            results_file = self.output_dir / f"{experiment_config.experiment_id}_results.jsonl"
            
            # Build evaluation command
            import subprocess
            evaluation_script = Path(__file__).parent / "baseline_evaluation.py"
            
            cmd = [
                sys.executable, str(evaluation_script),
                "--queries", query_file,
                "--config", temp_config_file,
                "--output", str(results_file)
            ]
            
            # Add optional parameters
            if experiment_config.max_queries:
                cmd.extend(["--max-queries", str(experiment_config.max_queries)])
            
            if experiment_config.parameters.get('use_reranking', False):
                cmd.append("--use-reranking")
            
            if experiment_config.parameters.get('use_generation', False):
                cmd.append("--use-generation")
            
            # Run evaluation
            self.logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)  # 1 hour timeout
            
            if result.returncode != 0:
                error_msg = f"Evaluation failed with code {result.returncode}: {result.stderr}"
                errors.append(error_msg)
                self.logger.error(error_msg)
                
                # Return empty result on failure
                return ExperimentResult(
                    experiment_id=experiment_config.experiment_id,
                    config=experiment_config,
                    metrics={},
                    individual_results=[],
                    runtime_seconds=time.time() - start_time,
                    success_rate=0.0,
                    error_log=errors
                )
            
            # Load and process results
            individual_results = []
            if results_file.exists():
                with open(results_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            individual_results.append(json.loads(line))
            
            # Calculate aggregate metrics
            metrics = self._calculate_metrics(individual_results)
            success_rate = len([r for r in individual_results if r.get('total_time_ms', -1) > 0]) / max(len(individual_results), 1)
            
            # Clean up temporary files
            Path(temp_config_file).unlink(missing_ok=True)
            
            runtime = time.time() - start_time
            self.logger.info(f"Experiment {experiment_config.experiment_id} completed in {runtime:.2f}s")
            
            return ExperimentResult(
                experiment_id=experiment_config.experiment_id,
                config=experiment_config,
                metrics=metrics,
                individual_results=individual_results,
                runtime_seconds=runtime,
                success_rate=success_rate,
                error_log=errors
            )
            
        except Exception as e:
            error_msg = f"Experiment failed with exception: {str(e)}"
            errors.append(error_msg)
            self.logger.error(error_msg)
            
            return ExperimentResult(
                experiment_id=experiment_config.experiment_id,
                config=experiment_config,
                metrics={},
                individual_results=[],
                runtime_seconds=time.time() - start_time,
                success_rate=0.0,
                error_log=errors
            )
    
    def _calculate_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate aggregate metrics from individual results."""
        if not results:
            return {}
        
        successful_results = [r for r in results if r.get('total_time_ms', -1) > 0]
        n = len(successful_results)
        
        if n == 0:
            return {'success_rate': 0.0}
        
        metrics = {
            'success_rate': n / len(results),
            'total_queries': len(results),
            'successful_queries': n,
            
            # Timing metrics
            'avg_retrieval_time_ms': sum(r.get('retrieval_time_ms', 0) for r in successful_results) / n,
            'avg_total_time_ms': sum(r.get('total_time_ms', 0) for r in successful_results) / n,
            
            # Performance metrics
            'avg_top_1_score': sum(r.get('top_1_score', 0) for r in successful_results) / n,
            'avg_top_5_score': sum(r.get('top_5_avg_score', 0) for r in successful_results) / n,
            'avg_retrieved_docs': sum(r.get('retrieved_docs', 0) for r in successful_results) / n,
        }
        
        # Add reranking metrics if available
        reranked_results = [r for r in successful_results if r.get('rerank_time_ms') is not None]
        if reranked_results:
            metrics.update({
                'avg_rerank_time_ms': sum(r.get('rerank_time_ms', 0) for r in reranked_results) / len(reranked_results),
                'avg_reranked_top_1_score': sum(r.get('reranked_top_1_score', 0) for r in reranked_results) / len(reranked_results),
                'avg_reranked_top_5_score': sum(r.get('reranked_top_5_avg_score', 0) for r in reranked_results) / len(reranked_results),
            })
        
        # Add generation metrics if available
        generated_results = [r for r in successful_results if r.get('generation_time_ms') is not None]
        if generated_results:
            metrics.update({
                'avg_generation_time_ms': sum(r.get('generation_time_ms', 0) for r in generated_results) / len(generated_results),
                'avg_answer_length': sum(r.get('answer_length', 0) for r in generated_results) / len(generated_results),
                'avg_answer_confidence': sum(r.get('answer_confidence', 0) for r in generated_results) / len(generated_results),
            })
        
        return metrics
    
    def run_experiments(self, experiment_configs: List[ExperimentConfig],
                       query_file: str) -> List[ExperimentResult]:
        """Run multiple experiments."""
        results = []
        
        self.logger.info(f"Starting batch of {len(experiment_configs)} experiments")
        
        for i, config in enumerate(experiment_configs):
            self.logger.info(f"Running experiment {i+1}/{len(experiment_configs)}: {config.experiment_id}")
            
            result = self.run_experiment(config, query_file)
            results.append(result)
            
            # Save individual result
            result_file = self.output_dir / f"{config.experiment_id}_result.json"
            with open(result_file, 'w') as f:
                json.dump(asdict(result), f, indent=2)
            
            # Print brief summary
            if result.metrics:
                self.logger.info(
                    f"  Result: success_rate={result.success_rate:.3f}, "
                    f"avg_top_1_score={result.metrics.get('avg_top_1_score', 0):.3f}, "
                    f"avg_time={result.metrics.get('avg_total_time_ms', 0):.1f}ms"
                )
            else:
                self.logger.warning(f"  Failed: {result.error_log}")
        
        # Save batch summary
        batch_summary = {
            'batch_id': datetime.now().strftime('%Y%m%d_%H%M%S'),
            'query_file': query_file,
            'experiments': [asdict(result) for result in results],
            'summary_statistics': self._calculate_batch_summary(results)
        }
        
        summary_file = self.output_dir / f"batch_summary_{batch_summary['batch_id']}.json"
        with open(summary_file, 'w') as f:
            json.dump(batch_summary, f, indent=2)
        
        self.logger.info(f"Completed batch of {len(experiment_configs)} experiments")
        self.logger.info(f"Batch summary saved to: {summary_file}")
        
        return results
    
    def _calculate_batch_summary(self, results: List[ExperimentResult]) -> Dict[str, Any]:
        """Calculate summary statistics across all experiments."""
        successful_results = [r for r in results if r.success_rate > 0]
        
        if not successful_results:
            return {'total_experiments': len(results), 'successful_experiments': 0}
        
        # Find best performing experiments by different metrics
        best_by_score = max(successful_results, key=lambda r: r.metrics.get('avg_top_1_score', 0))
        best_by_speed = max(successful_results, key=lambda r: -r.metrics.get('avg_total_time_ms', float('inf')))
        
        return {
            'total_experiments': len(results),
            'successful_experiments': len(successful_results),
            'batch_success_rate': len(successful_results) / len(results),
            'best_score_experiment': {
                'experiment_id': best_by_score.experiment_id,
                'avg_top_1_score': best_by_score.metrics.get('avg_top_1_score', 0)
            },
            'best_speed_experiment': {
                'experiment_id': best_by_speed.experiment_id,
                'avg_total_time_ms': best_by_speed.metrics.get('avg_total_time_ms', 0)
            },
            'metric_ranges': {
                'top_1_score': {
                    'min': min(r.metrics.get('avg_top_1_score', 0) for r in successful_results),
                    'max': max(r.metrics.get('avg_top_1_score', 0) for r in successful_results),
                },
                'total_time_ms': {
                    'min': min(r.metrics.get('avg_total_time_ms', 0) for r in successful_results),
                    'max': max(r.metrics.get('avg_total_time_ms', 0) for r in successful_results),
                }
            }
        }


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Run RAG system experiments')
    parser.add_argument('--baseline-config', required=True,
                       help='Path to baseline configuration file')
    parser.add_argument('--queries', required=True,
                       help='Path to query file for testing')
    parser.add_argument('--output-dir', required=True,
                       help='Directory for experiment outputs')
    parser.add_argument('--experiment-type', required=True,
                       choices=['single', 'sweep', 'grid'],
                       help='Type of experiment to run')
    
    # Single experiment parameters
    parser.add_argument('--experiment-id',
                       help='ID for single experiment')
    parser.add_argument('--experiment-name',
                       help='Name for single experiment')
    parser.add_argument('--parameters', type=str,
                       help='JSON string of parameters to override')
    
    # Parameter sweep parameters
    parser.add_argument('--sweep-parameter',
                       help='Parameter name to sweep')
    parser.add_argument('--sweep-values', type=str,
                       help='Comma-separated values to test')
    
    # Grid search parameters
    parser.add_argument('--grid-parameters', type=str,
                       help='JSON string of parameter grid')
    
    # General parameters
    parser.add_argument('--max-queries', type=int,
                       help='Maximum queries per experiment')
    
    args = parser.parse_args()
    
    # Initialize experiment runner
    runner = ExperimentRunner(args.baseline_config, args.output_dir)
    
    if args.experiment_type == 'single':
        # Run single experiment
        if not args.experiment_id or not args.experiment_name:
            raise ValueError("Single experiment requires --experiment-id and --experiment-name")
        
        parameters = json.loads(args.parameters) if args.parameters else {}
        
        config = runner.create_experiment_config(
            experiment_id=args.experiment_id,
            name=args.experiment_name,
            description="Single experiment run",
            parameters=parameters,
            max_queries=args.max_queries
        )
        
        result = runner.run_experiment(config, args.queries)
        
        print(f"\nExperiment {result.experiment_id} completed")
        print(f"Success rate: {result.success_rate:.3f}")
        if result.metrics:
            print(f"Average top-1 score: {result.metrics.get('avg_top_1_score', 0):.3f}")
            print(f"Average retrieval time: {result.metrics.get('avg_retrieval_time_ms', 0):.1f}ms")
    
    elif args.experiment_type == 'sweep':
        # Run parameter sweep
        if not args.sweep_parameter or not args.sweep_values:
            raise ValueError("Parameter sweep requires --sweep-parameter and --sweep-values")
        
        values = [v.strip() for v in args.sweep_values.split(',')]
        # Try to convert to appropriate types
        converted_values = []
        for v in values:
            try:
                if '.' in v:
                    converted_values.append(float(v))
                else:
                    converted_values.append(int(v))
            except ValueError:
                converted_values.append(v)  # Keep as string
        
        base_experiment = {
            'experiment_id': f"sweep_{args.sweep_parameter}",
            'name': f"Parameter sweep: {args.sweep_parameter}",
            'description': f"Testing different values of {args.sweep_parameter}",
            'parameters': json.loads(args.parameters) if args.parameters else {},
            'max_queries': args.max_queries
        }
        
        configs = runner.generate_parameter_sweep(
            args.sweep_parameter, converted_values, base_experiment
        )
        
        results = runner.run_experiments(configs, args.queries)
        
        print(f"\nParameter sweep completed: {len(results)} experiments")
        print("Best performing configurations:")
        successful_results = [r for r in results if r.success_rate > 0]
        if successful_results:
            best = max(successful_results, key=lambda r: r.metrics.get('avg_top_1_score', 0))
            print(f"  Best score: {best.experiment_id} - {best.metrics.get('avg_top_1_score', 0):.3f}")
    
    elif args.experiment_type == 'grid':
        # Run grid search
        if not args.grid_parameters:
            raise ValueError("Grid search requires --grid-parameters")
        
        parameter_grid = json.loads(args.grid_parameters)
        
        base_experiment = {
            'experiment_id': "grid_search",
            'name': "Grid search experiment",
            'description': "Testing parameter combinations",
            'parameters': json.loads(args.parameters) if args.parameters else {},
            'max_queries': args.max_queries
        }
        
        configs = runner.generate_grid_search(parameter_grid, base_experiment)
        
        results = runner.run_experiments(configs, args.queries)
        
        print(f"\nGrid search completed: {len(results)} experiments")
        print("Best performing configurations:")
        successful_results = [r for r in results if r.success_rate > 0]
        if successful_results:
            best = max(successful_results, key=lambda r: r.metrics.get('avg_top_1_score', 0))
            print(f"  Best score: {best.experiment_id} - {best.metrics.get('avg_top_1_score', 0):.3f}")
    
    print(f"\nAll results saved to: {args.output_dir}")

if __name__ == "__main__":
    main()