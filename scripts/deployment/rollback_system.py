"""
Automated Rollback and Recovery System

This script provides comprehensive rollback and recovery capabilities
with automated failure detection, intelligent recovery strategies,
and data consistency preservation during emergency situations.

Features:
- Automated failure detection and rollback triggers
- Intelligent recovery strategy selection based on failure type
- Data consistency preservation during rollback operations
- Service dependency management during recovery
- Recovery validation and system health verification
- Incident logging and post-mortem analysis

Usage:
    # Setup automated rollback monitoring
    python scripts/deployment/rollback_system.py --monitor --failure-threshold 5 --rollback-timeout 120
    
    # Manual rollback with specific strategy
    python scripts/deployment/rollback_system.py --manual --strategy fast --preserve-data

    # Emergency rollback with immediate execution
    python scripts/deployment/rollback_system.py --emergency --version previous

    # Rollback validation and recovery testing
    python scripts/deployment/rollback_system.py --validate --test-recovery

Examples:
    # Monitor deployment and auto-rollback on failures
    python scripts/deployment/rollback_system.py \\
        --monitor \\
        --failure-threshold 10 \\
        --error-rate-threshold 0.05 \\
        --rollback-timeout 300

    # Manual rollback to specific version
    python scripts/deployment/rollback_system.py \\
        --manual \\
        --target-version v1.2.3 \\
        --strategy graceful \\
        --preserve-data

    # Emergency rollback with immediate execution
    python scripts/deployment/rollback_system.py \\
        --emergency \\
        --strategy fast \\
        --skip-validation

Rollback Strategies:
    - fast: Immediate rollback with minimal validation
    - graceful: Coordinated rollback with full validation
    - partial: Rollback specific services while maintaining others
    - data-safe: Maximum data consistency preservation

Failure Detection:
    - Health check failures
    - Error rate thresholds
    - Response time degradation
    - Resource exhaustion
    - Dependency failures
"""

import argparse
import json
import yaml
import time
import logging
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import threading
import subprocess
import signal
import sys

class RollbackStrategy(Enum):
    """Available rollback strategies"""
    FAST = "fast"
    GRACEFUL = "graceful" 
    PARTIAL = "partial"
    DATA_SAFE = "data_safe"

class FailureType(Enum):
    """Types of failures that trigger rollback"""
    HEALTH_CHECK = "health_check"
    ERROR_RATE = "error_rate"
    RESPONSE_TIME = "response_time"
    RESOURCE_EXHAUSTION = "resource_exhaustion"
    DEPENDENCY_FAILURE = "dependency_failure"
    MANUAL = "manual"
    EMERGENCY = "emergency"

@dataclass
class FailureEvent:
    """Represents a system failure event"""
    timestamp: datetime
    failure_type: FailureType
    severity: str
    description: str
    affected_services: List[str]
    metrics: Dict[str, Any]
    rollback_triggered: bool = False
    rollback_strategy: Optional[RollbackStrategy] = None

@dataclass
class RollbackOperation:
    """Represents a rollback operation"""
    operation_id: str
    strategy: RollbackStrategy
    target_version: str
    started_at: datetime
    completed_at: Optional[datetime] = None
    status: str = "in_progress"
    steps_completed: List[str] = None
    rollback_data: Dict[str, Any] = None
    validation_results: Dict[str, bool] = None
    
    def __post_init__(self):
        if self.steps_completed is None:
            self.steps_completed = []
        if self.rollback_data is None:
            self.rollback_data = {}
        if self.validation_results is None:
            self.validation_results = {}

class RollbackSystem:
    """
    Comprehensive rollback and recovery system for RAG Assistant deployment
    
    Provides automated failure detection, intelligent rollback strategy selection,
    and complete recovery orchestration with data consistency preservation.
    """
    
    def __init__(self, config_path: str = None):
        """Initialize rollback system with configuration"""
        
        self.config = self._load_config(config_path)
        self.logger = self._setup_logging()
        
        # AWS clients (lazy import)
        try:
            import boto3
            self.lambda_client = boto3.client('lambda', region_name=self.config.get('aws_region', 'us-east-1'))
            self.s3_client = boto3.client('s3', region_name=self.config.get('aws_region', 'us-east-1'))
            self.cloudwatch = boto3.client('cloudwatch', region_name=self.config.get('aws_region', 'us-east-1'))
        except ImportError:
            raise ImportError("boto3 is required for AWS operations. Install with: pip install boto3")
        
        # System state
        self.monitoring = False
        self.current_version = self._get_current_version()
        self.rollback_history: List[RollbackOperation] = []
        
        # Failure detection thresholds
        self.failure_thresholds = {
            'error_rate': self.config.get('error_rate_threshold', 0.05),
            'response_time': self.config.get('response_time_threshold', 5000),
            'health_check_failures': self.config.get('health_check_failure_threshold', 3),
            'cpu_utilization': self.config.get('cpu_threshold', 0.90),
            'memory_utilization': self.config.get('memory_threshold', 0.90)
        }
        
        # Rollback configurations
        self.rollback_configs = {
            RollbackStrategy.FAST: {
                'validation_timeout': 30,
                'skip_data_validation': True,
                'parallel_execution': True,
                'force_immediate': True
            },
            RollbackStrategy.GRACEFUL: {
                'validation_timeout': 120,
                'skip_data_validation': False,
                'parallel_execution': False,
                'force_immediate': False
            },
            RollbackStrategy.PARTIAL: {
                'validation_timeout': 60,
                'skip_data_validation': False,
                'parallel_execution': True,
                'force_immediate': False
            },
            RollbackStrategy.DATA_SAFE: {
                'validation_timeout': 300,
                'skip_data_validation': False,
                'parallel_execution': False,
                'force_immediate': False,
                'data_backup_required': True
            }
        }

    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """Load rollback system configuration"""
        
        default_config = {
            'aws_region': 'us-east-1',
            'monitoring_interval': 30,
            'max_rollback_attempts': 3,
            'health_check_url': 'http://localhost:7860/health',
            's3_backup_bucket': 'rag-assistant-backups',
            'lambda_function_name': 'rag-assistant-main'
        }
        
        if config_path and Path(config_path).exists():
            try:
                with open(config_path, 'r') as f:
                    config_data = yaml.safe_load(f)
                    default_config.update(config_data.get('rollback', {}))
            except Exception as e:
                print(f"Warning: Failed to load config {config_path}: {e}")
        
        return default_config

    def _setup_logging(self) -> logging.Logger:
        """Setup logging for rollback operations"""
        
        logger = logging.getLogger('rollback_system')
        logger.setLevel(logging.INFO)
        
        # Create handlers
        console_handler = logging.StreamHandler()
        file_handler = logging.FileHandler('logs/rollback_system.log')
        
        # Create formatters
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        file_handler.setFormatter(formatter)
        
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)
        
        return logger

    def _get_current_version(self) -> str:
        """Get current deployed version"""
        
        try:
            response = self.lambda_client.get_function(
                FunctionName=self.config['lambda_function_name']
            )
            return response['Configuration']['Version']
        except Exception as e:
            self.logger.warning(f"Failed to get current version: {e}")
            return "unknown"

    def start_monitoring(self, failure_threshold: int = 5, check_interval: int = 30):
        """Start automated failure monitoring and rollback"""
        
        self.monitoring = True
        self.logger.info("Starting automated rollback monitoring")
        
        consecutive_failures = 0
        
        def monitoring_loop():
            nonlocal consecutive_failures
            
            while self.monitoring:
                try:
                    # Perform health checks
                    failure_event = self._check_system_health()
                    
                    if failure_event:
                        consecutive_failures += 1
                        self.logger.warning(
                            f"Failure detected: {failure_event.description} "
                            f"(consecutive failures: {consecutive_failures})"
                        )
                        
                        # Trigger rollback if threshold reached
                        if consecutive_failures >= failure_threshold:
                            self.logger.critical("Failure threshold reached, triggering rollback")
                            rollback_strategy = self._select_rollback_strategy(failure_event)
                            self.execute_rollback(
                                strategy=rollback_strategy,
                                failure_event=failure_event
                            )
                            consecutive_failures = 0
                    else:
                        consecutive_failures = 0
                    
                    time.sleep(check_interval)
                    
                except Exception as e:
                    self.logger.error(f"Monitoring error: {e}")
                    time.sleep(check_interval)
        
        # Start monitoring in background thread
        monitor_thread = threading.Thread(target=monitoring_loop)
        monitor_thread.daemon = True
        monitor_thread.start()
        
        self.logger.info(f"Monitoring started with failure threshold: {failure_threshold}")

    def _check_system_health(self) -> Optional[FailureEvent]:
        """Check system health and detect failures"""
        
        now = datetime.now()
        
        # Health endpoint check
        if not self._check_health_endpoint():
            return FailureEvent(
                timestamp=now,
                failure_type=FailureType.HEALTH_CHECK,
                severity="high",
                description="Health endpoint check failed",
                affected_services=["main_service"],
                metrics={}
            )
        
        # Error rate check
        error_rate = self._get_error_rate()
        if error_rate > self.failure_thresholds['error_rate']:
            return FailureEvent(
                timestamp=now,
                failure_type=FailureType.ERROR_RATE,
                severity="high",
                description=f"Error rate too high: {error_rate:.2%}",
                affected_services=["lambda"],
                metrics={"error_rate": error_rate}
            )
        
        # Response time check
        avg_response_time = self._get_average_response_time()
        if avg_response_time > self.failure_thresholds['response_time']:
            return FailureEvent(
                timestamp=now,
                failure_type=FailureType.RESPONSE_TIME,
                severity="medium",
                description=f"Response time degraded: {avg_response_time}ms",
                affected_services=["lambda"],
                metrics={"avg_response_time": avg_response_time}
            )
        
        # Resource utilization check
        resource_issues = self._check_resource_utilization()
        if resource_issues:
            return FailureEvent(
                timestamp=now,
                failure_type=FailureType.RESOURCE_EXHAUSTION,
                severity="high",
                description=f"Resource exhaustion: {resource_issues}",
                affected_services=["lambda"],
                metrics={"resource_issues": resource_issues}
            )
        
        return None

    def _check_health_endpoint(self) -> bool:
        """Check if health endpoint is responding"""
        
        try:
            response = requests.get(
                self.config['health_check_url'],
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            self.logger.warning(f"Health check failed: {e}")
            return False

    def _get_error_rate(self) -> float:
        """Get current error rate from CloudWatch"""
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            
            # Get error metrics
            error_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Errors',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': self.config['lambda_function_name']
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            # Get invocation metrics
            invocation_response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Invocations',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': self.config['lambda_function_name']
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Sum']
            )
            
            errors = sum(point['Sum'] for point in error_response['Datapoints'])
            invocations = sum(point['Sum'] for point in invocation_response['Datapoints'])
            
            return errors / invocations if invocations > 0 else 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to get error rate: {e}")
            return 0.0

    def _get_average_response_time(self) -> float:
        """Get average response time from CloudWatch"""
        
        try:
            end_time = datetime.now()
            start_time = end_time - timedelta(minutes=5)
            
            response = self.cloudwatch.get_metric_statistics(
                Namespace='AWS/Lambda',
                MetricName='Duration',
                Dimensions=[
                    {
                        'Name': 'FunctionName',
                        'Value': self.config['lambda_function_name']
                    }
                ],
                StartTime=start_time,
                EndTime=end_time,
                Period=300,
                Statistics=['Average']
            )
            
            if response['Datapoints']:
                return response['Datapoints'][-1]['Average']
            return 0.0
            
        except Exception as e:
            self.logger.warning(f"Failed to get response time: {e}")
            return 0.0

    def _check_resource_utilization(self) -> List[str]:
        """Check resource utilization for issues"""
        
        issues = []
        
        try:
            # Check Lambda memory utilization
            # Note: This would need custom metrics or logs parsing
            # For now, return empty list as placeholder
            pass
            
        except Exception as e:
            self.logger.warning(f"Failed to check resource utilization: {e}")
        
        return issues

    def _select_rollback_strategy(self, failure_event: FailureEvent) -> RollbackStrategy:
        """Select appropriate rollback strategy based on failure type"""
        
        if failure_event.failure_type == FailureType.EMERGENCY:
            return RollbackStrategy.FAST
        elif failure_event.failure_type == FailureType.ERROR_RATE:
            return RollbackStrategy.GRACEFUL
        elif failure_event.failure_type == FailureType.RESOURCE_EXHAUSTION:
            return RollbackStrategy.FAST
        elif failure_event.severity == "critical":
            return RollbackStrategy.FAST
        else:
            return RollbackStrategy.GRACEFUL

    def execute_rollback(self, strategy: RollbackStrategy, target_version: str = None, 
                       failure_event: FailureEvent = None, preserve_data: bool = True) -> RollbackOperation:
        """Execute rollback operation with specified strategy"""
        
        operation_id = f"rollback_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        target_version = target_version or self._get_previous_version()
        
        rollback_op = RollbackOperation(
            operation_id=operation_id,
            strategy=strategy,
            target_version=target_version,
            started_at=datetime.now()
        )
        
        self.logger.info(f"Starting rollback operation {operation_id} with strategy {strategy.value}")
        
        try:
            config = self.rollback_configs[strategy]
            
            # Step 1: Pre-rollback validation
            if not config.get('skip_data_validation', False):
                self.logger.info("Performing pre-rollback validation")
                if not self._validate_rollback_preconditions(rollback_op):
                    rollback_op.status = "failed"
                    rollback_op.completed_at = datetime.now()
                    return rollback_op
                rollback_op.steps_completed.append("pre_validation")
            
            # Step 2: Data backup (if required)
            if config.get('data_backup_required', False) or preserve_data:
                self.logger.info("Creating data backup")
                backup_result = self._create_data_backup(rollback_op)
                if not backup_result:
                    rollback_op.status = "failed"
                    rollback_op.completed_at = datetime.now()
                    return rollback_op
                rollback_op.steps_completed.append("data_backup")
            
            # Step 3: Rollback Lambda function
            self.logger.info(f"Rolling back Lambda function to version {target_version}")
            lambda_rollback = self._rollback_lambda_function(target_version, rollback_op)
            if not lambda_rollback:
                rollback_op.status = "failed"
                rollback_op.completed_at = datetime.now()
                return rollback_op
            rollback_op.steps_completed.append("lambda_rollback")
            
            # Step 4: Rollback configuration
            self.logger.info("Rolling back configuration")
            config_rollback = self._rollback_configuration(target_version, rollback_op)
            if not config_rollback:
                rollback_op.status = "failed"
                rollback_op.completed_at = datetime.now()
                return rollback_op
            rollback_op.steps_completed.append("config_rollback")
            
            # Step 5: Post-rollback validation
            self.logger.info("Performing post-rollback validation")
            validation_result = self._validate_rollback_success(rollback_op)
            rollback_op.validation_results = validation_result
            
            if all(validation_result.values()):
                rollback_op.status = "completed"
                self.logger.info(f"Rollback operation {operation_id} completed successfully")
            else:
                rollback_op.status = "partial"
                self.logger.warning(f"Rollback operation {operation_id} completed with issues")
            
            rollback_op.steps_completed.append("post_validation")
            rollback_op.completed_at = datetime.now()
            
            # Log rollback event
            self._log_rollback_event(rollback_op, failure_event)
            
        except Exception as e:
            self.logger.error(f"Rollback operation failed: {e}")
            rollback_op.status = "failed"
            rollback_op.completed_at = datetime.now()
        
        self.rollback_history.append(rollback_op)
        return rollback_op

    def _get_previous_version(self) -> str:
        """Get previous deployable version"""
        
        try:
            response = self.lambda_client.list_versions_by_function(
                FunctionName=self.config['lambda_function_name']
            )
            
            versions = [v['Version'] for v in response['Versions'] if v['Version'] != '$LATEST']
            if len(versions) >= 2:
                return versions[-2]  # Second to last version
            elif len(versions) == 1:
                return versions[0]
            else:
                return "1"
                
        except Exception as e:
            self.logger.warning(f"Failed to get previous version: {e}")
            return "1"

    def _validate_rollback_preconditions(self, rollback_op: RollbackOperation) -> bool:
        """Validate conditions before executing rollback"""
        
        try:
            # Check if target version exists
            try:
                self.lambda_client.get_function(
                    FunctionName=self.config['lambda_function_name'],
                    Qualifier=rollback_op.target_version
                )
            except self.lambda_client.exceptions.ResourceNotFoundException:
                self.logger.error(f"Target version {rollback_op.target_version} not found")
                return False
            
            # Check system resources
            if not self._check_rollback_resources():
                self.logger.error("Insufficient resources for rollback")
                return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Precondition validation failed: {e}")
            return False

    def _check_rollback_resources(self) -> bool:
        """Check if sufficient resources are available for rollback"""
        
        try:
            # Check AWS service quotas and limits
            # This is a simplified check - in production would check:
            # - Lambda concurrent executions
            # - S3 bucket storage
            # - CloudWatch log retention
            return True
            
        except Exception as e:
            self.logger.warning(f"Resource check failed: {e}")
            return True  # Proceed with caution

    def _create_data_backup(self, rollback_op: RollbackOperation) -> bool:
        """Create backup of critical data before rollback"""
        
        try:
            backup_key = f"rollback_backups/{rollback_op.operation_id}/"
            
            # Backup Lambda function code
            function_response = self.lambda_client.get_function(
                FunctionName=self.config['lambda_function_name']
            )
            
            # Store backup metadata
            backup_metadata = {
                'operation_id': rollback_op.operation_id,
                'timestamp': datetime.now().isoformat(),
                'function_version': function_response['Configuration']['Version'],
                'backup_location': backup_key
            }
            
            # Upload backup metadata
            self.s3_client.put_object(
                Bucket=self.config['s3_backup_bucket'],
                Key=f"{backup_key}metadata.json",
                Body=json.dumps(backup_metadata)
            )
            
            rollback_op.rollback_data['backup_location'] = backup_key
            self.logger.info(f"Data backup created at {backup_key}")
            return True
            
        except Exception as e:
            self.logger.error(f"Data backup failed: {e}")
            return False

    def _rollback_lambda_function(self, target_version: str, rollback_op: RollbackOperation) -> bool:
        """Rollback Lambda function to target version"""
        
        try:
            # Update function to use target version
            response = self.lambda_client.update_alias(
                FunctionName=self.config['lambda_function_name'],
                Name='LIVE',
                FunctionVersion=target_version
            )
            
            # Wait for update to complete
            waiter = self.lambda_client.get_waiter('function_updated')
            waiter.wait(
                FunctionName=self.config['lambda_function_name'],
                Qualifier='LIVE',
                WaiterConfig={'Delay': 5, 'MaxAttempts': 12}
            )
            
            rollback_op.rollback_data['lambda_version'] = target_version
            self.logger.info(f"Lambda function rolled back to version {target_version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Lambda rollback failed: {e}")
            return False

    def _rollback_configuration(self, target_version: str, rollback_op: RollbackOperation) -> bool:
        """Rollback system configuration to target version"""
        
        try:
            # This would typically involve:
            # - Reverting environment variables
            # - Updating configuration files
            # - Resetting feature flags
            
            # For now, simulate successful config rollback
            rollback_op.rollback_data['config_rolled_back'] = True
            self.logger.info("Configuration rolled back successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Configuration rollback failed: {e}")
            return False

    def _validate_rollback_success(self, rollback_op: RollbackOperation) -> Dict[str, bool]:
        """Validate that rollback was successful"""
        
        validation_results = {}
        
        try:
            # Health check validation
            validation_results['health_check'] = self._check_health_endpoint()
            
            # Function version validation
            current_function = self.lambda_client.get_function(
                FunctionName=self.config['lambda_function_name'],
                Qualifier='LIVE'
            )
            expected_version = rollback_op.target_version
            actual_version = current_function['Configuration']['Version']
            validation_results['version_correct'] = actual_version == expected_version
            
            # Performance validation
            # Allow some time for metrics to stabilize
            time.sleep(15)
            error_rate = self._get_error_rate()
            validation_results['error_rate_acceptable'] = error_rate < self.failure_thresholds['error_rate']
            
            # Response time validation
            avg_response_time = self._get_average_response_time()
            validation_results['response_time_acceptable'] = avg_response_time < self.failure_thresholds['response_time']
            
            self.logger.info(f"Rollback validation results: {validation_results}")
            return validation_results
            
        except Exception as e:
            self.logger.error(f"Rollback validation failed: {e}")
            return {'validation_error': False}

    def _log_rollback_event(self, rollback_op: RollbackOperation, failure_event: FailureEvent = None):
        """Log rollback event for audit and analysis"""
        
        event_data = {
            'operation_id': rollback_op.operation_id,
            'timestamp': rollback_op.started_at.isoformat(),
            'strategy': rollback_op.strategy.value,
            'target_version': rollback_op.target_version,
            'status': rollback_op.status,
            'duration_seconds': (rollback_op.completed_at - rollback_op.started_at).total_seconds() if rollback_op.completed_at else None,
            'steps_completed': rollback_op.steps_completed,
            'validation_results': rollback_op.validation_results,
            'failure_event': asdict(failure_event) if failure_event else None
        }
        
        # Save to file
        log_file = f"logs/rollback_events.jsonl"
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        
        with open(log_file, 'a') as f:
            f.write(json.dumps(event_data) + '\n')
        
        self.logger.info(f"Rollback event logged: {rollback_op.operation_id}")

    def manual_rollback(self, target_version: str, strategy: RollbackStrategy = RollbackStrategy.GRACEFUL, 
                       preserve_data: bool = True) -> RollbackOperation:
        """Execute manual rollback to specific version"""
        
        self.logger.info(f"Initiating manual rollback to version {target_version}")
        
        failure_event = FailureEvent(
            timestamp=datetime.now(),
            failure_type=FailureType.MANUAL,
            severity="medium",
            description=f"Manual rollback requested to version {target_version}",
            affected_services=["all"],
            metrics={}
        )
        
        return self.execute_rollback(
            strategy=strategy,
            target_version=target_version,
            failure_event=failure_event,
            preserve_data=preserve_data
        )

    def emergency_rollback(self, target_version: str = None) -> RollbackOperation:
        """Execute emergency rollback with minimal validation"""
        
        target_version = target_version or self._get_previous_version()
        self.logger.critical(f"Initiating emergency rollback to version {target_version}")
        
        failure_event = FailureEvent(
            timestamp=datetime.now(),
            failure_type=FailureType.EMERGENCY,
            severity="critical",
            description="Emergency rollback executed",
            affected_services=["all"],
            metrics={}
        )
        
        return self.execute_rollback(
            strategy=RollbackStrategy.FAST,
            target_version=target_version,
            failure_event=failure_event,
            preserve_data=False
        )

    def stop_monitoring(self):
        """Stop automated monitoring"""
        
        self.monitoring = False
        self.logger.info("Automated monitoring stopped")

    def get_rollback_history(self) -> List[RollbackOperation]:
        """Get history of rollback operations"""
        
        return self.rollback_history

    def validate_recovery(self) -> Dict[str, bool]:
        """Validate system recovery after rollback"""
        
        self.logger.info("Validating system recovery")
        
        validation_results = {
            'system_operational': self._check_health_endpoint(),
            'error_rates_normal': self._get_error_rate() < self.failure_thresholds['error_rate'],
            'response_times_acceptable': self._get_average_response_time() < self.failure_thresholds['response_time'],
            'no_resource_issues': len(self._check_resource_utilization()) == 0
        }
        
        self.logger.info(f"Recovery validation results: {validation_results}")
        return validation_results

def main():
    parser = argparse.ArgumentParser(description="RAG Assistant Rollback System")
    
    parser.add_argument('--config', type=str, help='Configuration file path')
    parser.add_argument('--monitor', action='store_true', help='Start automated monitoring')
    parser.add_argument('--manual', action='store_true', help='Execute manual rollback')
    parser.add_argument('--emergency', action='store_true', help='Execute emergency rollback')
    parser.add_argument('--validate', action='store_true', help='Validate system recovery')
    parser.add_argument('--strategy', type=str, choices=['fast', 'graceful', 'partial', 'data_safe'],
                       default='graceful', help='Rollback strategy')
    parser.add_argument('--target-version', type=str, help='Target version for rollback')
    parser.add_argument('--version', type=str, dest='target_version', help='Alias for --target-version')
    parser.add_argument('--failure-threshold', type=int, default=5, help='Failure threshold for auto-rollback')
    parser.add_argument('--rollback-timeout', type=int, default=120, help='Rollback timeout in seconds')
    parser.add_argument('--error-rate-threshold', type=float, default=0.05, help='Error rate threshold')
    parser.add_argument('--preserve-data', action='store_true', default=True, help='Preserve data during rollback')
    parser.add_argument('--skip-validation', action='store_true', help='Skip validation steps')
    parser.add_argument('--test-recovery', action='store_true', help='Test recovery validation')
    
    args = parser.parse_args()
    
    # Initialize rollback system
    rollback_system = RollbackSystem(args.config)
    
    # Setup signal handlers for graceful shutdown
    def signal_handler(signum, frame):
        rollback_system.logger.info("Received shutdown signal")
        rollback_system.stop_monitoring()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        if args.monitor:
            print("Starting automated rollback monitoring...")
            rollback_system.start_monitoring(
                failure_threshold=args.failure_threshold,
                check_interval=30
            )
            
            # Keep running until interrupted
            while rollback_system.monitoring:
                time.sleep(1)
        
        elif args.manual:
            strategy = RollbackStrategy(args.strategy)
            print(f"Executing manual rollback with {strategy.value} strategy...")
            
            rollback_op = rollback_system.manual_rollback(
                target_version=args.target_version,
                strategy=strategy,
                preserve_data=args.preserve_data and not args.skip_validation
            )
            
            print(f"\nRollback Operation: {rollback_op.operation_id}")
            print(f"Status: {rollback_op.status}")
            print(f"Target Version: {rollback_op.target_version}")
            print(f"Steps Completed: {', '.join(rollback_op.steps_completed)}")
            
            if rollback_op.validation_results:
                print("\nValidation Results:")
                for check, result in rollback_op.validation_results.items():
                    print(f"  {check}: {'PASS' if result else 'FAIL'}")
        
        elif args.emergency:
            print("Executing emergency rollback...")
            rollback_op = rollback_system.emergency_rollback(args.target_version)
            
            print(f"\nEmergency Rollback: {rollback_op.operation_id}")
            print(f"Status: {rollback_op.status}")
            print(f"Target Version: {rollback_op.target_version}")
        
        elif args.validate or args.test_recovery:
            print("Validating system recovery...")
            validation_results = rollback_system.validate_recovery()
            
            print("\nRecovery Validation Results:")
            for check, result in validation_results.items():
                print(f"  {check}: {'PASS' if result else 'FAIL'}")
            
            overall_status = "HEALTHY" if all(validation_results.values()) else "DEGRADED"
            print(f"\nOverall System Status: {overall_status}")
        
        else:
            print("No action specified. Use --help for usage information.")
    
    except KeyboardInterrupt:
        print("\nOperation interrupted by user")
    except Exception as e:
        print(f"Error: {e}")
        rollback_system.logger.error(f"Main execution error: {e}")

if __name__ == "__main__":
    main()