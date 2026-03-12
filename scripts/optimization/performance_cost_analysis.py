#!/usr/bin/env python3
"""
Performance vs Cost Analysis Script - Phase 2 MLOps Testing
==========================================================

Analyzes performance and cost trade-offs for different model configurations.
Provides comprehensive cost-benefit analysis for decision making.

Usage:
    python scripts/optimization/performance_cost_analysis.py \
        --embedding-results results/optimization/embedding_comparison.json \\
        --reranking-results results/optimization/reranking_evaluation.json \\
        --output results/optimization/cost_benefit_analysis.json

Author: AI RAG Assistant Team
Date: March 2026
Phase: 2 - Model Optimization
"""

import argparse
import json
import logging
import time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CostModel:
    """Cost model for different components."""
    # Compute costs (per query)
    embedding_inference_base: float = 0.00005  # Small model
    embedding_inference_large: float = 0.0001  # Large model
    
    # Re-ranking costs
    cross_encoder_cost: float = 0.0001
    llm_reranking_cost: float = 0.0  # Local Ollama
    hybrid_scoring_cost: float = 0.0  # No additional cost
    
    # Infrastructure costs (monthly)
    opensearch_monthly: float = 0.0  # Local development
    storage_monthly: float = 0.0     # Local development
    
    # Operational costs
    electricity_per_hour: float = 0.05  # Rough estimate for M1 Mac
    maintenance_monthly: float = 0.0    # Self-managed
    
    # Scale assumptions
    queries_per_month: int = 10000
    operational_hours_per_month: int = 30  # 1 hour per day average


@dataclass
class PerformanceMetrics:
    """Performance metrics for analysis."""
    precision_at_5: float
    mrr: float
    latency_ms: float
    memory_usage_mb: float
    throughput_qps: float


@dataclass
class CostBreakdown:
    """Cost breakdown for a configuration."""
    compute_cost_monthly: float
    infrastructure_cost_monthly: float
    operational_cost_monthly: float
    total_cost_monthly: float
    cost_per_query: float


@dataclass
class ConfigurationAnalysis:
    """Complete analysis for a configuration."""
    configuration_name: str
    performance: PerformanceMetrics
    cost_breakdown: CostBreakdown
    cost_effectiveness_score: float
    recommendation_rank: int
    pros: List[str]
    cons: List[str]


class PerformanceCostAnalyzer:
    """Analyzes performance vs cost trade-offs."""
    
    def __init__(self, cost_model: Optional[CostModel] = None):
        self.cost_model = cost_model or CostModel()
        self.configurations = []
        self.analysis_results = []
        
    def load_embedding_results(self, results_path: Path) -> List[Dict]:
        """Load embedding model comparison results."""
        try:
            with open(results_path, 'r') as f:
                data = json.load(f)
            
            models = data.get('model_performance', [])
            logger.info(f"Loaded {len(models)} embedding model results")
            return models
            
        except FileNotFoundError:
            logger.warning(f"Embedding results not found: {results_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing embedding results: {e}")
            return []
            
    def load_reranking_results(self, results_path: Path) -> List[Dict]:
        """Load re-ranking strategy results."""
        try:
            with open(results_path, 'r') as f:
                data = json.load(f)
                
            strategies = data.get('strategy_performance', [])
            logger.info(f"Loaded {len(strategies)} re-ranking strategy results")
            return strategies
            
        except FileNotFoundError:
            logger.warning(f"Re-ranking results not found: {results_path}")
            return []
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing re-ranking results: {e}")
            return []
            
    def calculate_embedding_cost(self, model_name: str, inference_time_ms: float) -> float:
        """Calculate cost per query for embedding model."""
        # Base cost depends on model size
        if 'mpnet' in model_name.lower() or 'large' in model_name.lower():
            base_cost = self.cost_model.embedding_inference_large
        else:
            base_cost = self.cost_model.embedding_inference_base
            
        # Adjust for inference time (longer = more expensive)
        time_multiplier = max(1.0, inference_time_ms / 50.0)  # 50ms baseline
        
        return base_cost * time_multiplier
        
    def calculate_reranking_cost(self, strategy_name: str, rerank_time_ms: float) -> float:
        """Calculate cost per query for re-ranking strategy."""
        if strategy_name == 'cross_encoder':
            return self.cost_model.cross_encoder_cost
        elif strategy_name == 'ollama_llm':
            return self.cost_model.llm_reranking_cost  # Local, no cost
        elif strategy_name == 'hybrid_scoring':
            return self.cost_model.hybrid_scoring_cost  # No additional cost
        else:
            return 0.0
            
    def calculate_total_cost_breakdown(self, embedding_cost: float, 
                                     reranking_cost: float) -> CostBreakdown:
        """Calculate total cost breakdown."""
        # Monthly compute cost
        compute_cost_monthly = (embedding_cost + reranking_cost) * self.cost_model.queries_per_month
        
        # Infrastructure cost
        infrastructure_cost_monthly = (
            self.cost_model.opensearch_monthly +
            self.cost_model.storage_monthly
        )
        
        # Operational cost
        operational_cost_monthly = (
            self.cost_model.electricity_per_hour * 
            self.cost_model.operational_hours_per_month +
            self.cost_model.maintenance_monthly
        )
        
        total_cost_monthly = compute_cost_monthly + infrastructure_cost_monthly + operational_cost_monthly
        cost_per_query = total_cost_monthly / self.cost_model.queries_per_month
        
        return CostBreakdown(
            compute_cost_monthly=compute_cost_monthly,
            infrastructure_cost_monthly=infrastructure_cost_monthly,
            operational_cost_monthly=operational_cost_monthly,
            total_cost_monthly=total_cost_monthly,
            cost_per_query=cost_per_query
        )
        
    def calculate_cost_effectiveness_score(self, performance: PerformanceMetrics, 
                                         cost_breakdown: CostBreakdown) -> float:
        """Calculate cost-effectiveness score (higher is better)."""
        # Normalize performance metrics (0-1 scale)
        normalized_precision = min(1.0, performance.precision_at_5 / 1.0)  # Max possible = 1.0
        normalized_mrr = min(1.0, performance.mrr / 1.0)  # Max possible = 1.0
        normalized_speed = min(1.0, 100.0 / max(performance.latency_ms, 1.0))  # 100ms = 1.0 score
        
        # Weighted performance score
        performance_score = (
            normalized_precision * 0.5 +  # 50% weight on precision
            normalized_mrr * 0.3 +        # 30% weight on MRR
            normalized_speed * 0.2         # 20% weight on speed
        )
        
        # Cost factor (lower cost = higher score)
        # Use log scale to handle wide cost range
        cost_factor = 1.0 / (1.0 + cost_breakdown.cost_per_query * 1000)  # Scale for readability
        
        # Combined score
        cost_effectiveness_score = performance_score * cost_factor * 1000  # Scale for readability
        
        return cost_effectiveness_score
        
    def analyze_configuration(self, embedding_model: Dict, reranking_strategy: Optional[Dict] = None) -> ConfigurationAnalysis:
        """Analyze a single configuration."""
        # Extract performance metrics
        performance = PerformanceMetrics(
            precision_at_5=embedding_model.get('precision_at_5', 0.0),
            mrr=embedding_model.get('mrr', 0.0),
            latency_ms=embedding_model.get('inference_time_ms', 0.0),
            memory_usage_mb=embedding_model.get('memory_usage_mb', 0.0),
            throughput_qps=1000.0 / max(embedding_model.get('inference_time_ms', 100.0), 1.0)
        )
        
        # Add re-ranking metrics if provided
        if reranking_strategy:
            performance.precision_at_5 = min(1.0, performance.precision_at_5 * (1 + reranking_strategy.get('quality_improvement', 0) / 100))
            performance.mrr = min(1.0, performance.mrr * (1 + reranking_strategy.get('quality_improvement', 0) / 100))
            performance.latency_ms += reranking_strategy.get('avg_rerank_time_ms', 0.0)
            performance.memory_usage_mb += reranking_strategy.get('memory_usage_mb', 0.0)
            performance.throughput_qps = 1000.0 / max(performance.latency_ms, 1.0)
            
        # Calculate costs
        embedding_cost = self.calculate_embedding_cost(
            embedding_model['model_name'], 
            embedding_model.get('inference_time_ms', 50.0)
        )
        
        reranking_cost = 0.0
        if reranking_strategy:
            reranking_cost = self.calculate_reranking_cost(
                reranking_strategy['strategy_name'],
                reranking_strategy.get('avg_rerank_time_ms', 0.0)
            )
            
        cost_breakdown = self.calculate_total_cost_breakdown(embedding_cost, reranking_cost)
        
        # Calculate cost-effectiveness
        cost_effectiveness_score = self.calculate_cost_effectiveness_score(performance, cost_breakdown)
        
        # Generate configuration name
        config_name = embedding_model['model_name']
        if reranking_strategy:
            config_name += f" + {reranking_strategy['strategy_name']}"
            
        # Generate pros and cons
        pros, cons = self.generate_pros_cons(embedding_model, reranking_strategy, performance, cost_breakdown)
        
        return ConfigurationAnalysis(
            configuration_name=config_name,
            performance=performance,
            cost_breakdown=cost_breakdown,
            cost_effectiveness_score=cost_effectiveness_score,
            recommendation_rank=0,  # Will be set after ranking
            pros=pros,
            cons=cons
        )
        
    def generate_pros_cons(self, embedding_model: Dict, reranking_strategy: Optional[Dict],
                          performance: PerformanceMetrics, cost_breakdown: CostBreakdown) -> Tuple[List[str], List[str]]:
        """Generate pros and cons for a configuration."""
        pros = []
        cons = []
        
        # Performance pros/cons
        if performance.precision_at_5 > 0.75:
            pros.append(f"High precision@5: {performance.precision_at_5:.3f}")
        elif performance.precision_at_5 < 0.65:
            cons.append(f"Low precision@5: {performance.precision_at_5:.3f}")
            
        if performance.mrr > 0.85:
            pros.append(f"Excellent MRR: {performance.mrr:.3f}")
        elif performance.mrr < 0.75:
            cons.append(f"Below target MRR: {performance.mrr:.3f}")
            
        if performance.latency_ms < 100:
            pros.append(f"Fast inference: {performance.latency_ms:.0f}ms")
        elif performance.latency_ms > 200:
            cons.append(f"High latency: {performance.latency_ms:.0f}ms")
            
        # Memory pros/cons
        if performance.memory_usage_mb < 200:
            pros.append(f"Low memory usage: {performance.memory_usage_mb:.0f}MB")
        elif performance.memory_usage_mb > 500:
            cons.append(f"High memory usage: {performance.memory_usage_mb:.0f}MB")
            
        # Cost pros/cons
        if cost_breakdown.total_cost_monthly < 2.0:
            pros.append(f"Very low cost: ${cost_breakdown.total_cost_monthly:.2f}/month")
        elif cost_breakdown.total_cost_monthly > 10.0:
            cons.append(f"High monthly cost: ${cost_breakdown.total_cost_monthly:.2f}")
            
        # Model-specific pros/cons
        model_name = embedding_model['model_name']
        if 'miniLM' in model_name:
            pros.append("Lightweight and efficient")
        elif 'mpnet' in model_name:
            pros.append("High-quality embeddings")
            cons.append("Larger model size")
        elif 'e5' in model_name:
            pros.append("Latest generation model")
        elif 'gte' in model_name:
            pros.append("ARM64 optimized")
            
        # Re-ranking pros/cons
        if reranking_strategy:
            strategy_name = reranking_strategy['strategy_name']
            if strategy_name == 'cross_encoder':
                pros.append("Proven re-ranking quality")
                cons.append("Additional inference cost")
            elif strategy_name == 'ollama_llm':
                pros.append("Advanced LLM reasoning")
                cons.append("High latency overhead")
            elif strategy_name == 'hybrid_scoring':
                pros.append("No additional cost")
                pros.append("Fast processing")
                
        return pros, cons
        
    def run_analysis(self, embedding_results: List[Dict], 
                    reranking_results: List[Dict]) -> List[ConfigurationAnalysis]:
        """Run comprehensive analysis on all configurations."""
        logger.info("Starting performance vs cost analysis")
        
        analyses = []
        
        # Analyze embedding models alone
        for embedding_model in embedding_results:
            analysis = self.analyze_configuration(embedding_model)
            analyses.append(analysis)
            
        # Analyze combined configurations
        for embedding_model in embedding_results:
            for reranking_strategy in reranking_results:
                analysis = self.analyze_configuration(embedding_model, reranking_strategy)
                analyses.append(analysis)
                
        # Rank by cost-effectiveness
        analyses.sort(key=lambda x: x.cost_effectiveness_score, reverse=True)
        for i, analysis in enumerate(analyses):
            analysis.recommendation_rank = i + 1
            
        self.analysis_results = analyses
        logger.info(f"Analysis completed for {len(analyses)} configurations")
        
        return analyses
        
    def generate_recommendations(self, analyses: List[ConfigurationAnalysis]) -> Dict[str, Any]:
        """Generate recommendations based on analysis."""
        if not analyses:
            return {'status': 'no_analyses_available'}
            
        recommendations = {
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'total_configurations_analyzed': len(analyses),
            'top_recommendation': {},
            'best_performance': {},
            'best_cost_efficiency': {},
            'balanced_choice': {},
            'decision_framework': {}
        }
        
        # Top overall recommendation
        top_choice = analyses[0]
        recommendations['top_recommendation'] = {
            'configuration': top_choice.configuration_name,
            'cost_effectiveness_score': top_choice.cost_effectiveness_score,
            'monthly_cost': top_choice.cost_breakdown.total_cost_monthly,
            'precision_at_5': top_choice.performance.precision_at_5,
            'latency_ms': top_choice.performance.latency_ms,
            'pros': top_choice.pros[:3],  # Top 3 pros
            'reason': 'Highest cost-effectiveness score'
        }
        
        # Best performance (regardless of cost)
        best_perf = max(analyses, key=lambda x: x.performance.precision_at_5 * 0.6 + x.performance.mrr * 0.4)
        recommendations['best_performance'] = {
            'configuration': best_perf.configuration_name,
            'precision_at_5': best_perf.performance.precision_at_5,
            'mrr': best_perf.performance.mrr,
            'monthly_cost': best_perf.cost_breakdown.total_cost_monthly,
            'latency_ms': best_perf.performance.latency_ms,
            'reason': 'Highest quality metrics'
        }
        
        # Best cost efficiency (lowest cost)
        best_cost = min(analyses, key=lambda x: x.cost_breakdown.total_cost_monthly)
        recommendations['best_cost_efficiency'] = {
            'configuration': best_cost.configuration_name,
            'monthly_cost': best_cost.cost_breakdown.total_cost_monthly,
            'precision_at_5': best_cost.performance.precision_at_5,
            'latency_ms': best_cost.performance.latency_ms,
            'reason': 'Lowest total cost'
        }
        
        # Balanced choice (good performance, reasonable cost)
        balanced_candidates = [a for a in analyses 
                             if a.performance.precision_at_5 > 0.70 and 
                                a.cost_breakdown.total_cost_monthly < 5.0 and
                                a.performance.latency_ms < 200]
        if balanced_candidates:
            balanced_choice = max(balanced_candidates, key=lambda x: x.cost_effectiveness_score)
            recommendations['balanced_choice'] = {
                'configuration': balanced_choice.configuration_name,
                'cost_effectiveness_score': balanced_choice.cost_effectiveness_score,
                'precision_at_5': balanced_choice.performance.precision_at_5,
                'monthly_cost': balanced_choice.cost_breakdown.total_cost_monthly,
                'latency_ms': balanced_choice.performance.latency_ms,
                'reason': 'Best balance of performance, cost, and speed'
            }
        
        # Decision framework
        recommendations['decision_framework'] = {
            'factors_to_consider': [
                'Quality requirements (precision@5 target)',
                'Budget constraints (monthly cost limit)', 
                'Latency requirements (response time SLA)',
                'Memory constraints (available RAM)',
                'Operational complexity'
            ],
            'decision_tree': {
                'budget_sensitive': 'Choose best_cost_efficiency option',
                'performance_critical': 'Choose best_performance option',
                'general_use': 'Choose top_recommendation option',
                'balanced_needs': 'Choose balanced_choice option'
            }
        }
        
        return recommendations
        
    def create_visualizations(self, analyses: List[ConfigurationAnalysis], output_dir: Path):
        """Create visualization charts."""
        if not analyses:
            logger.warning("No analyses to visualize")
            return
            
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Prepare data for plotting
        data = []
        for analysis in analyses:
            data.append({
                'Configuration': analysis.configuration_name,
                'Precision@5': analysis.performance.precision_at_5,
                'MRR': analysis.performance.mrr,
                'Latency (ms)': analysis.performance.latency_ms,
                'Monthly Cost ($)': analysis.cost_breakdown.total_cost_monthly,
                'Cost Effectiveness': analysis.cost_effectiveness_score,
                'Memory (MB)': analysis.performance.memory_usage_mb
            })
            
        df = pd.DataFrame(data)
        
        # 1. Performance vs Cost Scatter Plot
        plt.figure(figsize=(12, 8))
        scatter = plt.scatter(df['Monthly Cost ($)'], df['Precision@5'], 
                            s=df['Cost Effectiveness']*2, 
                            c=df['Latency (ms)'], cmap='viridis_r', alpha=0.7)
        plt.xlabel('Monthly Cost ($)')
        plt.ylabel('Precision@5')
        plt.title('Performance vs Cost Analysis\\n(Size = Cost Effectiveness, Color = Latency)')
        plt.colorbar(scatter, label='Latency (ms)')
        
        # Add labels for top configurations
        for i in range(min(5, len(df))):
            plt.annotate(df.iloc[i]['Configuration'], 
                        (df.iloc[i]['Monthly Cost ($)'], df.iloc[i]['Precision@5']),
                        xytext=(5, 5), textcoords='offset points', fontsize=8)
                        
        plt.tight_layout()
        plt.savefig(output_dir / 'performance_vs_cost.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 2. Cost Breakdown Bar Chart
        top_5 = df.head(5)
        plt.figure(figsize=(12, 6))
        x = range(len(top_5))
        plt.bar(x, top_5['Monthly Cost ($)'])
        plt.xlabel('Configuration')
        plt.ylabel('Monthly Cost ($)')
        plt.title('Top 5 Configurations - Monthly Cost Comparison')
        plt.xticks(x, [config.split(' + ')[0].split('/')[-1] for config in top_5['Configuration']], rotation=45)
        plt.tight_layout()
        plt.savefig(output_dir / 'cost_comparison.png', dpi=300, bbox_inches='tight')
        plt.close()
        
        # 3. Performance Metrics Radar Chart
        if len(top_5) > 0:
            metrics = ['Precision@5', 'MRR', 'Cost Effectiveness']
            
            # Normalize metrics for radar chart
            normalized_data = top_5[metrics].copy()
            for col in metrics:
                normalized_data[col] = normalized_data[col] / normalized_data[col].max()
                
            angles = np.linspace(0, 2*np.pi, len(metrics), endpoint=False).tolist()
            angles += angles[:1]  # Complete the circle
            
            fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(projection='polar'))
            
            for i, (idx, row) in enumerate(normalized_data.iterrows()):
                values = row.tolist()
                values += values[:1]  # Complete the circle
                ax.plot(angles, values, 'o-', linewidth=2, label=top_5.iloc[i]['Configuration'].split(' + ')[0].split('/')[-1])
                ax.fill(angles, values, alpha=0.25)
                
            ax.set_xticks(angles[:-1])
            ax.set_xticklabels(metrics)
            ax.set_ylim(0, 1)
            plt.legend(loc='upper right', bbox_to_anchor=(1.3, 1.0))
            plt.title('Top 5 Configurations - Performance Comparison')
            plt.tight_layout()
            plt.savefig(output_dir / 'performance_radar.png', dpi=300, bbox_inches='tight')
            plt.close()
            
        logger.info(f"Visualizations saved to: {output_dir}")
        
    def save_results(self, analyses: List[ConfigurationAnalysis], 
                    recommendations: Dict[str, Any], output_path: Path):
        """Save analysis results to JSON."""
        results = {
            'analysis_metadata': {
                'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
                'framework': 'Phase 2 MLOps Testing - Performance vs Cost Analysis',
                'cost_model': asdict(self.cost_model),
                'total_configurations': len(analyses)
            },
            'configuration_analyses': [asdict(analysis) for analysis in analyses],
            'recommendations': recommendations,
            'summary_statistics': {
                'cost_range': {
                    'min': min(a.cost_breakdown.total_cost_monthly for a in analyses) if analyses else 0,
                    'max': max(a.cost_breakdown.total_cost_monthly for a in analyses) if analyses else 0,
                    'avg': sum(a.cost_breakdown.total_cost_monthly for a in analyses) / len(analyses) if analyses else 0
                },
                'performance_range': {
                    'min_precision': min(a.performance.precision_at_5 for a in analyses) if analyses else 0,
                    'max_precision': max(a.performance.precision_at_5 for a in analyses) if analyses else 0,
                    'avg_precision': sum(a.performance.precision_at_5 for a in analyses) / len(analyses) if analyses else 0
                },
                'latency_range': {
                    'min_latency': min(a.performance.latency_ms for a in analyses) if analyses else 0,
                    'max_latency': max(a.performance.latency_ms for a in analyses) if analyses else 0,
                    'avg_latency': sum(a.performance.latency_ms for a in analyses) / len(analyses) if analyses else 0
                }
            }
        }
        
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(results, f, indent=2)
            
        logger.info(f"Analysis results saved to: {output_path}")


def main():
    """Main execution function."""
    parser = argparse.ArgumentParser(
        description="Analyze performance vs cost trade-offs for RAG configurations",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--embedding-results',
        type=Path,
        required=True,
        help='Path to embedding model comparison results JSON'
    )
    
    parser.add_argument(
        '--reranking-results', 
        type=Path,
        required=True,
        help='Path to re-ranking evaluation results JSON'
    )
    
    parser.add_argument(
        '--output',
        type=Path,
        required=True,
        help='Output path for analysis results JSON'
    )
    
    parser.add_argument(
        '--visualizations',
        type=Path,
        help='Output directory for visualization charts'
    )
    
    parser.add_argument(
        '--queries-per-month',
        type=int,
        default=10000,
        help='Estimated monthly query volume'
    )
    
    args = parser.parse_args()
    
    # Validate inputs
    if not args.embedding_results.exists():
        logger.error(f"Embedding results not found: {args.embedding_results}")
        return 1
        
    if not args.reranking_results.exists():
        logger.error(f"Re-ranking results not found: {args.reranking_results}")
        return 1
        
    # Create analyzer with custom cost model
    cost_model = CostModel(queries_per_month=args.queries_per_month)
    analyzer = PerformanceCostAnalyzer(cost_model)
    
    try:
        # Load results
        embedding_results = analyzer.load_embedding_results(args.embedding_results)
        reranking_results = analyzer.load_reranking_results(args.reranking_results)
        
        if not embedding_results:
            logger.error("No embedding results loaded")
            return 1
            
        if not reranking_results:
            logger.error("No re-ranking results loaded")
            return 1
            
        # Run analysis
        analyses = analyzer.run_analysis(embedding_results, reranking_results)
        
        if not analyses:
            logger.error("No analyses generated")
            return 1
            
        # Generate recommendations
        recommendations = analyzer.generate_recommendations(analyses)
        
        # Save results
        analyzer.save_results(analyses, recommendations, args.output)
        
        # Create visualizations if requested
        if args.visualizations:
            analyzer.create_visualizations(analyses, args.visualizations)
            
        # Print summary
        print("\\n" + "="*60)
        print("PERFORMANCE vs COST ANALYSIS SUMMARY")
        print("="*60)
        print(f"Configurations Analyzed: {len(analyses)}")
        
        if 'top_recommendation' in recommendations:
            top = recommendations['top_recommendation']
            print(f"\\nTop Recommendation: {top['configuration']}")
            print(f"  Cost Effectiveness Score: {top['cost_effectiveness_score']:.1f}")
            print(f"  Monthly Cost: ${top['monthly_cost']:.2f}")
            print(f"  Precision@5: {top['precision_at_5']:.3f}")
            print(f"  Latency: {top['latency_ms']:.0f}ms")
            
        if 'balanced_choice' in recommendations:
            balanced = recommendations['balanced_choice']
            print(f"\\nBalanced Choice: {balanced.get('configuration', 'N/A')}")
            if 'precision_at_5' in balanced:
                print(f"  Precision@5: {balanced['precision_at_5']:.3f}")
                print(f"  Monthly Cost: ${balanced['monthly_cost']:.2f}")
                print(f"  Latency: {balanced['latency_ms']:.0f}ms")
                
        print(f"\\nDetailed analysis saved to: {args.output}")
        if args.visualizations:
            print(f"Visualizations saved to: {args.visualizations}")
        
        return 0
        
    except Exception as e:
        logger.error(f"Analysis failed: {e}")
        return 1


if __name__ == '__main__':
    exit(main())