"""
Model Performance Monitoring and Drift Detection System

This script implements comprehensive model monitoring capabilities for the RAG system
including performance tracking, data/model drift detection, automated alerting,
and real-time production model health monitoring.

Features:
- Real-time model performance monitoring and tracking
- Data drift detection using statistical methods (KS test, PSI, Jensen-Shannon)
- Model drift identification and quantification
- Automated alerting for performance degradation
- Historical performance analysis and trending
- Feature importance drift monitoring
- Integration with CloudWatch and MLflow

Usage:
    # Start continuous monitoring with drift detection
    python scripts/mlops/model_monitoring.py \
        --mode continuous \
        --drift-threshold 0.1 \
        --monitoring-interval 300

    # Run historical analysis
    python scripts/mlops/model_monitoring.py \
        --mode analyze-history \
        --days 30 \
        --generate-report

    # Setup monitoring alerts
    python scripts/mlops/model_monitoring.py \
        --mode setup-alerts \
        --alert-config configs/mlops/alerts.yaml
"""

import argparse
import json
import logging
import time
import warnings
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from scipy import stats
from scipy.spatial.distance import jensenshannon
import yaml

try:
    import mlflow
    import mlflow.tracking
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class DriftDetector:
    """Statistical drift detection for model monitoring"""
    
    def __init__(self, baseline_data: pd.DataFrame, significance_level: float = 0.05):
        self.baseline_data = baseline_data
        self.significance_level = significance_level
        
        # Calculate baseline statistics
        self.baseline_stats = self.calculate_baseline_statistics()
    
    def calculate_baseline_statistics(self) -> Dict[str, Any]:
        """Calculate baseline statistics for drift detection"""
        stats_dict = {}
        
        for column in self.baseline_data.columns:
            if self.baseline_data[column].dtype in ['float64', 'int64']:
                stats_dict[column] = {
                    'mean': self.baseline_data[column].mean(),
                    'std': self.baseline_data[column].std(),
                    'quantiles': self.baseline_data[column].quantile([0.25, 0.5, 0.75]).to_dict(),
                    'min': self.baseline_data[column].min(),
                    'max': self.baseline_data[column].max()
                }
        
        return stats_dict
    
    def detect_drift_ks_test(self, current_data: pd.DataFrame) -> Dict[str, Dict[str, float]]:
        """Kolmogorov-Smirnov test for data drift detection"""
        drift_results = {}
        
        for column in self.baseline_data.columns:
            if column in current_data.columns and self.baseline_data[column].dtype in ['float64', 'int64']:
                ks_statistic, p_value = stats.ks_2samp(
                    self.baseline_data[column].dropna(),
                    current_data[column].dropna()
                )
                
                drift_results[column] = {
                    'ks_statistic': ks_statistic,
                    'p_value': p_value,
                    'drift_detected': p_value < self.significance_level,
                    'drift_severity': 'high' if ks_statistic > 0.2 else 'medium' if ks_statistic > 0.1 else 'low'
                }
        
        return drift_results
    
    def calculate_psi(self, current_data: pd.DataFrame, num_bins: int = 10) -> Dict[str, float]:
        """Population Stability Index (PSI) for drift detection"""
        psi_results = {}
        
        for column in self.baseline_data.columns:
            if column in current_data.columns and self.baseline_data[column].dtype in ['float64', 'int64']:
                baseline_col = self.baseline_data[column].dropna()
                current_col = current_data[column].dropna()
                
                # Create bins based on baseline data
                bins = np.histogram_bin_edges(baseline_col, bins=num_bins)
                
                # Calculate distributions
                baseline_dist, _ = np.histogram(baseline_col, bins=bins)
                current_dist, _ = np.histogram(current_col, bins=bins)
                
                # Convert to proportions (add small epsilon to avoid division by zero)
                baseline_prop = (baseline_dist + 1e-6) / (baseline_dist.sum() + num_bins * 1e-6)
                current_prop = (current_dist + 1e-6) / (current_dist.sum() + num_bins * 1e-6)
                
                # Calculate PSI
                psi = np.sum((current_prop - baseline_prop) * np.log(current_prop / baseline_prop))
                psi_results[column] = psi
        
        return psi_results
    
    def detect_drift_jensen_shannon(self, current_data: pd.DataFrame, num_bins: int = 20) -> Dict[str, float]:
        """Jensen-Shannon divergence for drift detection"""
        js_results = {}
        
        for column in self.baseline_data.columns:
            if column in current_data.columns and self.baseline_data[column].dtype in ['float64', 'int64']:
                baseline_col = self.baseline_data[column].dropna()
                current_col = current_data[column].dropna()
                
                # Create bins
                bins = np.histogram_bin_edges(
                    np.concatenate([baseline_col, current_col]), 
                    bins=num_bins
                )
                
                # Calculate distributions
                baseline_hist, _ = np.histogram(baseline_col, bins=bins, density=True)
                current_hist, _ = np.histogram(current_col, bins=bins, density=True)
                
                # Normalize to ensure they are probability distributions
                baseline_prob = baseline_hist / baseline_hist.sum()
                current_prob = current_hist / current_hist.sum()
                
                # Calculate Jensen-Shannon divergence
                js_divergence = jensenshannon(baseline_prob, current_prob)
                js_results[column] = js_divergence
        
        return js_results


class ModelPerformanceMonitor:
    """Comprehensive model performance monitoring system"""
    
    def __init__(self, project_path: str, monitoring_config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self.config = monitoring_config or self.load_default_config()
        
        # Setup logging
        self.setup_logging()
        
        # Performance metrics buffer
        self.metrics_buffer = deque(maxlen=1000)
        
        # Initialize monitoring components
        self.drift_detector = None
        self.baseline_metrics = None
        
        # Setup MLflow if available
        if MLFLOW_AVAILABLE:
            mlflow.set_tracking_uri(str(self.project_path / "mlruns"))
            self.experiment_name = self.config.get("mlflow_experiment", "production-monitoring")
            
        # Create monitoring directories
        self.create_monitoring_directories()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.project_path / "logs" / "mlops" / "model_monitoring.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(log_file),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def create_monitoring_directories(self):
        """Create necessary directories for monitoring"""
        directories = [
            "monitoring/metrics",
            "monitoring/drift_reports", 
            "monitoring/performance_reports",
            "monitoring/alerts",
            "monitoring/dashboards"
        ]
        
        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)
    
    def load_default_config(self) -> Dict[str, Any]:
        """Load default monitoring configuration"""
        return {
            "monitoring_interval": 300,  # 5 minutes
            "drift_detection": {
                "enabled": True,
                "methods": ["ks_test", "psi", "jensen_shannon"],
                "thresholds": {
                    "ks_test_significance": 0.05,
                    "psi_threshold": 0.25,
                    "jensen_shannon_threshold": 0.2
                }
            },
            "performance_thresholds": {
                "precision_at_5": {"critical": 0.65, "warning": 0.70},
                "mrr": {"critical": 0.60, "warning": 0.65},
                "latency_p95_ms": {"critical": 3000, "warning": 2500},
                "error_rate": {"critical": 0.10, "warning": 0.05}
            },
            "alerting": {
                "enabled": True,
                "channels": ["cloudwatch", "file", "mlflow"],
                "cooldown_minutes": 30
            },
            "reporting": {
                "generate_daily_reports": True,
                "generate_weekly_summaries": True,
                "retention_days": 90
            }
        }
    
    def load_baseline_data(self, baseline_file: str = None) -> pd.DataFrame:
        """Load baseline data for drift detection"""
        if baseline_file is None:
            # Use sample baseline data
            baseline_data = pd.DataFrame({
                'query_embedding_similarity': np.random.normal(0.75, 0.1, 500),
                'retrieval_score': np.random.normal(0.68, 0.08, 500),
                'query_length': np.random.poisson(25, 500),
                'response_length': np.random.poisson(150, 500),
                'processing_time_ms': np.random.gamma(2, 90, 500)
            })
        else:
            baseline_data = pd.read_csv(baseline_file)
        
        self.drift_detector = DriftDetector(
            baseline_data,
            significance_level=self.config["drift_detection"]["thresholds"]["ks_test_significance"]
        )
        
        return baseline_data
    
    def collect_current_metrics(self) -> Dict[str, float]:
        """Collect current model performance metrics"""
        # In production, this would connect to actual monitoring endpoints
        # For demo purposes, we simulate realistic metrics with some variation
        
        current_time = datetime.now()
        
        # Simulate performance degradation over time for demo
        degradation_factor = min(1.0, (current_time.hour / 24) * 0.1)  # Slight degradation over day
        
        metrics = {
            "timestamp": current_time.isoformat(),
            "precision_at_5": max(0.5, 0.72 - degradation_factor + np.random.normal(0, 0.02)),
            "mrr": max(0.4, 0.68 - degradation_factor + np.random.normal(0, 0.015)),
            "recall_at_10": max(0.3, 0.65 - degradation_factor + np.random.normal(0, 0.02)),
            "latency_mean_ms": 180 + degradation_factor * 50 + np.random.normal(0, 10),
            "latency_p95_ms": 400 + degradation_factor * 100 + np.random.normal(0, 20),
            "error_rate": max(0.0, degradation_factor * 0.05 + np.random.exponential(0.005)),
            "queries_per_minute": max(1, 50 + np.random.normal(0, 10)),
            "memory_usage_mb": 2048 + np.random.normal(0, 100),
            "cpu_utilization": min(100, 45 + degradation_factor * 20 + np.random.normal(0, 5))
        }
        
        return metrics
    
    def collect_current_data_sample(self) -> pd.DataFrame:
        """Collect current data sample for drift detection"""
        # Simulate data with potential drift
        drift_factor = np.random.uniform(0, 0.3)  # Random drift for demo
        
        current_data = pd.DataFrame({
            'query_embedding_similarity': np.random.normal(0.75 - drift_factor * 0.1, 0.1, 100),
            'retrieval_score': np.random.normal(0.68 - drift_factor * 0.08, 0.08, 100),
            'query_length': np.random.poisson(25 + drift_factor * 10, 100),
            'response_length': np.random.poisson(150 + drift_factor * 20, 100),  
            'processing_time_ms': np.random.gamma(2, 90 + drift_factor * 30, 100)
        })
        
        return current_data
    
    def check_performance_thresholds(self, metrics: Dict[str, float]) -> Dict[str, str]:
        """Check if metrics exceed defined thresholds"""
        alerts = {}
        thresholds = self.config["performance_thresholds"]
        
        for metric_name, value in metrics.items():
            if metric_name in thresholds:
                threshold_config = thresholds[metric_name]
                
                if metric_name in ["latency_mean_ms", "latency_p95_ms", "error_rate"]:
                    # Higher is worse for these metrics
                    if value >= threshold_config["critical"]:
                        alerts[metric_name] = "critical"
                    elif value >= threshold_config["warning"]:
                        alerts[metric_name] = "warning"
                else:
                    # Lower is worse for these metrics
                    if value <= threshold_config["critical"]:
                        alerts[metric_name] = "critical"
                    elif value <= threshold_config["warning"]:
                        alerts[metric_name] = "warning"
        
        return alerts
    
    def log_to_mlflow(self, metrics: Dict[str, float], drift_results: Dict[str, Any] = None):
        """Log metrics and drift results to MLflow"""
        if not MLFLOW_AVAILABLE:
            return
        
        try:
            # Get or create experiment
            experiment = mlflow.get_experiment_by_name(self.experiment_name)
            if experiment is None:
                mlflow.create_experiment(self.experiment_name)
            
            mlflow.set_experiment(self.experiment_name)
            
            with mlflow.start_run(run_name=f"monitoring_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                # Log performance metrics
                for metric_name, value in metrics.items():
                    if isinstance(value, (int, float)):
                        mlflow.log_metric(metric_name, value)
                
                # Log drift metrics if available
                if drift_results:
                    for column, drift_info in drift_results.items():
                        if isinstance(drift_info, dict):
                            for drift_metric, drift_value in drift_info.items():
                                if isinstance(drift_value, (int, float)):
                                    mlflow.log_metric(f"drift_{column}_{drift_metric}", drift_value)
                
                # Add monitoring tags
                mlflow.set_tag("monitoring_type", "production")
                mlflow.set_tag("timestamp", metrics.get("timestamp", datetime.now().isoformat()))
                
        except Exception as e:
            self.logger.error(f"Failed to log to MLflow: {e}")
    
    def send_cloudwatch_metrics(self, metrics: Dict[str, float]):
        """Send metrics to CloudWatch"""
        if not AWS_AVAILABLE:
            return
        
        try:
            cloudwatch = boto3.client('cloudwatch')
            namespace = "RAGAssistant/MLOps"
            
            metric_data = []
            for metric_name, value in metrics.items():
                if isinstance(value, (int, float)) and metric_name != "timestamp":
                    metric_data.append({
                        'MetricName': metric_name,
                        'Value': float(value),
                        'Unit': 'None',
                        'Timestamp': datetime.now()
                    })
            
            if metric_data:
                cloudwatch.put_metric_data(
                    Namespace=namespace,
                    MetricData=metric_data
                )
                self.logger.info(f"Sent {len(metric_data)} metrics to CloudWatch")
                
        except Exception as e:
            self.logger.error(f"Failed to send metrics to CloudWatch: {e}")
    
    def generate_drift_report(self, drift_results: Dict[str, Any]) -> str:
        """Generate comprehensive drift detection report"""
        report = f"""
Data Drift Detection Report
Generated: {datetime.now().isoformat()}

DRIFT DETECTION SUMMARY:
"""
        
        # Check for overall drift
        any_drift = False
        for column, results in drift_results.items():
            if isinstance(results, dict) and results.get("drift_detected", False):
                any_drift = True
                break
        
        status = "DRIFT DETECTED" if any_drift else "NO DRIFT DETECTED"
        report += f"Overall Status: {status}\n\n"
        
        # Detailed results per feature
        report += "FEATURE-LEVEL DRIFT ANALYSIS:\n"
        for column, results in drift_results.items():
            if isinstance(results, dict):
                report += f"\nFeature: {column}\n"
                report += f"  KS Statistic: {results.get('ks_statistic', 'N/A'):.4f}\n"
                report += f"  P-value: {results.get('p_value', 'N/A'):.4f}\n"
                report += f"  Drift Detected: {'Yes' if results.get('drift_detected', False) else 'No'}\n"
                report += f"  Severity: {results.get('drift_severity', 'Unknown')}\n"
        
        # Recommendations
        report += f"\nRECOMMENDations:\n"
        if any_drift:
            report += "- Investigate data pipeline for changes\n"
            report += "- Consider model retraining\n" 
            report += "- Review data quality processes\n"
            report += "- Monitor performance metrics closely\n"
        else:
            report += "- Continue normal monitoring\n"
            report += "- Maintain current model in production\n"
        
        # Save report
        report_file = self.project_path / "monitoring" / "drift_reports" / f"drift_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return report
    
    def generate_performance_report(self, metrics_history: List[Dict[str, float]]) -> str:
        """Generate performance monitoring report"""
        if not metrics_history:
            return "No metrics data available for reporting"
        
        df = pd.DataFrame(metrics_history)
        
        # Calculate summary statistics
        summary_stats = {}
        metric_columns = ['precision_at_5', 'mrr', 'latency_mean_ms', 'error_rate']
        
        for metric in metric_columns:
            if metric in df.columns:
                summary_stats[metric] = {
                    'mean': df[metric].mean(),
                    'std': df[metric].std(),
                    'min': df[metric].min(),
                    'max': df[metric].max(),
                    'current': df[metric].iloc[-1]
                }
        
        report = f"""
Model Performance Monitoring Report
Generated: {datetime.now().isoformat()}
Monitoring Period: {df['timestamp'].iloc[0]} to {df['timestamp'].iloc[-1]}
Total Data Points: {len(df)}

PERFORMANCE SUMMARY:
"""
        
        for metric, stats in summary_stats.items():
            report += f"\n{metric.replace('_', ' ').title()}:\n"
            report += f"  Current: {stats['current']:.4f}\n"
            report += f"  Average: {stats['mean']:.4f}\n"
            report += f"  Std Dev: {stats['std']:.4f}\n"
            report += f"  Range: {stats['min']:.4f} - {stats['max']:.4f}\n"
        
        # Performance trends
        report += f"\nPERFORMANCE TRENDS:\n"
        for metric in metric_columns:
            if metric in df.columns and len(df) > 10:
                # Simple trend analysis
                recent_mean = df[metric].tail(10).mean()
                earlier_mean = df[metric].head(10).mean()
                trend = "improving" if recent_mean > earlier_mean else "declining"
                
                if metric in ["latency_mean_ms", "error_rate"]:
                    trend = "improving" if recent_mean < earlier_mean else "declining"
                
                report += f"  {metric.replace('_', ' ').title()}: {trend}\n"
        
        # Save report
        report_file = self.project_path / "monitoring" / "performance_reports" / f"performance_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return report
    
    def run_monitoring_cycle(self) -> Dict[str, Any]:
        """Run a single monitoring cycle"""
        cycle_start = datetime.now()
        
        # Collect current metrics
        current_metrics = self.collect_current_metrics()
        self.metrics_buffer.append(current_metrics)
        
        # Check performance thresholds
        alerts = self.check_performance_thresholds(current_metrics)
        
        # Drift detection if enabled
        drift_results = None
        if self.config["drift_detection"]["enabled"] and self.drift_detector:
            current_data = self.collect_current_data_sample()
            drift_results = self.drift_detector.detect_drift_ks_test(current_data)
        
        # Log metrics
        self.log_to_mlflow(current_metrics, drift_results)
        self.send_cloudwatch_metrics(current_metrics)
        
        # Generate alerts if needed
        if alerts:
            self.handle_alerts(alerts, current_metrics)
        
        # Log cycle completion
        cycle_duration = (datetime.now() - cycle_start).total_seconds()
        self.logger.info(f"Monitoring cycle completed in {cycle_duration:.2f}s")
        
        return {
            "timestamp": cycle_start.isoformat(),
            "metrics": current_metrics,
            "alerts": alerts,
            "drift_results": drift_results,
            "cycle_duration_seconds": cycle_duration
        }
    
    def handle_alerts(self, alerts: Dict[str, str], metrics: Dict[str, float]):
        """Handle performance alerts"""
        alert_message = f"Model Performance Alert - {datetime.now().isoformat()}\n\n"
        
        for metric, severity in alerts.items():
            alert_message += f"{severity.upper()} ALERT: {metric} = {metrics[metric]:.4f}\n"
        
        # Log alert
        self.logger.warning(f"Performance alerts triggered: {alerts}")
        
        # Save alert to file
        alert_file = self.project_path / "monitoring" / "alerts" / f"alert_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(alert_file, 'w') as f:
            f.write(alert_message)
    
    def run_continuous_monitoring(self, duration_minutes: int = None):
        """Run continuous monitoring loop"""
        self.logger.info("Starting continuous monitoring...")
        
        # Load baseline data
        self.load_baseline_data()
        
        start_time = datetime.now()
        cycle_count = 0
        
        try:
            while True:
                # Run monitoring cycle
                cycle_result = self.run_monitoring_cycle()
                cycle_count += 1
                
                # Check duration limit
                if duration_minutes:
                    elapsed = (datetime.now() - start_time).total_seconds() / 60
                    if elapsed >= duration_minutes:
                        break
                
                # Wait for next cycle
                time.sleep(self.config["monitoring_interval"])
                
        except KeyboardInterrupt:
            self.logger.info("Monitoring stopped by user")
        except Exception as e:
            self.logger.error(f"Monitoring error: {e}")
        
        self.logger.info(f"Monitoring completed. Ran {cycle_count} cycles")
        
        # Generate summary report
        if self.metrics_buffer:
            metrics_list = list(self.metrics_buffer)
            report = self.generate_performance_report(metrics_list)
            self.logger.info(f"Generated performance report")
    
    def analyze_historical_performance(self, days: int = 30):
        """Analyze historical performance data"""
        self.logger.info(f"Analyzing historical performance for last {days} days")
        
        # In production, would query actual metrics store
        # For demo, generate sample historical data
        historical_data = []
        start_date = datetime.now() - timedelta(days=days)
        
        for i in range(days * 24):  # Hourly data points
            timestamp = start_date + timedelta(hours=i)
            
            # Simulate performance variation over time
            day_factor = np.sin(2 * np.pi * i / 24) * 0.05  # Daily pattern
            week_factor = np.sin(2 * np.pi * i / (24 * 7)) * 0.03  # Weekly pattern
            trend_factor = i / (days * 24) * 0.1  # Gradual degradation
            
            metrics = {
                "timestamp": timestamp.isoformat(),
                "precision_at_5": 0.72 + day_factor + week_factor - trend_factor + np.random.normal(0, 0.01),
                "mrr": 0.68 + day_factor + week_factor - trend_factor + np.random.normal(0, 0.008),
                "latency_mean_ms": 180 - day_factor * 20 - week_factor * 15 + trend_factor * 50 + np.random.normal(0, 5),
                "error_rate": max(0, 0.01 + trend_factor * 0.02 + np.random.exponential(0.002))
            }
            historical_data.append(metrics)
        
        # Generate comprehensive analysis
        report = self.generate_performance_report(historical_data)
        
        # Create visualization
        self.create_performance_dashboard(historical_data)
        
        return historical_data, report
    
    def create_performance_dashboard(self, metrics_data: List[Dict[str, float]]):
        """Create performance monitoring dashboard"""
        df = pd.DataFrame(metrics_data)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Create dashboard visualization
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        fig.suptitle('Model Performance Dashboard', fontsize=16, fontweight='bold')
        
        # Precision at 5
        axes[0, 0].plot(df['timestamp'], df['precision_at_5'], color='blue', linewidth=2)
        axes[0, 0].axhline(y=0.70, color='orange', linestyle='--', alpha=0.7, label='Warning')
        axes[0, 0].axhline(y=0.65, color='red', linestyle='--', alpha=0.7, label='Critical')
        axes[0, 0].set_title('Precision@5')
        axes[0, 0].set_ylabel('Precision')
        axes[0, 0].legend()
        axes[0, 0].grid(True, alpha=0.3)
        
        # MRR
        axes[0, 1].plot(df['timestamp'], df['mrr'], color='green', linewidth=2)
        axes[0, 1].axhline(y=0.65, color='orange', linestyle='--', alpha=0.7, label='Warning')
        axes[0, 1].axhline(y=0.60, color='red', linestyle='--', alpha=0.7, label='Critical')
        axes[0, 1].set_title('Mean Reciprocal Rank (MRR)')
        axes[0, 1].set_ylabel('MRR')
        axes[0, 1].legend()
        axes[0, 1].grid(True, alpha=0.3)
        
        # Latency
        axes[1, 0].plot(df['timestamp'], df['latency_mean_ms'], color='purple', linewidth=2)
        axes[1, 0].axhline(y=2500, color='orange', linestyle='--', alpha=0.7, label='Warning')
        axes[1, 0].axhline(y=3000, color='red', linestyle='--', alpha=0.7, label='Critical')
        axes[1, 0].set_title('Response Latency')
        axes[1, 0].set_ylabel('Latency (ms)')
        axes[1, 0].legend()
        axes[1, 0].grid(True, alpha=0.3)
        
        # Error Rate
        axes[1, 1].plot(df['timestamp'], df['error_rate'], color='red', linewidth=2)
        axes[1, 1].axhline(y=0.05, color='orange', linestyle='--', alpha=0.7, label='Warning')
        axes[1, 1].axhline(y=0.10, color='red', linestyle='--', alpha=0.7, label='Critical')
        axes[1, 1].set_title('Error Rate')
        axes[1, 1].set_ylabel('Error Rate')
        axes[1, 1].legend()
        axes[1, 1].grid(True, alpha=0.3)
        
        # Format x-axes
        for ax in axes.flat:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        
        # Save dashboard
        dashboard_file = self.project_path / "monitoring" / "dashboards" / f"performance_dashboard_{datetime.now().strftime('%Y%m%d_%H%M%S')}.png"
        plt.savefig(dashboard_file, dpi=300, bbox_inches='tight')
        plt.close()
        
        self.logger.info(f"Performance dashboard saved to: {dashboard_file}")


def main():
    parser = argparse.ArgumentParser(description='Model Performance Monitoring System')
    parser.add_argument('--project-path', default='/Users/peter/Desktop/ai_rag_assistant',
                       help='Path to RAG project')
    parser.add_argument('--mode', choices=['continuous', 'analyze-history', 'setup-alerts', 'single-check'],
                       default='single-check', help='Monitoring mode')
    parser.add_argument('--duration-minutes', type=int, help='Duration for continuous monitoring')
    parser.add_argument('--monitoring-interval', type=int, default=300,
                       help='Monitoring interval in seconds')
    parser.add_argument('--drift-threshold', type=float, default=0.1,
                       help='Drift detection threshold')
    parser.add_argument('--days', type=int, default=30,
                       help='Days for historical analysis')
    parser.add_argument('--generate-report', action='store_true',
                       help='Generate performance report')
    parser.add_argument('--setup-cloudwatch', action='store_true',
                       help='Setup CloudWatch integration')
    
    args = parser.parse_args()
    
    try:
        # Initialize monitoring system
        monitor = ModelPerformanceMonitor(
            project_path=args.project_path
        )
        monitor.config["monitoring_interval"] = args.monitoring_interval
        
        print("Model Performance Monitoring System")
        print("=" * 40)
        
        if args.mode == 'continuous':
            print(f"Starting continuous monitoring (interval: {args.monitoring_interval}s)")
            if args.duration_minutes:
                print(f"Duration: {args.duration_minutes} minutes")
            monitor.run_continuous_monitoring(args.duration_minutes)
            
        elif args.mode == 'analyze-history':
            print(f"Analyzing last {args.days} days of performance")
            historical_data, report = monitor.analyze_historical_performance(args.days)
            print("\nHistorical Analysis Complete")
            print(f"Analyzed {len(historical_data)} data points")
            
            if args.generate_report:
                print("\nGenerated Performance Report:")
                print(report)
                
        elif args.mode == 'single-check':
            print("Running single monitoring check")
            result = monitor.run_monitoring_cycle()
            
            print("\nMonitoring Results:")
            print(f"Timestamp: {result['timestamp']}")
            print(f"Cycle Duration: {result['cycle_duration_seconds']:.2f}s")
            
            print("\nCurrent Metrics:")
            for metric, value in result['metrics'].items():
                if metric != 'timestamp' and isinstance(value, (int, float)):
                    print(f"  {metric}: {value:.4f}")
            
            if result['alerts']:
                print(f"\nAlerts Triggered: {result['alerts']}")
            else:
                print("\nNo alerts triggered")
                
        elif args.mode == 'setup-alerts':
            print("Setting up monitoring alerts")
            # Create default alert configuration
            alert_config = monitor.config
            config_file = monitor.project_path / "configs" / "mlops" / "monitoring_alerts.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(alert_config, f, indent=2)
            print(f"Alert configuration saved to: {config_file}")
        
        print("\nMonitoring session completed successfully")
        
    except Exception as e:
        print(f"[ERROR] Monitoring failed: {e}")
        raise


if __name__ == "__main__":
    main()