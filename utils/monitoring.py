"""Performance Monitoring
====================

This module provides performance monitoring functionality.
"""

import time
from functools import wraps
from typing import Dict, Any, Callable
from flask import request, current_app, g
import psutil
import threading
from collections import deque
import json
import logging
from datetime import datetime

class PerformanceMonitor:
    """Monitor application performance metrics."""
    
    def __init__(self):
        self.metrics = {
            'endpoints': {},
            'errors': {},
            'system': {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0
            }
        }
        self.start_time = time.time()

    def record_request(self, endpoint: str, method: str, status_code: int, duration: float):
        """Record a request with its duration and status code."""
        if endpoint not in self.metrics['endpoints']:
            self.metrics['endpoints'][endpoint] = {
                'count': 0,
                'total_time': 0,
                'avg_time': 0,
                'status_codes': {}
            }
        
        endpoint_metrics = self.metrics['endpoints'][endpoint]
        endpoint_metrics['count'] += 1
        endpoint_metrics['total_time'] += duration
        endpoint_metrics['avg_time'] = endpoint_metrics['total_time'] / endpoint_metrics['count']
        
        status_code_str = str(status_code)
        if status_code_str not in endpoint_metrics['status_codes']:
            endpoint_metrics['status_codes'][status_code_str] = 0
        endpoint_metrics['status_codes'][status_code_str] += 1

    def record_error(self, endpoint: str, method: str, error_message: str, status_code: int = 500):
        """Record an error occurrence."""
        error_key = f"{endpoint}:{method}"
        if error_key not in self.metrics['errors']:
            self.metrics['errors'][error_key] = {
                'count': 0,
                'last_error': None,
                'last_occurrence': None,
                'status_codes': {}
            }
        
        error_metrics = self.metrics['errors'][error_key]
        error_metrics['count'] += 1
        error_metrics['last_error'] = error_message
        error_metrics['last_occurrence'] = datetime.utcnow().isoformat()
        
        status_code_str = str(status_code)
        if status_code_str not in error_metrics['status_codes']:
            error_metrics['status_codes'][status_code_str] = 0
        error_metrics['status_codes'][status_code_str] += 1

    def record_system_metrics(self):
        """Record system resource usage metrics."""
        try:
            # CPU usage
            self.metrics['system']['cpu_usage'] = psutil.cpu_percent(interval=1)
            
            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics['system']['memory_usage'] = memory.percent
            
            # Disk usage
            disk = psutil.disk_usage('/')
            self.metrics['system']['disk_usage'] = disk.percent
            
        except Exception as e:
            logging.error(f"Error recording system metrics: {e}")

    def get_metrics(self) -> Dict[str, Any]:
        """Get all recorded metrics."""
        return {
            'endpoints': self.metrics['endpoints'],
            'errors': self.metrics['errors'],
            'system': self.metrics['system'],
            'uptime': time.time() - self.start_time
        }

    def reset_metrics(self):
        """Reset all metrics to their initial state."""
        self.metrics = {
            'endpoints': {},
            'errors': {},
            'system': {
                'cpu_usage': 0,
                'memory_usage': 0,
                'disk_usage': 0
            }
        }
        self.start_time = time.time()

# Create global monitor instance
monitor = PerformanceMonitor()

def monitor_performance(f: Callable) -> Callable:
    """Decorator to monitor function performance."""
    @wraps(f)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        start_time = time.time()
        
        try:
            result = f(*args, **kwargs)
            duration = time.time() - start_time
            
            # Get the monitor instance from Flask's g object
            if 'performance_monitor' not in g:
                g.performance_monitor = PerformanceMonitor()
            
            # Record the request
            g.performance_monitor.record_request(
                endpoint=f.__name__,
                method='function',
                status_code=200,
                duration=duration
            )
            
            return result
        except Exception as e:
            duration = time.time() - start_time
            
            # Record the error
            if 'performance_monitor' in g:
                g.performance_monitor.record_error(
                    endpoint=f.__name__,
                    method='function',
                    error_message=str(e)
                )
            
            raise
    return decorated_function

def start_monitoring_loop():
    """Start background monitoring loop."""
    def monitor_loop():
        while True:
            monitor.record_system_metrics()
            time.sleep(60)  # Record every minute
            
    thread = threading.Thread(target=monitor_loop, daemon=True)
    thread.start()

def get_performance_report() -> str:
    """Get formatted performance report."""
    summary = monitor.get_metrics()
    return json.dumps(summary, indent=2) 