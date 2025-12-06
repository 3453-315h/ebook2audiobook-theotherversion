#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Advanced Memory Management System for ebook2audiobook
Provides comprehensive memory monitoring, optimization, and cleanup
"""

import os
import gc
import psutil
import torch
import tracemalloc
import time
import logging
import weakref
import threading
import warnings
from typing import Any, Dict, List, Optional, Tuple, Callable, Union
from enum import Enum
from collections import defaultdict
from datetime import datetime
import numpy as np

# Import custom exceptions and error reporting
from lib.classes.exceptions import MemoryError, ProcessingError, ExceptionHandler
from lib.classes.error_reporter import report_error, ErrorReport

class MemoryStrategy(Enum):
    """Memory management strategies"""
    CONSERVATIVE = "conservative"  # Minimal memory usage, frequent cleanup
    BALANCED = "balanced"          # Balanced approach between performance and memory
    AGGRESSIVE = "aggressive"      # Maximize performance, higher memory usage
    AUTO = "auto"                  # Automatic based on system resources

class MemoryThreshold(Enum):
    """Memory threshold levels"""
    CRITICAL = 0.95  # 95% memory usage - emergency cleanup
    HIGH = 0.85      # 85% memory usage - aggressive cleanup
    MEDIUM = 0.75    # 75% memory usage - normal cleanup
    LOW = 0.65       # 65% memory usage - light cleanup
    SAFE = 0.50      # 50% memory usage - optimal range

class MemoryMonitor:
    """
    Advanced memory monitoring system
    Tracks memory usage across different components and provides real-time monitoring
    """

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.system_info = self._get_system_info()
        self.memory_history = []
        self.max_history = 1000  # Keep last 1000 measurements
        self.monitoring_active = False
        self.monitor_thread = None
        self.monitor_interval = 5.0  # seconds
        self.thresholds = {
            'critical': MemoryThreshold.CRITICAL.value,
            'high': MemoryThreshold.HIGH.value,
            'medium': MemoryThreshold.MEDIUM.value,
            'low': MemoryThreshold.LOW.value
        }

    def _get_system_info(self) -> Dict[str, Any]:
        """Get comprehensive system information"""
        try:
            # Get virtual memory info
            vmem = psutil.virtual_memory()

            # Get swap memory info
            swap = psutil.swap_memory() if hasattr(psutil, 'swap_memory') else None

            # Get CPU info
            cpu_count = psutil.cpu_count(logical=True)
            cpu_physical = psutil.cpu_count(logical=False)

            return {
                'total_ram_gb': round(vmem.total / (1024 ** 3), 2),
                'available_ram_gb': round(vmem.available / (1024 ** 3), 2),
                'used_ram_gb': round(vmem.used / (1024 ** 3), 2),
                'ram_usage_percent': vmem.percent,
                'swap_total_gb': round(swap.total / (1024 ** 3), 2) if swap else 0,
                'swap_used_gb': round(swap.used / (1024 ** 3), 2) if swap else 0,
                'swap_free_gb': round(swap.free / (1024 ** 3), 2) if swap else 0,
                'cpu_cores': cpu_count,
                'cpu_physical_cores': cpu_physical,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_get_system_info'})
            return {
                'total_ram_gb': 0,
                'available_ram_gb': 0,
                'used_ram_gb': 0,
                'ram_usage_percent': 0,
                'swap_total_gb': 0,
                'swap_used_gb': 0,
                'swap_free_gb': 0,
                'cpu_cores': 0,
                'cpu_physical_cores': 0,
                'timestamp': datetime.now().isoformat()
            }

    def start_monitoring(self, interval: float = 5.0) -> None:
        """Start continuous memory monitoring"""
        if self.monitoring_active:
            return

        self.monitor_interval = interval
        self.monitoring_active = True

        def monitor_loop():
            """Monitoring loop that runs in background thread"""
            while self.monitoring_active:
                try:
                    # Get current memory usage
                    memory_info = self.get_current_memory_usage()

                    # Store in history
                    self.memory_history.append({
                        'timestamp': datetime.now().isoformat(),
                        'memory_info': memory_info,
                        'system_info': self._get_system_info()
                    })

                    # Keep history size manageable
                    if len(self.memory_history) > self.max_history:
                        self.memory_history.pop(0)

                    # Check thresholds and trigger cleanup if needed
                    self._check_memory_thresholds(memory_info)

                    # Sleep for interval
                    time.sleep(self.monitor_interval)

                except Exception as e:
                    ExceptionHandler.handle_exception(e, {'function': 'monitor_loop'})
                    time.sleep(self.monitor_interval)  # Continue monitoring even if error occurs

        # Start monitoring thread
        self.monitor_thread = threading.Thread(
            target=monitor_loop,
            name="MemoryMonitor",
            daemon=True
        )
        self.monitor_thread.start()

    def stop_monitoring(self) -> None:
        """Stop continuous memory monitoring"""
        self.monitoring_active = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5.0)

    def get_current_memory_usage(self) -> Dict[str, Any]:
        """Get current memory usage statistics"""
        try:
            # Get process memory info
            mem_info = self.process.memory_info()

            # Get GPU memory if available
            gpu_memory = self._get_gpu_memory() if torch.cuda.is_available() else None

            # Get Python memory allocator stats
            python_memory = self._get_python_memory_stats()

            return {
                'rss_mb': round(mem_info.rss / (1024 ** 2), 2),  # Resident Set Size
                'vms_mb': round(mem_info.vms / (1024 ** 2), 2),  # Virtual Memory Size
                'shared_mb': round(mem_info.shared / (1024 ** 2), 2),
                'text_mb': round(mem_info.text / (1024 ** 2), 2),
                'data_mb': round(mem_info.data / (1024 ** 2), 2),
                'percent': self.process.memory_percent(),
                'gpu_memory': gpu_memory,
                'python_memory': python_memory,
                'timestamp': datetime.now().isoformat()
            }
        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'get_current_memory_usage'})
            return {
                'rss_mb': 0,
                'vms_mb': 0,
                'shared_mb': 0,
                'text_mb': 0,
                'data_mb': 0,
                'percent': 0,
                'gpu_memory': None,
                'python_memory': None,
                'timestamp': datetime.now().isoformat()
            }

    def _get_gpu_memory(self) -> Optional[Dict[str, Any]]:
        """Get GPU memory usage if CUDA is available"""
        try:
            if not torch.cuda.is_available():
                return None

            # Get memory info for all GPUs
            gpu_memory = []
            for i in range(torch.cuda.device_count()):
                device = torch.cuda.get_device_properties(i)
                allocated = torch.cuda.memory_allocated(i)
                reserved = torch.cuda.memory_reserved(i)
                free, total = torch.cuda.mem_get_info(i)

                gpu_memory.append({
                    'device_id': i,
                    'device_name': device.name,
                    'total_gb': round(total / (1024 ** 3), 2),
                    'free_gb': round(free / (1024 ** 3), 2),
                    'used_gb': round((total - free) / (1024 ** 3), 2),
                    'allocated_gb': round(allocated / (1024 ** 3), 2),
                    'reserved_gb': round(reserved / (1024 ** 3), 2),
                    'usage_percent': round((total - free) / total * 100, 2)
                })

            return gpu_memory
        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_get_gpu_memory'})
            return None

    def _get_python_memory_stats(self) -> Dict[str, Any]:
        """Get Python memory allocator statistics"""
        try:
            # Get tracemalloc stats if enabled
            tracemalloc_stats = None
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')

                tracemalloc_stats = []
                for stat in top_stats[:10]:  # Top 10 memory consumers
                    tracemalloc_stats.append({
                        'filename': stat.traceback[0].filename,
                        'lineno': stat.traceback[0].lineno,
                        'size_kb': round(stat.size / 1024, 2),
                        'count': stat.count
                    })

            return {
                'gc_objects': len(gc.get_objects()),
                'gc_thresholds': gc.get_threshold(),
                'gc_collections': gc.get_count(),
                'tracemalloc_enabled': tracemalloc.is_tracing(),
                'tracemalloc_stats': tracemalloc_stats
            }
        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_get_python_memory_stats'})
            return {
                'gc_objects': 0,
                'gc_thresholds': (0, 0, 0),
                'gc_collections': 0,
                'tracemalloc_enabled': False,
                'tracemalloc_stats': None
            }

    def _check_memory_thresholds(self, memory_info: Dict[str, Any]) -> None:
        """Check memory thresholds and trigger cleanup if needed"""
        try:
            # Check system memory thresholds
            system_usage = memory_info['percent'] / 100.0
            if system_usage > self.thresholds['critical']:
                self._trigger_memory_cleanup(MemoryStrategy.CONSERVATIVE, "CRITICAL memory threshold exceeded")
            elif system_usage > self.thresholds['high']:
                self._trigger_memory_cleanup(MemoryStrategy.BALANCED, "HIGH memory threshold exceeded")
            elif system_usage > self.thresholds['medium']:
                self._trigger_memory_cleanup(MemoryStrategy.AGGRESSIVE, "MEDIUM memory threshold exceeded")

            # Check GPU memory if available
            if memory_info['gpu_memory']:
                for gpu in memory_info['gpu_memory']:
                    if gpu['usage_percent'] > self.thresholds['critical'] * 100:
                        self._trigger_gpu_cleanup(gpu['device_id'], "CRITICAL GPU memory threshold exceeded")
                    elif gpu['usage_percent'] > self.thresholds['high'] * 100:
                        self._trigger_gpu_cleanup(gpu['device_id'], "HIGH GPU memory threshold exceeded")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_check_memory_thresholds'})

    def _trigger_memory_cleanup(self, strategy: MemoryStrategy, reason: str) -> None:
        """Trigger memory cleanup based on strategy"""
        try:
            # Report the memory issue
            context = {
                'strategy': strategy.value,
                'reason': reason,
                'current_memory': self.get_current_memory_usage()
            }

            report_error(
                MemoryError(
                    message=f"Memory threshold exceeded: {reason}",
                    severity=ErrorSeverity.HIGH,
                    context=context
                ),
                context
            )

            # Perform cleanup based on strategy
            if strategy == MemoryStrategy.CONSERVATIVE:
                self.conservative_cleanup()
            elif strategy == MemoryStrategy.BALANCED:
                self.balanced_cleanup()
            elif strategy == MemoryStrategy.AGGRESSIVE:
                self.aggressive_cleanup()

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_trigger_memory_cleanup'})

    def _trigger_gpu_cleanup(self, device_id: int, reason: str) -> None:
        """Trigger GPU memory cleanup"""
        try:
            # Report the GPU memory issue
            context = {
                'device_id': device_id,
                'reason': reason,
                'gpu_memory': self._get_gpu_memory()
            }

            report_error(
                MemoryError(
                    message=f"GPU memory threshold exceeded: {reason}",
                    severity=ErrorSeverity.HIGH,
                    context=context
                ),
                context
            )

            # Perform GPU cleanup
            self.gpu_memory_cleanup(device_id)

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_trigger_gpu_cleanup'})

    def conservative_cleanup(self) -> None:
        """Perform conservative memory cleanup"""
        try:
            # Force garbage collection
            gc.collect()

            # Clear Python caches
            self._clear_python_caches()

            # Clean up weak references
            self._cleanup_weak_references()

            # Log the cleanup
            logging.info("Performed conservative memory cleanup")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'conservative_cleanup'})

    def balanced_cleanup(self) -> None:
        """Perform balanced memory cleanup"""
        try:
            # Multiple GC passes
            for _ in range(3):
                gc.collect()

            # Clear Python caches
            self._clear_python_caches()

            # Clean up weak references
            self._cleanup_weak_references()

            # Clear module caches
            self._clear_module_caches()

            # Log the cleanup
            logging.info("Performed balanced memory cleanup")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'balanced_cleanup'})

    def aggressive_cleanup(self) -> None:
        """Perform aggressive memory cleanup"""
        try:
            # Multiple GC passes with different generations
            for generation in range(3):
                gc.collect(generation)

            # Clear Python caches
            self._clear_python_caches()

            # Clean up weak references
            self._cleanup_weak_references()

            # Clear module caches
            self._clear_module_caches()

            # Clear import caches
            self._clear_import_caches()

            # Log the cleanup
            logging.info("Performed aggressive memory cleanup")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'aggressive_cleanup'})

    def gpu_memory_cleanup(self, device_id: Optional[int] = None) -> None:
        """Clean up GPU memory"""
        try:
            if not torch.cuda.is_available():
                return

            # Empty CUDA cache
            torch.cuda.empty_cache()

            # If specific device, clean that device
            if device_id is not None and torch.cuda.device_count() > device_id:
                with torch.cuda.device(device_id):
                    torch.cuda.empty_cache()
                    torch.cuda.ipc_collect()

            # Log the cleanup
            logging.info(f"Performed GPU memory cleanup for device {device_id}")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'gpu_memory_cleanup'})

    def _clear_python_caches(self) -> None:
        """Clear various Python caches"""
        try:
            # Clear import caches
            if hasattr(gc, 'clear'):
                gc.clear()

            # Clear warnings registry
            if hasattr(warnings, '_filters_mutated'):
                warnings._filters_mutated()

            # Clear regex cache
            if hasattr(re, '_cache'):
                re._cache.clear()

            # Clear linecache
            import linecache
            linecache.clearcache()

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_clear_python_caches'})

    def _cleanup_weak_references(self) -> None:
        """Clean up weak references"""
        try:
            # Get all weak references
            weak_refs = weakref.WeakValueDictionary()

            # Clear any weak references that are no longer needed
            for ref in list(weak_refs):
                if ref() is None:
                    del weak_refs[ref]

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_cleanup_weak_references'})

    def _clear_module_caches(self) -> None:
        """Clear module-level caches"""
        try:
            # Clear numpy caches
            if hasattr(np, 'getbufsize'):
                np.getbufsize()

            # Clear other module caches as needed
            # This would be extended based on specific modules used

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_clear_module_caches'})

    def _clear_import_caches(self) -> None:
        """Clear import-related caches"""
        try:
            # Clear importlib caches
            import importlib
            if hasattr(importlib, '_bootstrap'):
                importlib.invalidate_caches()

            # Clear module caches
            for module in list(sys.modules.values()):
                if hasattr(module, '__dict__'):
                    module_dict = module.__dict__
                    if '_cache' in module_dict:
                        module_dict['_cache'].clear()

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_clear_import_caches'})

    def get_memory_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get memory usage history"""
        if limit:
            return self.memory_history[-limit:]
        return self.memory_history.copy()

    def generate_memory_report(self) -> ErrorReport:
        """Generate a comprehensive memory report"""
        try:
            current_memory = self.get_current_memory_usage()
            system_info = self._get_system_info()

            # Create memory error for reporting
            memory_error = MemoryError(
                message="Memory usage report generated",
                severity=ErrorSeverity.INFO,
                context={
                    'current_memory': current_memory,
                    'system_info': system_info,
                    'memory_history_count': len(self.memory_history),
                    'monitoring_active': self.monitoring_active
                }
            )

            # Report and return
            return report_error(memory_error, {
                'current_memory': current_memory,
                'system_info': system_info
            })

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'generate_memory_report'})
            return report_error(e)

class MemoryOptimizer:
    """
    Memory optimization system
    Provides strategies for optimizing memory usage in different scenarios
    """

    def __init__(self, strategy: MemoryStrategy = MemoryStrategy.BALANCED):
        self.strategy = strategy
        self.memory_monitor = MemoryMonitor()
        self.optimization_stats = {
            'total_optimizations': 0,
            'memory_saved_mb': 0.0,
            'operations': defaultdict(int)
        }

    def set_strategy(self, strategy: MemoryStrategy) -> None:
        """Set memory optimization strategy"""
        self.strategy = strategy
        logging.info(f"Memory optimization strategy set to: {strategy.value}")

    def optimize_function(self, func: Callable) -> Callable:
        """Optimize a function for memory usage"""
        def optimized_func(*args, **kwargs):
            try:
                # Start memory tracking
                start_memory = self.memory_monitor.get_current_memory_usage()

                # Execute the function
                result = func(*args, **kwargs)

                # End memory tracking
                end_memory = self.memory_monitor.get_current_memory_usage()

                # Calculate memory usage
                memory_used = end_memory['rss_mb'] - start_memory['rss_mb']
                self._record_optimization('function_execution', memory_used)

                return result

            except Exception as e:
                ExceptionHandler.handle_exception(e, {
                    'function': func.__name__,
                    'strategy': self.strategy.value
                })
                raise

        return optimized_func

    def optimize_generator(self, generator_func: Callable) -> Callable:
        """Optimize a generator function for memory usage"""
        def optimized_generator(*args, **kwargs):
            try:
                # Get the generator
                gen = generator_func(*args, **kwargs)

                # Wrap it with memory-optimized iteration
                for item in gen:
                    # Periodically check memory and cleanup
                    if self.optimization_stats['total_optimizations'] % 100 == 0:
                        self._periodic_cleanup()

                    yield item
                    self.optimization_stats['total_optimizations'] += 1

                # Final cleanup
                self._periodic_cleanup()

            except Exception as e:
                ExceptionHandler.handle_exception(e, {
                    'function': generator_func.__name__,
                    'strategy': self.strategy.value
                })
                raise

        return optimized_generator

    def optimize_batch_processing(self, items: List[Any], batch_size: int = 100,
                                process_func: Callable[[Any], Any]) -> List[Any]:
        """Optimize batch processing for memory efficiency"""
        try:
            results = []
            start_time = time.time()

            for i in range(0, len(items), batch_size):
                batch = items[i:i + batch_size]

                # Process batch with memory monitoring
                batch_start_memory = self.memory_monitor.get_current_memory_usage()

                # Process the batch
                batch_results = [process_func(item) for item in batch]

                # Check memory after batch
                batch_end_memory = self.memory_monitor.get_current_memory_usage()
                memory_used = batch_end_memory['rss_mb'] - batch_start_memory['rss_mb']

                # Record optimization stats
                self._record_optimization('batch_processing', memory_used, batch_size=batch_size)

                # Periodic cleanup
                if i > 0 and i % (batch_size * 10) == 0:
                    self._periodic_cleanup()

                results.extend(batch_results)

            # Final cleanup
            self._periodic_cleanup()

            processing_time = time.time() - start_time
            logging.info(f"Batch processing completed: {len(items)} items in {processing_time:.2f}s")

            return results

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'function': 'optimize_batch_processing',
                'items_count': len(items),
                'batch_size': batch_size
            })
            raise

    def _periodic_cleanup(self) -> None:
        """Perform periodic cleanup based on strategy"""
        try:
            if self.strategy == MemoryStrategy.CONSERVATIVE:
                self.memory_monitor.conservative_cleanup()
            elif self.strategy == MemoryStrategy.BALANCED:
                self.memory_monitor.balanced_cleanup()
            elif self.strategy == MemoryStrategy.AGGRESSIVE:
                # Don't cleanup during aggressive mode
                pass

            # Always do basic cleanup
            gc.collect()

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_periodic_cleanup'})

    def _record_optimization(self, operation: str, memory_used: float,
                           **kwargs) -> None:
        """Record memory optimization statistics"""
        try:
            self.optimization_stats['total_optimizations'] += 1
            self.optimization_stats['memory_saved_mb'] += max(0, -memory_used)  # Only count savings
            self.optimization_stats['operations'][operation] += 1

            # Log significant memory usage
            if abs(memory_used) > 100:  # More than 100MB
                logging.info(f"Memory optimization {operation}: {memory_used:.2f}MB")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_record_optimization'})

    def get_optimization_stats(self) -> Dict[str, Any]:
        """Get current optimization statistics"""
        return {
            'strategy': self.strategy.value,
            'stats': self.optimization_stats.copy(),
            'current_memory': self.memory_monitor.get_current_memory_usage()
        }

    def optimize_torch_operations(self) -> Callable:
        """Decorator to optimize PyTorch operations for memory"""
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                try:
                    # Start with cleanup
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()
                        torch.cuda.ipc_collect()

                    # Execute the function
                    result = func(*args, **kwargs)

                    # Cleanup after
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                    # Force garbage collection
                    gc.collect()

                    return result

                except Exception as e:
                    ExceptionHandler.handle_exception(e, {
                        'function': func.__name__,
                        'torch_operation': True
                    })
                    raise

            return wrapper
        return decorator

    def create_memory_context(self) -> Any:
        """Create a memory-optimized context manager"""
        class MemoryContext:
            def __enter__(self):
                # Start memory tracking
                self.start_memory = self.memory_monitor.get_current_memory_usage()
                self.start_time = time.time()
                return self

            def __exit__(self, exc_type, exc_val, exc_tb):
                # End memory tracking
                end_memory = self.memory_monitor.get_current_memory_usage()
                end_time = time.time()

                # Calculate memory usage
                memory_used = end_memory['rss_mb'] - self.start_memory['rss_mb']
                processing_time = end_time - self.start_time

                # Record optimization
                self._record_optimization('memory_context', memory_used)

                # Handle exceptions
                if exc_type is not None:
                    ExceptionHandler.handle_exception(exc_val, {
                        'memory_used': memory_used,
                        'processing_time': processing_time
                    })
                    return False  # Don't suppress exception

                return True  # No exception occurred

        return MemoryContext()

class MemoryProfiler:
    """
    Memory profiling system
    Provides detailed memory profiling for debugging and optimization
    """

    def __init__(self):
        self.profiling_active = False
        self.profile_data = []
        self.max_profile_entries = 10000
        self.start_time = None
        self.start_memory = None

    def start_profiling(self) -> None:
        """Start memory profiling"""
        if self.profiling_active:
            return

        # Start tracemalloc if available
        if hasattr(tracemalloc, 'start'):
            tracemalloc.start(25)  # 25 frames deep

        # Record start metrics
        self.start_time = time.time()
        self.start_memory = MemoryMonitor().get_current_memory_usage()
        self.profiling_active = True

        logging.info("Memory profiling started")

    def stop_profiling(self) -> None:
        """Stop memory profiling and generate report"""
        if not self.profiling_active:
            return

        # Stop tracemalloc
        if hasattr(tracemalloc, 'stop'):
            tracemalloc.stop()

        # Record end metrics
        end_time = time.time()
        end_memory = MemoryMonitor().get_current_memory_usage()

        # Generate profiling report
        self._generate_profiling_report(self.start_time, end_time,
                                      self.start_memory, end_memory)

        self.profiling_active = False
        logging.info("Memory profiling stopped")

    def profile_function(self, func: Callable, *args, **kwargs) -> Any:
        """Profile a single function call"""
        if not self.profiling_active:
            return func(*args, **kwargs)

        try:
            # Get memory before
            start_mem = MemoryMonitor().get_current_memory_usage()
            start_time = time.time()

            # Execute function
            result = func(*args, **kwargs)

            # Get memory after
            end_mem = MemoryMonitor().get_current_memory_usage()
            end_time = time.time()

            # Record profiling data
            self._record_profile_data(
                function_name=func.__name__,
                start_time=start_time,
                end_time=end_time,
                start_memory=start_mem,
                end_memory=end_mem,
                args=args,
                kwargs=kwargs
            )

            return result

        except Exception as e:
            ExceptionHandler.handle_exception(e, {
                'function': func.__name__,
                'profiling': True
            })
            raise

    def _record_profile_data(self, **profile_entry) -> None:
        """Record profiling data"""
        try:
            self.profile_data.append(profile_entry)

            # Keep data size manageable
            if len(self.profile_data) > self.max_profile_entries:
                self.profile_data.pop(0)

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_record_profile_data'})

    def _generate_profiling_report(self, start_time: float, end_time: float,
                                start_memory: Dict[str, Any], end_memory: Dict[str, Any]) -> None:
        """Generate comprehensive profiling report"""
        try:
            # Calculate overall statistics
            total_time = end_time - start_time
            memory_diff = {
                'rss_mb': end_memory['rss_mb'] - start_memory['rss_mb'],
                'percent': end_memory['percent'] - start_memory['percent']
            }

            # Get tracemalloc stats if available
            tracemalloc_stats = None
            if tracemalloc.is_tracing():
                snapshot = tracemalloc.take_snapshot()
                top_stats = snapshot.statistics('lineno')

                tracemalloc_stats = []
                for stat in top_stats[:20]:  # Top 20 memory consumers
                    tracemalloc_stats.append({
                        'filename': stat.traceback[0].filename,
                        'lineno': stat.traceback[0].lineno,
                        'size_kb': round(stat.size / 1024, 2),
                        'count': stat.count,
                        'function': stat.traceback[0].name if len(stat.traceback) > 1 else 'unknown'
                    })

            # Create profiling report
            profiling_report = {
                'start_time': datetime.fromtimestamp(start_time).isoformat(),
                'end_time': datetime.fromtimestamp(end_time).isoformat(),
                'total_time_seconds': total_time,
                'memory_diff': memory_diff,
                'tracemalloc_stats': tracemalloc_stats,
                'profile_entries_count': len(self.profile_data),
                'system_info': MemoryMonitor()._get_system_info()
            }

            # Generate error report
            report_error(
                ProcessingError(
                    message="Memory profiling report generated",
                    severity=ErrorSeverity.INFO,
                    context=profiling_report
                ),
                profiling_report
            )

            # Log summary
            logging.info(f"Memory profiling completed: {total_time:.2f}s, {memory_diff['rss_mb']:.2f}MB change")

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': '_generate_profiling_report'})

    def get_profile_summary(self) -> Dict[str, Any]:
        """Get summary of profiling data"""
        if not self.profile_data:
            return {'message': 'No profiling data available'}

        try:
            # Calculate statistics
            total_time = sum(entry['end_time'] - entry['start_time'] for entry in self.profile_data)
            total_memory_change = sum(entry['end_memory']['rss_mb'] - entry['start_memory']['rss_mb']
                                     for entry in self.profile_data)

            # Get function statistics
            function_stats = defaultdict(lambda: {'count': 0, 'total_time': 0.0, 'total_memory': 0.0})
            for entry in self.profile_data:
                func_name = entry.get('function_name', 'unknown')
                function_stats[func_name]['count'] += 1
                function_stats[func_name]['total_time'] += entry['end_time'] - entry['start_time']
                function_stats[func_name]['total_memory'] += entry['end_memory']['rss_mb'] - entry['start_memory']['rss_mb']

            return {
                'total_entries': len(self.profile_data),
                'total_time': total_time,
                'total_memory_change_mb': total_memory_change,
                'average_time_per_call': total_time / len(self.profile_data) if self.profile_data else 0,
                'average_memory_per_call': total_memory_change / len(self.profile_data) if self.profile_data else 0,
                'function_stats': dict(function_stats),
                'profiling_active': self.profiling_active
            }

        except Exception as e:
            ExceptionHandler.handle_exception(e, {'function': 'get_profile_summary'})
            return {'error': str(e)}

# Global memory manager instance
global_memory_manager = MemoryManager()

def start_memory_monitoring(interval: float = 5.0) -> None:
    """Start global memory monitoring"""
    global_memory_manager.start_monitoring(interval)

def stop_memory_monitoring() -> None:
    """Stop global memory monitoring"""
    global_memory_manager.stop_monitoring()

def get_current_memory_usage() -> Dict[str, Any]:
    """Get current memory usage"""
    return global_memory_manager.get_current_memory_usage()

def get_memory_history(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """Get memory usage history"""
    return global_memory_manager.get_memory_history(limit)

def generate_memory_report() -> ErrorReport:
    """Generate memory report"""
    return global_memory_manager.generate_memory_report()

def optimize_function(func: Callable, strategy: MemoryStrategy = MemoryStrategy.BALANCED) -> Callable:
    """Optimize a function with memory management"""
    optimizer = MemoryOptimizer(strategy)
    return optimizer.optimize_function(func)

def optimize_generator(generator_func: Callable, strategy: MemoryStrategy = MemoryStrategy.BALANCED) -> Callable:
    """Optimize a generator function with memory management"""
    optimizer = MemoryOptimizer(strategy)
    return optimizer.optimize_generator(generator_func)

def optimize_batch_processing(items: List[Any], batch_size: int = 100,
                             process_func: Callable[[Any], Any],
                             strategy: MemoryStrategy = MemoryStrategy.BALANCED) -> List[Any]:
    """Optimize batch processing with memory management"""
    optimizer = MemoryOptimizer(strategy)
    return optimizer.optimize_batch_processing(items, batch_size, process_func)

def torch_optimized(func: Callable) -> Callable:
    """Optimize PyTorch operations for memory"""
    optimizer = MemoryOptimizer()
    return optimizer.optimize_torch_operations()(func)

def start_memory_profiling() -> None:
    """Start memory profiling"""
    profiler = MemoryProfiler()
    profiler.start_profiling()
    return profiler

def get_memory_optimization_stats(strategy: MemoryStrategy = MemoryStrategy.BALANCED) -> Dict[str, Any]:
    """Get memory optimization statistics"""
    optimizer = MemoryOptimizer(strategy)
    return optimizer.get_optimization_stats()