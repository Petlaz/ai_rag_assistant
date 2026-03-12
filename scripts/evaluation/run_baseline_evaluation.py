#!/usr/bin/env python3
"""
Baseline Evaluation Master Orchestrator

This script orchestrates the complete baseline evaluation pipeline for RAG systems.
It establishes comprehensive performance benchmarks and statistical baselines for model
comparison and optimization.

Features:
- Automated baseline performance measurement
- Multi-domain query evaluation
- Statistical confidence interval calculation
- Comprehensive results aggregation
- Experiment setup and environment validation
- Standardized evaluation methodology
- Performance degradation detection
- Quality assurance checks

Usage:
    # Run complete baseline evaluation
    python scripts/evaluation/run_baseline_evaluation.py
    
    # Quick evaluation with limited queries
    python scripts/evaluation/run_baseline_evaluation.py --max-queries 50 --skip-analysis
    
    # Domain-specific evaluation
    python scripts/evaluation/run_baseline_evaluation.py --domains "medical,technical"
"""

import subprocess
import json
import argparse
import sys
import os
from pathlib import Path
from datetime import datetime

def run_command(cmd, description="", check=True):
    """Run a shell command and handle output."""
    print(f"\n>>> {description}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, check=check, capture_output=True, text=True)
        
        if result.stdout:
            print("Output:", result.stdout.strip())
        
        if result.stderr and result.returncode == 0:
            print("Warnings:", result.stderr.strip())
        
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error running command: {e}")
        if e.stderr:
            print(f"Error output: {e.stderr}")
        if not check:
            return e
        raise

def create_directory_structure(base_dir):
    """Create directory structure for baseline evaluation."""
    directories = [
        "data/evaluation",
        "results/baseline_evaluation/baseline",
        "results/baseline_evaluation/experiments", 
        "results/baseline_evaluation/analysis",
        "logs",
        "mlruns",
        ".github/workflows"
    ]
    
    base_path = Path(base_dir)
    created = []
    
    for directory in directories:
        dir_path = base_path / directory
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All directories already exist")

def generate_test_queries(output_dir, domains="cs_ai,life_sciences,physics,social_sciences", 
                         queries_per_domain=25):
    """Create domain-specific test queries."""
    
    script_path = Path(__file__).parent / "create_domain_queries.py"
    output_path = Path(output_dir) / "evaluation"
    
    cmd = [
        sys.executable, str(script_path),
        "--domains", domains,
        "--queries-per-domain", str(queries_per_domain),
        "--output-dir", str(output_path),
        "--cross-domain"
    ]
    
    run_command(cmd, f"Creating domain-specific queries in {output_path}")
    
    # Return list of created query files
    query_files = list(output_path.glob("*_queries.jsonl"))
    return [str(f) for f in query_files]

def run_baseline_evaluation(query_file, config_file, output_file, max_queries=None):
    """Run baseline evaluation on query set."""
    
    script_path = Path(__file__).parent / "baseline_evaluation.py"
    
    cmd = [
        sys.executable, str(script_path),
        "--queries", query_file,
        "--config", config_file,
        "--output", output_file,
        "--use-reranking"  # Enable reranking for baseline
    ]
    
    if max_queries:
        cmd.extend(["--max-queries", str(max_queries)])
    
    run_command(cmd, f"Running baseline evaluation: {Path(query_file).stem}")

def run_statistical_analysis(results_file, output_dir):
    """Run statistical analysis on evaluation results."""
    
    script_path = Path(__file__).parent / "analyze_eval_results.py"
    
    cmd = [
        sys.executable, str(script_path),
        "--results", results_file,
        "--output-dir", output_dir,
        "--analysis-type", "baseline",
        "--confidence-level", "0.95"
    ]
    
    run_command(cmd, f"Analyzing results: {Path(results_file).name}")

def main():
    """Main baseline evaluation execution function."""
    parser = argparse.ArgumentParser(description='Baseline Evaluation Setup and Execution')
    parser.add_argument('--project-dir', default='.',
                       help='Project root directory (default: current directory)')
    parser.add_argument('--domains', default='cs_ai,life_sciences,physics,social_sciences',
                       help='Comma-separated domains to test')
    parser.add_argument('--queries-per-domain', type=int, default=25,
                       help='Number of queries per domain')
    parser.add_argument('--max-queries', type=int, 
                       help='Maximum queries per evaluation (for testing)')
    parser.add_argument('--skip-setup', action='store_true',
                       help='Skip directory setup and query creation')
    parser.add_argument('--skip-evaluation', action='store_true',
                       help='Skip baseline evaluation')
    parser.add_argument('--skip-analysis', action='store_true',
                       help='Skip statistical analysis')
    
    args = parser.parse_args()
    
    # Setup paths
    project_dir = Path(args.project_dir).resolve()
    data_dir = project_dir / "data"
    results_dir = project_dir / "results" / "baseline_evaluation"
    config_file = project_dir / "configs" / "baseline_config.json"
    
    print(f"=== BASELINE EVALUATION ===\n")
    print(f"Project directory: {project_dir}")
    print(f"Timestamp: {datetime.now().isoformat()}")
    
    # Step 1: Directory setup
    if not args.skip_setup:
        print(f"\n--- Step 1: Directory Setup ---")
        create_directory_structure(project_dir)
        
        # Step 2: Query Creation
        print(f"\n--- Step 2: Query Creation ---")
        query_files = generate_test_queries(
            data_dir, 
            args.domains, 
            args.queries_per_domain
        )
        print(f"Created query files: {query_files}")
    else:
        # Look for existing query files
        query_files = list((data_dir / "evaluation").glob("*_queries.jsonl"))
        query_files = [str(f) for f in query_files]
        print(f"Using existing query files: {query_files}")
    
    # Step 3: Baseline Evaluation
    if not args.skip_evaluation and query_files:
        print(f"\n--- Step 3: Baseline Evaluation ---")
        
        if not config_file.exists():
            print(f"Error: Configuration file not found: {config_file}")
            print("Please ensure baseline_config.json exists in configs/")
            return 1
        
        # Run evaluation for each domain
        evaluation_results = []
        for query_file in query_files:
            domain = Path(query_file).stem.replace('_queries', '')
            output_file = results_dir / "baseline" / f"{domain}_results.jsonl"
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            try:
                run_baseline_evaluation(
                    query_file, 
                    str(config_file), 
                    str(output_file),
                    args.max_queries
                )
                evaluation_results.append(str(output_file))
            except Exception as e:
                print(f"Warning: Failed to evaluate {domain}: {e}")
        
        print(f"Evaluation complete. Results saved: {evaluation_results}")
    
    # Step 4: Statistical Analysis
    if not args.skip_analysis:
        print(f"\n--- Step 4: Statistical Analysis ---")
        
        result_files = list((results_dir / "baseline").glob("*_results.jsonl"))
        
        for result_file in result_files:
            analysis_dir = results_dir / "analysis" / result_file.stem.replace('_results', '')
            analysis_dir.mkdir(parents=True, exist_ok=True)
            
            try:
                run_statistical_analysis(str(result_file), str(analysis_dir))
            except Exception as e:
                print(f"Warning: Failed to analyze {result_file.name}: {e}")
    
    # Summary
    print(f"\n=== BASELINE EVALUATION COMPLETE ===\n")
    print(f"Results directory: {results_dir}")
    
    if (results_dir / "baseline").exists():
        result_files = list((results_dir / "baseline").glob("*_results.jsonl"))
        print(f"Baseline results: {len(result_files)} files")
    
    if (results_dir / "analysis").exists():
        analysis_dirs = list((results_dir / "analysis").glob("*"))
        print(f"Analysis reports: {len(analysis_dirs)} directories")
    
    print("\nNext Steps:")
    print("1. Review baseline analysis reports")
    print("2. Identify optimization opportunities") 
    print("3. Plan model optimization experiments")
    print("4. Use ab_testing/experiment_pipeline.py for parameter testing")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())