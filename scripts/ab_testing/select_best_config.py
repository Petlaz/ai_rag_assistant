"""
Automated Configuration Selection from A/B Testing Results

This script implements intelligent configuration selection based on
A/B testing results, considering multiple metrics, statistical
significance, and business constraints for optimal deployment decisions.

Features:
- Multi-objective configuration ranking and selection
- Statistical significance-based decision making  
- Cost-benefit analysis integration for optimal selection
- Pareto frontier analysis for trade-off optimization
- Automated winner selection with configurable criteria
- Configuration validation and safety checks
- Risk assessment and deployment readiness scoring

Usage:
    # Select best configuration from A/B test results
    python scripts/ab_testing/select_best_config.py \
        --results results/ab_testing/ab_test_results.json \
        --criteria precision,cost,latency \
        --weights 0.5,0.3,0.2

    # Multi-objective optimization with constraints
    python scripts/ab_testing/select_best_config.py \
        --results results/ab_testing/ab_test_results.json \
        --max-latency 2000 \
        --min-precision 0.75 \
        --pareto-analysis
"""

import argparse
import json
import logging
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')


class ConfigurationSelector:
    """Intelligent configuration selection from A/B testing results"""
    
    def __init__(self, 
                 criteria_weights: Dict[str, float] = None,
                 constraints: Dict[str, float] = None):
        
        # Default criteria weights
        self.criteria_weights = criteria_weights or {
            'precision_at_5': 0.35,
            'mrr': 0.25,
            'recall_at_10': 0.20,
            'latency': 0.10,       # Lower is better
            'cost': 0.10           # Lower is better
        }
        
        # Performance constraints
        self.constraints = constraints or {
            'min_precision_at_5': 0.70,
            'min_mrr': 0.60,
            'min_recall_at_10': 0.50,
            'max_latency_p95': 3000,
            'max_cost_relative': 1.5  # 50% more than baseline
        }
        
        # Setup logging
        logging.basicConfig(level=logging.INFO,
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.selection_results = {
            'metadata': {},
            'candidate_scores': {},
            'pareto_analysis': {},
            'constraint_analysis': {},
            'final_selection': {},
            'recommendations': {}
        }
    
    def load_ab_test_results(self, results_path: str) -> Dict[str, Any]:
        """Load A/B test results from JSON file"""
        try:
            with open(results_path, 'r') as f:
                results = json.load(f)
            
            self.logger.info(f"Loaded A/B test results from {results_path}")
            return results
            
        except Exception as e:
            self.logger.error(f"Failed to load A/B test results: {e}")
            raise
    
    def extract_configuration_metrics(self, ab_results: Dict[str, Any]) -> pd.DataFrame:
        """Extract and normalize metrics for all configurations"""
        config_data = []
        
        for config_name, config_results in ab_results['configuration_results'].items():
            metrics = config_results['aggregated_metrics']
            
            # Extract configuration details
            config_info = config_results['config']
            
            # Estimate relative cost based on configuration complexity
            cost_multiplier = self.estimate_cost_multiplier(config_info)
            
            config_data.append({
                'config_name': config_name,
                'precision_at_5': metrics.get('precision_at_5_mean', 0),
                'mrr': metrics.get('mrr_mean', 0),
                'recall_at_10': metrics.get('recall_at_10_mean', 0),
                'latency_p95': metrics.get('latency_ms_p95', float('inf')),
                'latency_mean': metrics.get('latency_ms_mean', float('inf')),
                'std_precision': metrics.get('precision_at_5_std', 0),
                'std_mrr': metrics.get('mrr_std', 0),
                'cost_multiplier': cost_multiplier,
                'query_count': metrics.get('precision_at_5_count', 0),
                'config_details': config_info
            })
        
        df = pd.DataFrame(config_data)
        df = df.sort_values('precision_at_5', ascending=False)
        
        return df
    
    def estimate_cost_multiplier(self, config: Dict[str, Any]) -> float:
        """Estimate cost multiplier based on configuration complexity"""
        base_cost = 1.0
        
        # Embedding model cost factors
        embedding_model = config.get('embedding_model', 'all-MiniLM-L6-v2')
        if 'large' in embedding_model.lower() or 'e5' in embedding_model.lower():
            base_cost += 0.3
        elif 'mpnet' in embedding_model.lower():
            base_cost += 0.2
        
        # Reranker cost factors
        reranker = config.get('reranker', 'passthrough')
        if reranker == 'cross_encoder':
            base_cost += 0.4
        
        # Top-k factors (more documents = higher cost)
        top_k = config.get('top_k_final', 5)
        if top_k > 10:
            base_cost += 0.1 * (top_k - 10) / 10
        
        # Hybrid search complexity
        bm25_weight = config.get('bm25_weight', 0.7)
        semantic_weight = config.get('semantic_weight', 0.3)
        if abs(bm25_weight - semantic_weight) < 0.2:  # Complex hybrid balancing
            base_cost += 0.15
        
        return round(base_cost, 2)
    
    def calculate_weighted_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate weighted scores for all configurations"""
        df = df.copy()
        
        # Normalize metrics to 0-1 scale
        # Performance metrics (higher is better)
        for metric in ['precision_at_5', 'mrr', 'recall_at_10']:
            if metric in df.columns:
                max_val = df[metric].max()
                if max_val > 0:
                    df[f'{metric}_norm'] = df[metric] / max_val
                else:
                    df[f'{metric}_norm'] = 0
        
        # Cost and latency metrics (lower is better)
        for metric in ['latency_p95', 'cost_multiplier']:
            if metric in df.columns:
                min_val = df[metric].min()
                max_val = df[metric].max()
                if max_val > min_val:
                    df[f'{metric}_norm'] = 1 - (df[metric] - min_val) / (max_val - min_val)
                else:
                    df[f'{metric}_norm'] = 1
        
        # Calculate weighted score
        df['weighted_score'] = 0
        
        for metric, weight in self.criteria_weights.items():
            if metric in ['precision_at_5', 'mrr', 'recall_at_10']:
                norm_col = f'{metric}_norm'
                if norm_col in df.columns:
                    df['weighted_score'] += weight * df[norm_col]
            elif metric == 'latency':
                if 'latency_p95_norm' in df.columns:
                    df['weighted_score'] += weight * df['latency_p95_norm']
            elif metric == 'cost':
                if 'cost_multiplier_norm' in df.columns:
                    df['weighted_score'] += weight * df['cost_multiplier_norm']
        
        return df.sort_values('weighted_score', ascending=False)
    
    def apply_constraints(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply performance and business constraints"""
        df = df.copy()
        df['meets_constraints'] = True
        df['constraint_violations'] = ""
        
        violations = []
        
        # Precision constraint
        if 'min_precision_at_5' in self.constraints:
            min_precision = self.constraints['min_precision_at_5']
            precision_mask = df['precision_at_5'] >= min_precision
            df.loc[~precision_mask, 'meets_constraints'] = False
            violations.extend(df.loc[~precision_mask, 'config_name'].tolist())
            df.loc[~precision_mask, 'constraint_violations'] += f"precision_at_5 < {min_precision}; "
        
        # MRR constraint
        if 'min_mrr' in self.constraints:
            min_mrr = self.constraints['min_mrr']
            mrr_mask = df['mrr'] >= min_mrr
            df.loc[~mrr_mask, 'meets_constraints'] = False
            df.loc[~mrr_mask, 'constraint_violations'] += f"mrr < {min_mrr}; "
        
        # Recall constraint
        if 'min_recall_at_10' in self.constraints:
            min_recall = self.constraints['min_recall_at_10']
            recall_mask = df['recall_at_10'] >= min_recall
            df.loc[~recall_mask, 'meets_constraints'] = False
            df.loc[~recall_mask, 'constraint_violations'] += f"recall_at_10 < {min_recall}; "
        
        # Latency constraint
        if 'max_latency_p95' in self.constraints:
            max_latency = self.constraints['max_latency_p95']
            latency_mask = df['latency_p95'] <= max_latency
            df.loc[~latency_mask, 'meets_constraints'] = False
            df.loc[~latency_mask, 'constraint_violations'] += f"latency_p95 > {max_latency}ms; "
        
        # Cost constraint
        if 'max_cost_relative' in self.constraints:
            max_cost = self.constraints['max_cost_relative']
            cost_mask = df['cost_multiplier'] <= max_cost
            df.loc[~cost_mask, 'meets_constraints'] = False
            df.loc[~cost_mask, 'constraint_violations'] += f"cost > {max_cost}x baseline; "
        
        self.logger.info(f"Applied constraints: {len(df[df['meets_constraints']])} of {len(df)} configs pass")
        
        return df
    
    def perform_pareto_analysis(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Perform Pareto frontier analysis for trade-off optimization"""
        pareto_results = {
            'pareto_front': [],
            'dominated_configs': [],
            'trade_off_analysis': {}
        }
        
        if len(df) < 2:
            return pareto_results
        
        # Define objectives (higher is better for all after normalization)
        objectives = ['precision_at_5_norm', 'mrr_norm', 'latency_p95_norm', 'cost_multiplier_norm']
        available_objectives = [obj for obj in objectives if obj in df.columns]
        
        if len(available_objectives) < 2:
            return pareto_results
        
        # Find Pareto frontier
        pareto_indices = []
        all_configs = df.index.tolist()
        
        for i, config_i in enumerate(all_configs):
            is_pareto = True
            config_i_data = df.loc[config_i]
            
            for j, config_j in enumerate(all_configs):
                if i == j:
                    continue
                
                config_j_data = df.loc[config_j]
                
                # Check if config_j dominates config_i
                dominates = True
                better_in_any = False
                
                for obj in available_objectives:
                    val_i = config_i_data[obj]
                    val_j = config_j_data[obj]
                    
                    if val_j < val_i:  # config_j is worse in this objective
                        dominates = False
                        break
                    elif val_j > val_i:  # config_j is better in this objective
                        better_in_any = True
                
                if dominates and better_in_any:
                    is_pareto = False
                    break
            
            if is_pareto:
                pareto_indices.append(config_i)
            else:
                pareto_results['dominated_configs'].append(config_i_data['config_name'])
        
        # Store Pareto front configurations
        pareto_configs = df.loc[pareto_indices]
        pareto_results['pareto_front'] = pareto_configs['config_name'].tolist()
        
        # Analyze trade-offs among Pareto-optimal solutions
        if len(pareto_configs) > 1:
            trade_offs = {}
            for obj in available_objectives:
                obj_values = pareto_configs[obj].tolist()
                trade_offs[obj.replace('_norm', '')] = {
                    'min': float(min(obj_values)),
                    'max': float(max(obj_values)),
                    'range': float(max(obj_values) - min(obj_values)),
                    'configs': pareto_configs.loc[pareto_configs[obj] == max(obj_values), 'config_name'].tolist()
                }
            
            pareto_results['trade_off_analysis'] = trade_offs
        
        return pareto_results
    
    def select_best_configuration(self, df: pd.DataFrame, 
                                ab_results: Dict[str, Any]) -> Dict[str, Any]:
        """Select the best configuration based on comprehensive criteria"""
        selection_results = {
            'winner': None,
            'runner_ups': [],
            'selection_criteria': {},
            'confidence_metrics': {},
            'risk_assessment': {}
        }
        
        if len(df) == 0:
            selection_results['error'] = "No configurations available"
            return selection_results
        
        # Filter for constraint-meeting configs first
        viable_configs = df[df['meets_constraints']] if 'meets_constraints' in df.columns else df
        
        if len(viable_configs) == 0:
            self.logger.warning("No configurations meet all constraints, selecting best available")
            viable_configs = df.head(3)  # Top 3 by weighted score
        
        # Primary selection: highest weighted score among viable configs
        winner = viable_configs.iloc[0]
        selection_results['winner'] = {
            'config_name': winner['config_name'],
            'weighted_score': float(winner['weighted_score']),
            'precision_at_5': float(winner['precision_at_5']),
            'mrr': float(winner['mrr']),
            'latency_p95': float(winner['latency_p95']),
            'cost_multiplier': float(winner['cost_multiplier']),
            'meets_constraints': winner.get('meets_constraints', True),
            'config_details': winner['config_details']
        }
        
        # Runner-ups
        if len(viable_configs) > 1:
            runner_ups = viable_configs.iloc[1:min(4, len(viable_configs))]
            for _, config in runner_ups.iterrows():
                selection_results['runner_ups'].append({
                    'config_name': config['config_name'],
                    'weighted_score': float(config['weighted_score']),
                    'precision_at_5': float(config['precision_at_5']),
                    'score_diff': float(winner['weighted_score'] - config['weighted_score'])
                })
        
        # Selection criteria summary
        selection_results['selection_criteria'] = {
            'primary_metric': 'weighted_score',
            'weights_used': self.criteria_weights,
            'constraints_applied': self.constraints,
            'total_candidates': len(df),
            'viable_candidates': len(viable_configs)
        }
        
        # Statistical confidence from A/B test results
        winner_stats = ab_results['statistical_analysis']['pairwise_comparisons'].get(
            winner['config_name'], {})
        
        selection_results['confidence_metrics'] = {
            'baseline_improvement': winner_stats.get('improvements', {}),
            'sample_size': int(winner['query_count']),
            'precision_std': float(winner['std_precision']),
            'confidence_interval_width': float(2 * winner['std_precision'] / np.sqrt(winner['query_count'])) 
                                          if winner['query_count'] > 0 else None
        }
        
        # Risk assessment
        selection_results['risk_assessment'] = self.assess_deployment_risk(winner, df)
        
        return selection_results
    
    def assess_deployment_risk(self, winner: pd.Series, all_configs: pd.DataFrame) -> Dict[str, Any]:
        """Assess deployment risk for selected configuration"""
        risk_assessment = {
            'overall_risk': 'LOW',
            'risk_factors': [],
            'mitigation_recommendations': []
        }
        
        # Performance stability risk
        if winner.get('std_precision', 0) > 0.1:
            risk_assessment['risk_factors'].append("High precision variance")
            risk_assessment['mitigation_recommendations'].append("Increase sample size for validation")
        
        # Latency risk  
        if winner.get('latency_p95', 0) > 2000:
            risk_assessment['risk_factors'].append("High latency P95")
            risk_assessment['mitigation_recommendations'].append("Consider latency optimization")
        
        # Cost risk
        if winner.get('cost_multiplier', 1) > 1.3:
            risk_assessment['risk_factors'].append("Significant cost increase")
            risk_assessment['mitigation_recommendations'].append("Budget approval required")
        
        # Complexity risk
        config_details = winner.get('config_details', {})
        if config_details.get('reranker') == 'cross_encoder':
            risk_assessment['risk_factors'].append("Complex reranking pipeline")
            risk_assessment['mitigation_recommendations'].append("Extra monitoring for reranker performance")
        
        # Margin of victory risk
        if len(all_configs) > 1:
            second_best_score = all_configs.iloc[1]['weighted_score']
            score_margin = winner['weighted_score'] - second_best_score
            if score_margin < 0.05:  # Less than 5% improvement
                risk_assessment['risk_factors'].append("Small margin over alternatives")
                risk_assessment['mitigation_recommendations'].append("Consider extended A/B testing period")
        
        # Overall risk calculation
        num_risks = len(risk_assessment['risk_factors'])
        if num_risks == 0:
            risk_assessment['overall_risk'] = 'LOW'
        elif num_risks <= 2:
            risk_assessment['overall_risk'] = 'MEDIUM'
        else:
            risk_assessment['overall_risk'] = 'HIGH'
        
        return risk_assessment
    
    def generate_deployment_recommendations(self, selection_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate deployment recommendations based on selection results"""
        recommendations = {
            'deploy_immediate': False,
            'deploy_conditional': False,
            'requires_further_testing': False,
            'action_items': [],
            'monitoring_requirements': []
        }
        
        winner = selection_results['winner']
        risk_assessment = selection_results['risk_assessment']
        
        # Decision logic
        if (winner['meets_constraints'] and 
            risk_assessment['overall_risk'] in ['LOW', 'MEDIUM'] and
            winner['weighted_score'] > 0.7):
            
            if risk_assessment['overall_risk'] == 'LOW':
                recommendations['deploy_immediate'] = True
                recommendations['action_items'].append("[READY] Ready for immediate deployment")
            else:
                recommendations['deploy_conditional'] = True
                recommendations['action_items'].append("[WARNING] Deploy with enhanced monitoring")
                recommendations['action_items'].extend(risk_assessment['mitigation_recommendations'])
        else:
            recommendations['requires_further_testing'] = True
            recommendations['action_items'].append("[REVIEW] Requires further optimization or testing")
            recommendations['action_items'].extend(risk_assessment['mitigation_recommendations'])
        
        # Monitoring requirements
        recommendations['monitoring_requirements'] = [
            f"Monitor precision_at_5 (target: >{winner['precision_at_5']:.3f})",
            f"Monitor latency P95 (target: <{winner['latency_p95']:.0f}ms)",
            "Track user satisfaction metrics",
            "Monitor cost per query"
        ]
        
        # Additional recommendations based on config complexity
        config_details = winner['config_details']
        if config_details.get('reranker') == 'cross_encoder':
            recommendations['monitoring_requirements'].append("Monitor reranker model performance")
        
        if winner['cost_multiplier'] > 1.2:
            recommendations['monitoring_requirements'].append("Track infrastructure cost trends")
        
        return recommendations
    
    def run_configuration_selection(self, results_path: str) -> Dict[str, Any]:
        """Main function to run complete configuration selection"""
        self.logger.info("Starting configuration selection process")
        
        # Load A/B test results
        ab_results = self.load_ab_test_results(results_path)
        
        # Extract and process configuration metrics
        config_df = self.extract_configuration_metrics(ab_results)
        
        # Calculate weighted scores
        scored_df = self.calculate_weighted_scores(config_df)
        
        # Apply constraints
        constrained_df = self.apply_constraints(scored_df)
        
        # Perform Pareto analysis
        pareto_results = self.perform_pareto_analysis(constrained_df)
        
        # Select best configuration
        selection = self.select_best_configuration(constrained_df, ab_results)
        
        # Generate deployment recommendations
        deployment_rec = self.generate_deployment_recommendations(selection)
        
        # Compile full results
        self.selection_results = {
            'metadata': {
                'selection_timestamp': datetime.now().isoformat(),
                'criteria_weights': self.criteria_weights,
                'constraints': self.constraints,
                'total_configurations': len(config_df)
            },
            'candidate_scores': constrained_df.to_dict('records'),
            'pareto_analysis': pareto_results,
            'final_selection': selection,
            'deployment_recommendations': deployment_rec
        }
        
        return self.selection_results
    
    def save_selection_results(self, output_path: str):
        """Save configuration selection results"""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.selection_results, f, indent=2, default=str)
            
            self.logger.info(f"Selection results saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save selection results: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Select Best Configuration from A/B Test Results')
    parser.add_argument('--results', required=True,
                       help='Path to A/B test results JSON file')
    parser.add_argument('--criteria', default='precision,mrr,latency,cost',
                       help='Comma-separated selection criteria')
    parser.add_argument('--weights', default='0.35,0.25,0.2,0.1,0.1',
                       help='Comma-separated weights for criteria')
    parser.add_argument('--min-precision', type=float, default=0.70,
                       help='Minimum precision requirement')
    parser.add_argument('--max-latency', type=float, default=3000,
                       help='Maximum latency P95 (ms)')
    parser.add_argument('--max-cost', type=float, default=1.5,
                       help='Maximum cost multiplier vs baseline')
    parser.add_argument('--pareto-analysis', action='store_true',
                       help='Include Pareto frontier analysis')
    parser.add_argument('--output', default=None,
                       help='Output path for selection results')
    
    args = parser.parse_args()
    
    # Parse criteria and weights
    criteria_list = args.criteria.split(',')
    weights_list = [float(w) for w in args.weights.split(',')]
    
    if len(criteria_list) != len(weights_list):
        raise ValueError("Number of criteria must match number of weights")
    
    criteria_weights = dict(zip(criteria_list, weights_list))
    
    # Setup constraints
    constraints = {
        'min_precision_at_5': args.min_precision,
        'max_latency_p95': args.max_latency,
        'max_cost_relative': args.max_cost
    }
    
    # Initialize selector
    selector = ConfigurationSelector(criteria_weights=criteria_weights, constraints=constraints)
    
    try:
        # Run selection
        results = selector.run_configuration_selection(args.results)
        
        # Determine output path
        if args.output is None:
            results_path = Path(args.results)
            output_path = results_path.parent / f"config_selection_{results_path.stem}.json"
        else:
            output_path = args.output
        
        # Save results
        selector.save_selection_results(output_path)
        
        # Print summary
        print("\n" + "="*60)
        print("CONFIGURATION SELECTION SUMMARY")
        print("="*60)
        
        winner = results['final_selection']['winner']
        deployment = results['deployment_recommendations']
        
        print(f"Selected Configuration: {winner['config_name']}")
        print(f"Weighted Score: {winner['weighted_score']:.3f}")
        print(f"Key Metrics: P@5={winner['precision_at_5']:.3f}, "
              f"MRR={winner['mrr']:.3f}, "
              f"Latency={winner['latency_p95']:.0f}ms")
        
        # Deployment recommendation
        if deployment['deploy_immediate']:
            print("[READY] RECOMMENDED FOR IMMEDIATE DEPLOYMENT")
        elif deployment['deploy_conditional']:
            print("[WARNING] CONDITIONAL DEPLOYMENT RECOMMENDED")
        else:
            print("[REVIEW] FURTHER TESTING REQUIRED")
        
        print("\nAction Items:")
        for item in deployment['action_items']:
            print(f"  • {item}")
        
        print(f"\nFull selection results saved to: {output_path}")
        
    except Exception as e:
        print(f"[ERROR] Configuration selection failed: {e}")
        raise


if __name__ == "__main__":
    main()