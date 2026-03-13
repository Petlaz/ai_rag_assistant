"""
Automated Log Analysis and Monitoring System

This script provides comprehensive log analysis capabilities for the RAG Assistant
production environment, including real-time log monitoring, anomaly detection,
error pattern analysis, and automated log aggregation from multiple sources.

Features:
- Real-time log monitoring and streaming analysis
- Multi-source log aggregation (application, system, infrastructure)
- Error pattern detection and correlation analysis
- Performance bottleneck identification through log analysis
- Anomaly detection in log patterns and frequencies
- Automated log rotation and archival management
- Custom alert generation based on log patterns
- ELK stack integration for advanced log visualization

Usage:
    # Start real-time log monitoring
    python scripts/monitoring/log_analysis.py \
        --mode monitor \
        --watch-logs /var/log/rag-assistant \
        --alert-patterns configs/alert_patterns.yaml

    # Analyze historical logs
    python scripts/monitoring/log_analysis.py \
        --mode analyze \
        --log-files logs/application/*.log \
        --timeframe 24hours \
        --generate-report

    # Setup log aggregation pipeline
    python scripts/monitoring/log_analysis.py \
        --setup-pipeline \
        --elastic-host localhost:9200 \
        --kibana-host localhost:5601
"""

import argparse
import gzip
import json
import logging
import re
import time
import warnings
from collections import defaultdict, Counter, deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple, Set
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
import yaml

try:
    from watchdog.observers import Observer
    from watchdog.events import FileSystemEventHandler, FileModifiedEvent
    WATCHDOG_AVAILABLE = True
    
    class LogFileWatcher(FileSystemEventHandler):
        """Watch log files for real-time monitoring"""
        
        def __init__(self, log_analyzer):
            self.log_analyzer = log_analyzer
            self.file_positions = {}
            self.logger = logging.getLogger(__name__)
        
        def on_modified(self, event):
            """Handle file modification events"""
            if not isinstance(event, FileModifiedEvent) or event.is_directory:
                return
            
            file_path = Path(event.src_path)
            if file_path.suffix in ['.log', '.txt'] or 'log' in file_path.name.lower():
                self.process_file_updates(file_path)
        
        def process_file_updates(self, file_path: Path):
            """Process new lines in updated file"""
            try:
                file_size = file_path.stat().st_size
                last_position = self.file_positions.get(str(file_path), 0)
                
                if file_size < last_position:
                    # File was truncated or rotated
                    last_position = 0
                
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    f.seek(last_position)
                    new_lines = f.readlines()
                    self.file_positions[str(file_path)] = f.tell()
                
                # Process new lines
                for line in new_lines:
                    log_entry = self.log_analyzer.parser.parse_log_line(line, str(file_path))
                    if log_entry:
                        self.log_analyzer.process_log_entry(log_entry)
                        
            except Exception as e:
                self.logger.error(f"Error processing file updates for {file_path}: {e}")

except ImportError:
    WATCHDOG_AVAILABLE = False
    
    # Dummy class when watchdog is not available
    class LogFileWatcher:
        def __init__(self, log_analyzer):
            self.log_analyzer = log_analyzer
            self.logger = logging.getLogger(__name__)
            self.logger.warning("Watchdog library not available - file watching disabled")

try:
    from elasticsearch import Elasticsearch
    ELASTICSEARCH_AVAILABLE = True
except ImportError:
    ELASTICSEARCH_AVAILABLE = False


class LogEntry:
    """Structured representation of a log entry"""
    
    def __init__(self, timestamp: datetime, level: str, message: str, 
                 source: str = "unknown", metadata: Dict[str, Any] = None):
        self.timestamp = timestamp
        self.level = level.upper()
        self.message = message
        self.source = source
        self.metadata = metadata or {}
        
        # Analysis fields
        self.error_type = None
        self.error_code = None
        self.anomaly_score = 0.0
        self.patterns_matched = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for analysis"""
        return {
            "timestamp": self.timestamp.isoformat(),
            "level": self.level,
            "message": self.message,
            "source": self.source,
            "metadata": self.metadata,
            "error_type": self.error_type,
            "error_code": self.error_code,
            "anomaly_score": self.anomaly_score,
            "patterns_matched": self.patterns_matched
        }


class LogParser:
    """Parse various log formats into structured LogEntry objects"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        
        # Common log patterns
        self.patterns = {
            "apache_common": re.compile(
                r'(?P<host>\S+) \S+ \S+ \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\d+) (?P<size>\S+)'
            ),
            "python_logging": re.compile(
                r'(?P<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}[,\d]*) - (?P<logger>\S+) - (?P<level>\S+) - (?P<message>.*)'
            ),
            "nginx_access": re.compile(
                r'(?P<remote_addr>\S+) - \S+ \[(?P<time>[^\]]+)\] "(?P<request>[^"]*)" (?P<status>\d+) (?P<body_bytes_sent>\S+) "(?P<http_referer>[^"]*)" "(?P<http_user_agent>[^"]*)"'
            ),
            "syslog": re.compile(
                r'(?P<time>\w{3} \d{2} \d{2}:\d{2}:\d{2}) (?P<host>\S+) (?P<program>\S+)(?:\[(?P<pid>\d+)\])?: (?P<message>.*)'
            ),
            "docker": re.compile(
                r'(?P<time>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d+Z) (?P<stream>stdout|stderr) (?P<log>.*)'
            ),
            "aws_cloudwatch": re.compile(
                r'\[(?P<time>[^\]]+)\] (?P<level>\S+)\s+(?P<message>.*)'
            ),
            "json": re.compile(r'^\{.*\}$')
        }
        
        # Error classification patterns
        self.error_patterns = {
            "connection_error": [
                r"connection.*(?:refused|timeout|failed)",
                r"unable to connect",
                r"network.*(?:unreachable|error)"
            ],
            "authentication_error": [
                r"authentication.*failed",
                r"invalid.*(?:credential|token|key)",
                r"unauthorized|forbidden"
            ],
            "resource_error": [
                r"out of memory",
                r"disk.*full",
                r"no space left",
                r"resource.*(?:exhausted|unavailable)"
            ],
            "database_error": [
                r"database.*(?:connection|error|timeout)",
                r"sql.*(?:error|exception)",
                r"deadlock|lock.*timeout"
            ],
            "api_error": [
                r"http.*(?:5\d{2}|4\d{2})",
                r"api.*(?:error|failure|timeout)",
                r"rate.*limit.*exceeded"
            ],
            "ml_model_error": [
                r"model.*(?:error|failure|timeout)",
                r"inference.*(?:failed|error)",
                r"embedding.*(?:error|timeout)"
            ]
        }
    
    def parse_log_line(self, line: str, source: str = "unknown") -> Optional[LogEntry]:
        """Parse a single log line into LogEntry"""
        line = line.strip()
        if not line:
            return None
        
        # Try JSON format first
        if line.startswith('{') and line.endswith('}'):
            try:
                json_data = json.loads(line)
                return self.parse_json_log(json_data, source)
            except json.JSONDecodeError:
                pass
        
        # Try pattern matching
        for pattern_name, pattern in self.patterns.items():
            match = pattern.match(line)
            if match:
                return self.parse_pattern_match(match, pattern_name, source, line)
        
        # Fallback: create basic entry
        return LogEntry(
            timestamp=datetime.now(),
            level="INFO",
            message=line,
            source=source,
            metadata={"format": "unknown"}
        )
    
    def parse_json_log(self, json_data: Dict[str, Any], source: str) -> LogEntry:
        """Parse JSON formatted log entry"""
        # Extract timestamp
        timestamp_str = json_data.get("timestamp") or json_data.get("time") or json_data.get("@timestamp")
        if timestamp_str:
            timestamp = self.parse_timestamp(timestamp_str)
        else:
            timestamp = datetime.now()
        
        # Extract level
        level = json_data.get("level") or json_data.get("severity") or "INFO"
        
        # Extract message
        message = json_data.get("message") or json_data.get("msg") or str(json_data)
        
        # Extract metadata
        metadata = {k: v for k, v in json_data.items() if k not in ["timestamp", "time", "@timestamp", "level", "severity", "message", "msg"]}
        metadata["format"] = "json"
        
        return LogEntry(timestamp, level, message, source, metadata)
    
    def parse_pattern_match(self, match: re.Match, pattern_name: str, source: str, original_line: str) -> LogEntry:
        """Parse matched pattern into LogEntry"""
        groups = match.groupdict()
        
        # Extract timestamp
        if 'time' in groups:
            timestamp = self.parse_timestamp(groups['time'])
        else:
            timestamp = datetime.now()
        
        # Extract level
        level = groups.get('level', 'INFO')
        
        # Extract message
        if 'message' in groups:
            message = groups['message']
        elif 'request' in groups:
            message = groups['request']
        else:
            message = original_line
        
        # Create metadata
        metadata = {k: v for k, v in groups.items() if k not in ['time', 'level', 'message']}
        metadata["format"] = pattern_name
        
        return LogEntry(timestamp, level, message, source, metadata)
    
    def parse_timestamp(self, timestamp_str: str) -> datetime:
        """Parse timestamp string into datetime object"""
        timestamp_formats = [
            "%Y-%m-%d %H:%M:%S,%f",
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%dT%H:%M:%S.%fZ",
            "%Y-%m-%dT%H:%M:%SZ",
            "%d/%b/%Y:%H:%M:%S %z",
            "%b %d %H:%M:%S",
            "%Y-%m-%d %H:%M:%S.%f%z",
        ]
        
        for fmt in timestamp_formats:
            try:
                return datetime.strptime(timestamp_str, fmt)
            except ValueError:
                continue
        
        # If parsing fails, use current time
        return datetime.now()
    
    def classify_error(self, log_entry: LogEntry) -> Optional[str]:
        """Classify error type based on message content"""
        if log_entry.level not in ['ERROR', 'CRITICAL', 'FATAL']:
            return None
        
        message_lower = log_entry.message.lower()
        
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, message_lower, re.IGNORECASE):
                    log_entry.error_type = error_type
                    return error_type
        
        log_entry.error_type = "unknown_error"
        return "unknown_error"


class LogAnomalyDetector:
    """Detect anomalies in log patterns and frequencies"""
    
    def __init__(self, window_size: int = 100):
        self.window_size = window_size
        self.message_frequencies = deque(maxlen=window_size)
        self.level_frequencies = deque(maxlen=window_size)
        self.time_intervals = deque(maxlen=window_size)
        
        self.baseline_stats = {}
        self.anomaly_threshold = 3.0  # Standard deviations
        
        self.logger = logging.getLogger(__name__)
    
    def update_baselines(self, log_entry: LogEntry):
        """Update baseline statistics with new log entry"""
        current_time = log_entry.timestamp.timestamp()
        
        # Update message frequency
        message_hash = hash(log_entry.message[:50])  # First 50 chars for similarity
        self.message_frequencies.append(message_hash)
        
        # Update level frequency
        self.level_frequencies.append(log_entry.level)
        
        # Update time intervals
        if len(self.time_intervals) > 0:
            last_time = self.time_intervals[-1]
            interval = current_time - last_time
            self.time_intervals.append(current_time)
            
            # Recalculate baseline stats
            self.calculate_baseline_stats()
        else:
            self.time_intervals.append(current_time)
    
    def calculate_baseline_stats(self):
        """Calculate baseline statistics for anomaly detection"""
        if len(self.time_intervals) < 10:
            return
        
        # Calculate time interval statistics
        intervals = [
            self.time_intervals[i] - self.time_intervals[i-1]
            for i in range(1, len(self.time_intervals))
        ]
        
        self.baseline_stats = {
            "avg_interval": np.mean(intervals),
            "std_interval": np.std(intervals),
            "message_diversity": len(set(self.message_frequencies)),
            "level_distribution": Counter(self.level_frequencies)
        }
    
    def detect_anomaly(self, log_entry: LogEntry) -> float:
        """Detect anomalies and return anomaly score (0-1)"""
        if not self.baseline_stats:
            self.update_baselines(log_entry)
            return 0.0
        
        anomaly_score = 0.0
        
        # Check time interval anomaly
        if len(self.time_intervals) > 1:
            current_time = log_entry.timestamp.timestamp()
            last_time = self.time_intervals[-1]
            current_interval = current_time - last_time
            
            avg_interval = self.baseline_stats["avg_interval"]
            std_interval = self.baseline_stats["std_interval"]
            
            if std_interval > 0:
                z_score = abs(current_interval - avg_interval) / std_interval
                if z_score > self.anomaly_threshold:
                    anomaly_score += min(z_score / 10, 0.5)
        
        # Check error level anomaly
        level_dist = self.baseline_stats["level_distribution"]
        total_logs = sum(level_dist.values())
        expected_freq = level_dist.get(log_entry.level, 0) / total_logs
        
        if log_entry.level in ["ERROR", "CRITICAL", "FATAL"] and expected_freq < 0.1:
            anomaly_score += 0.3
        
        # Check message pattern anomaly
        message_hash = hash(log_entry.message[:50])
        if message_hash not in self.message_frequencies:
            anomaly_score += 0.2
        
        # Update baselines with new entry
        self.update_baselines(log_entry)
        
        log_entry.anomaly_score = min(anomaly_score, 1.0)
        return log_entry.anomaly_score


class LogAnalyzer:
    """Main log analysis engine"""
    
    def __init__(self, project_path: str, config: Dict[str, Any] = None):
        self.project_path = Path(project_path)
        self.config = config or {}
        
        # Setup logging
        self.setup_logging()
        
        # Initialize components
        self.parser = LogParser()
        self.anomaly_detector = LogAnomalyDetector()
        
        # Analysis storage
        self.log_entries = []
        self.error_stats = defaultdict(int)
        self.performance_metrics = []
        
        # Real-time monitoring
        self.observer = None
        self.is_monitoring = False
        
        # Create analysis directories
        self.create_analysis_directories()
    
    def setup_logging(self):
        """Setup logging configuration"""
        log_file = self.project_path / "logs" / "monitoring" / "log_analysis.log"
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
    
    def create_analysis_directories(self):
        """Create necessary analysis directories"""
        directories = [
            "logs/monitoring",
            "monitoring/log_analysis",
            "monitoring/anomalies",
            "monitoring/patterns"
        ]
        
        for directory in directories:
            (self.project_path / directory).mkdir(parents=True, exist_ok=True)
    
    def start_real_time_monitoring(self, watch_paths: List[str]):
        """Start real-time log monitoring"""
        if not WATCHDOG_AVAILABLE:
            self.logger.error("Watchdog library not available for real-time monitoring")
            return False
        
        self.logger.info("Starting real-time log monitoring")
        
        self.observer = Observer()
        event_handler = LogFileWatcher(self)
        
        for path in watch_paths:
            path_obj = Path(path)
            if path_obj.exists():
                if path_obj.is_dir():
                    self.observer.schedule(event_handler, str(path_obj), recursive=True)
                else:
                    self.observer.schedule(event_handler, str(path_obj.parent), recursive=False)
                self.logger.info(f"Watching: {path}")
        
        self.observer.start()
        self.is_monitoring = True
        
        try:
            while self.is_monitoring:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_monitoring()
        
        return True
    
    def stop_monitoring(self):
        """Stop real-time monitoring"""
        self.is_monitoring = False
        if self.observer:
            self.observer.stop()
            self.observer.join()
            self.logger.info("Stopped real-time log monitoring")
    
    def process_log_entry(self, log_entry: LogEntry):
        """Process a single log entry for analysis"""
        # Classify errors
        self.parser.classify_error(log_entry)
        
        # Detect anomalies
        anomaly_score = self.anomaly_detector.detect_anomaly(log_entry)
        
        # Store entry
        self.log_entries.append(log_entry)
        
        # Update statistics
        if log_entry.error_type:
            self.error_stats[log_entry.error_type] += 1
        
        # Handle high anomaly scores
        if anomaly_score > 0.7:
            self.handle_anomaly(log_entry)
        
        # Extract performance metrics
        self.extract_performance_metrics(log_entry)
    
    def handle_anomaly(self, log_entry: LogEntry):
        """Handle detected anomaly"""
        anomaly_file = (self.project_path / "monitoring" / "anomalies" / 
                       f"anomaly_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        anomaly_data = {
            "detected_at": datetime.now().isoformat(),
            "anomaly_score": log_entry.anomaly_score,
            "log_entry": log_entry.to_dict()
        }
        
        with open(anomaly_file, 'w') as f:
            json.dump(anomaly_data, f, indent=2)
        
        self.logger.warning(f"Anomaly detected (score: {log_entry.anomaly_score:.2f}): {log_entry.message[:100]}")
    
    def extract_performance_metrics(self, log_entry: LogEntry):
        """Extract performance metrics from log entries"""
        # Look for response time patterns
        response_time_matches = re.findall(r'(?:response|took|duration)[:\s]*(\d+(?:\.\d+)?)\s*(?:ms|milliseconds)', 
                                         log_entry.message, re.IGNORECASE)
        
        if response_time_matches:
            for match in response_time_matches:
                self.performance_metrics.append({
                    "timestamp": log_entry.timestamp,
                    "metric": "response_time_ms",
                    "value": float(match),
                    "source": log_entry.source
                })
        
        # Look for memory usage patterns
        memory_matches = re.findall(r'(?:memory|mem)[:\s]*(\d+(?:\.\d+)?)\s*(?:mb|gb|bytes)', 
                                   log_entry.message, re.IGNORECASE)
        
        if memory_matches:
            for match in memory_matches:
                self.performance_metrics.append({
                    "timestamp": log_entry.timestamp,
                    "metric": "memory_usage",
                    "value": float(match),
                    "source": log_entry.source
                })
    
    def analyze_historical_logs(self, log_files: List[str], timeframe_hours: int = 24) -> Dict[str, Any]:
        """Analyze historical log files"""
        self.logger.info(f"Analyzing historical logs: {len(log_files)} files")
        
        start_time = datetime.now()
        cutoff_time = start_time - timedelta(hours=timeframe_hours)
        processed_entries = 0
        
        for log_file in log_files:
            file_path = Path(log_file)
            if not file_path.exists():
                self.logger.warning(f"Log file not found: {log_file}")
                continue
            
            try:
                self.process_log_file(file_path, cutoff_time)
                processed_entries += len([e for e in self.log_entries if e.timestamp > cutoff_time])
                
            except Exception as e:
                self.logger.error(f"Error processing log file {log_file}: {e}")
        
        # Generate analysis results
        analysis_results = {
            "analysis_period": {
                "start_time": cutoff_time.isoformat(),
                "end_time": start_time.isoformat(),
                "duration_hours": timeframe_hours
            },
            "processed_entries": processed_entries,
            "error_analysis": self.analyze_errors(),
            "anomaly_analysis": self.analyze_anomalies(),
            "performance_analysis": self.analyze_performance(),
            "pattern_analysis": self.analyze_patterns()
        }
        
        # Save analysis results
        results_file = (self.project_path / "monitoring" / "log_analysis" / 
                       f"analysis_{start_time.strftime('%Y%m%d_%H%M%S')}.json")
        
        with open(results_file, 'w') as f:
            json.dump(analysis_results, f, indent=2)
        
        return analysis_results
    
    def process_log_file(self, file_path: Path, cutoff_time: datetime):
        """Process a single log file"""
        try:
            if file_path.suffix == '.gz':
                with gzip.open(file_path, 'rt', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            else:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
            
            for line in lines:
                log_entry = self.parser.parse_log_line(line, str(file_path))
                if log_entry and log_entry.timestamp > cutoff_time:
                    self.process_log_entry(log_entry)
                    
        except Exception as e:
            self.logger.error(f"Error reading log file {file_path}: {e}")
    
    def analyze_errors(self) -> Dict[str, Any]:
        """Analyze error patterns and frequencies"""
        error_entries = [e for e in self.log_entries if e.level in ['ERROR', 'CRITICAL', 'FATAL']]
        
        if not error_entries:
            return {"total_errors": 0, "error_types": {}, "error_trends": []}
        
        # Error type analysis
        error_type_counts = Counter([e.error_type for e in error_entries if e.error_type])
        
        # Error trends over time
        error_trends = []
        current_hour = None
        hourly_count = 0
        
        for entry in sorted(error_entries, key=lambda x: x.timestamp):
            hour = entry.timestamp.replace(minute=0, second=0, microsecond=0)
            if current_hour != hour:
                if current_hour:
                    error_trends.append({
                        "hour": current_hour.isoformat(),
                        "count": hourly_count
                    })
                current_hour = hour
                hourly_count = 1
            else:
                hourly_count += 1
        
        if current_hour:
            error_trends.append({
                "hour": current_hour.isoformat(),
                "count": hourly_count
            })
        
        return {
            "total_errors": len(error_entries),
            "error_types": dict(error_type_counts),
            "error_trends": error_trends,
            "top_error_messages": self.get_top_error_messages(error_entries)
        }
    
    def get_top_error_messages(self, error_entries: List[LogEntry], top_n: int = 10) -> List[Dict[str, Any]]:
        """Get most frequent error messages"""
        message_counts = Counter([e.message[:100] for e in error_entries])
        return [
            {"message": msg, "count": count}
            for msg, count in message_counts.most_common(top_n)
        ]
    
    def analyze_anomalies(self) -> Dict[str, Any]:
        """Analyze detected anomalies"""
        anomalous_entries = [e for e in self.log_entries if e.anomaly_score > 0.3]
        
        if not anomalous_entries:
            return {"total_anomalies": 0, "anomaly_distribution": {}}
        
        # Anomaly score distribution
        score_ranges = {
            "low": [0.3, 0.5],
            "medium": [0.5, 0.7],
            "high": [0.7, 1.0]
        }
        
        anomaly_distribution = {}
        for range_name, (min_score, max_score) in score_ranges.items():
            count = len([e for e in anomalous_entries 
                        if min_score <= e.anomaly_score < max_score])
            anomaly_distribution[range_name] = count
        
        return {
            "total_anomalies": len(anomalous_entries),
            "anomaly_distribution": anomaly_distribution,
            "highest_anomaly_score": max(e.anomaly_score for e in anomalous_entries),
            "recent_anomalies": [
                {
                    "timestamp": e.timestamp.isoformat(),
                    "score": e.anomaly_score,
                    "message": e.message[:100]
                }
                for e in sorted(anomalous_entries, key=lambda x: x.anomaly_score, reverse=True)[:10]
            ]
        }
    
    def analyze_performance(self) -> Dict[str, Any]:
        """Analyze performance metrics extracted from logs"""
        if not self.performance_metrics:
            return {"metrics_found": 0, "response_time_stats": {}, "memory_stats": {}}
        
        # Response time analysis
        response_times = [m["value"] for m in self.performance_metrics if m["metric"] == "response_time_ms"]
        response_time_stats = {}
        
        if response_times:
            response_time_stats = {
                "count": len(response_times),
                "mean": np.mean(response_times),
                "median": np.median(response_times),
                "p95": np.percentile(response_times, 95),
                "p99": np.percentile(response_times, 99),
                "max": np.max(response_times),
                "min": np.min(response_times)
            }
        
        # Memory usage analysis
        memory_values = [m["value"] for m in self.performance_metrics if m["metric"] == "memory_usage"]
        memory_stats = {}
        
        if memory_values:
            memory_stats = {
                "count": len(memory_values),
                "mean": np.mean(memory_values),
                "max": np.max(memory_values),
                "min": np.min(memory_values)
            }
        
        return {
            "metrics_found": len(self.performance_metrics),
            "response_time_stats": response_time_stats,
            "memory_stats": memory_stats
        }
    
    def analyze_patterns(self) -> Dict[str, Any]:
        """Analyze common log patterns"""
        # Message pattern analysis
        message_words = []
        for entry in self.log_entries:
            words = re.findall(r'\b\w+\b', entry.message.lower())
            message_words.extend(words)
        
        word_counts = Counter(message_words)
        common_patterns = word_counts.most_common(20)
        
        # Level distribution
        level_distribution = Counter([e.level for e in self.log_entries])
        
        # Source distribution
        source_distribution = Counter([e.source for e in self.log_entries])
        
        return {
            "total_entries": len(self.log_entries),
            "level_distribution": dict(level_distribution),
            "source_distribution": dict(source_distribution),
            "common_words": dict(common_patterns),
            "time_span": {
                "start": min(e.timestamp for e in self.log_entries).isoformat() if self.log_entries else None,
                "end": max(e.timestamp for e in self.log_entries).isoformat() if self.log_entries else None
            }
        }


def main():
    parser = argparse.ArgumentParser(description='Automated Log Analysis and Monitoring')
    parser.add_argument('--project-path', default='/Users/peter/Desktop/ai_rag_assistant',
                       help='Path to RAG project')
    parser.add_argument('--mode', choices=['setup', 'monitor', 'analyze', 'report'],
                       default='analyze', help='Analysis mode')
    parser.add_argument('--watch-logs', nargs='+',
                       help='Log paths to watch for real-time monitoring')
    parser.add_argument('--log-files', nargs='+',
                       help='Log files to analyze')
    parser.add_argument('--timeframe', default='24hours',
                       help='Analysis timeframe (e.g., 24hours, 7days)')
    parser.add_argument('--generate-report', action='store_true',
                       help='Generate analysis report')
    parser.add_argument('--alert-patterns', 
                       help='Path to alert pattern configuration')
    parser.add_argument('--setup-pipeline', action='store_true',
                       help='Setup log aggregation pipeline')
    
    args = parser.parse_args()
    
    try:
        # Initialize log analyzer
        log_analyzer = LogAnalyzer(args.project_path)
        
        print("Automated Log Analysis and Monitoring")
        print("=" * 40)
        
        if args.mode == 'setup' or args.setup_pipeline:
            print("Setting up log analysis infrastructure...")
            
            # Create default configuration
            config = {
                "monitoring": {
                    "log_paths": [
                        "/var/log/rag-assistant",
                        "logs/application",
                        "logs/monitoring"
                    ],
                    "file_patterns": ["*.log", "*.txt"],
                    "real_time": True
                },
                "analysis": {
                    "retention_days": 30,
                    "anomaly_threshold": 0.7,
                    "error_patterns": log_analyzer.parser.error_patterns
                },
                "alerting": {
                    "enabled": True,
                    "channels": ["file", "cloudwatch"],
                    "error_threshold": 10
                }
            }
            
            config_file = Path(args.project_path) / "configs" / "log_analysis.yaml"
            config_file.parent.mkdir(exist_ok=True)
            with open(config_file, 'w') as f:
                yaml.dump(config, f, indent=2)
            
            print(f"Configuration saved to: {config_file}")
        
        elif args.mode == 'monitor':
            watch_paths = args.watch_logs or [
                str(Path(args.project_path) / "logs"),
                "/var/log/rag-assistant"
            ]
            
            print(f"Starting real-time log monitoring...")
            print(f"Watch paths: {watch_paths}")
            
            # Filter existing paths
            existing_paths = [path for path in watch_paths if Path(path).exists()]
            if not existing_paths:
                print("No valid watch paths found")
                return
            
            log_analyzer.start_real_time_monitoring(existing_paths)
            
        elif args.mode == 'analyze':
            # Parse timeframe
            if 'hour' in args.timeframe:
                hours = int(args.timeframe.replace('hours', '').replace('hour', ''))
            elif 'day' in args.timeframe:
                hours = int(args.timeframe.replace('days', '').replace('day', '')) * 24
            else:
                hours = 24
            
            log_files = args.log_files or []
            if not log_files:
                # Find log files automatically
                log_dir = Path(args.project_path) / "logs"
                if log_dir.exists():
                    log_files = [str(f) for f in log_dir.rglob("*.log")]
            
            if not log_files:
                print("No log files found for analysis")
                return
            
            print(f"Analyzing {len(log_files)} log files over {hours} hours...")
            
            results = log_analyzer.analyze_historical_logs(log_files, hours)
            
            print(f"\nAnalysis Results:")
            print(f"Processed entries: {results['processed_entries']}")
            print(f"Total errors: {results['error_analysis']['total_errors']}")
            print(f"Anomalies detected: {results['anomaly_analysis']['total_anomalies']}")
            print(f"Performance metrics: {results['performance_analysis']['metrics_found']}")
            
            if args.generate_report:
                # Generate detailed report
                report = f"""
Log Analysis Report
Generated: {datetime.now().isoformat()}

SUMMARY:
- Analysis Period: {results['analysis_period']['duration_hours']} hours
- Processed Entries: {results['processed_entries']}
- Total Errors: {results['error_analysis']['total_errors']}
- Anomalies Detected: {results['anomaly_analysis']['total_anomalies']}

ERROR ANALYSIS:
Top Error Types:
"""
                
                for error_type, count in list(results['error_analysis']['error_types'].items())[:5]:
                    report += f"  - {error_type}: {count}\n"
                
                if results['performance_analysis']['response_time_stats']:
                    stats = results['performance_analysis']['response_time_stats']
                    report += f"""
PERFORMANCE METRICS:
Response Time Statistics:
  - Mean: {stats.get('mean', 0):.2f}ms
  - P95: {stats.get('p95', 0):.2f}ms
  - P99: {stats.get('p99', 0):.2f}ms
  - Max: {stats.get('max', 0):.2f}ms
"""
                
                report_file = (Path(args.project_path) / "monitoring" / "reports" / 
                              f"log_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt")
                with open(report_file, 'w') as f:
                    f.write(report)
                
                print(f"\nDetailed report saved to: {report_file}")
        
        print("\nLog analysis session completed successfully")
        
    except Exception as e:
        print(f"[ERROR] Log analysis failed: {e}")
        raise


if __name__ == "__main__":
    main()