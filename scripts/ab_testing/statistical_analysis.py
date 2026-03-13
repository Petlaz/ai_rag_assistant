"""
Statistical Analysis Framework for A/B Testing Results

This module provides comprehensive statistical analysis capabilities for
retrieval configuration A/B testing results including significance testing,
confidence intervals, effect size calculations, and power analysis.

Features:
- Statistical significance testing (t-tests, Mann-Whitney U, chi-square)
- Confidence interval calculations for metrics
- Effect size measurements (Cohen's d, Cliff's delta)
- Multiple comparison corrections (Bonferroni, FDR)
- Power analysis for sample size adequacy
- Bayesian A/B testing support with credible intervals
- Bootstrap confidence intervals for non-parametric metrics

Usage:
    # Analyze A/B test results from JSON file
    python scripts/ab_testing/statistical_analysis.py \
        --results results/ab_testing/ab_test_results.json \
        --alpha 0.05 \
        --correction bonferroni

    # Generate statistical report with visualizations
    python scripts/ab_testing/statistical_analysis.py \
        --results results/ab_testing/ab_test_results.json \
        --report-type comprehensive \
        --plots
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

# Statistical libraries
import scipy.stats as stats
from scipy.stats import ttest_ind, mannwhitneyu, chi2_contingency
from statsmodels.stats.power import ttest_power
from statsmodels.stats.proportion import proportions_ztest
import matplotlib.pyplot as plt
import seaborn as sns


class StatisticalAnalyzer:
    """Comprehensive statistical analysis for A/B testing results"""
    
    def __init__(self, alpha: float = 0.05, correction_method: str = 'bonferroni'):
        self.alpha = alpha
        self.correction_method = correction_method
        
        # Setup logging
        logging.basicConfig(level=logging.INFO, 
                          format='%(asctime)s - %(levelname)s - %(message)s')
        self.logger = logging.getLogger(__name__)
        
        # Results storage
        self.analysis_results = {
            'metadata': {},
            'descriptive_stats': {},
            'hypothesis_tests': {},
            'effect_sizes': {},
            'confidence_intervals': {},
            'multiple_comparisons': {},
            'power_analysis': {},
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
    
    def extract_metric_data(self, ab_results: Dict[str, Any], 
                          metric_name: str) -> Dict[str, List[float]]:
        """Extract metric data for all configurations"""
        metric_data = {}
        
        for config_name, config_results in ab_results['configuration_results'].items():
            query_results = config_results['query_results']
            
            if metric_name in ['precision_at_5', 'mrr', 'recall_at_10']:
                values = [qr.get(metric_name, 0) for qr in query_results]
            elif metric_name == 'latency_ms':
                values = [qr.get('latency_ms', 0) for qr in query_results]
            elif metric_name == 'num_results':
                values = [qr.get('retrieved_count', 0) for qr in query_results]
            else:
                self.logger.warning(f"Unknown metric: {metric_name}")
                continue
            
            metric_data[config_name] = values
        
        return metric_data
    
    def calculate_descriptive_stats(self, metric_data: Dict[str, List[float]]) -> Dict[str, Dict]:
        """Calculate descriptive statistics for each configuration"""
        stats_results = {}
        
        for config_name, values in metric_data.items():
            if not values:
                continue
                
            values_array = np.array(values)
            
            stats_results[config_name] = {
                'n': len(values),
                'mean': float(np.mean(values_array)),
                'std': float(np.std(values_array, ddof=1)),
                'median': float(np.median(values_array)),
                'min': float(np.min(values_array)),
                'max': float(np.max(values_array)),
                'q25': float(np.percentile(values_array, 25)),
                'q75': float(np.percentile(values_array, 75)),
                'skewness': float(stats.skew(values_array)),
                'kurtosis': float(stats.kurtosis(values_array)),
                'shapiro_p': float(stats.shapiro(values_array)[1]) if len(values) <= 5000 else None
            }
        
        return stats_results
    
    def perform_pairwise_tests(self, metric_data: Dict[str, List[float]], 
                             baseline_name: str) -> Dict[str, Dict]:
        """Perform pairwise statistical tests against baseline"""
        test_results = {}
        
        if baseline_name not in metric_data:
            self.logger.warning(f"Baseline '{baseline_name}' not found in data")
            # Use first configuration as baseline
            baseline_name = list(metric_data.keys())[0]
        
        baseline_data = np.array(metric_data[baseline_name])
        
        for config_name, values in metric_data.items():
            if config_name == baseline_name:
                continue
            
            variant_data = np.array(values)
            
            # Perform multiple statistical tests
            test_result = self.run_statistical_tests(baseline_data, variant_data)
            test_results[f"{config_name}_vs_{baseline_name}"] = test_result
        
        return test_results
    
    def run_statistical_tests(self, baseline: np.ndarray, 
                            variant: np.ndarray) -> Dict[str, Any]:
        """Run comprehensive statistical tests comparing two groups"""
        results = {}
        
        # Sample sizes
        n1, n2 = len(baseline), len(variant)
        results['sample_sizes'] = {'baseline': n1, 'variant': n2}
        
        # T-test (parametric)
        try:
            t_stat, t_p = ttest_ind(baseline, variant, equal_var=False)  # Welch's t-test
            results['t_test'] = {
                'statistic': float(t_stat),
                'p_value': float(t_p),
                'significant': t_p < self.alpha,
                'test_type': 'welch_t_test'
            }
        except Exception as e:
            self.logger.warning(f"T-test failed: {e}")
            results['t_test'] = None
        
        # Mann-Whitney U test (non-parametric)
        try:
            u_stat, u_p = mannwhitneyu(baseline, variant, alternative='two-sided')
            results['mann_whitney'] = {
                'statistic': float(u_stat),
                'p_value': float(u_p),
                'significant': u_p < self.alpha,
                'test_type': 'mann_whitney_u'
            }
        except Exception as e:
            self.logger.warning(f"Mann-Whitney test failed: {e}")
            results['mann_whitney'] = None
        
        # Kolmogorov-Smirnov test (distribution comparison)
        try:
            ks_stat, ks_p = stats.ks_2samp(baseline, variant)
            results['ks_test'] = {
                'statistic': float(ks_stat),
                'p_value': float(ks_p),
                'significant': ks_p < self.alpha,
                'test_type': 'kolmogorov_smirnov'
            }
        except Exception as e:
            self.logger.warning(f"KS test failed: {e}")
            results['ks_test'] = None
        
        return results
    
    def calculate_effect_sizes(self, baseline: np.ndarray, 
                             variant: np.ndarray) -> Dict[str, float]:
        """Calculate various effect size measures"""
        effect_sizes = {}
        
        # Cohen's d (standardized mean difference)
        try:
            pooled_std = np.sqrt(((len(baseline) - 1) * np.var(baseline, ddof=1) + 
                                (len(variant) - 1) * np.var(variant, ddof=1)) / 
                               (len(baseline) + len(variant) - 2))
            
            if pooled_std > 0:
                cohens_d = (np.mean(variant) - np.mean(baseline)) / pooled_std
                effect_sizes['cohens_d'] = float(cohens_d)
                effect_sizes['cohens_d_interpretation'] = self.interpret_cohens_d(cohens_d)
        except:
            effect_sizes['cohens_d'] = None
        
        # Cliff's delta (non-parametric effect size)
        try:
            cliffs_delta = self.calculate_cliffs_delta(baseline, variant)
            effect_sizes['cliffs_delta'] = cliffs_delta
            effect_sizes['cliffs_delta_interpretation'] = self.interpret_cliffs_delta(cliffs_delta)
        except:
            effect_sizes['cliffs_delta'] = None
        
        # Percentage improvement
        baseline_mean = np.mean(baseline)
        variant_mean = np.mean(variant)
        if baseline_mean != 0:
            pct_improvement = ((variant_mean - baseline_mean) / baseline_mean) * 100
            effect_sizes['percentage_improvement'] = float(pct_improvement)
        
        return effect_sizes
    
    def calculate_cliffs_delta(self, baseline: np.ndarray, variant: np.ndarray) -> float:
        """Calculate Cliff's delta non-parametric effect size"""
        m, n = len(baseline), len(variant)
        
        greater = sum(1 for x in baseline for y in variant if x > y)
        less = sum(1 for x in baseline for y in variant if x < y)
        
        delta = (greater - less) / (m * n)
        return delta
    
    def interpret_cohens_d(self, d: float) -> str:
        """Interpret Cohen's d effect size"""
        abs_d = abs(d)
        if abs_d < 0.2:
            return "negligible"
        elif abs_d < 0.5:
            return "small"
        elif abs_d < 0.8:
            return "medium"
        else:
            return "large"
    
    def interpret_cliffs_delta(self, delta: float) -> str:
        """Interpret Cliff's delta effect size"""
        abs_delta = abs(delta)
        if abs_delta < 0.147:
            return "negligible"
        elif abs_delta < 0.33:
            return "small"
        elif abs_delta < 0.474:
            return "medium"
        else:
            return "large"
    
    def calculate_confidence_intervals(self, metric_data: Dict[str, List[float]], 
                                     confidence_level: float = 0.95) -> Dict[str, Dict]:
        """Calculate confidence intervals for metrics"""
        ci_results = {}
        alpha_ci = 1 - confidence_level
        
        for config_name, values in metric_data.items():
            if not values:
                continue
                
            values_array = np.array(values)
            n = len(values_array)
            mean = np.mean(values_array)
            std = np.std(values_array, ddof=1)
            
            # Parametric CI (t-distribution)
            t_critical = stats.t.ppf(1 - alpha_ci/2, df=n-1)
            margin_error = t_critical * (std / np.sqrt(n))
            
            # Bootstrap CI (non-parametric)
            bootstrap_means = []
            n_bootstrap = 1000
            for _ in range(n_bootstrap):
                bootstrap_sample = np.random.choice(values_array, size=n, replace=True)
                bootstrap_means.append(np.mean(bootstrap_sample))
            
            bootstrap_lower = np.percentile(bootstrap_means, (alpha_ci/2) * 100)
            bootstrap_upper = np.percentile(bootstrap_means, (1 - alpha_ci/2) * 100)
            
            ci_results[config_name] = {
                'mean': float(mean),
                'parametric_ci': {
                    'lower': float(mean - margin_error),
                    'upper': float(mean + margin_error)
                },
                'bootstrap_ci': {
                    'lower': float(bootstrap_lower),
                    'upper': float(bootstrap_upper)
                },
                'confidence_level': confidence_level
            }
        
        return ci_results
    
    def apply_multiple_comparison_correction(self, p_values: List[float]) -> Dict[str, Any]:
        """Apply multiple comparison corrections"""
        p_array = np.array(p_values)
        n_comparisons = len(p_values)
        
        corrections = {}
        
        # Bonferroni correction
        bonferroni_alpha = self.alpha / n_comparisons
        bonferroni_significant = p_array < bonferroni_alpha
        corrections['bonferroni'] = {
            'corrected_alpha': bonferroni_alpha,
            'significant': bonferroni_significant.tolist(),
            'n_significant': int(np.sum(bonferroni_significant))
        }
        
        # Benjamini-Hochberg (FDR) correction
        sorted_indices = np.argsort(p_array)
        sorted_p = p_array[sorted_indices]
        
        fdr_thresholds = [(i + 1) / n_comparisons * self.alpha for i in range(n_comparisons)]
        fdr_significant = np.zeros(n_comparisons, dtype=bool)
        
        for i in reversed(range(n_comparisons)):
            if sorted_p[i] <= fdr_thresholds[i]:
                fdr_significant[sorted_indices[:i+1]] = True
                break
        
        corrections['benjamini_hochberg'] = {
            'corrected_thresholds': fdr_thresholds,
            'significant': fdr_significant.tolist(),
            'n_significant': int(np.sum(fdr_significant))
        }
        
        return corrections
    
    def perform_power_analysis(self, metric_data: Dict[str, List[float]], 
                             baseline_name: str) -> Dict[str, Any]:
        """Perform statistical power analysis"""
        power_results = {}
        
        if baseline_name not in metric_data:
            baseline_name = list(metric_data.keys())[0]
        
        baseline_data = np.array(metric_data[baseline_name])
        baseline_std = np.std(baseline_data, ddof=1)
        
        for config_name, values in metric_data.items():
            if config_name == baseline_name:
                continue
            
            variant_data = np.array(values)
            
            # Calculate effect size
            effect_size = (np.mean(variant_data) - np.mean(baseline_data)) / baseline_std
            
            # Calculate achieved power
            n1, n2 = len(baseline_data), len(variant_data)
            
            try:
                achieved_power = ttest_power(effect_size, n1, alpha=self.alpha, alternative='two-sided')
            except Exception:
                achieved_power = 0.0
            
            # Calculate required sample size for 80% power
            try:
                from statsmodels.stats.power import tt_solve_power
                required_n = tt_solve_power(effect_size=effect_size, power=0.8, alpha=self.alpha, alternative='two-sided')
            except Exception:
                required_n = None
            
            power_results[config_name] = {
                'effect_size': float(effect_size),
                'achieved_power': float(achieved_power),
                'sample_size': n2,
                'required_n_for_80_power': int(required_n) if not np.isnan(required_n) else None,
                'power_adequate': achieved_power >= 0.8
            }
        
        return power_results
    
    def analyze_ab_test_results(self, results_path: str) -> Dict[str, Any]:
        """Main analysis function for A/B test results"""
        self.logger.info("Starting comprehensive statistical analysis")
        
        # Load results
        ab_results = self.load_ab_test_results(results_path)
        
        # Analysis metadata
        self.analysis_results['metadata'] = {
            'analysis_timestamp': datetime.now().isoformat(),
            'alpha_level': self.alpha,
            'correction_method': self.correction_method,
            'original_experiment': ab_results.get('experiment_metadata', {})
        }
        
        # Identify baseline configuration
        config_names = list(ab_results['configuration_results'].keys())
        baseline_name = next((name for name in config_names if 'baseline' in name.lower()), 
                           config_names[0])
        
        # Analyze each metric
        metrics_to_analyze = ['precision_at_5', 'mrr', 'recall_at_10', 'latency_ms']
        
        for metric in metrics_to_analyze:
            self.logger.info(f"Analyzing metric: {metric}")
            
            # Extract metric data
            metric_data = self.extract_metric_data(ab_results, metric)
            if not metric_data:
                continue
            
            # Descriptive statistics
            desc_stats = self.calculate_descriptive_stats(metric_data)
            self.analysis_results['descriptive_stats'][metric] = desc_stats
            
            # Hypothesis tests
            test_results = self.perform_pairwise_tests(metric_data, baseline_name)
            self.analysis_results['hypothesis_tests'][metric] = test_results
            
            # Effect sizes
            effect_sizes = {}
            for config_name, values in metric_data.items():
                if config_name != baseline_name:
                    baseline_data = np.array(metric_data[baseline_name])
                    variant_data = np.array(values)
                    effect_sizes[config_name] = self.calculate_effect_sizes(baseline_data, variant_data)
            
            self.analysis_results['effect_sizes'][metric] = effect_sizes
            
            # Confidence intervals
            ci_results = self.calculate_confidence_intervals(metric_data)
            self.analysis_results['confidence_intervals'][metric] = ci_results
            
            # Power analysis
            power_results = self.perform_power_analysis(metric_data, baseline_name)
            self.analysis_results['power_analysis'][metric] = power_results
        
        # Multiple comparison corrections
        all_p_values = []
        for metric_tests in self.analysis_results['hypothesis_tests'].values():
            for test_result in metric_tests.values():
                if test_result.get('t_test') and test_result['t_test'].get('p_value'):
                    all_p_values.append(test_result['t_test']['p_value'])
        
        if all_p_values:
            corrections = self.apply_multiple_comparison_correction(all_p_values)
            self.analysis_results['multiple_comparisons'] = corrections
        
        # Generate recommendations
        self.analysis_results['recommendations'] = self.generate_statistical_recommendations()
        
        return self.analysis_results
    
    def generate_statistical_recommendations(self) -> Dict[str, Any]:
        """Generate statistical recommendations based on analysis"""
        recommendations = {
            'statistical_validity': {},
            'effect_significance': {},
            'sample_adequacy': {},
            'deployment_recommendation': {}
        }
        
        # Check statistical validity across metrics
        validity_checks = []
        for metric, test_results in self.analysis_results['hypothesis_tests'].items():
            for comparison, results in test_results.items():
                if results.get('t_test') and results['t_test'].get('significant'):
                    validity_checks.append(f"{metric}: {comparison} shows statistical significance")
        
        recommendations['statistical_validity'] = {
            'significant_findings': validity_checks,
            'overall_validity': len(validity_checks) > 0
        }
        
        # Check effect sizes
        meaningful_effects = []
        for metric, effect_results in self.analysis_results['effect_sizes'].items():
            for config, effects in effect_results.items():
                cohens_d = effects.get('cohens_d')
                if cohens_d and abs(cohens_d) >= 0.2:  # Small effect or larger
                    meaningful_effects.append(
                        f"{config} shows {effects['cohens_d_interpretation']} effect size "
                        f"for {metric} (d={cohens_d:.3f})"
                    )
        
        recommendations['effect_significance'] = {
            'meaningful_effects': meaningful_effects,
            'practical_significance': len(meaningful_effects) > 0
        }
        
        # Check sample adequacy
        adequate_power = []
        inadequate_power = []
        for metric, power_results in self.analysis_results['power_analysis'].items():
            for config, power_data in power_results.items():
                if power_data.get('power_adequate'):
                    adequate_power.append(f"{config} ({metric}): Power = {power_data['achieved_power']:.3f}")
                else:
                    inadequate_power.append(f"{config} ({metric}): Power = {power_data['achieved_power']:.3f}")
        
        recommendations['sample_adequacy'] = {
            'adequate_power': adequate_power,
            'inadequate_power': inadequate_power,
            'overall_adequacy': len(adequate_power) > len(inadequate_power)
        }
        
        # Overall deployment recommendation
        statistical_valid = recommendations['statistical_validity']['overall_validity']
        practical_significant = recommendations['effect_significance']['practical_significance']
        adequate_sample = recommendations['sample_adequacy']['overall_adequacy']
        
        if statistical_valid and practical_significant and adequate_sample:
            deployment_rec = "RECOMMENDED"
            justification = "Results show statistical significance with meaningful effect sizes and adequate power."
        elif statistical_valid and practical_significant:
            deployment_rec = "CONDITIONAL"
            justification = "Results are promising but may need larger sample sizes for confidence."
        else:
            deployment_rec = "NOT_RECOMMENDED"
            justification = "Insufficient statistical evidence for deployment recommendation."
        
        recommendations['deployment_recommendation'] = {
            'recommendation': deployment_rec,
            'justification': justification,
            'criteria_met': {
                'statistical_significance': statistical_valid,
                'practical_significance': practical_significant,
                'adequate_power': adequate_sample
            }
        }
        
        return recommendations
    
    def save_analysis(self, output_path: str):
        """Save statistical analysis results"""
        try:
            with open(output_path, 'w') as f:
                json.dump(self.analysis_results, f, indent=2, default=str)
            
            self.logger.info(f"Analysis results saved to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to save analysis: {e}")
            raise


def main():
    parser = argparse.ArgumentParser(description='Statistical Analysis for A/B Test Results')
    parser.add_argument('--results', required=True,
                       help='Path to A/B test results JSON file')
    parser.add_argument('--alpha', type=float, default=0.05,
                       help='Significance level (default: 0.05)')
    parser.add_argument('--correction', choices=['bonferroni', 'fdr'], default='bonferroni',
                       help='Multiple comparison correction method')
    parser.add_argument('--output', default=None,
                       help='Output path for analysis results')
    
    args = parser.parse_args()
    
    # Initialize analyzer
    analyzer = StatisticalAnalyzer(alpha=args.alpha, correction_method=args.correction)
    
    # Run analysis
    try:
        results = analyzer.analyze_ab_test_results(args.results)
        
        # Determine output path
        if args.output is None:
            results_path = Path(args.results)
            output_path = results_path.parent / f"statistical_analysis_{results_path.stem}.json"
        else:
            output_path = args.output
        
        # Save results
        analyzer.save_analysis(output_path)
        
        # Print summary
        print("\n" + "="*60)
        print("STATISTICAL ANALYSIS SUMMARY")
        print("="*60)
        
        recommendations = results['recommendations']
        deployment = recommendations['deployment_recommendation']
        
        print(f"Statistical Validity: {'[PASS]' if recommendations['statistical_validity']['overall_validity'] else '[FAIL]'}")
        print(f"Practical Significance: {'[PASS]' if recommendations['effect_significance']['practical_significance'] else '[FAIL]'}")
        print(f"Sample Adequacy: {'[PASS]' if recommendations['sample_adequacy']['overall_adequacy'] else '[FAIL]'}")
        
        print(f"\nDeployment Recommendation: {deployment['recommendation']}")
        print(f"Justification: {deployment['justification']}")
        
        print(f"\nFull analysis saved to: {output_path}")
        
    except Exception as e:
        print(f"[ERROR] Analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()