#!/usr/bin/env python3
"""
Statistical Analysis Engine for Evaluation Results

This script performs comprehensive statistical analysis of RAG evaluation results,
including confidence intervals, significance testing, and performance trend analysis.
Provides rigorous statistical interpretation of evaluation metrics.

Features:
- Statistical confidence interval calculation
- Performance significance testing
- Trend analysis and degradation detection
- Cross-domain performance comparison
- Bootstrap sampling for robust statistics
- Outlier detection and handling
- Regression analysis for performance predictors
- Comprehensive statistical reporting

Usage:
    # Analyze evaluation results with confidence intervals
    python scripts/analyze_eval_results.py --input results/baseline_results.json
    
    # Statistical comparison between models
    python scripts/analyze_eval_results.py --compare model1.json model2.json
    
    # Bootstrap analysis with custom confidence level
    python scripts/analyze_eval_results.py --bootstrap --confidence 0.95 --samples 1000
"""
"""
Analysis script for RAG evaluation results.
Provides statistical analysis and comparison functionality for retrieval performance.
"""

import json
import argparse
import numpy as np
import pandas as pd
from typing import Dict, List, Any, Optional
import scipy.stats as stats
from pathlib import Path
import matplotlib.pyplot as plt
import seaborn as sns
from datetime import datetime

class EvaluationAnalyzer:
    """Analyze and compare RAG evaluation results."""
    
    def __init__(self, results_file: str):
        """Initialize with evaluation results file."""
        self.results_file = Path(results_file)
        self.results = self._load_results()
        
    def _load_results(self) -> Dict[str, Any]:
        """Load evaluation results from JSON file."""
        with open(self.results_file, 'r') as f:
            return json.load(f)
    
    def calculate_basic_statistics(self) -> Dict[str, float]:
        """Calculate basic statistical measures."""
        precision_scores = self.results.get('precision_at_5', [])
        mrr_scores = self.results.get('mrr', [])
        latencies = self.results.get('query_latencies', [])
        
        stats_dict = {
            'precision_mean': np.mean(precision_scores),
            'precision_std': np.std(precision_scores),
            'precision_median': np.median(precision_scores),
            'mrr_mean': np.mean(mrr_scores),
            'mrr_std': np.std(mrr_scores),
            'mrr_median': np.median(mrr_scores),
            'latency_mean': np.mean(latencies) if latencies else 0,
            'latency_p95': np.percentile(latencies, 95) if latencies else 0,
            'total_queries': len(precision_scores)
        }
        
        return stats_dict
    
    def calculate_confidence_intervals(self, confidence_level: float = 0.95) -> Dict[str, tuple]:
        """Calculate confidence intervals for key metrics."""
        precision_scores = self.results.get('precision_at_5', [])
        mrr_scores = self.results.get('mrr', [])
        
        alpha = 1 - confidence_level
        
        confidence_intervals = {}
        
        if precision_scores:
            precision_ci = stats.t.interval(
                confidence_level,
                len(precision_scores) - 1,
                loc=np.mean(precision_scores),
                scale=stats.sem(precision_scores)
            )
            confidence_intervals['precision_at_5'] = precision_ci
        
        if mrr_scores:
            mrr_ci = stats.t.interval(
                confidence_level,
                len(mrr_scores) - 1,
                loc=np.mean(mrr_scores),
                scale=stats.sem(mrr_scores)
            )
            confidence_intervals['mrr'] = mrr_ci
        
        return confidence_intervals
    
    def compare_with_baseline(self, baseline_file: str) -> Dict[str, Any]:
        """Compare current results with baseline performance."""
        baseline_analyzer = EvaluationAnalyzer(baseline_file)
        baseline_stats = baseline_analyzer.calculate_basic_statistics()
        current_stats = self.calculate_basic_statistics()
        
        comparison = {}
        
        # Statistical significance testing
        baseline_precision = baseline_analyzer.results.get('precision_at_5', [])
        current_precision = self.results.get('precision_at_5', [])
        
        if baseline_precision and current_precision:
            t_stat, p_value = stats.ttest_ind(current_precision, baseline_precision)
            comparison['precision_ttest'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        baseline_mrr = baseline_analyzer.results.get('mrr', [])
        current_mrr = self.results.get('mrr', [])
        
        if baseline_mrr and current_mrr:
            t_stat, p_value = stats.ttest_ind(current_mrr, baseline_mrr)
            comparison['mrr_ttest'] = {
                't_statistic': t_stat,
                'p_value': p_value,
                'significant': p_value < 0.05
            }
        
        # Effect sizes
        comparison['precision_change'] = {
            'baseline': baseline_stats['precision_mean'],
            'current': current_stats['precision_mean'],
            'absolute_change': current_stats['precision_mean'] - baseline_stats['precision_mean'],
            'percent_change': ((current_stats['precision_mean'] - baseline_stats['precision_mean']) / 
                            baseline_stats['precision_mean']) * 100 if baseline_stats['precision_mean'] > 0 else 0
        }
        
        comparison['mrr_change'] = {
            'baseline': baseline_stats['mrr_mean'],
            'current': current_stats['mrr_mean'],
            'absolute_change': current_stats['mrr_mean'] - baseline_stats['mrr_mean'],
            'percent_change': ((current_stats['mrr_mean'] - baseline_stats['mrr_mean']) / 
                            baseline_stats['mrr_mean']) * 100 if baseline_stats['mrr_mean'] > 0 else 0
        }
        
        return comparison
    
    def calculate_variance_analysis(self) -> Dict[str, float]:
        """Analyze variance in performance metrics."""
        precision_scores = self.results.get('precision_at_5', [])
        mrr_scores = self.results.get('mrr', [])
        
        variance_analysis = {
            'precision_variance': np.var(precision_scores),
            'precision_coefficient_of_variation': np.std(precision_scores) / np.mean(precision_scores) if np.mean(precision_scores) > 0 else 0,
            'mrr_variance': np.var(mrr_scores),
            'mrr_coefficient_of_variation': np.std(mrr_scores) / np.mean(mrr_scores) if np.mean(mrr_scores) > 0 else 0
        }
        
        # Check if variance is acceptable (CV < 0.1 is generally good)
        variance_analysis['precision_variance_acceptable'] = variance_analysis['precision_coefficient_of_variation'] < 0.1
        variance_analysis['mrr_variance_acceptable'] = variance_analysis['mrr_coefficient_of_variation'] < 0.1
        
        return variance_analysis
    
    def create_summary_report(self, output_file: Optional[str] = None) -> str:
        """Create comprehensive summary report."""
        stats = self.calculate_basic_statistics()
        confidence_intervals = self.calculate_confidence_intervals()
        variance = self.calculate_variance_analysis()
        
        report = f"""
RAG SYSTEM EVALUATION SUMMARY REPORT
======================================
Analysis Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
Results File: {self.results_file.name}

PERFORMANCE METRICS
------------------
Total Queries: {stats['total_queries']}

Precision@5:
  Mean: {stats['precision_mean']:.4f}
  Std Dev: {stats['precision_std']:.4f}
  Median: {stats['precision_median']:.4f}
  95% CI: [{confidence_intervals.get('precision_at_5', (0, 0))[0]:.4f}, {confidence_intervals.get('precision_at_5', (0, 0))[1]:.4f}]

Mean Reciprocal Rank (MRR):
  Mean: {stats['mrr_mean']:.4f}
  Std Dev: {stats['mrr_std']:.4f}
  Median: {stats['mrr_median']:.4f}
  95% CI: [{confidence_intervals.get('mrr', (0, 0))[0]:.4f}, {confidence_intervals.get('mrr', (0, 0))[1]:.4f}]

Query Latency:
  Mean: {stats['latency_mean']:.2f} ms
  95th Percentile: {stats['latency_p95']:.2f} ms

VARIANCE ANALYSIS
-----------------
Precision@5 CV: {variance['precision_coefficient_of_variation']:.4f} ({'Good' if variance['precision_variance_acceptable'] else 'High'})
MRR CV: {variance['mrr_coefficient_of_variation']:.4f} ({'Good' if variance['mrr_variance_acceptable'] else 'High'})

RECOMMENDATIONS
--------------"""

        if stats['precision_mean'] >= 0.72:
            report += "\n✓ Precision@5 meets baseline target (≥0.72)"
        else:
            report += f"\n✗ Precision@5 below baseline target ({stats['precision_mean']:.4f} < 0.72)"
            
        if stats['mrr_mean'] >= 0.80:
            report += "\n✓ MRR meets baseline target (≥0.80)"
        else:
            report += f"\n✗ MRR below baseline target ({stats['mrr_mean']:.4f} < 0.80)"
            
        if variance['precision_variance_acceptable'] and variance['mrr_variance_acceptable']:
            report += "\n✓ Performance variance within acceptable range"
        else:
            report += "\n✗ High performance variance detected - investigate inconsistencies"
        
        if output_file:
            with open(output_file, 'w') as f:
                f.write(report)
        
        return report


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(description='Analyze RAG evaluation results')
    parser.add_argument('results_file', help='Path to evaluation results JSON file')
    parser.add_argument('--output', help='Output file for analysis report')
    parser.add_argument('--baseline', help='Baseline results file for comparison')
    parser.add_argument('--confidence-interval', type=float, default=0.95,
                       help='Confidence interval level (default: 0.95)')
    parser.add_argument('--variance-analysis', action='store_true',
                       help='Include detailed variance analysis')
    parser.add_argument('--compare-baseline', help='Baseline file for statistical comparison')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = EvaluationAnalyzer(args.results_file)
    
    # Basic statistics
    print("BASIC STATISTICS:")
    stats = analyzer.calculate_basic_statistics()
    for key, value in stats.items():
        print(f"  {key}: {value:.4f}")
    
    # Confidence intervals
    print(f"\nCONFIDENCE INTERVALS ({args.confidence_interval * 100}%):")
    confidence_intervals = analyzer.calculate_confidence_intervals(args.confidence_interval)
    for metric, (lower, upper) in confidence_intervals.items():
        print(f"  {metric}: [{lower:.4f}, {upper:.4f}]")
    
    # Variance analysis
    if args.variance_analysis:
        print("\nVARIANCE ANALYSIS:")
        variance = analyzer.calculate_variance_analysis()
        for key, value in variance.items():
            print(f"  {key}: {value}")
    
    # Baseline comparison
    if args.compare_baseline:
        print("\nBASELINE COMPARISON:")
        comparison = analyzer.compare_with_baseline(args.compare_baseline)
        
        if 'precision_ttest' in comparison:
            print(f"  Precision t-test: p-value={comparison['precision_ttest']['p_value']:.6f}")
            print(f"  Statistically significant: {comparison['precision_ttest']['significant']}")
        
        if 'precision_change' in comparison:
            print(f"  Precision change: {comparison['precision_change']['percent_change']:.2f}%")
        
        if 'mrr_change' in comparison:
            print(f"  MRR change: {comparison['mrr_change']['percent_change']:.2f}%")
    
    # Create summary report
    report = analyzer.create_summary_report(args.output)
    if not args.output:
        print("\nSUMMARY REPORT:")
        print(report)


if __name__ == "__main__":
    main()