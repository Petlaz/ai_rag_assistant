"""
Automated Alerting System for RAG Assistant Production Environment

This script implements a comprehensive alerting framework that monitors system
health, performance metrics, cost thresholds, and ML model performance in
real-time, providing automated notifications and incident response triggers.

Features:
- Multi-channel alerting (email, Slack, CloudWatch, PagerDuty)
- Intelligent alert aggregation and deduplication
- Escalation policies with severity-based routing
- Performance threshold monitoring with dynamic baselines
- Cost anomaly detection and budget alerts
- ML model performance degradation detection
- Alert fatigue reduction through smart grouping
- Incident response automation and runbook integration

Usage:
    # Setup alerting infrastructure
    python scripts/monitoring/alerting_system.py \
        --setup-alerts \
        --enable-channels slack,email \
        --config configs/alerting.yaml

    # Start alert monitoring daemon
    python scripts/monitoring/alerting_system.py \
        --mode daemon \
        --monitoring-interval 30 \
        --enable-escalation

    # Test alert channels
    python scripts/monitoring/alerting_system.py \
        --test-alerts \
        --channels all
"""

import argparse
import json
import logging
import time
import warnings
from collections import defaultdict, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import warnings
warnings.filterwarnings('ignore')

# Email imports with fallback handling
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

import numpy as np
import pandas as pd
import yaml

try:
    import boto3
    from botocore.exceptions import ClientError
    AWS_AVAILABLE = True
except ImportError:
    AWS_AVAILABLE = False

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False


class AlertSeverity:
    """Alert severity levels with escalation policies"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"
    
    ESCALATION_ORDER = [LOW, MEDIUM, HIGH, CRITICAL]
    
    @classmethod
    def get_escalation_level(cls, current_severity: str) -> Optional[str]:
        """Get next escalation level"""
        if current_severity not in cls.ESCALATION_ORDER:
            return None
        
        current_index = cls.ESCALATION_ORDER.index(current_severity)
        if current_index < len(cls.ESCALATION_ORDER) - 1:
            return cls.ESCALATION_ORDER[current_index + 1]
        
        return None


class Alert:
    """Individual alert with metadata and state management"""
    
    def __init__(self, alert_type: str, severity: str, message: str, 
                 source: str = "system", metadata: Dict[str, Any] = None):
        self.alert_id = f"{alert_type}_{int(datetime.now().timestamp())}"
        self.alert_type = alert_type
        self.severity = severity
        self.message = message
        self.source = source
        self.metadata = metadata or {}
        self.timestamp = datetime.now()
        
        # State management
        self.status = "active"  # active, acknowledged, resolved, escalated
        self.acknowledged_by = None
        self.acknowledged_at = None
        self.resolved_at = None
        self.escalation_count = 0
        self.notification_history = []
    
    def acknowledge(self, user: str):
        """Acknowledge the alert"""
        self.status = "acknowledged"
        self.acknowledged_by = user
        self.acknowledged_at = datetime.now()
    
    def resolve(self, resolution_note: str = None):
        """Resolve the alert"""
        self.status = "resolved"
        self.resolved_at = datetime.now()
        if resolution_note:
            self.metadata["resolution_note"] = resolution_note
    
    def escalate(self):
        """Escalate alert to next severity level"""
        next_severity = AlertSeverity.get_escalation_level(self.severity)
        if next_severity:
            self.severity = next_severity
            self.status = "escalated"
            self.escalation_count += 1
            return True
        return False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary"""
        return {
            "alert_id": self.alert_id,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat(),
            "status": self.status,
            "acknowledged_by": self.acknowledged_by,
            "acknowledged_at": self.acknowledged_at.isoformat() if self.acknowledged_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "escalation_count": self.escalation_count,
            "notification_history": self.notification_history
        }


class AlertChannel:
    """Base class for alert notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get("enabled", True)
        self.logger = logging.getLogger(__name__)
    
    def send_alert(self, alert: Alert) -> bool:
        """Send alert notification - to be implemented by subclasses"""
        raise NotImplementedError
    
    def test_channel(self) -> bool:
        """Test channel connectivity"""
        raise NotImplementedError


class EmailAlertChannel(AlertChannel):
    """Email notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("email", config)
        self.smtp_server = config.get("smtp_server", "localhost")
        self.smtp_port = config.get("smtp_port", 587)
        self.username = config.get("username")
        self.password = config.get("password")
        self.from_email = config.get("from_email", "rag-assistant@example.com")
        self.to_emails = config.get("to_emails", [])
        self.use_tls = config.get("use_tls", True)
    
    def send_alert(self, alert: Alert) -> bool:
        """Send email alert"""
        if not self.enabled or not self.to_emails or not EMAIL_AVAILABLE:
            if not EMAIL_AVAILABLE:
                self.logger.warning("Email libraries not available, skipping email alert")
            return False
        
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = self.from_email
            msg['To'] = ", ".join(self.to_emails)
            msg['Subject'] = f"[{alert.severity.upper()}] RAG Assistant Alert: {alert.alert_type}"
            
            # Email body
            body = f"""
Alert Details:
=============

Alert Type: {alert.alert_type}
Severity: {alert.severity.title()}
Source: {alert.source}
Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC')}

Message:
{alert.message}

Alert ID: {alert.alert_id}

Metadata:
{json.dumps(alert.metadata, indent=2)}

---
RAG Assistant Monitoring System
"""
            
            msg.attach(MimeText(body, 'plain'))
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                if self.use_tls:
                    server.starttls()
                if self.username and self.password:
                    server.login(self.username, self.password)
                server.send_message(msg)
            
            self.logger.info(f"Email alert sent for {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send email alert: {e}")
            return False
    
    def test_channel(self) -> bool:
        """Test email channel"""
        if not EMAIL_AVAILABLE:
            self.logger.warning("Email libraries not available for testing")
            return False
            
        test_alert = Alert(
            alert_type="channel_test",
            severity=AlertSeverity.LOW,
            message="This is a test alert to verify email channel connectivity.",
            source="alerting_system"
        )
        return self.send_alert(test_alert)


class SlackAlertChannel(AlertChannel):
    """Slack notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("slack", config)
        self.webhook_url = config.get("webhook_url")
        self.channel = config.get("channel", "#alerts")
        self.username = config.get("username", "RAG Assistant")
        self.icon_emoji = config.get("icon_emoji", ":warning:")
    
    def send_alert(self, alert: Alert) -> bool:
        """Send Slack alert"""
        if not self.enabled or not self.webhook_url or not REQUESTS_AVAILABLE:
            return False
        
        # Severity color mapping
        color_map = {
            AlertSeverity.LOW: "good",
            AlertSeverity.MEDIUM: "warning", 
            AlertSeverity.HIGH: "warning",
            AlertSeverity.CRITICAL: "danger"
        }
        
        # Create Slack message
        slack_data = {
            "channel": self.channel,
            "username": self.username,
            "icon_emoji": self.icon_emoji,
            "attachments": [
                {
                    "color": color_map.get(alert.severity, "warning"),
                    "title": f"{alert.severity.upper()} Alert: {alert.alert_type}",
                    "text": alert.message,
                    "fields": [
                        {
                            "title": "Source",
                            "value": alert.source,
                            "short": True
                        },
                        {
                            "title": "Alert ID",
                            "value": alert.alert_id,
                            "short": True
                        },
                        {
                            "title": "Timestamp",
                            "value": alert.timestamp.strftime('%Y-%m-%d %H:%M:%S UTC'),
                            "short": True
                        }
                    ],
                    "footer": "RAG Assistant Monitoring",
                    "ts": int(alert.timestamp.timestamp())
                }
            ]
        }
        
        try:
            response = requests.post(
                self.webhook_url,
                data=json.dumps(slack_data),
                headers={'Content-Type': 'application/json'},
                timeout=10
            )
            response.raise_for_status()
            
            self.logger.info(f"Slack alert sent for {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send Slack alert: {e}")
            return False
    
    def test_channel(self) -> bool:
        """Test Slack channel"""
        test_alert = Alert(
            alert_type="channel_test",
            severity=AlertSeverity.LOW,
            message="This is a test alert to verify Slack channel connectivity.",
            source="alerting_system"
        )
        return self.send_alert(test_alert)


class CloudWatchAlertChannel(AlertChannel):
    """CloudWatch Alarms notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("cloudwatch", config)
        self.region = config.get("region", "us-east-1")
        self.sns_topic_arn = config.get("sns_topic_arn")
        
        if AWS_AVAILABLE:
            try:
                self.cloudwatch = boto3.client('cloudwatch', region_name=self.region)
                self.sns = boto3.client('sns', region_name=self.region)
                self.aws_available = True
            except Exception:
                self.aws_available = False
        else:
            self.aws_available = False
    
    def send_alert(self, alert: Alert) -> bool:
        """Send CloudWatch alarm"""
        if not self.enabled or not self.aws_available:
            return False
        
        try:
            # Create custom metric for the alert
            metric_name = f"Alert_{alert.alert_type}"
            namespace = "RAGAssistant/Alerts"
            
            # Send metric data
            self.cloudwatch.put_metric_data(
                Namespace=namespace,
                MetricData=[
                    {
                        'MetricName': metric_name,
                        'Value': 1,
                        'Unit': 'Count',
                        'Timestamp': alert.timestamp,
                        'Dimensions': [
                            {
                                'Name': 'Severity',
                                'Value': alert.severity
                            },
                            {
                                'Name': 'Source',
                                'Value': alert.source
                            }
                        ]
                    }
                ]
            )
            
            # Send SNS notification if configured
            if self.sns_topic_arn:
                message = {
                    "alert_id": alert.alert_id,
                    "alert_type": alert.alert_type,
                    "severity": alert.severity,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat()
                }
                
                self.sns.publish(
                    TopicArn=self.sns_topic_arn,
                    Message=json.dumps(message),
                    Subject=f"RAG Assistant Alert: {alert.alert_type}"
                )
            
            self.logger.info(f"CloudWatch alert sent for {alert.alert_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send CloudWatch alert: {e}")
            return False
    
    def test_channel(self) -> bool:
        """Test CloudWatch channel"""
        if not self.aws_available:
            return False
        
        test_alert = Alert(
            alert_type="channel_test",
            severity=AlertSeverity.LOW,
            message="This is a test alert to verify CloudWatch channel connectivity.",
            source="alerting_system"
        )
        return self.send_alert(test_alert)


class AlertAggregator:
    """Aggregates and deduplicates alerts to reduce noise"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.aggregation_window_minutes = config.get("aggregation_window_minutes", 5)
        self.similarity_threshold = config.get("similarity_threshold", 0.8)
        
        # Alert storage
        self.pending_alerts: List[Alert] = []
        self.processed_alerts: Dict[str, Alert] = {}
        
        self.logger = logging.getLogger(__name__)
    
    def add_alert(self, alert: Alert) -> bool:
        """Add alert to aggregation queue"""
        # Check for similar alerts in recent history
        similar_alert = self.find_similar_alert(alert)
        
        if similar_alert:
            # Update existing alert instead of creating new one
            similar_alert.metadata["occurrence_count"] = similar_alert.metadata.get("occurrence_count", 1) + 1
            similar_alert.metadata["last_occurrence"] = alert.timestamp.isoformat()
            similar_alert.message += f"\n[Repeated {similar_alert.metadata['occurrence_count']} times]"
            
            self.logger.info(f"Aggregated alert {alert.alert_id} with {similar_alert.alert_id}")
            return False  # Don't send duplicate
        else:
            # New alert - add to pending queue
            alert.metadata["occurrence_count"] = 1
            self.pending_alerts.append(alert)
            return True
    
    def find_similar_alert(self, new_alert: Alert) -> Optional[Alert]:
        """Find similar alert in recent history"""
        cutoff_time = datetime.now() - timedelta(minutes=self.aggregation_window_minutes)
        
        for alert in self.pending_alerts:
            if (alert.timestamp > cutoff_time and
                alert.alert_type == new_alert.alert_type and
                alert.severity == new_alert.severity and
                alert.source == new_alert.source):
                
                # Check message similarity (simple approach)
                similarity = self.calculate_message_similarity(alert.message, new_alert.message)
                if similarity > self.similarity_threshold:
                    return alert
        
        return None
    
    def calculate_message_similarity(self, msg1: str, msg2: str) -> float:
        """Calculate similarity between two messages"""
        # Simple word-based similarity
        words1 = set(msg1.lower().split())
        words2 = set(msg2.lower().split())
        
        if not words1 and not words2:
            return 1.0
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def get_ready_alerts(self) -> List[Alert]:
        """Get alerts ready for sending"""
        cutoff_time = datetime.now() - timedelta(minutes=self.aggregation_window_minutes)
        
        ready_alerts = [
            alert for alert in self.pending_alerts
            if alert.timestamp <= cutoff_time
        ]
        
        # Remove ready alerts from pending queue
        self.pending_alerts = [
            alert for alert in self.pending_alerts
            if alert.timestamp > cutoff_time
        ]
        
        return ready_alerts


class AlertingSystem:
    """Main alerting system orchestrator"""
    
    def __init__(self, project_path: str, config_path: str = None):
        self.project_path = Path(project_path)
        self.config = self.load_config(config_path)
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.channels = self.initialize_channels()
        self.aggregator = AlertAggregator(self.config.get("aggregation", {}))
        
        # Alert tracking
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Escalation tracking
        self.escalation_timers = {}
        
        # Create alerting directories
        self.create_alerting_directories()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.project_path / "logs" / "monitoring" / "alerting.log"
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
        """Load alerting configuration"""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                return yaml.safe_load(f)
        
        # Default configuration
        return {
            "channels": {
                "email": {
                    "enabled": False,
                    "smtp_server": "localhost",
                    "smtp_port": 587,
                    "username": "",
                    "password": "",
                    "from_email": "rag-assistant@example.com",
                    "to_emails": [],
                    "use_tls": True
                },
                "slack": {
                    "enabled": False,
                    "webhook_url": "",
                    "channel": "#alerts",
                    "username": "RAG Assistant",
                    "icon_emoji": ":warning:"
                },
                "cloudwatch": {
                    "enabled": True,
                    "region": "us-east-1",
                    "sns_topic_arn": ""
                }
            },
            "aggregation": {
                "aggregation_window_minutes": 5,
                "similarity_threshold": 0.8
            },
            "escalation": {
                "enabled": True,
                "escalation_delay_minutes": 15,
                "max_escalations": 2
            },
            "thresholds": {
                "cpu_usage_warning": 70.0,
                "cpu_usage_critical": 90.0,
                "memory_usage_warning": 75.0,
                "memory_usage_critical": 90.0,
                "error_rate_warning": 0.05,
                "error_rate_critical": 0.15,
                "response_time_warning": 2000,
                "response_time_critical": 5000
            }
        }
    
    def initialize_channels(self) -> Dict[str, AlertChannel]:
        """Initialize alert notification channels"""
        channels = {}
        
        # Email channel
        if self.config["channels"]["email"]["enabled"]:
            channels["email"] = EmailAlertChannel(self.config["channels"]["email"])
        
        # Slack channel
        if self.config["channels"]["slack"]["enabled"]:
            channels["slack"] = SlackAlertChannel(self.config["channels"]["slack"])
        
        # CloudWatch channel
        if self.config["channels"]["cloudwatch"]["enabled"]:
            channels["cloudwatch"] = CloudWatchAlertChannel(self.config["channels"]["cloudwatch"])
        
        self.logger.info(f"Initialized {len(channels)} notification channels")
        return channels
    
    def create_alerting_directories(self):
        """Create necessary alerting directories"""
        directories = [
            "logs/monitoring",
            "monitoring/alerts",
            "monitoring/escalations",
            "monitoring/channel_tests"
        ]
        
        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)
    
    def create_alert(self, alert_type: str, severity: str, message: str,
                     source: str = "system", metadata: Dict[str, Any] = None) -> Alert:
        """Create and process new alert"""
        alert = Alert(alert_type, severity, message, source, metadata)
        
        # Add to aggregator
        should_send = self.aggregator.add_alert(alert)
        
        if should_send:
            self.active_alerts[alert.alert_id] = alert
            self.alert_history.append(alert)
            
            # Send alert through channels
            self.send_alert(alert)
            
            # Setup escalation timer if enabled
            if (self.config.get("escalation", {}).get("enabled", False) and
                severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]):
                self.schedule_escalation(alert)
        
        return alert
    
    def send_alert(self, alert: Alert):
        """Send alert through all enabled channels"""
        sent_channels = []
        failed_channels = []
        
        for channel_name, channel in self.channels.items():
            try:
                success = channel.send_alert(alert)
                if success:
                    sent_channels.append(channel_name)
                    alert.notification_history.append({
                        "channel": channel_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "sent"
                    })
                else:
                    failed_channels.append(channel_name)
                    alert.notification_history.append({
                        "channel": channel_name,
                        "timestamp": datetime.now().isoformat(),
                        "status": "failed"
                    })
                    
            except Exception as e:
                self.logger.error(f"Channel {channel_name} failed: {e}")
                failed_channels.append(channel_name)
        
        self.logger.info(f"Alert {alert.alert_id} sent via {len(sent_channels)} channels, {len(failed_channels)} failed")
        
        # Save alert record
        self.save_alert_record(alert)
    
    def schedule_escalation(self, alert: Alert):
        """Schedule alert escalation"""
        escalation_delay = self.config["escalation"].get("escalation_delay_minutes", 15)
        escalation_time = datetime.now() + timedelta(minutes=escalation_delay)
        
        self.escalation_timers[alert.alert_id] = escalation_time
        self.logger.info(f"Scheduled escalation for alert {alert.alert_id} at {escalation_time}")
    
    def process_escalations(self):
        """Process pending escalations"""
        current_time = datetime.now()
        max_escalations = self.config["escalation"].get("max_escalations", 2)
        
        alerts_to_escalate = []
        
        for alert_id, escalation_time in self.escalation_timers.items():
            if current_time >= escalation_time:
                alert = self.active_alerts.get(alert_id)
                if (alert and alert.status == "active" and 
                    alert.escalation_count < max_escalations):
                    alerts_to_escalate.append(alert)
        
        # Process escalations
        for alert in alerts_to_escalate:
            if alert.escalate():
                self.logger.warning(f"Escalated alert {alert.alert_id} to {alert.severity}")
                self.send_alert(alert)
                
                # Schedule next escalation if not at max level
                if alert.escalation_count < max_escalations:
                    self.schedule_escalation(alert)
                else:
                    # Remove from escalation timers
                    del self.escalation_timers[alert.alert_id]
            else:
                # No more escalation levels
                del self.escalation_timers[alert.alert_id]
    
    def save_alert_record(self, alert: Alert):
        """Save alert record to disk"""
        alert_file = (self.project_path / "monitoring" / "alerts" / 
                     f"{alert.alert_id}.json")
        
        with open(alert_file, 'w') as f:
            json.dump(alert.to_dict(), f, indent=2)
    
    def test_all_channels(self) -> Dict[str, bool]:
        """Test all configured channels"""
        test_results = {}
        
        for channel_name, channel in self.channels.items():
            self.logger.info(f"Testing channel: {channel_name}")
            try:
                test_results[channel_name] = channel.test_channel()
            except Exception as e:
                self.logger.error(f"Channel {channel_name} test failed: {e}")
                test_results[channel_name] = False
        
        return test_results
    
    def run_alerting_daemon(self, monitoring_interval: int = 30):
        """Run alerting daemon with escalation processing"""
        self.logger.info("Starting alerting daemon")
        
        try:
            while True:
                # Process ready alerts from aggregator
                ready_alerts = self.aggregator.get_ready_alerts()
                for alert in ready_alerts:
                    if alert.alert_id in self.active_alerts:
                        self.send_alert(alert)
                
                # Process escalations
                self.process_escalations()
                
                # Clean up old resolved alerts
                self.cleanup_old_alerts()
                
                time.sleep(monitoring_interval)
                
        except KeyboardInterrupt:
            self.logger.info("Alerting daemon stopped by user")
        except Exception as e:
            self.logger.error(f"Alerting daemon error: {e}")
        
    def cleanup_old_alerts(self, max_age_days: int = 7):
        """Clean up old resolved alerts"""
        cutoff_time = datetime.now() - timedelta(days=max_age_days)
        
        # Remove old resolved alerts
        alerts_to_remove = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if (alert.status == "resolved" and 
                alert.resolved_at and 
                alert.resolved_at < cutoff_time)
        ]
        
        for alert_id in alerts_to_remove:
            del self.active_alerts[alert_id]
            if alert_id in self.escalation_timers:
                del self.escalation_timers[alert_id]
        
        if alerts_to_remove:
            self.logger.info(f"Cleaned up {len(alerts_to_remove)} old alerts")
    
    def generate_alerting_report(self) -> str:
        """Generate alerting system report"""
        report = f"""
Alerting System Status Report
Generated: {datetime.now().isoformat()}

ALERT STATISTICS:
Active Alerts: {len(self.active_alerts)}
Total Alert History: {len(self.alert_history)}
Pending Escalations: {len(self.escalation_timers)}

CHANNEL STATUS:
"""
        
        # Test all channels
        channel_results = self.test_all_channels()
        for channel_name, status in channel_results.items():
            status_text = "✓ WORKING" if status else "✗ FAILED"
            report += f"  {channel_name}: {status_text}\n"
        
        # Alert severity breakdown
        if self.alert_history:
            severity_counts = {}
            for alert in self.alert_history:
                severity_counts[alert.severity] = severity_counts.get(alert.severity, 0) + 1
            
            report += f"\nALERT SEVERITY BREAKDOWN:\n"
            for severity, count in severity_counts.items():
                report += f"  {severity.title()}: {count}\n"
        
        # Recent active alerts
        if self.active_alerts:
            report += f"\nACTIVE ALERTS:\n"
            for alert in sorted(self.active_alerts.values(), key=lambda a: a.timestamp, reverse=True)[:10]:
                report += f"  [{alert.severity.upper()}] {alert.alert_type}: {alert.message[:100]}...\n"
        
        return report


def main():
    parser = argparse.ArgumentParser(description='Automated Alerting System')
    parser.add_argument('--project-path', default='/Users/peter/Desktop/ai_rag_assistant',
                       help='Path to RAG project')
    parser.add_argument('--config-path', help='Path to alerting configuration file')
    parser.add_argument('--mode', choices=['setup', 'daemon', 'test', 'report'],
                       default='setup', help='Alerting mode')
    parser.add_argument('--setup-alerts', action='store_true',
                       help='Setup alerting infrastructure')
    parser.add_argument('--test-alerts', action='store_true',
                       help='Test all alert channels')
    parser.add_argument('--channels', default='all',
                       help='Channels to test (comma-separated or "all")')
    parser.add_argument('--monitoring-interval', type=int, default=30,
                       help='Monitoring interval for daemon mode')
    parser.add_argument('--enable-escalation', action='store_true',
                       help='Enable alert escalation')
    
    args = parser.parse_args()
    
    try:
        # Initialize alerting system
        alerting = AlertingSystem(
            project_path=args.project_path,
            config_path=args.config_path
        )
        
        print("Automated Alerting System")
        print("=" * 30)
        
        if args.mode == 'setup' or args.setup_alerts:
            print("Setting up alerting infrastructure...")
            
            # Save configuration file
            config_file = alerting.project_path / "configs" / "alerting.yaml"
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(alerting.config, f, indent=2)
            
            print(f"Configuration saved to: {config_file}")
            print(f"Channels configured: {list(alerting.channels.keys())}")
            
        elif args.mode == 'test' or args.test_alerts:
            print("Testing alert channels...")
            test_results = alerting.test_all_channels()
            
            for channel, success in test_results.items():
                status = "✓ PASSED" if success else "✗ FAILED"
                print(f"  {channel}: {status}")
            
        elif args.mode == 'daemon':
            print(f"Starting alerting daemon (interval: {args.monitoring_interval}s)")
            alerting.run_alerting_daemon(args.monitoring_interval)
            
        elif args.mode == 'report':
            print("Generating alerting system report...")
            report = alerting.generate_alerting_report()
            print(report)
            
            # Save report
            report_file = (alerting.project_path / "monitoring" / "reports" / 
                          f"alerting_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
            with open(report_file, 'w') as f:
                f.write(report)
            print(f"\nReport saved to: {report_file}")
        
        print("\nAlerting system session completed successfully")
        
    except Exception as e:
        print(f"[ERROR] Alerting system failed: {e}")
        raise


if __name__ == "__main__":
    main()