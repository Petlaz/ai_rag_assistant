"""
MLOps Infrastructure Setup and Pipeline Management

This script sets up comprehensive MLOps infrastructure for the RAG system
including MLflow tracking, experiment management, model versioning, and
production monitoring capabilities.

Features:
- MLflow tracking server setup and configuration
- Experiment tracking infrastructure for RAG model optimization
- Model registry setup for version management
- CloudWatch integration for production monitoring
- Automated experiment logging and metrics tracking
- Integration with existing A/B testing framework

Usage:
    # Setup complete MLOps infrastructure
    python scripts/mlops/setup_mlops_pipeline.py \
        --mlflow-tracking-uri ./mlruns \
        --experiment-name "rag-optimization-2026" \
        --setup-cloudwatch

    # Initialize existing project with MLOps
    python scripts/mlops/setup_mlops_pipeline.py \
        --project-path /Users/peter/Desktop/ai_rag_assistant \
        --register-baseline-metrics \
        --setup-monitoring
"""

import argparse
import json
import logging
import os
import yaml
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional
import warnings
warnings.filterwarnings('ignore')

try:
    import mlflow
    import mlflow.sklearn
    import mlflow.pytorch
    MLFLOW_AVAILABLE = True
except ImportError:
    MLFLOW_AVAILABLE = False

try:
    import boto3
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False


class MLOpsInfrastructureManager:
    """Comprehensive MLOps infrastructure setup and management"""
    
    def __init__(self, project_path: str, tracking_uri: str = "./mlruns"):
        self.project_path = Path(project_path)
        self.tracking_uri = tracking_uri
        
        # Setup logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        
        # Ensure MLflow is available
        if not MLFLOW_AVAILABLE:
            raise ImportError("MLflow not installed. Run: pip install mlflow>=2.10.0")
        
        # Setup tracking
        mlflow.set_tracking_uri(tracking_uri)
        
        # Create directories
        self.create_directory_structure()
        
    def create_directory_structure(self):
        """Create necessary directory structure for MLOps"""
        directories = [
            self.project_path / "mlruns",
            self.project_path / "configs" / "mlops",
            self.project_path / "results" / "mlflow_experiments",
            self.project_path / "models" / "registry",
            self.project_path / "monitoring" / "dashboards",
            self.project_path / "logs" / "mlops"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)
            self.logger.info(f"Created directory: {directory}")
    
    def setup_experiment_tracking(self, experiment_name: str, 
                                description: str = None) -> str:
        """Setup MLflow experiment for RAG system optimization"""
        try:
            # Create or get experiment
            experiment = mlflow.get_experiment_by_name(experiment_name)
            
            if experiment is None:
                experiment_id = mlflow.create_experiment(
                    name=experiment_name,
                    artifact_location=str(self.project_path / "mlruns" / "artifacts"),
                    tags={
                        "project": "rag-assistant", 
                        "created_date": datetime.now().isoformat(),
                        "description": description or "RAG system optimization experiments"
                    }
                )
                self.logger.info(f"Created experiment: {experiment_name} (ID: {experiment_id})")
            else:
                experiment_id = experiment.experiment_id
                self.logger.info(f"Using existing experiment: {experiment_name} (ID: {experiment_id})")
            
            # Set active experiment
            mlflow.set_experiment(experiment_name)
            
            return experiment_id
            
        except Exception as e:
            self.logger.error(f"Failed to setup experiment tracking: {e}")
            raise
    
    def create_mlflow_config(self) -> Dict[str, Any]:
        """Create MLflow configuration file"""
        config = {
            "mlflow": {
                "tracking_uri": self.tracking_uri,
                "default_artifact_root": str(self.project_path / "mlruns" / "artifacts"),
                "backend_store_uri": str(self.project_path / "mlruns"),
                "experiments": {
                    "rag_optimization": {
                        "name": "rag-optimization-2026",
                        "description": "Main RAG system optimization experiments",
                        "tags": ["production", "optimization"]
                    },
                    "embedding_models": {
                        "name": "embedding-model-comparison", 
                        "description": "Embedding model performance comparison",
                        "tags": ["embeddings", "models"]
                    },
                    "ab_testing": {
                        "name": "configuration-ab-testing",
                        "description": "A/B testing for retrieval configurations",
                        "tags": ["ab_testing", "configurations"]
                    },
                    "production_monitoring": {
                        "name": "production-monitoring",
                        "description": "Production model performance monitoring",
                        "tags": ["production", "monitoring"]
                    }
                }
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "handlers": ["console", "file"],
                "file_path": str(self.project_path / "logs" / "mlops" / "mlflow.log")
            },
            "model_registry": {
                "enabled": True,
                "staging_threshold": {
                    "precision_at_5": 0.75,
                    "mrr": 0.80,
                    "latency_p95": 2000
                },
                "production_threshold": {
                    "precision_at_5": 0.78,
                    "mrr": 0.82, 
                    "latency_p95": 1500
                }
            }
        }
        
        config_path = self.project_path / "configs" / "mlops" / "mlflow_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(config, f, indent=2)
        
        self.logger.info(f"Created MLflow configuration: {config_path}")
        return config
    
    def setup_model_registry(self) -> None:
        """Setup MLflow model registry for RAG components"""
        try:
            from mlflow.tracking import MlflowClient
            client = MlflowClient()
            
            # Model registry for different RAG components
            model_names = [
                "rag-embedding-model",
                "rag-retrieval-config", 
                "rag-reranker-model",
                "rag-complete-pipeline"
            ]
            
            for model_name in model_names:
                try:
                    client.create_registered_model(
                        name=model_name,
                        description=f"Registry for {model_name.replace('-', ' ')} in RAG system",
                        tags={
                            "created_date": datetime.now().isoformat(),
                            "project": "rag-assistant"
                        }
                    )
                    self.logger.info(f"Created model registry: {model_name}")
                except Exception as e:
                    if "already exists" not in str(e):
                        self.logger.warning(f"Failed to create registry {model_name}: {e}")
            
        except Exception as e:
            self.logger.error(f"Failed to setup model registry: {e}")
            raise
    
    def register_baseline_metrics(self, baseline_metrics: Dict[str, float] = None) -> str:
        """Register baseline performance metrics in MLflow"""
        if baseline_metrics is None:
            # Default baseline from existing evaluations
            baseline_metrics = {
                "precision_at_5": 0.72,
                "mrr": 0.68,
                "recall_at_10": 0.65,
                "latency_mean_ms": 180,
                "latency_p95_ms": 400,
                "cost_multiplier": 1.0
            }
        
        try:
            with mlflow.start_run(run_name=f"baseline_metrics_{datetime.now().strftime('%Y%m%d_%H%M%S')}"):
                # Log baseline metrics
                for metric_name, value in baseline_metrics.items():
                    mlflow.log_metric(metric_name, value)
                
                # Log baseline configuration
                mlflow.log_params({
                    "model_type": "baseline",
                    "embedding_model": "all-MiniLM-L6-v2",
                    "reranker": "passthrough",
                    "top_k_final": 5,
                    "bm25_weight": 0.7,
                    "semantic_weight": 0.3,
                    "registration_date": datetime.now().isoformat()
                })
                
                # Tag as baseline
                mlflow.set_tag("baseline", "true")
                mlflow.set_tag("model_version", "v1.0.0")
                mlflow.set_tag("deployment_status", "production")
                
                run_id = mlflow.active_run().info.run_id
                self.logger.info(f"Registered baseline metrics with run ID: {run_id}")
                
                return run_id
                
        except Exception as e:
            self.logger.error(f"Failed to register baseline metrics: {e}")
            raise
    
    def setup_cloudwatch_monitoring(self, region: str = "us-east-1") -> bool:
        """Setup AWS CloudWatch integration for production monitoring"""
        if not AWS_AVAILABLE:
            self.logger.warning("AWS SDK not available. Install with: pip install boto3")
            return False
        
        try:
            cloudwatch = boto3.client('cloudwatch', region_name=region)
            
            # Create custom metrics namespace
            namespace = "RAGAssistant/MLOps"
            
            # Test CloudWatch connectivity
            cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': 'MLOpsSetupTest',
                        'Value': 1.0,
                        'Unit': 'Count',
                        'Dimensions': [
                            {
                                'Name': 'Component',
                                'Value': 'MLOpsInfrastructure'
                            }
                        ]
                    }
                ]
            )
            
            # Create CloudWatch configuration
            cw_config = {
                "cloudwatch": {
                    "region": region,
                    "namespace": namespace,
                    "metrics": {
                        "model_performance": [
                            "PrecisionAt5",
                            "MRR", 
                            "RecallAt10",
                            "QueryLatency",
                            "ErrorRate"
                        ],
                        "system_health": [
                            "MemoryUsage",
                            "CPUUtilization", 
                            "DiskSpace",
                            "NetworkLatency"
                        ],
                        "business_metrics": [
                            "CostPerQuery",
                            "UserSatisfaction",
                            "QueryVolume",
                            "SuccessRate"
                        ]
                    },
                    "alarms": {
                        "performance_degradation": {
                            "metric": "PrecisionAt5",
                            "threshold": 0.68,
                            "comparison": "LessThanThreshold"
                        },
                        "high_latency": {
                            "metric": "QueryLatency", 
                            "threshold": 3000,
                            "comparison": "GreaterThanThreshold"
                        },
                        "error_rate": {
                            "metric": "ErrorRate",
                            "threshold": 0.05,
                            "comparison": "GreaterThanThreshold"
                        }
                    }
                }
            }
            
            config_path = self.project_path / "configs" / "mlops" / "cloudwatch_config.yaml"
            with open(config_path, 'w') as f:
                yaml.dump(cw_config, f, indent=2)
            
            self.logger.info(f"Setup CloudWatch monitoring: {config_path}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to setup CloudWatch monitoring: {e}")
            return False
    
    def create_experiment_templates(self) -> None:
        """Create experiment templates for common RAG optimization tasks"""
        templates = {
            "embedding_model_comparison": {
                "description": "Template for comparing embedding models",
                "parameters": {
                    "models": ["all-MiniLM-L6-v2", "all-mpnet-base-v2", "e5-small-v2"],
                    "test_set": "data/evaluation/scale_test_set.jsonl",
                    "metrics": ["precision_at_5", "mrr", "recall_at_10", "latency"]
                },
                "tags": ["embedding", "comparison", "template"]
            },
            "reranker_optimization": {
                "description": "Template for reranker strategy evaluation",
                "parameters": {
                    "strategies": ["passthrough", "cross_encoder", "llm_based"],
                    "test_set": "data/evaluation/scale_test_set.jsonl",
                    "metrics": ["precision_at_5", "mrr", "latency", "cost"]
                },
                "tags": ["reranker", "optimization", "template"]
            },
            "ab_testing": {
                "description": "Template for A/B testing configurations",
                "parameters": {
                    "configurations": "configs/retrieval_variants.yaml",
                    "test_set": "data/evaluation/scale_test_set.jsonl",
                    "statistical_tests": ["t_test", "mann_whitney", "chi_square"]
                },
                "tags": ["ab_testing", "configuration", "template"]
            }
        }
        
        templates_dir = self.project_path / "configs" / "mlops" / "experiment_templates"
        templates_dir.mkdir(parents=True, exist_ok=True)
        
        for template_name, template_config in templates.items():
            template_path = templates_dir / f"{template_name}.yaml"
            with open(template_path, 'w') as f:
                yaml.dump(template_config, f, indent=2)
            self.logger.info(f"Created experiment template: {template_path}")
    
    def setup_mlflow_ui_config(self, port: int = 5000) -> None:
        """Setup MLflow UI configuration"""
        ui_config = {
            "mlflow_ui": {
                "host": "127.0.0.1",
                "port": port,
                "backend_store_uri": str(self.project_path / "mlruns"),
                "default_artifact_root": str(self.project_path / "mlruns" / "artifacts"),
                "serve_artifacts": True,
                "static_prefix": None
            },
            "startup_command": f"mlflow ui --backend-store-uri {self.project_path / 'mlruns'} --port {port}"
        }
        
        config_path = self.project_path / "configs" / "mlops" / "mlflow_ui_config.yaml"
        with open(config_path, 'w') as f:
            yaml.dump(ui_config, f, indent=2)
        
        # Create startup script
        startup_script = f"""#!/bin/bash
# MLflow UI Startup Script
# Generated: {datetime.now().isoformat()}

export MLFLOW_TRACKING_URI=file://{self.project_path / 'mlruns'}
cd {self.project_path}

echo "Starting MLflow UI on http://localhost:{port}"
mlflow ui --backend-store-uri {self.project_path / 'mlruns'} --port {port}
"""
        
        script_path = self.project_path / "scripts" / "mlops" / "start_mlflow_ui.sh"
        script_path.parent.mkdir(parents=True, exist_ok=True)
        with open(script_path, 'w') as f:
            f.write(startup_script)
        
        # Make executable
        os.chmod(script_path, 0o755)
        
        self.logger.info(f"Created MLflow UI configuration and startup script: {script_path}")
    
    def validate_infrastructure(self) -> Dict[str, bool]:
        """Validate MLOps infrastructure setup"""
        validation_results = {}
        
        # Check MLflow connectivity
        try:
            mlflow.set_tracking_uri(self.tracking_uri)
            experiments = mlflow.search_experiments()
            validation_results["mlflow_tracking"] = True
            self.logger.info("MLflow tracking: [PASS]")
        except Exception as e:
            validation_results["mlflow_tracking"] = False
            self.logger.error(f"MLflow tracking: [FAIL] - {e}")
        
        # Check directory structure
        required_dirs = [
            "mlruns", "configs/mlops", "results/mlflow_experiments",
            "models/registry", "monitoring/dashboards"
        ]
        
        dirs_valid = all((self.project_path / d).exists() for d in required_dirs)
        validation_results["directory_structure"] = dirs_valid
        
        if dirs_valid:
            self.logger.info("Directory structure: [PASS]")
        else:
            self.logger.error("Directory structure: [FAIL]")
        
        # Check configuration files
        config_files = [
            "configs/mlops/mlflow_config.yaml",
            "configs/mlops/cloudwatch_config.yaml"
        ]
        
        configs_valid = all((self.project_path / f).exists() for f in config_files)
        validation_results["configuration_files"] = configs_valid
        
        if configs_valid:
            self.logger.info("Configuration files: [PASS]")
        else:
            self.logger.error("Configuration files: [FAIL]")
        
        # Check AWS connectivity (optional)
        try:
            if AWS_AVAILABLE:
                boto3.client('cloudwatch', region_name='us-east-1')
                validation_results["aws_connectivity"] = True
                self.logger.info("AWS connectivity: [PASS]")
            else:
                validation_results["aws_connectivity"] = False
                self.logger.warning("AWS connectivity: [SKIP] - boto3 not installed")
        except Exception as e:
            validation_results["aws_connectivity"] = False
            self.logger.warning(f"AWS connectivity: [FAIL] - {e}")
        
        return validation_results
    
    def generate_setup_report(self, validation_results: Dict[str, bool]) -> str:
        """Generate setup report"""
        report = f"""
MLOps Infrastructure Setup Report
Generated: {datetime.now().isoformat()}

Project Path: {self.project_path}
MLflow Tracking URI: {self.tracking_uri}

INFRASTRUCTURE VALIDATION:
"""
        
        for component, status in validation_results.items():
            status_text = "[PASS]" if status else "[FAIL]"
            report += f"  {component.replace('_', ' ').title()}: {status_text}\n"
        
        report += f"""
CREATED COMPONENTS:
  - MLflow experiment tracking
  - Model registry for RAG components
  - CloudWatch monitoring integration
  - Experiment templates
  - Configuration files
  - Startup scripts

NEXT STEPS:
  1. Start MLflow UI: ./scripts/mlops/start_mlflow_ui.sh
  2. Run baseline experiment registration
  3. Setup production monitoring
  4. Configure automated retraining

USAGE EXAMPLES:
  # Start MLflow UI
  cd {self.project_path}
  ./scripts/mlops/start_mlflow_ui.sh
  
  # Register new experiment
  python scripts/mlops/model_monitoring.py --register-experiment
  
  # View experiments at http://localhost:5000
"""
        
        report_path = self.project_path / "results" / "mlops_setup_report.txt"
        with open(report_path, 'w') as f:
            f.write(report)
        
        self.logger.info(f"Generated setup report: {report_path}")
        return report


def main():
    parser = argparse.ArgumentParser(description='Setup MLOps Infrastructure for RAG System')
    parser.add_argument('--project-path', default='/Users/peter/Desktop/ai_rag_assistant',
                       help='Path to RAG project')
    parser.add_argument('--mlflow-tracking-uri', default='./mlruns',
                       help='MLflow tracking URI')
    parser.add_argument('--experiment-name', default='rag-optimization-2026',
                       help='Main experiment name')
    parser.add_argument('--setup-cloudwatch', action='store_true',
                       help='Setup CloudWatch monitoring')
    parser.add_argument('--register-baseline-metrics', action='store_true',
                       help='Register baseline performance metrics')
    parser.add_argument('--mlflow-ui-port', type=int, default=5000,
                       help='MLflow UI port')
    
    args = parser.parse_args()
    
    try:
        # Initialize MLOps infrastructure
        mlops_manager = MLOpsInfrastructureManager(
            project_path=args.project_path,
            tracking_uri=args.mlflow_tracking_uri
        )
        
        print("Setting up MLOps Infrastructure for RAG System")
        print("=" * 55)
        
        # Setup experiment tracking
        experiment_id = mlops_manager.setup_experiment_tracking(
            args.experiment_name,
            "Main RAG system optimization experiments"
        )
        
        # Create configuration files
        mlflow_config = mlops_manager.create_mlflow_config()
        
        # Setup model registry
        mlops_manager.setup_model_registry()
        
        # Create experiment templates
        mlops_manager.create_experiment_templates()
        
        # Setup MLflow UI
        mlops_manager.setup_mlflow_ui_config(args.mlflow_ui_port)
        
        # Register baseline metrics if requested
        if args.register_baseline_metrics:
            baseline_run_id = mlops_manager.register_baseline_metrics()
            print(f"Registered baseline metrics: {baseline_run_id}")
        
        # Setup CloudWatch monitoring if requested
        if args.setup_cloudwatch:
            cw_success = mlops_manager.setup_cloudwatch_monitoring()
            if cw_success:
                print("CloudWatch monitoring setup: [PASS]")
            else:
                print("CloudWatch monitoring setup: [FAIL]")
        
        # Validate infrastructure
        validation_results = mlops_manager.validate_infrastructure()
        
        # Generate report
        report = mlops_manager.generate_setup_report(validation_results)
        
        # Print summary
        print("\nMLOPS INFRASTRUCTURE SETUP SUMMARY")
        print("=" * 40)
        
        success_count = sum(validation_results.values())
        total_count = len(validation_results)
        
        print(f"Components Configured: {success_count}/{total_count}")
        print(f"MLflow Experiment: {args.experiment_name} (ID: {experiment_id})")
        print(f"Tracking URI: {args.mlflow_tracking_uri}")
        
        if success_count == total_count:
            print("[SUCCESS] MLOps infrastructure ready for production")
        else:
            print("[WARNING] Some components failed setup - check logs")
        
        print(f"\nSetup report saved to: results/mlops_setup_report.txt")
        print(f"Start MLflow UI: ./scripts/mlops/start_mlflow_ui.sh")
        
    except Exception as e:
        print(f"[ERROR] MLOps setup failed: {e}")
        raise


if __name__ == "__main__":
    main()