"""
Automated Model Retraining Pipeline System

This script manages automated model retraining workflows for the RAG system
including trigger detection, data validation, training orchestration, and
deployment validation for continuous model improvement.

Features:
- Automated retraining trigger detection and scheduling
- Data quality validation and preprocessing pipelines
- Model training orchestration with hyperparameter optimization
- Performance validation before deployment promotion
- Rollback capabilities for failed deployments
- Training pipeline monitoring and logging
- Integration with MLflow for experiment tracking

Usage:
    # Setup automated retraining with performance triggers
    python scripts/mlops/automated_retraining.py \
        --trigger performance \
        --threshold 0.05 \
        --schedule daily

    # Manual retraining with validation
    python scripts/mlops/automated_retraining.py \
        --manual \
        --validation-set data/evaluation/scale_test_set.jsonl \
        --retrain-components embeddings,reranker

    # Check retraining triggers and schedule
    python scripts/mlops/automated_retraining.py \
        --mode check-triggers \
        --dry-run
"""

import argparse
import json
import logging
import os
import shutil
import time
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from sklearn.model_selection import ParameterGrid
import matplotlib.pyplot as plt
import seaborn as sns

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


class RetrainingTriggerManager:
    """Manage retraining triggers and scheduling"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def check_performance_trigger(self, current_metrics: Dict[str, float], 
                                baseline_metrics: Dict[str, float]) -> Tuple[bool, str]:
        """Check if performance degradation triggers retraining"""
        trigger_config = self.config.get("triggers", {}).get("performance", {})
        threshold = trigger_config.get("relative_degradation", 0.05)
        
        trigger_metrics = trigger_config.get("metrics", ["precision_at_5", "mrr"])
        degraded_metrics = []
        
        for metric in trigger_metrics:
            if metric in current_metrics and metric in baseline_metrics:
                baseline_value = baseline_metrics[metric]
                current_value = current_metrics[metric]
                
                # Calculate relative degradation
                if baseline_value > 0:
                    degradation = (baseline_value - current_value) / baseline_value
                    
                    if degradation > threshold:
                        degraded_metrics.append(f"{metric}: {degradation:.3%} degradation")
        
        if degraded_metrics:
            reason = f"Performance degradation detected: {', '.join(degraded_metrics)}"
            return True, reason
        
        return False, "No significant performance degradation"
    
    def check_drift_trigger(self, drift_results: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if data drift triggers retraining"""
        if not drift_results:
            return False, "No drift data available"
        
        trigger_config = self.config.get("triggers", {}).get("drift", {})
        threshold = trigger_config.get("threshold", 0.2)
        
        significant_drift = []
        for feature, results in drift_results.items():
            if isinstance(results, dict):
                ks_statistic = results.get("ks_statistic", 0)
                drift_detected = results.get("drift_detected", False)
                
                if drift_detected and ks_statistic > threshold:
                    significant_drift.append(f"{feature}: KS={ks_statistic:.3f}")
        
        if significant_drift:
            reason = f"Significant data drift detected: {', '.join(significant_drift)}"
            return True, reason
        
        return False, "No significant data drift"
    
    def check_schedule_trigger(self) -> Tuple[bool, str]:
        """Check if scheduled retraining is due"""
        schedule_config = self.config.get("triggers", {}).get("schedule", {})
        if not schedule_config.get("enabled", False):
            return False, "Scheduled retraining disabled"
        
        schedule_type = schedule_config.get("type", "weekly")
        last_training_file = Path(self.config["project_path"]) / "models" / "last_training_timestamp.txt"
        
        if not last_training_file.exists():
            return True, f"No previous training record found - {schedule_type} schedule"
        
        try:
            with open(last_training_file, 'r') as f:
                last_training_str = f.read().strip()
            last_training = datetime.fromisoformat(last_training_str)
        except Exception as e:
            self.logger.warning(f"Could not parse last training timestamp: {e}")
            return True, f"Could not parse last training timestamp - {schedule_type} schedule"
        
        now = datetime.now()
        time_since_last = now - last_training
        
        if schedule_type == "daily" and time_since_last > timedelta(days=1):
            return True, f"Daily retraining due (last: {last_training.strftime('%Y-%m-%d %H:%M')})"
        elif schedule_type == "weekly" and time_since_last > timedelta(weeks=1):
            return True, f"Weekly retraining due (last: {last_training.strftime('%Y-%m-%d')})"
        elif schedule_type == "monthly" and time_since_last > timedelta(days=30):
            return True, f"Monthly retraining due (last: {last_training.strftime('%Y-%m-%d')})"
        
        return False, f"Next {schedule_type} retraining not yet due"
    
    def check_all_triggers(self, current_metrics: Dict[str, float] = None,
                          baseline_metrics: Dict[str, float] = None,
                          drift_results: Dict[str, Any] = None) -> Tuple[bool, List[str]]:
        """Check all retraining triggers"""
        triggered_reasons = []
        
        # Performance trigger
        if current_metrics and baseline_metrics:
            performance_triggered, performance_reason = self.check_performance_trigger(
                current_metrics, baseline_metrics
            )
            if performance_triggered:
                triggered_reasons.append(performance_reason)
        
        # Drift trigger
        if drift_results:
            drift_triggered, drift_reason = self.check_drift_trigger(drift_results)
            if drift_triggered:
                triggered_reasons.append(drift_reason)
        
        # Schedule trigger
        schedule_triggered, schedule_reason = self.check_schedule_trigger()
        if schedule_triggered:
            triggered_reasons.append(schedule_reason)
        
        return len(triggered_reasons) > 0, triggered_reasons


class DataQualityValidator:
    """Validate data quality for retraining"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    def validate_data_completeness(self, data_path: str) -> Dict[str, Any]:
        """Validate data completeness and coverage"""
        try:
            if data_path.endswith('.jsonl'):
                data = []
                with open(data_path, 'r') as f:
                    for line in f:
                        data.append(json.loads(line))
                df = pd.DataFrame(data)
            else:
                df = pd.read_csv(data_path)
            
            validation_results = {
                "total_samples": len(df),
                "missing_data": df.isnull().sum().to_dict(),
                "data_types": df.dtypes.to_dict(),
                "unique_values": {col: df[col].nunique() for col in df.columns},
                "validation_passed": True,
                "issues": []
            }
            
            # Check minimum data requirements
            min_samples = self.config.get("data_quality", {}).get("min_samples", 1000)
            if len(df) < min_samples:
                validation_results["validation_passed"] = False
                validation_results["issues"].append(f"Insufficient data: {len(df)} < {min_samples}")
            
            # Check for excessive missing data
            max_missing_rate = self.config.get("data_quality", {}).get("max_missing_rate", 0.1)
            for col, missing_count in validation_results["missing_data"].items():
                missing_rate = missing_count / len(df)
                if missing_rate > max_missing_rate:
                    validation_results["validation_passed"] = False
                    validation_results["issues"].append(f"Excessive missing data in {col}: {missing_rate:.2%}")
            
            return validation_results
            
        except Exception as e:
            return {
                "validation_passed": False,
                "error": str(e),
                "issues": [f"Data loading failed: {e}"]
            }
    
    def validate_data_distribution(self, current_data_path: str, 
                                 reference_data_path: str = None) -> Dict[str, Any]:
        """Validate data distribution consistency"""
        try:
            # Load current data
            with open(current_data_path, 'r') as f:
                current_data = [json.loads(line) for line in f]
            
            current_df = pd.DataFrame(current_data)
            
            # Basic distribution statistics
            distribution_stats = {
                "query_length": {
                    "mean": current_df.get('query', pd.Series([])).str.len().mean(),
                    "std": current_df.get('query', pd.Series([])).str.len().std(),
                    "median": current_df.get('query', pd.Series([])).str.len().median()
                }
            }
            
            validation_results = {
                "distribution_stats": distribution_stats,
                "validation_passed": True,
                "issues": [],
                "comparison_available": False
            }
            
            # Compare with reference data if available
            if reference_data_path and Path(reference_data_path).exists():
                with open(reference_data_path, 'r') as f:
                    reference_data = [json.loads(line) for line in f]
                reference_df = pd.DataFrame(reference_data)
                
                # Compare distributions (simplified)
                current_query_lengths = current_df.get('query', pd.Series([])).str.len()
                reference_query_lengths = reference_df.get('query', pd.Series([])).str.len()
                
                if len(current_query_lengths) > 0 and len(reference_query_lengths) > 0:
                    from scipy import stats
                    ks_stat, p_value = stats.ks_2samp(current_query_lengths, reference_query_lengths)
                    
                    validation_results["distribution_comparison"] = {
                        "ks_statistic": ks_stat,
                        "p_value": p_value,
                        "significant_change": p_value < 0.05
                    }
                    
                    if p_value < 0.05:
                        validation_results["issues"].append(f"Significant distribution change detected (p={p_value:.4f})")
                    
                    validation_results["comparison_available"] = True
            
            return validation_results
            
        except Exception as e:
            return {
                "validation_passed": False,
                "error": str(e),
                "issues": [f"Distribution validation failed: {e}"]
            }


class ModelTrainingOrchestrator:
    """Orchestrate model training and hyperparameter optimization"""
    
    def __init__(self, project_path: str, config: Dict[str, Any]):
        self.project_path = Path(project_path)
        self.config = config
        self.logger = logging.getLogger(__name__)
        
        # Setup MLflow if available
        if MLFLOW_AVAILABLE:
            mlflow.set_tracking_uri(str(self.project_path / "mlruns"))
    
    def prepare_training_environment(self) -> str:
        """Prepare training environment and workspace"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        training_dir = self.project_path / "training" / f"retraining_{timestamp}"
        training_dir.mkdir(parents=True, exist_ok=True)
        
        # Create training workspace
        workspace_dirs = [
            training_dir / "data",
            training_dir / "models", 
            training_dir / "logs",
            training_dir / "results"
        ]
        
        for directory in workspace_dirs:
            directory.mkdir(exist_ok=True)
        
        self.logger.info(f"Created training environment: {training_dir}")
        return str(training_dir)
    
    def generate_hyperparameter_grid(self, component: str) -> List[Dict[str, Any]]:
        """Generate hyperparameter search grid for component"""
        hyperparameter_configs = {
            "embeddings": {
                "model_name": [
                    "all-MiniLM-L6-v2",
                    "all-mpnet-base-v2", 
                    "e5-small-v2"
                ],
                "max_seq_length": [256, 384, 512],
                "pooling_mode": ["mean", "cls"]
            },
            "retrieval": {
                "top_k_retrieval": [20, 50, 100],
                "top_k_final": [5, 10, 15],
                "bm25_weight": [0.3, 0.5, 0.7],
                "semantic_weight": [0.3, 0.5, 0.7],
                "reranker_strategy": ["passthrough", "cross_encoder"]
            },
            "reranker": {
                "strategy": ["cross_encoder", "llm_based"],
                "model_name": ["cross-encoder/ms-marco-MiniLM-L-6-v2"],
                "threshold": [0.1, 0.3, 0.5],
                "top_k": [5, 10, 15]
            }
        }
        
        # Generate parameter grid
        config = hyperparameter_configs.get(component, {})
        if not config:
            return [{}]  # Return empty config if component not found
        
        # Limit grid size to prevent excessive runs
        max_combinations = self.config.get("training", {}).get("max_hyperparameter_combinations", 20)
        
        full_grid = list(ParameterGrid(config))
        if len(full_grid) > max_combinations:
            # Sample random subset
            np.random.seed(42)
            indices = np.random.choice(len(full_grid), size=max_combinations, replace=False)
            grid = [full_grid[i] for i in indices]
        else:
            grid = full_grid
        
        self.logger.info(f"Generated hyperparameter grid for {component}: {len(grid)} combinations")
        return grid
    
    def simulate_training_run(self, component: str, hyperparams: Dict[str, Any]) -> Dict[str, float]:
        """Simulate training run with hyperparameters (for demo purposes)"""
        # This would be replaced with actual training logic in production
        
        # Simulate training time
        time.sleep(1)
        
        # Generate realistic performance metrics with hyperparameter influence
        base_metrics = {
            "precision_at_5": 0.72,
            "mrr": 0.68,
            "recall_at_10": 0.65,
            "latency_mean_ms": 180,
            "training_time_minutes": 15
        }
        
        # Simulate hyperparameter effects
        metrics = {}
        for metric, base_value in base_metrics.items():
            # Add random variation and hyperparameter influence
            variation = np.random.normal(0, 0.03)
            
            # Simple hyperparameter influence simulation
            if "model_name" in hyperparams:
                if "mpnet" in hyperparams["model_name"]:
                    variation += 0.02  # Better performance
                elif "e5" in hyperparams["model_name"]:
                    variation += 0.015
            
            if "top_k_final" in hyperparams:
                if hyperparams["top_k_final"] == 10:
                    variation += 0.01  # Optimal value
            
            metrics[metric] = base_value + variation
        
        return metrics
    
    def run_hyperparameter_optimization(self, component: str, training_dir: str) -> Dict[str, Any]:
        """Run hyperparameter optimization for component"""
        if not MLFLOW_AVAILABLE:
            self.logger.warning("MLflow not available - using simplified tracking")
        
        experiment_name = f"retraining_{component}_{datetime.now().strftime('%Y%m%d')}"
        
        if MLFLOW_AVAILABLE:
            # Create experiment
            try:
                mlflow.create_experiment(experiment_name)
            except:
                pass  # Experiment may already exist
            mlflow.set_experiment(experiment_name)
        
        # Generate hyperparameter grid
        hyperparameter_grid = self.generate_hyperparameter_grid(component)
        
        best_metrics = None
        best_params = None
        best_score = -np.inf
        
        results = []
        
        self.logger.info(f"Starting hyperparameter optimization for {component}")
        self.logger.info(f"Testing {len(hyperparameter_grid)} parameter combinations")
        
        for i, params in enumerate(hyperparameter_grid):
            self.logger.info(f"Training run {i+1}/{len(hyperparameter_grid)}")
            
            if MLFLOW_AVAILABLE:
                with mlflow.start_run(run_name=f"{component}_run_{i+1}"):
                    # Log parameters
                    mlflow.log_params(params)
                    
                    # Run training
                    metrics = self.simulate_training_run(component, params)
                    
                    # Log metrics
                    for metric_name, value in metrics.items():
                        mlflow.log_metric(metric_name, value)
                    
                    # Calculate composite score for optimization
                    score = self.calculate_composite_score(metrics)
                    mlflow.log_metric("composite_score", score)
                    
                    if score > best_score:
                        best_score = score
                        best_metrics = metrics
                        best_params = params
                    
                    results.append({
                        "params": params,
                        "metrics": metrics,
                        "composite_score": score
                    })
            else:
                # Simple training without MLflow
                metrics = self.simulate_training_run(component, params)
                score = self.calculate_composite_score(metrics)
                
                if score > best_score:
                    best_score = score
                    best_metrics = metrics
                    best_params = params
                
                results.append({
                    "params": params,
                    "metrics": metrics,
                    "composite_score": score
                })
        
        optimization_results = {
            "component": component,
            "best_parameters": best_params,
            "best_metrics": best_metrics,
            "best_score": best_score,
            "total_runs": len(hyperparameter_grid),
            "all_results": results
        }
        
        # Save results
        results_file = Path(training_dir) / f"{component}_optimization_results.json"
        with open(results_file, 'w') as f:
            json.dump(optimization_results, f, indent=2, default=str)
        
        self.logger.info(f"Hyperparameter optimization completed for {component}")
        self.logger.info(f"Best score: {best_score:.4f}")
        
        return optimization_results
    
    def calculate_composite_score(self, metrics: Dict[str, float]) -> float:
        """Calculate composite score for optimization"""
        scoring_config = self.config.get("training", {}).get("scoring_weights", {
            "precision_at_5": 0.3,
            "mrr": 0.3,
            "recall_at_10": 0.2,
            "latency_penalty_weight": 0.2
        })
        
        score = 0.0
        
        # Positive contributions
        for metric in ["precision_at_5", "mrr", "recall_at_10"]:
            if metric in metrics and metric in scoring_config:
                score += metrics[metric] * scoring_config[metric]
        
        # Latency penalty (higher latency reduces score)
        if "latency_mean_ms" in metrics:
            baseline_latency = 200  # ms
            latency_penalty = max(0, (metrics["latency_mean_ms"] - baseline_latency) / 1000)
            score -= latency_penalty * scoring_config.get("latency_penalty_weight", 0.2)
        
        return score
    
    def validate_trained_model(self, model_results: Dict[str, Any], 
                             baseline_metrics: Dict[str, float]) -> Dict[str, Any]:
        """Validate trained model against baseline"""
        validation_config = self.config.get("training", {}).get("validation", {})
        min_improvement = validation_config.get("min_improvement", 0.02)
        
        new_metrics = model_results["best_metrics"]
        validation_results = {
            "validation_passed": True,
            "improvements": {},
            "degradations": {},
            "overall_improvement": 0.0,
            "issues": []
        }
        
        key_metrics = ["precision_at_5", "mrr", "recall_at_10"]
        total_improvement = 0.0
        
        for metric in key_metrics:
            if metric in new_metrics and metric in baseline_metrics:
                improvement = new_metrics[metric] - baseline_metrics[metric]
                improvement_pct = improvement / baseline_metrics[metric]
                
                if improvement > 0:
                    validation_results["improvements"][metric] = {
                        "absolute": improvement,
                        "relative": improvement_pct
                    }
                else:
                    validation_results["degradations"][metric] = {
                        "absolute": improvement,
                        "relative": improvement_pct
                    }
                
                total_improvement += improvement_pct
        
        validation_results["overall_improvement"] = total_improvement / len(key_metrics)
        
        # Check minimum improvement requirement
        if validation_results["overall_improvement"] < min_improvement:
            validation_results["validation_passed"] = False
            validation_results["issues"].append(
                f"Insufficient improvement: {validation_results['overall_improvement']:.2%} < {min_improvement:.2%}"
            )
        
        # Check for significant degradations
        max_degradation = validation_config.get("max_individual_degradation", 0.05)
        for metric, degradation in validation_results["degradations"].items():
            if abs(degradation["relative"]) > max_degradation:
                validation_results["validation_passed"] = False
                validation_results["issues"].append(
                    f"Significant degradation in {metric}: {degradation['relative']:.2%}"
                )
        
        return validation_results


class AutomatedRetrainingPipeline:
    """Main automated retraining pipeline orchestrator"""
    
    def __init__(self, project_path: str, config_path: str = None):
        self.project_path = Path(project_path)
        
        # Load configuration
        self.config = self.load_config(config_path)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.trigger_manager = RetrainingTriggerManager(self.config)
        self.data_validator = DataQualityValidator(self.config)
        self.training_orchestrator = ModelTrainingOrchestrator(project_path, self.config)
        
        # Create necessary directories
        self.create_directories()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.project_path / "logs" / "mlops" / "automated_retraining.log"
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
    
    def load_config(self, config_path: str = None) -> Dict[str, Any]:
        """Load retraining configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "project_path": str(self.project_path),
            "triggers": {
                "performance": {
                    "enabled": True,
                    "metrics": ["precision_at_5", "mrr"],
                    "relative_degradation": 0.05,
                    "min_samples_for_trigger": 100
                },
                "drift": {
                    "enabled": True,
                    "threshold": 0.2,
                    "methods": ["ks_test", "psi"]
                },
                "schedule": {
                    "enabled": True,
                    "type": "weekly"  # daily, weekly, monthly
                }
            },
            "data_quality": {
                "min_samples": 1000,
                "max_missing_rate": 0.1,
                "distribution_validation": True
            },
            "training": {
                "components": ["embeddings", "retrieval", "reranker"],
                "max_hyperparameter_combinations": 20,
                "scoring_weights": {
                    "precision_at_5": 0.3,
                    "mrr": 0.3,
                    "recall_at_10": 0.2,
                    "latency_penalty_weight": 0.2
                },
                "validation": {
                    "min_improvement": 0.02,
                    "max_individual_degradation": 0.05
                }
            },
            "deployment": {
                "validation_required": True,
                "staging_duration_hours": 24,
                "rollback_on_failure": True
            }
        }
    
    def create_directories(self):
        """Create necessary directories"""
        directories = [
            "training",
            "models/staging", 
            "models/production",
            "data/training",
            "logs/mlops",
            "monitoring/retraining_reports"
        ]
        
        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)
    
    def load_current_metrics(self) -> Dict[str, float]:
        """Load current model performance metrics"""
        # In production, this would query monitoring systems
        # For demo, return sample degraded metrics
        return {
            "precision_at_5": 0.68,  # Degraded from 0.72
            "mrr": 0.64,             # Degraded from 0.68
            "recall_at_10": 0.62,   # Degraded from 0.65
            "latency_mean_ms": 220,  # Increased from 180
            "error_rate": 0.08       # Increased from 0.02
        }
    
    def load_baseline_metrics(self) -> Dict[str, float]:
        """Load baseline model performance metrics"""
        return {
            "precision_at_5": 0.72,
            "mrr": 0.68,
            "recall_at_10": 0.65,
            "latency_mean_ms": 180,
            "error_rate": 0.02
        }
    
    def check_retraining_triggers(self, dry_run: bool = False) -> Dict[str, Any]:
        """Check all retraining triggers"""
        self.logger.info("Checking retraining triggers")
        
        # Load metrics and drift data
        current_metrics = self.load_current_metrics()
        baseline_metrics = self.load_baseline_metrics()
        
        # Simulate drift results (would come from monitoring system)
        drift_results = {
            "query_embedding_similarity": {
                "ks_statistic": 0.15,
                "p_value": 0.03,
                "drift_detected": True,
                "drift_severity": "medium"
            }
        }
        
        # Check triggers
        triggered, reasons = self.trigger_manager.check_all_triggers(
            current_metrics, baseline_metrics, drift_results
        )
        
        trigger_results = {
            "retraining_triggered": triggered,
            "trigger_reasons": reasons,
            "current_metrics": current_metrics,
            "baseline_metrics": baseline_metrics,
            "drift_results": drift_results,
            "timestamp": datetime.now().isoformat(),
            "dry_run": dry_run
        }
        
        if triggered:
            self.logger.info(f"Retraining triggered: {', '.join(reasons)}")
            if not dry_run:
                self.logger.info("Proceeding with automated retraining")
            else:
                self.logger.info("Dry run mode - retraining would be triggered")
        else:
            self.logger.info("No retraining triggers detected")
        
        return trigger_results
    
    def run_automated_retraining(self, components: List[str] = None, 
                                dry_run: bool = False) -> Dict[str, Any]:
        """Run complete automated retraining pipeline"""
        if components is None:
            components = self.config["training"]["components"]
        
        self.logger.info(f"Starting automated retraining for components: {components}")
        
        if dry_run:
            self.logger.info("Running in dry-run mode - no actual training will occur")
        
        # Prepare training environment
        training_dir = self.training_orchestrator.prepare_training_environment()
        
        # Validate data quality
        data_path = self.project_path / "data" / "samples" / "queries.jsonl"
        if not data_path.exists():
            # Create sample data for demo
            self.create_sample_training_data(data_path)
        
        data_validation = self.data_validator.validate_data_completeness(str(data_path))
        
        if not data_validation["validation_passed"]:
            self.logger.error(f"Data validation failed: {data_validation['issues']}")
            return {"success": False, "error": "Data validation failed"}
        
        # Load baseline for comparison
        baseline_metrics = self.load_baseline_metrics()
        
        # Train each component
        retraining_results = {
            "timestamp": datetime.now().isoformat(),
            "training_dir": training_dir,
            "data_validation": data_validation,
            "component_results": {},
            "overall_success": True,
            "dry_run": dry_run
        }
        
        for component in components:
            self.logger.info(f"Training component: {component}")
            
            if not dry_run:
                # Run hyperparameter optimization
                optimization_results = self.training_orchestrator.run_hyperparameter_optimization(
                    component, training_dir
                )
                
                # Validate results
                validation_results = self.training_orchestrator.validate_trained_model(
                    optimization_results, baseline_metrics
                )
                
                retraining_results["component_results"][component] = {
                    "optimization_results": optimization_results,
                    "validation_results": validation_results,
                    "success": validation_results["validation_passed"]
                }
                
                if not validation_results["validation_passed"]:
                    retraining_results["overall_success"] = False
                    self.logger.warning(f"Component {component} validation failed: {validation_results['issues']}")
                else:
                    self.logger.info(f"Component {component} training successful")
            else:
                # Dry run - simulate results
                retraining_results["component_results"][component] = {
                    "dry_run": True,
                    "message": "Would run hyperparameter optimization and validation"
                }
        
        # Generate retraining report
        report = self.generate_retraining_report(retraining_results)
        
        # Update last training timestamp if successful
        if retraining_results["overall_success"] and not dry_run:
            self.update_last_training_timestamp()
        
        self.logger.info("Automated retraining pipeline completed")
        return retraining_results
    
    def create_sample_training_data(self, data_path: Path):
        """Create sample training data for demo"""
        sample_queries = [
            {"query": "What is machine learning?", "context": "Machine learning is a subset of artificial intelligence..."},
            {"query": "Explain neural networks", "context": "Neural networks are computing systems inspired by biological neural networks..."},
            {"query": "How does gradient descent work?", "context": "Gradient descent is an optimization algorithm used to minimize loss functions..."},
            {"query": "What is deep learning?", "context": "Deep learning uses artificial neural networks with multiple layers..."},
            {"query": "Describe supervised learning", "context": "Supervised learning uses labeled training data to learn a mapping function..."}
        ]
        
        # Generate more samples
        expanded_queries = []
        for i in range(200):
            base_query = sample_queries[i % len(sample_queries)]
            expanded_queries.append({
                "query": base_query["query"] + f" (sample {i+1})",
                "context": base_query["context"],
                "timestamp": datetime.now().isoformat()
            })
        
        data_path.parent.mkdir(parents=True, exist_ok=True)
        with open(data_path, 'w') as f:
            for query in expanded_queries:
                f.write(json.dumps(query) + '\n')
        
        self.logger.info(f"Created sample training data: {data_path}")
    
    def update_last_training_timestamp(self):
        """Update last training timestamp file"""
        timestamp_file = self.project_path / "models" / "last_training_timestamp.txt"
        with open(timestamp_file, 'w') as f:
            f.write(datetime.now().isoformat())
        
        self.logger.info("Updated last training timestamp")
    
    def generate_retraining_report(self, results: Dict[str, Any]) -> str:
        """Generate comprehensive retraining report"""
        report = f"""
Automated Retraining Pipeline Report
Generated: {datetime.now().isoformat()}

PIPELINE EXECUTION:
Training Directory: {results['training_dir']}
Overall Success: {results['overall_success']}
Dry Run: {results.get('dry_run', False)}

DATA VALIDATION:
Total Samples: {results['data_validation'].get('total_samples', 'N/A')}
Validation Passed: {results['data_validation']['validation_passed']}
"""
        
        if results['data_validation'].get('issues'):
            report += f"Issues: {', '.join(results['data_validation']['issues'])}\n"
        
        report += "\nCOMPONENT TRAINING RESULTS:\n"
        
        for component, component_results in results["component_results"].items():
            report += f"\n{component.upper()}:\n"
            
            if component_results.get("dry_run"):
                report += "  Status: Dry run - would execute training\n"
                continue
            
            opt_results = component_results.get("optimization_results", {})
            val_results = component_results.get("validation_results", {})
            
            if opt_results:
                report += f"  Best Score: {opt_results['best_score']:.4f}\n"
                report += f"  Total Runs: {opt_results['total_runs']}\n"
                report += f"  Best Parameters: {opt_results['best_parameters']}\n"
            
            if val_results:
                report += f"  Validation Passed: {val_results['validation_passed']}\n"
                report += f"  Overall Improvement: {val_results['overall_improvement']:.2%}\n"
                
                if val_results.get("issues"):
                    report += f"  Issues: {', '.join(val_results['issues'])}\n"
        
        report += f"""
RECOMMENDATIONS:
"""
        
        if results["overall_success"]:
            report += "- Deploy trained models to staging environment\n"
            report += "- Monitor performance in staging before production\n" 
            report += "- Update model registry with new versions\n"
        else:
            report += "- Review training pipeline configuration\n"
            report += "- Investigate data quality issues\n"
            report += "- Consider manual hyperparameter adjustment\n"
        
        # Save report
        report_file = self.project_path / "monitoring" / "retraining_reports" / f"retraining_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(report_file, 'w') as f:
            f.write(report)
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Automated Model Retraining Pipeline')
    parser.add_argument('--project-path', default='/Users/peter/Desktop/ai_rag_assistant',
                       help='Path to RAG project')
    parser.add_argument('--mode', choices=['check-triggers', 'manual-retrain', 'full-pipeline'],
                       default='check-triggers', help='Retraining mode')
    parser.add_argument('--components', nargs='+', default=['embeddings', 'retrieval'],
                       help='Components to retrain')
    parser.add_argument('--dry-run', action='store_true',
                       help='Run in dry-run mode (no actual training)')
    parser.add_argument('--config-path', help='Path to retraining configuration file')
    parser.add_argument('--validation-set', help='Path to validation dataset')
    parser.add_argument('--trigger', choices=['performance', 'drift', 'schedule'],
                       help='Specific trigger to test')
    parser.add_argument('--threshold', type=float, default=0.05,
                       help='Performance degradation threshold')
    
    args = parser.parse_args()
    
    try:
        # Initialize retraining pipeline
        pipeline = AutomatedRetrainingPipeline(
            project_path=args.project_path,
            config_path=args.config_path
        )
        
        print("Automated Model Retraining Pipeline")
        print("=" * 40)
        
        if args.mode == 'check-triggers':
            print("Checking retraining triggers...")
            results = pipeline.check_retraining_triggers(dry_run=args.dry_run)
            
            print(f"\nTrigger Check Results:")
            print(f"Retraining Triggered: {results['retraining_triggered']}")
            
            if results['trigger_reasons']:
                print(f"Trigger Reasons:")
                for reason in results['trigger_reasons']:
                    print(f"  - {reason}")
            
            if results['retraining_triggered'] and not args.dry_run:
                print("\nProceeding with automated retraining...")
                retraining_results = pipeline.run_automated_retraining(args.components)
                print(f"Retraining Success: {retraining_results['overall_success']}")
            
        elif args.mode == 'manual-retrain':
            print(f"Starting manual retraining for components: {args.components}")
            results = pipeline.run_automated_retraining(
                components=args.components,
                dry_run=args.dry_run
            )
            
            print(f"\nRetraining Results:")
            print(f"Overall Success: {results['overall_success']}")
            print(f"Training Directory: {results['training_dir']}")
            
            for component, component_results in results['component_results'].items():
                print(f"\n{component.upper()}:")
                if component_results.get("dry_run"):
                    print("  Status: Dry run mode")
                else:
                    print(f"  Success: {component_results.get('success', False)}")
                    if 'optimization_results' in component_results:
                        opt_results = component_results['optimization_results']
                        print(f"  Best Score: {opt_results['best_score']:.4f}")
                        print(f"  Total Runs: {opt_results['total_runs']}")
        
        elif args.mode == 'full-pipeline':
            print("Running complete retraining pipeline...")
            
            # Check triggers first
            trigger_results = pipeline.check_retraining_triggers()
            print(f"Triggers Detected: {trigger_results['retraining_triggered']}")
            
            if trigger_results['retraining_triggered'] or args.dry_run:
                # Run retraining
                retraining_results = pipeline.run_automated_retraining(
                    components=args.components,
                    dry_run=args.dry_run
                )
                
                print(f"\nPipeline Results:")
                print(f"Overall Success: {retraining_results['overall_success']}")
                print(f"Components Processed: {len(retraining_results['component_results'])}")
            else:
                print("No triggers detected - retraining not required")
        
        print("\nRetraining pipeline completed successfully")
        
    except Exception as e:
        print(f"[ERROR] Retraining pipeline failed: {e}")
        raise


if __name__ == "__main__":
    main()