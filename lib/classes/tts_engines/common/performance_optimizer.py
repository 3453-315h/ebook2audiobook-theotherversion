import torch
import gc
import time
import psutil
import numpy as np
from typing import Optional, Dict, Any, Callable
from functools import wraps
import warnings

from lib.conf import (
    enable_torch_compile, enable_cuda_graphs, enable_memory_profiling,
    enable_performance_monitoring, cuda_memory_fraction, batch_size_optimization,
    gpu_memory_strategy, cuda_benchmark_mode, cuda_deterministic_mode,
    cuda_tf32_enabled, cuda_fp16_reduction, torch_compile_mode, torch_compile_dynamic,
    min_vram_for_optimization, max_batch_size, min_batch_size
)

class PerformanceOptimizer:
    """
    Advanced performance optimization utilities for TTS engines.
    Handles torch compilation, CUDA graphs, memory management, and batch optimization.
    """

    def __init__(self):
        self.memory_profile = []
        self.performance_metrics = []
        self.cuda_graphs_cache = {}
        self.compile_cache = {}
        self.last_gc_time = 0
        self.gc_interval = 60  # seconds between GC calls

    def setup_cuda_environment(self) -> None:
        """Configure CUDA environment for optimal performance"""
        if torch.cuda.is_available():
            # Set CUDA memory fraction
            torch.cuda.set_per_process_memory_fraction(cuda_memory_fraction)

            # Configure CUDA backends
            torch.backends.cudnn.enabled = True
            torch.backends.cudnn.benchmark = cuda_benchmark_mode
            torch.backends.cudnn.deterministic = cuda_deterministic_mode
            torch.backends.cudnn.allow_tf32 = cuda_tf32_enabled

            if cuda_fp16_reduction:
                torch.backends.cuda.matmul.allow_fp16_reduced_precision_reduction = True

            # Set memory allocation strategy based on configuration
            self._set_memory_strategy()

    def _set_memory_strategy(self) -> None:
        """Set memory allocation strategy based on gpu_memory_strategy setting"""
        if gpu_memory_strategy == "aggressive":
            # Aggressive strategy: allow more memory usage for better performance
            torch.cuda.set_per_process_memory_fraction(max(0.8, cuda_memory_fraction))
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:64,garbage_collection_threshold:0.8'
        elif gpu_memory_strategy == "conservative":
            # Conservative strategy: limit memory usage to prevent OOM
            torch.cuda.set_per_process_memory_fraction(min(0.7, cuda_memory_fraction))
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:16,garbage_collection_threshold:0.5'
        else:
            # Balanced strategy: default settings
            os.environ['PYTORCH_CUDA_ALLOC_CONF'] = 'max_split_size_mb:32,garbage_collection_threshold:0.6'

    def optimize_model(self, model: torch.nn.Module, example_inputs: Optional[Any] = None) -> torch.nn.Module:
        """
        Optimize model using torch.compile() and other performance techniques

        Args:
            model: The model to optimize
            example_inputs: Example inputs for tracing/compilation

        Returns:
            Optimized model
        """
        if not enable_torch_compile:
            return model

        try:
            # Apply torch.compile with appropriate mode
            compile_mode = self._get_compile_mode()

            if torch_compile_dynamic:
                # Dynamic compilation for variable input sizes
                optimized_model = torch.compile(
                    model,
                    mode=compile_mode,
                    dynamic=True,
                    fullgraph=True
                )
            else:
                # Static compilation
                optimized_model = torch.compile(
                    model,
                    mode=compile_mode,
                    fullgraph=True
                )

            print(f"✅ Model optimized with torch.compile (mode: {compile_mode})")
            return optimized_model

        except Exception as e:
            warnings.warn(f"⚠️  torch.compile() failed: {e}. Falling back to original model.")
            return model

    def _get_compile_mode(self) -> str:
        """Get the appropriate torch compile mode based on configuration"""
        if torch_compile_mode == "reduce-overhead":
            return "reduce-overhead"
        elif torch_compile_mode == "max-autotune":
            return "max-autotune"
        else:
            return "default"

    def create_cuda_graph(self, model: torch.nn.Module, example_inputs: Any, key: str) -> Callable:
        """
        Create and cache CUDA graphs for faster inference

        Args:
            model: The model to create graphs for
            example_inputs: Example inputs for graph capture
            key: Cache key for the graph

        Returns:
            Function that executes the cached CUDA graph
        """
        if not enable_cuda_graphs or not torch.cuda.is_available():
            return None

        if key in self.cuda_graphs_cache:
            return self.cuda_graphs_cache[key]

        try:
            # Warmup runs
            for _ in range(3):
                with torch.no_grad():
                    _ = model(*example_inputs)

            # Create static inputs for graph capture
            static_inputs = []
            for input_tensor in example_inputs:
                if isinstance(input_tensor, torch.Tensor):
                    static_inputs.append(input_tensor.clone())
                else:
                    static_inputs.append(input_tensor)

            # Capture CUDA graph
            static_inputs = tuple(static_inputs)
            s = torch.cuda.Stream()
            s.wait_stream(torch.cuda.current_stream())
            with torch.cuda.stream(s):
                with torch.no_grad():
                    static_outputs = model(*static_inputs)

            # Create graph
            graph = torch.cuda.CUDAGraph()
            with torch.cuda.graph(graph):
                with torch.no_grad():
                    static_outputs = model(*static_inputs)

            def run_graph(inputs):
                # Convert inputs to match graph expectations
                graph_inputs = []
                for i, input_tensor in enumerate(inputs):
                    if isinstance(input_tensor, torch.Tensor):
                        # Ensure tensor is on correct device and has correct shape
                        graph_inputs.append(input_tensor.to(static_inputs[i].device))
                    else:
                        graph_inputs.append(input_tensor)

                # Execute graph
                with torch.no_grad():
                    outputs = graph.replay()

                return outputs

            self.cuda_graphs_cache[key] = run_graph
            print(f"✅ CUDA graph created and cached for key: {key}")
            return run_graph

        except Exception as e:
            warnings.warn(f"⚠️  CUDA graph creation failed: {e}")
            return None

    def optimize_batch_size(self, current_batch_size: int, vram_available: float) -> int:
        """
        Dynamically optimize batch size based on available VRAM and performance settings

        Args:
            current_batch_size: Current batch size
            vram_available: Available VRAM in GB

        Returns:
            Optimized batch size
        """
        if not batch_size_optimization:
            return current_batch_size

        # Base optimization based on VRAM
        if vram_available >= 16.0:
            base_batch_size = max_batch_size
        elif vram_available >= 8.0:
            base_batch_size = max(512, min_batch_size)
        elif vram_available >= 4.0:
            base_batch_size = max(256, min_batch_size)
        else:
            base_batch_size = max(128, min_batch_size)

        # Apply memory strategy adjustments
        if gpu_memory_strategy == "aggressive" and vram_available >= min_vram_for_optimization:
            optimized_batch_size = min(base_batch_size * 2, max_batch_size)
        elif gpu_memory_strategy == "conservative":
            optimized_batch_size = max(base_batch_size // 2, min_batch_size)
        else:
            optimized_batch_size = base_batch_size

        # Ensure we don't exceed reasonable limits
        return max(min_batch_size, min(optimized_batch_size, max_batch_size))

    def smart_memory_cleanup(self, force: bool = False) -> None:
        """
        Intelligent memory cleanup with rate limiting to avoid performance impact

        Args:
            force: Force cleanup regardless of timing
        """
        current_time = time.time()

        # Rate limit GC calls to avoid performance impact
        if not force and (current_time - self.last_gc_time) < self.gc_interval:
            return

        self.last_gc_time = current_time

        # Python garbage collection
        gc.collect()

        # CUDA memory cleanup if available
        if torch.cuda.is_available():
            torch.cuda.empty_cache()
            torch.cuda.ipc_collect()

        if enable_memory_profiling:
            self._log_memory_usage()

    def _log_memory_usage(self) -> None:
        """Log memory usage for profiling"""
        if not enable_memory_profiling:
            return

        mem_info = {
            'timestamp': time.time(),
            'cpu_memory': psutil.virtual_memory().used / (1024 ** 3),  # GB
            'cpu_percent': psutil.virtual_memory().percent,
            'process_memory': psutil.Process().memory_info().rss / (1024 ** 3)  # GB
        }

        if torch.cuda.is_available():
            mem_info.update({
                'cuda_memory_allocated': torch.cuda.memory_allocated() / (1024 ** 3),
                'cuda_memory_reserved': torch.cuda.memory_reserved() / (1024 ** 3),
                'cuda_memory_cached': torch.cuda.memory_cached() / (1024 ** 3),
                'cuda_utilization': torch.cuda.utilization()
            })

        self.memory_profile.append(mem_info)

        # Keep only recent history to limit memory usage
        if len(self.memory_profile) > 100:
            self.memory_profile = self.memory_profile[-100:]

    def get_memory_profile(self) -> Dict:
        """Get current memory profile data"""
        return {
            'memory_profile': self.memory_profile,
            'current_memory': self._get_current_memory_stats()
        }

    def _get_current_memory_stats(self) -> Dict:
        """Get current memory statistics"""
        stats = {
            'cpu_total': psutil.virtual_memory().total / (1024 ** 3),
            'cpu_available': psutil.virtual_memory().available / (1024 ** 3),
            'cpu_used': psutil.virtual_memory().used / (1024 ** 3),
            'cpu_percent': psutil.virtual_memory().percent,
            'process_rss': psutil.Process().memory_info().rss / (1024 ** 3)
        }

        if torch.cuda.is_available():
            stats.update({
                'cuda_total': torch.cuda.get_device_properties(0).total_memory / (1024 ** 3),
                'cuda_allocated': torch.cuda.memory_allocated() / (1024 ** 3),
                'cuda_reserved': torch.cuda.memory_reserved() / (1024 ** 3),
                'cuda_cached': torch.cuda.memory_cached() / (1024 ** 3),
                'cuda_utilization': torch.cuda.utilization()
            })

        return stats

    def start_performance_monitoring(self, model_name: str = "TTS") -> Callable:
        """
        Create a performance monitoring decorator

        Args:
            model_name: Name of the model being monitored

        Returns:
            Decorator function
        """
        if not enable_performance_monitoring:
            return lambda f: f

        def decorator(func):
            @wraps(func)
            def wrapper(*args, **kwargs):
                start_time = time.time()
                start_mem = self._get_current_memory_stats()

                try:
                    result = func(*args, **kwargs)
                finally:
                    end_time = time.time()
                    end_mem = self._get_current_memory_stats()

                    # Calculate metrics
                    duration = end_time - start_time
                    memory_change = {
                        'cpu_used_change': end_mem['cpu_used'] - start_mem['cpu_used'],
                        'process_rss_change': end_mem['process_rss'] - start_mem['process_rss']
                    }

                    if torch.cuda.is_available():
                        memory_change.update({
                            'cuda_allocated_change': end_mem['cuda_allocated'] - start_mem['cuda_allocated'],
                            'cuda_reserved_change': end_mem['cuda_reserved'] - start_mem['cuda_reserved']
                        })

                    # Store metrics
                    self.performance_metrics.append({
                        'timestamp': time.time(),
                        'model': model_name,
                        'function': func.__name__,
                        'duration_seconds': duration,
                        'memory_change_gb': memory_change,
                        'input_args': len(args),
                        'input_kwargs': len(kwargs)
                    })

                    # Keep only recent history
                    if len(self.performance_metrics) > 100:
                        self.performance_metrics = self.performance_metrics[-100:]

                    print(f"📊 {model_name}.{func.__name__}: {duration:.3f}s | "
                          f"CPU: {memory_change['cpu_used_change']:+.2f}GB | "
                          f"Process: {memory_change['process_rss_change']:+.2f}GB")

                return result

            return wrapper

        return decorator

    def get_performance_metrics(self) -> Dict:
        """Get accumulated performance metrics"""
        return {
            'metrics': self.performance_metrics,
            'summary': self._generate_performance_summary()
        }

    def _generate_performance_summary(self) -> Dict:
        """Generate summary statistics from performance metrics"""
        if not self.performance_metrics:
            return {}

        durations = [m['duration_seconds'] for m in self.performance_metrics]
        cpu_changes = [m['memory_change_gb']['cpu_used_change'] for m in self.performance_metrics]
        process_changes = [m['memory_change_gb']['process_rss_change'] for m in self.performance_metrics]

        return {
            'total_calls': len(self.performance_metrics),
            'avg_duration': np.mean(durations),
            'median_duration': np.median(durations),
            'min_duration': np.min(durations),
            'max_duration': np.max(durations),
            'avg_cpu_change': np.mean(cpu_changes),
            'avg_process_change': np.mean(process_changes),
            'total_time': np.sum(durations),
            'calls_per_second': len(self.performance_metrics) / (self.performance_metrics[-1]['timestamp'] - self.performance_metrics[0]['timestamp'])
                if len(self.performance_metrics) > 1 else 0
        }

    def clear_cache(self) -> None:
        """Clear all optimization caches"""
        self.cuda_graphs_cache.clear()
        self.compile_cache.clear()
        self.smart_memory_cleanup(force=True)

    def get_optimization_status(self) -> Dict:
        """Get current optimization status"""
        return {
            'torch_compile_enabled': enable_torch_compile,
            'cuda_graphs_enabled': enable_cuda_graphs,
            'memory_profiling_enabled': enable_memory_profiling,
            'performance_monitoring_enabled': enable_performance_monitoring,
            'batch_optimization_enabled': batch_size_optimization,
            'gpu_memory_strategy': gpu_memory_strategy,
            'cuda_memory_fraction': cuda_memory_fraction,
            'cuda_graphs_cached': len(self.cuda_graphs_cache),
            'memory_profile_size': len(self.memory_profile),
            'performance_metrics_size': len(self.performance_metrics)
        }

# Global performance optimizer instance
performance_optimizer = PerformanceOptimizer()

def optimize_inference_context():
    """
    Context manager for optimized inference operations.
    Handles torch.no_grad(), memory cleanup, and performance monitoring.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            # Setup optimization context
            torch_context = torch.inference_mode() if hasattr(torch, 'inference_mode') else torch.no_grad()

            try:
                with torch_context:
                    # Apply memory strategy
                    performance_optimizer.smart_memory_cleanup()

                    # Execute function
                    result = func(*args, **kwargs)

                    # Post-execution cleanup
                    performance_optimizer.smart_memory_cleanup()

                    return result
            finally:
                if enable_performance_monitoring:
                    duration = time.time() - start_time
                    print(f"🚀 {func.__name__}: {duration:.3f}s")

        return wrapper
    return decorator