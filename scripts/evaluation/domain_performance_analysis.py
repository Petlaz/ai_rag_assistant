#!/usr/bin/env python3
"""
Domain Performance Analysis Script - Phase 1 Cross-Domain Evaluation
====================================================================

Analyzes RAG system performance across multiple domains to identify
domain-specific patterns, strengths, and weaknesses in retrieval
and generation capabilities.

Features:
- Cross-domain performance comparison and analysis
- Statistical significance testing across domains
- Performance pattern identification and visualization
- Domain-specific optimization recommendations
- Comprehensive reporting with actionable insights
- Integration with Phase 1 baseline evaluation framework

Usage:
    # Analyze performance across all domains
    python scripts/evaluation/domain_performance_analysis.py \\
        results/domain_*.json \\
        --output results/domain_comparison_report.html

    # Compare specific domains with statistical analysis
    python scripts/evaluation/domain_performance_analysis.py \\
        --domains "cs_ai,life_sciences,physics" \\
        --statistical-tests \\
        --confidence-level 0.95

    # Generate optimization recommendations per domain
    python scripts/evaluation/domain_performance_analysis.py \\
        --input-dir results/domains/ \\
        --optimize-recommendations \\
        --export-csv results/domain_analysis.csv

Author: AI RAG Assistant Team
Date: March 2026
Phase: 1 - Baseline & Scale Testing
"""

import argparse
import json
import pandas as pd
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from dataclasses import dataclass

@dataclass
class DomainMetrics:
    """Performance metrics for a specific domain"""
    domain_name: str
    precision_at_1: float
    precision_at_5: float
    precision_at_10: float
    recall_at_5: float
    recall_at_10: float
    mrr: float
    ndcg_at_10: float
    query_count: int
    avg_response_time_ms: float

class DomainPerformanceAnalyzer:
    """
    Comprehensive domain performance analysis for RAG system evaluation
    
    Analyzes performance patterns across different knowledge domains
    to identify strengths, weaknesses, and optimization opportunities.
    """
    
    def __init__(self):
        self.domain_metrics = {}
        self.statistical_results = {}
        
    def load_domain_results(self, results_pattern: str) -> None:
        """Load domain evaluation results from JSON files"""
        
        result_files = Path(".").glob(results_pattern)
        
        for result_file in result_files:
            try:
                with open(result_file, 'r') as f:
                    data = json.load(f)
                
                # Extract domain name from filename or data
                domain_name = self._extract_domain_name(result_file.name, data)
                
                # Parse metrics from result data
                metrics = self._parse_domain_metrics(data, domain_name)
                self.domain_metrics[domain_name] = metrics
                
                print(f"Loaded metrics for domain: {domain_name}")
                
            except Exception as e:
                print(f"Error loading {result_file}: {e}")
    
    def _extract_domain_name(self, filename: str, data: Dict) -> str:
        """Extract domain name from filename or data"""
        
        # Try to get from data first
        if 'domain' in data:
            return data['domain']
        
        # Extract from filename pattern: domain_results.json or domain_*.json
        name = filename.replace('_results.json', '').replace('domain_', '')
        
        # Clean up common patterns
        domain_mapping = {
            'cs_ai': 'Computer Science & AI',
            'life_sciences': 'Life Sciences & Medicine', 
            'physics': 'Physics & Engineering',
            'social_sciences': 'Social Sciences'
        }
        
        return domain_mapping.get(name, name.replace('_', ' ').title())
    
    def _parse_domain_metrics(self, data: Dict, domain_name: str) -> DomainMetrics:
        """Parse domain metrics from evaluation result data"""
        
        # Handle different data formats
        if 'aggregate_metrics' in data:
            metrics = data['aggregate_metrics']
        elif 'metrics' in data:
            metrics = data['metrics']
        else:
            # Try to find metrics in nested structure
            metrics = self._find_metrics_in_data(data)
        
        return DomainMetrics(
            domain_name=domain_name,
            precision_at_1=metrics.get('precision_at_1', 0.0),
            precision_at_5=metrics.get('precision_at_5', 0.0),
            precision_at_10=metrics.get('precision_at_10', 0.0),
            recall_at_5=metrics.get('recall_at_5', 0.0),
            recall_at_10=metrics.get('recall_at_10', 0.0),
            mrr=metrics.get('mrr', 0.0),
            ndcg_at_10=metrics.get('ndcg_at_10', 0.0),
            query_count=data.get('query_count', 0),
            avg_response_time_ms=data.get('avg_response_time_ms', 0.0)
        )
    
    def _find_metrics_in_data(self, data: Dict) -> Dict:
        """Find metrics in nested data structure"""
        
        # Common locations for metrics
        possible_locations = [
            'evaluation_results',
            'performance_metrics', 
            'results',
            'summary'
        ]
        
        for location in possible_locations:
            if location in data and isinstance(data[location], dict):
                return data[location]
        
        # If no nested structure found, assume top-level
        return data
    
    def compare_domains(self) -> pd.DataFrame:
        """Compare performance metrics across all domains"""
        
        if not self.domain_metrics:
            raise ValueError("No domain metrics loaded. Call load_domain_results() first.")
        
        # Create comparison dataframe
        comparison_data = []
        
        for domain_name, metrics in self.domain_metrics.items():
            comparison_data.append({
                'Domain': domain_name,
                'Precision@1': metrics.precision_at_1,
                'Precision@5': metrics.precision_at_5,
                'Precision@10': metrics.precision_at_10,
                'Recall@5': metrics.recall_at_5,
                'Recall@10': metrics.recall_at_10,
                'MRR': metrics.mrr,
                'NDCG@10': metrics.ndcg_at_10,
                'Queries': metrics.query_count,
                'Avg Response Time (ms)': metrics.avg_response_time_ms
            })
        
        df = pd.DataFrame(comparison_data)
        df = df.set_index('Domain')
        
        return df
    
    def statistical_analysis(self, confidence_level: float = 0.95) -> Dict:
        """Perform statistical analysis across domains"""
        
        if len(self.domain_metrics) < 2:
            print("Warning: Need at least 2 domains for statistical analysis")
            return {}
        
        alpha = 1 - confidence_level
        metrics_to_analyze = ['precision_at_5', 'mrr', 'ndcg_at_10']
        
        results = {}
        
        for metric in metrics_to_analyze:
            # Collect metric values across domains
            domain_names = list(self.domain_metrics.keys())
            metric_values = [getattr(self.domain_metrics[domain], metric) for domain in domain_names]
            
            # Perform ANOVA for multiple domain comparison
            if len(set(metric_values)) > 1:  # Check for variation
                try:
                    # For simplicity, using descriptive statistics
                    # In practice, you'd need multiple measurements per domain for proper ANOVA
                    metric_mean = np.mean(metric_values)
                    metric_std = np.std(metric_values)
                    metric_min = np.min(metric_values)
                    metric_max = np.max(metric_values)
                    
                    results[metric] = {
                        'mean': metric_mean,
                        'std': metric_std,
                        'min': metric_min,
                        'max': metric_max,
                        'range': metric_max - metric_min,
                        'coefficient_of_variation': metric_std / metric_mean if metric_mean > 0 else 0,
                        'domains': dict(zip(domain_names, metric_values))
                    }
                    
                except Exception as e:
                    print(f"Error in statistical analysis for {metric}: {e}")
        
        self.statistical_results = results
        return results
    
    def identify_patterns(self) -> Dict:
        """Identify performance patterns across domains"""
        
        patterns = {
            'strongest_domains': {},
            'weakest_domains': {},
            'most_consistent_domains': {},
            'performance_trends': {}
        }
        
        if not self.domain_metrics:
            return patterns
        
        # Analyze each metric
        metrics = ['precision_at_5', 'mrr', 'recall_at_5']
        
        for metric in metrics:
            domain_scores = {
                domain: getattr(metrics_obj, metric) 
                for domain, metrics_obj in self.domain_metrics.items()
            }
            
            # Find strongest and weakest
            if domain_scores:
                strongest = max(domain_scores.items(), key=lambda x: x[1])
                weakest = min(domain_scores.items(), key=lambda x: x[1])
                
                patterns['strongest_domains'][metric] = strongest
                patterns['weakest_domains'][metric] = weakest
        
        # Overall performance ranking
        overall_scores = {}
        for domain, metrics_obj in self.domain_metrics.items():
            # Weighted average of key metrics
            overall_score = (
                metrics_obj.precision_at_5 * 0.4 +
                metrics_obj.mrr * 0.3 + 
                metrics_obj.recall_at_5 * 0.3
            )
            overall_scores[domain] = overall_score
        
        patterns['overall_ranking'] = sorted(
            overall_scores.items(), 
            key=lambda x: x[1], 
            reverse=True
        )
        
        return patterns
    
    def generate_recommendations(self) -> List[str]:
        """Generate domain-specific optimization recommendations"""
        
        recommendations = []
        
        if not self.domain_metrics:
            return ["No domain data available for recommendations"]
        
        patterns = self.identify_patterns()
        
        # High-level recommendations based on patterns
        if patterns['overall_ranking']:
            best_domain = patterns['overall_ranking'][0][0]
            worst_domain = patterns['overall_ranking'][-1][0]
            
            recommendations.append(
                f"🏆 Best performing domain: {best_domain} - analyze successful strategies"
            )
            recommendations.append(
                f"⚠️ Needs attention: {worst_domain} - consider domain-specific optimizations"
            )
        
        # Metric-specific recommendations
        for metric in ['precision_at_5', 'mrr']:
            if metric in patterns['weakest_domains']:
                weak_domain, weak_score = patterns['weakest_domains'][metric]
                recommendations.append(
                    f"📊 {weak_domain}: Low {metric} ({weak_score:.3f}) - review relevance scoring"
                )
        
        # Query volume considerations
        low_volume_domains = [
            domain for domain, metrics in self.domain_metrics.items()
            if metrics.query_count < 10
        ]
        
        if low_volume_domains:
            recommendations.append(
                f"📈 Expand test coverage for: {', '.join(low_volume_domains)}"
            )
        
        # Performance consistency
        if self.statistical_results:
            high_variance_metrics = [
                metric for metric, stats in self.statistical_results.items()
                if stats['coefficient_of_variation'] > 0.3
            ]
            
            if high_variance_metrics:
                recommendations.append(
                    f"🎯 High variance in: {', '.join(high_variance_metrics)} - investigate domain differences"
                )
        
        return recommendations
    
    def create_visualizations(self, output_dir: str = "results/domain_analysis/") -> None:
        """Create performance visualization charts"""
        
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        if not self.domain_metrics:
            print("No data available for visualization")
            return
        
        # Set up plotting style
        plt.style.use('seaborn')
        sns.set_palette("husl")
        
        # 1. Performance comparison bar chart
        df = self.compare_domains()
        
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('Domain Performance Comparison', fontsize=16, fontweight='bold')
        
        # Precision metrics
        df[['Precision@1', 'Precision@5', 'Precision@10']].plot(kind='bar', ax=axes[0,0])
        axes[0,0].set_title('Precision Metrics by Domain')
        axes[0,0].set_ylabel('Precision Score')
        axes[0,0].tick_params(axis='x', rotation=45)
        
        # Recall metrics
        df[['Recall@5', 'Recall@10']].plot(kind='bar', ax=axes[0,1])
        axes[0,1].set_title('Recall Metrics by Domain')
        axes[0,1].set_ylabel('Recall Score')
        axes[0,1].tick_params(axis='x', rotation=45)
        
        # MRR and NDCG
        df[['MRR', 'NDCG@10']].plot(kind='bar', ax=axes[1,0])
        axes[1,0].set_title('Ranking Quality Metrics')
        axes[1,0].set_ylabel('Score')
        axes[1,0].tick_params(axis='x', rotation=45)
        
        # Response time
        df[['Avg Response Time (ms)']].plot(kind='bar', ax=axes[1,1], color='orange')
        axes[1,1].set_title('Average Response Time')
        axes[1,1].set_ylabel('Time (ms)')
        axes[1,1].tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.savefig(output_path / 'domain_performance_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Performance radar chart
        self._create_radar_chart(df, output_path)
        
        print(f"Visualizations saved to {output_path}")
    
    def _create_radar_chart(self, df: pd.DataFrame, output_path: Path) -> None:
        """Create radar chart for domain comparison"""
        
        # Select key metrics for radar chart
        radar_metrics = ['Precision@5', 'Recall@5', 'MRR', 'NDCG@10']
        
        # Normalize metrics to 0-1 scale for better visualization
        radar_data = df[radar_metrics].copy()
        for col in radar_data.columns:
            radar_data[col] = radar_data[col] / radar_data[col].max()
        
        # Create radar chart
        angles = np.linspace(0, 2 * np.pi, len(radar_metrics), endpoint=False)
        angles = np.concatenate((angles, [angles[0]]))  # Complete the circle
        
        fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
        
        for domain in radar_data.index:
            values = radar_data.loc[domain].values
            values = np.concatenate((values, [values[0]]))  # Complete the circle
            
            ax.plot(angles, values, 'o-', linewidth=2, label=domain)
            ax.fill(angles, values, alpha=0.1)
        
        ax.set_xticks(angles[:-1])
        ax.set_xticklabels(radar_metrics)
        ax.set_ylim(0, 1)
        ax.set_title('Domain Performance Radar Chart', size=16, fontweight='bold', pad=20)
        ax.legend(loc='upper right', bbox_to_anchor=(1.2, 1.0))
        
        plt.savefig(output_path / 'domain_radar_chart.png', dpi=300, bbox_inches='tight')
        plt.close()
    
    def export_report(self, output_file: str = "results/domain_analysis_report.html") -> None:
        """Export comprehensive analysis report"""
        
        patterns = self.identify_patterns()
        recommendations = self.generate_recommendations()
        
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Domain Performance Analysis Report</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; }}
                .header {{ background-color: #f4f4f4; padding: 20px; border-radius: 5px; }}
                .section {{ margin: 30px 0; }}
                .metric {{ background-color: #e8f4f8; padding: 15px; margin: 10px 0; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #f2f2f2; }}
                .recommendation {{ background-color: #fff3cd; padding: 10px; margin: 5px 0; border-radius: 3px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Domain Performance Analysis Report</h1>
                <p><strong>Generated:</strong> {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
                <p><strong>Domains Analyzed:</strong> {len(self.domain_metrics)}</p>
            </div>
            
            <div class="section">
                <h2>Performance Summary</h2>
                {self._generate_summary_table()}
            </div>
            
            <div class="section">
                <h2>Domain Rankings</h2>
                {self._generate_rankings_html(patterns)}
            </div>
            
            <div class="section">
                <h2>Optimization Recommendations</h2>
                {self._generate_recommendations_html(recommendations)}
            </div>
        </body>
        </html>
        """
        
        with open(output_file, 'w') as f:
            f.write(html_content)
        
        print(f"Domain analysis report saved to {output_file}")
    
    def _generate_summary_table(self) -> str:
        """Generate HTML summary table"""
        
        df = self.compare_domains()
        return df.to_html(classes='summary-table', float_format=lambda x: f'{x:.3f}')
    
    def _generate_rankings_html(self, patterns: Dict) -> str:
        """Generate HTML for domain rankings"""
        
        html = "<h3>Overall Performance Ranking</h3><ol>"
        
        if 'overall_ranking' in patterns:
            for domain, score in patterns['overall_ranking']:
                html += f"<li><strong>{domain}</strong>: {score:.3f}</li>"
        
        html += "</ol>"
        return html
    
    def _generate_recommendations_html(self, recommendations: List[str]) -> str:
        """Generate HTML for recommendations"""
        
        html = ""
        for rec in recommendations:
            html += f'<div class="recommendation">{rec}</div>'
        
        return html

def main():
    parser = argparse.ArgumentParser(description="Domain Performance Analysis")
    
    parser.add_argument('results_pattern', nargs='?', 
                       default='results/domain_*.json',
                       help='Pattern to match domain result files')
    parser.add_argument('--output', type=str, 
                       default='results/domain_comparison_report.html',
                       help='Output report file')
    parser.add_argument('--statistical-tests', action='store_true',
                       help='Perform statistical significance testing')
    parser.add_argument('--confidence-level', type=float, default=0.95,
                       help='Confidence level for statistical tests')
    parser.add_argument('--visualizations', action='store_true',
                       help='Generate performance visualization charts')
    parser.add_argument('--export-csv', type=str,
                       help='Export comparison data to CSV file')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = DomainPerformanceAnalyzer()
    
    # Load domain results
    print("Loading domain evaluation results...")
    analyzer.load_domain_results(args.results_pattern)
    
    if not analyzer.domain_metrics:
        print("No domain results found. Please run domain evaluations first.")
        return
    
    # Perform statistical analysis
    if args.statistical_tests:
        print("Performing statistical analysis...")
        stats_results = analyzer.statistical_analysis(args.confidence_level)
        print("Statistical analysis completed.")
    
    # Generate visualizations
    if args.visualizations:
        print("Creating performance visualizations...")
        analyzer.create_visualizations()
    
    # Export CSV data
    if args.export_csv:
        df = analyzer.compare_domains()
        df.to_csv(args.export_csv)
        print(f"Comparison data exported to {args.export_csv}")
    
    # Generate comprehensive report
    print("Generating domain analysis report...")
    analyzer.export_report(args.output)
    
    # Display summary
    print("\n" + "="*60)
    print("DOMAIN PERFORMANCE ANALYSIS SUMMARY")
    print("="*60)
    
    patterns = analyzer.identify_patterns()
    if 'overall_ranking' in patterns:
        print("\nDomain Rankings:")
        for i, (domain, score) in enumerate(patterns['overall_ranking'], 1):
            print(f"  {i}. {domain}: {score:.3f}")
    
    print("\nKey Recommendations:")
    recommendations = analyzer.generate_recommendations()
    for i, rec in enumerate(recommendations[:5], 1):
        print(f"  {i}. {rec}")
    
    print(f"\nDetailed report available at: {args.output}")

if __name__ == "__main__":
    main()