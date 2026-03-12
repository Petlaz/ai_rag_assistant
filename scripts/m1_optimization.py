#!/usr/bin/env python3
"""
M1 Mac Optimization Utilities - Phase 2 MLOps Testing
====================================================

Utilities for optimizing RAG system performance on Apple M1/M2 Macs.
Includes memory management, ARM64 optimization, and hardware-specific tuning.

Usage:
    from scripts.m1_optimization import M1Optimizer
    
    optimizer = M1Optimizer()
    optimizer.optimize_for_embeddings()
    optimizer.optimize_pytorch_settings()
    optimizer.monitor_performance()

Author: AI RAG Assistant Team
Date: March 2026
Phase: 2 - Model Optimization
"""

import logging
import os
import platform
import psutil
import time
import gc
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any
import json

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class SystemInfo:
    """System information for M1/M2 Macs."""
    cpu_model: str
    cpu_cores: int
    cpu_cores_performance: int
    cpu_cores_efficiency: int
    total_memory_gb: float
    available_memory_gb: float
    unified_memory: bool
    has_neural_engine: bool
    pytorch_mps_available: bool
    torch_version: str
    

@dataclass
class PerformanceMetrics:
    """Performance metrics for optimization tracking."""
    timestamp: str
    cpu_usage_percent: float
    memory_usage_gb: float
    memory_usage_percent: float
    gpu_memory_usage_mb: float  # If available
    temperature_celsius: float  # If available
    power_usage_watts: float    # If available
    inference_time_ms: float
    throughput_qps: float


class M1Optimizer:
    """Optimizer for M1/M2 Mac hardware."""
    
    def __init__(self, max_memory_gb: float = 6.0, target_temp_celsius: float = 70.0):
        self.max_memory_gb = max_memory_gb
        self.target_temp_celsius = target_temp_celsius
        self.system_info = self.get_system_info()
        self.optimization_history = []
        
        logger.info("M1 Optimizer initialized")
        self.log_system_info()
        
    def get_system_info(self) -> SystemInfo:
        """Get comprehensive system information."""
        # Detect Apple Silicon
        is_apple_silicon = platform.machine() in ['arm64', 'aarch64']
        
        # CPU information
        cpu_count = psutil.cpu_count()
        cpu_physical = psutil.cpu_count(logical=False)
        
        # Estimate performance vs efficiency cores for Apple Silicon
        if is_apple_silicon:
            if cpu_count >= 10:  # M1 Pro/Max/Ultra
                perf_cores = 8
                eff_cores = cpu_count - 8
            elif cpu_count == 8:  # M1
                perf_cores = 4
                eff_cores = 4
            else:
                perf_cores = cpu_physical
                eff_cores = cpu_count - cpu_physical
        else:
            perf_cores = cpu_physical
            eff_cores = 0
            
        # Memory information
        memory = psutil.virtual_memory()
        total_memory_gb = memory.total / (1024**3)
        available_memory_gb = memory.available / (1024**3)
        
        # PyTorch MPS availability
        pytorch_mps_available = False
        torch_version = "N/A"
        if TORCH_AVAILABLE:
            torch_version = torch.__version__
            pytorch_mps_available = torch.backends.mps.is_available() if hasattr(torch.backends, 'mps') else False
            
        return SystemInfo(
            cpu_model=platform.processor() or platform.machine(),
            cpu_cores=cpu_count,
            cpu_cores_performance=perf_cores,
            cpu_cores_efficiency=eff_cores,
            total_memory_gb=total_memory_gb,
            available_memory_gb=available_memory_gb,
            unified_memory=is_apple_silicon,  # Apple Silicon uses unified memory
            has_neural_engine=is_apple_silicon,
            pytorch_mps_available=pytorch_mps_available,
            torch_version=torch_version
        )
        
    def log_system_info(self):
        """Log system information."""
        info = self.system_info
        logger.info(f"System: {info.cpu_model}")
        logger.info(f"Total CPU Cores: {info.cpu_cores} (P: {info.cpu_cores_performance}, E: {info.cpu_cores_efficiency})")
        logger.info(f"Memory: {info.total_memory_gb:.1f}GB total, {info.available_memory_gb:.1f}GB available")
        logger.info(f"Unified Memory: {info.unified_memory}")
        logger.info(f"Neural Engine: {info.has_neural_engine}")
        logger.info(f"PyTorch MPS: {info.pytorch_mps_available}")
        logger.info(f"PyTorch Version: {info.torch_version}")
        
    def optimize_pytorch_settings(self) -> Dict[str, Any]:
        """Optimize PyTorch settings for M1/M2."""
        if not TORCH_AVAILABLE:
            logger.warning("PyTorch not available, skipping PyTorch optimization")
            return {'status': 'skipped', 'reason': 'PyTorch not available'}
            
        optimizations = {}
        
        # Set MPS device if available
        if self.system_info.pytorch_mps_available:
            device = torch.device("mps")
            logger.info("Using MPS (Metal Performance Shaders) acceleration")
            optimizations['device'] = 'mps'
        else:
            device = torch.device("cpu")
            logger.info("Using CPU (MPS not available)")
            optimizations['device'] = 'cpu'
            
        # Memory optimization
        if self.system_info.unified_memory:
            # Set memory fraction for unified memory
            memory_fraction = min(0.7, self.max_memory_gb / self.system_info.total_memory_gb)
            optimizations['memory_fraction'] = memory_fraction
            logger.info(f"Set memory fraction: {memory_fraction:.2f}")
            
        # Thread optimization for Apple Silicon
        if self.system_info.cpu_cores_performance > 0:
            # Use performance cores for compute-intensive tasks
            torch.set_num_threads(self.system_info.cpu_cores_performance)
            optimizations['num_threads'] = self.system_info.cpu_cores_performance
            logger.info(f"Set PyTorch threads: {self.system_info.cpu_cores_performance}")
            
        # Optimize for inference
        torch.set_grad_enabled(False)  # Disable gradient computation
        optimizations['grad_enabled'] = False
        
        # Set environment variables
        env_vars = {
            'PYTORCH_MPS_HIGH_WATERMARK_RATIO': '0.0',  # Disable memory caching for MPS
            'OMP_NUM_THREADS': str(self.system_info.cpu_cores_performance),
            'MKL_NUM_THREADS': str(self.system_info.cpu_cores_performance)
        }
        
        for var, value in env_vars.items():
            os.environ[var] = value
            optimizations[var] = value
            
        logger.info("PyTorch optimization completed")
        return optimizations
        
    def optimize_for_embeddings(self, model_size_mb: float = 100) -> Dict[str, Any]:
        """Optimize settings specifically for embedding model inference."""
        optimizations = {}
        
        # Calculate optimal batch size based on available memory
        available_memory_mb = self.system_info.available_memory_gb * 1024
        
        # Reserve memory for system and other processes
        usable_memory_mb = available_memory_mb * 0.6  # Use 60% of available
        
        # Estimate memory per embedding
        # Rough estimate: model_size + (embedding_dim * batch_size * 4 bytes)
        embedding_dim = 384  # Common embedding dimension
        memory_per_item = (embedding_dim * 4) / 1024  # Convert to MB
        
        # Calculate optimal batch size
        memory_for_batches = usable_memory_mb - model_size_mb
        optimal_batch_size = int(memory_for_batches / memory_per_item)
        optimal_batch_size = max(1, min(optimal_batch_size, 32))  # Clamp between 1-32
        
        optimizations['optimal_batch_size'] = optimal_batch_size
        optimizations['estimated_memory_usage_mb'] = model_size_mb + (optimal_batch_size * memory_per_item)
        
        # Set inference mode optimizations
        if TORCH_AVAILABLE:
            torch.set_grad_enabled(False)
            optimizations['inference_mode'] = True
            
        logger.info(f"Embedding optimization complete:")
        logger.info(f"  - Optimal batch size: {optimal_batch_size}")
        logger.info(f"  - Estimated memory usage: {optimizations['estimated_memory_usage_mb']:.1f}MB")
        
        return optimizations
        
    def get_performance_metrics(self) -> PerformanceMetrics:
        """Get current performance metrics."""
        # CPU and memory metrics
        cpu_usage = psutil.cpu_percent(interval=1)
        memory = psutil.virtual_memory()
        memory_usage_gb = (memory.total - memory.available) / (1024**3)
        memory_usage_percent = memory.percent
        
        # GPU memory (if MPS available)
        gpu_memory_usage_mb = 0
        if TORCH_AVAILABLE and self.system_info.pytorch_mps_available:
            try:
                # MPS memory tracking is limited, estimate based on model usage
                gpu_memory_usage_mb = 100  # Placeholder
            except Exception:
                pass
                
        # Temperature and power (limited on macOS)
        temperature_celsius = 0.0
        power_usage_watts = 0.0
        
        # Inference metrics (to be updated by calling code)
        inference_time_ms = 0.0
        throughput_qps = 0.0
        
        return PerformanceMetrics(
            timestamp=time.strftime('%Y-%m-%d %H:%M:%S'),
            cpu_usage_percent=cpu_usage,
            memory_usage_gb=memory_usage_gb,
            memory_usage_percent=memory_usage_percent,
            gpu_memory_usage_mb=gpu_memory_usage_mb,
            temperature_celsius=temperature_celsius,
            power_usage_watts=power_usage_watts,
            inference_time_ms=inference_time_ms,
            throughput_qps=throughput_qps
        )
        
    def monitor_performance(self, duration_seconds: int = 60) -> List[PerformanceMetrics]:
        """Monitor performance over time."""
        logger.info(f"Starting performance monitoring for {duration_seconds} seconds")
        
        metrics_history = []
        start_time = time.time()
        
        while time.time() - start_time < duration_seconds:
            metrics = self.get_performance_metrics()
            metrics_history.append(metrics)
            
            # Log current metrics
            logger.info(f"CPU: {metrics.cpu_usage_percent:.1f}%, "
                       f"Memory: {metrics.memory_usage_gb:.1f}GB ({metrics.memory_usage_percent:.1f}%)")
            
            time.sleep(5)  # Sample every 5 seconds
            
        logger.info("Performance monitoring completed")
        return metrics_history
        
    def optimize_garbage_collection(self) -> Dict[str, Any]:
        """Optimize garbage collection for memory efficiency."""
        optimizations = {}
        
        # Force garbage collection
        collected = gc.collect()
        optimizations['objects_collected'] = collected
        
        # Set garbage collection thresholds for Apple Silicon
        # More frequent collection to prevent memory pressure
        original_thresholds = gc.get_threshold()
        optimizations['original_gc_thresholds'] = original_thresholds
        
        if self.system_info.unified_memory:
            # Smaller thresholds for unified memory
            new_thresholds = (500, 8, 8)  # More aggressive collection
            gc.set_threshold(*new_thresholds)
            optimizations['new_gc_thresholds'] = new_thresholds
            
        # Clear PyTorch caches if available
        if TORCH_AVAILABLE:
            torch.cuda.empty_cache()  # Clear CUDA cache (no-op on MPS)
            optimizations['pytorch_cache_cleared'] = True
            
        logger.info(f"Garbage collection optimization complete: collected {collected} objects")
        return optimizations
        
    def get_optimal_worker_count(self, task_type: str = "embedding") -> int:
        """Get optimal number of workers for different tasks."""
        if task_type == "embedding":
            # CPU-bound task, use performance cores
            return max(1, self.system_info.cpu_cores_performance - 1)  # Leave 1 core for system
        elif task_type == "io":
            # I/O-bound task, can use more workers
            return max(1, self.system_info.cpu_cores - 2)  # Leave 2 cores for system
        else:
            # Default: conservative approach
            return max(1, self.system_info.cpu_cores // 2)
            
    def check_thermal_throttling(self) -> Dict[str, Any]:
        """Check for thermal throttling indicators."""
        # Note: macOS doesn't provide direct thermal throttling info
        # We use CPU frequency and usage patterns as proxies
        
        cpu_freq = psutil.cpu_freq()
        cpu_usage = psutil.cpu_percent(interval=2)
        
        throttling_indicators = {
            'cpu_frequency_mhz': cpu_freq.current if cpu_freq else 0,
            'cpu_usage_percent': cpu_usage,
            'likely_throttling': False,
            'recommendations': []
        }
        
        # Heuristics for throttling detection
        if cpu_freq and cpu_freq.current < cpu_freq.max * 0.8:
            throttling_indicators['likely_throttling'] = True
            throttling_indicators['recommendations'].append("CPU frequency reduced, possible thermal throttling")
            
        if cpu_usage > 90:
            throttling_indicators['recommendations'].append("High CPU usage detected")
            
        return throttling_indicators
        
    def optimize_for_model_size(self, model_size_mb: float) -> Dict[str, Any]:
        """Optimize settings based on model size."""
        optimizations = {}
        
        # Memory-based optimizations
        if model_size_mb > 1000:  # Large model (>1GB)
            optimizations['batch_size'] = 1
            optimizations['recommended_approach'] = "sequential_processing"
            optimizations['memory_mapping'] = True
        elif model_size_mb > 500:  # Medium model (500MB-1GB)
            optimizations['batch_size'] = 2
            optimizations['recommended_approach'] = "small_batch_processing"
            optimizations['memory_mapping'] = False
        else:  # Small model (<500MB)
            optimizations['batch_size'] = self.optimize_for_embeddings(model_size_mb)['optimal_batch_size']
            optimizations['recommended_approach'] = "batch_processing"
            optimizations['memory_mapping'] = False
            
        # Calculate memory requirements
        total_memory_needed = model_size_mb + (optimizations['batch_size'] * 10)  # 10MB per batch item
        optimizations['total_memory_needed_mb'] = total_memory_needed
        optimizations['memory_available'] = total_memory_needed < (self.system_info.available_memory_gb * 1024 * 0.8)
        
        logger.info(f"Model size optimization for {model_size_mb}MB model:")
        logger.info(f"  - Recommended batch size: {optimizations['batch_size']}")
        logger.info(f"  - Processing approach: {optimizations['recommended_approach']}")
        logger.info(f"  - Total memory needed: {total_memory_needed:.1f}MB")
        
        return optimizations
        
    def save_optimization_profile(self, profile_name: str, optimizations: Dict[str, Any]) -> Path:
        """Save optimization profile for reuse."""
        profile_path = Path(f"configs/m1_optimization_{profile_name}.json")
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        
        profile_data = {
            'profile_name': profile_name,
            'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
            'system_info': asdict(self.system_info),
            'optimizations': optimizations,
            'performance_targets': {
                'max_memory_gb': self.max_memory_gb,
                'target_temp_celsius': self.target_temp_celsius
            }
        }
        
        with open(profile_path, 'w') as f:
            json.dump(profile_data, f, indent=2)
            
        logger.info(f"Optimization profile saved: {profile_path}")
        return profile_path
        
    def load_optimization_profile(self, profile_path: Path) -> Dict[str, Any]:
        """Load previously saved optimization profile."""
        try:
            with open(profile_path, 'r') as f:
                profile_data = json.load(f)
                
            logger.info(f"Loaded optimization profile: {profile_path}")
            return profile_data['optimizations']
            
        except FileNotFoundError:
            logger.warning(f"Optimization profile not found: {profile_path}")
            return {}
        except (json.JSONDecodeError, KeyError) as e:
            logger.error(f"Error loading optimization profile: {e}")
            return {}
            
    def benchmark_inference_performance(self, model_function, test_data: List, 
                                      batch_sizes: List[int] = [1, 2, 4, 8, 16]) -> Dict[str, Any]:
        """Benchmark inference performance with different batch sizes."""
        logger.info("Starting inference performance benchmark")
        
        results = {}
        
        for batch_size in batch_sizes:
            if batch_size > len(test_data):
                continue
                
            logger.info(f"Testing batch size: {batch_size}")
            
            # Prepare batches
            batches = [test_data[i:i+batch_size] for i in range(0, len(test_data), batch_size)]
            
            # Benchmark
            start_time = time.time()
            total_items = 0
            
            for batch in batches[:5]:  # Test first 5 batches
                try:
                    before_mem = self.get_performance_metrics().memory_usage_gb
                    
                    # Run inference
                    model_function(batch)
                    
                    after_mem = self.get_performance_metrics().memory_usage_gb
                    total_items += len(batch)
                    
                    # Force garbage collection
                    gc.collect()
                    
                except Exception as e:
                    logger.warning(f"Batch size {batch_size} failed: {e}")
                    break
                    
            end_time = time.time()
            
            if total_items > 0:
                duration = end_time - start_time
                throughput = total_items / duration
                
                results[batch_size] = {
                    'throughput_items_per_second': throughput,
                    'avg_time_per_item_ms': (duration / total_items) * 1000,
                    'total_duration_seconds': duration,
                    'items_processed': total_items,
                    'memory_usage_increase_mb': (after_mem - before_mem) * 1024
                }
                
                logger.info(f"Batch size {batch_size}: {throughput:.1f} items/sec")
                
        # Find optimal batch size
        if results:
            optimal_batch = max(results.keys(), key=lambda k: results[k]['throughput_items_per_second'])
            results['optimal_batch_size'] = optimal_batch
            results['optimal_throughput'] = results[optimal_batch]['throughput_items_per_second']
            
        logger.info(f"Benchmark completed. Optimal batch size: {results.get('optimal_batch_size', 'N/A')}")
        return results


def create_m1_optimization_script():
    """Create a standalone optimization script."""
    script_content = '''#!/usr/bin/env python3
"""
M1 Mac Optimization Script
Run this script to optimize your system for RAG operations.
"""

from m1_optimization import M1Optimizer

def main():
    print("🚀 Optimizing M1 Mac for RAG Assistant...")
    
    optimizer = M1Optimizer(max_memory_gb=6.0)
    
    # Run optimizations
    print("\\n1. Optimizing PyTorch settings...")
    pytorch_opts = optimizer.optimize_pytorch_settings()
    
    print("\\n2. Optimizing for embedding models...")
    embedding_opts = optimizer.optimize_for_embeddings(model_size_mb=100)
    
    print("\\n3. Optimizing garbage collection...")
    gc_opts = optimizer.optimize_garbage_collection()
    
    print("\\n4. Checking thermal status...")
    thermal_status = optimizer.check_thermal_throttling()
    
    # Save profile
    all_optimizations = {
        'pytorch': pytorch_opts,
        'embeddings': embedding_opts,
        'garbage_collection': gc_opts,
        'thermal_status': thermal_status
    }
    
    profile_path = optimizer.save_optimization_profile('default', all_optimizations)
    
    print(f"\\n✅ Optimization complete!")
    print(f"📋 Profile saved to: {profile_path}")
    print(f"💡 Recommended batch size: {embedding_opts['optimal_batch_size']}")
    
    if thermal_status['likely_throttling']:
        print("⚠️  Thermal throttling detected. Consider reducing workload.")

if __name__ == '__main__':
    main()
'''
    
    script_path = Path("scripts/optimize_m1.py")
    with open(script_path, 'w') as f:
        f.write(script_content)
        
    # Make executable
    os.chmod(script_path, 0o755)
    
    return script_path


if __name__ == '__main__':
    # Quick test of M1 optimization utilities
    optimizer = M1Optimizer()
    
    print("\\n=== M1 Mac Optimization Test ===")
    
    # Test optimizations
    pytorch_opts = optimizer.optimize_pytorch_settings()
    print(f"PyTorch optimizations: {pytorch_opts}")
    
    embedding_opts = optimizer.optimize_for_embeddings()
    print(f"Embedding optimizations: {embedding_opts}")
    
    # Save test profile
    profile_path = optimizer.save_optimization_profile('test', {
        'pytorch': pytorch_opts,
        'embeddings': embedding_opts
    })
    
    print(f"\\nTest completed. Profile saved: {profile_path}")