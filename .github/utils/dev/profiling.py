"""
Profiling Utilities
================

Tools for profiling and performance analysis.
"""

import cProfile
import pstats
import io
import time
import logging
from functools import wraps
from flask import request, g

logger = logging.getLogger(__name__)

def profile_function(func):
    """Profile a function's execution."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        pr = cProfile.Profile()
        pr.enable()
        
        result = func(*args, **kwargs)
        
        pr.disable()
        s = io.StringIO()
        ps = pstats.Stats(pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        logger.debug(f"Profile for {func.__name__}:\n{s.getvalue()}")
        return result
    return wrapper

def profile_request(f):
    """Profile a request's execution time and memory usage."""
    @wraps(f)
    def wrapped(*args, **kwargs):
        from memory_profiler import memory_usage
        import tracemalloc
        
        # Start tracemalloc
        tracemalloc.start()
        
        # Time the request
        start_time = time.time()
        
        # Profile memory usage
        def run_request():
            return f(*args, **kwargs)
        
        mem_usage = memory_usage((run_request, (), {}), interval=0.1)
        
        # Get memory snapshot
        current, peak = tracemalloc.get_traced_memory()
        snapshot = tracemalloc.take_snapshot()
        tracemalloc.stop()
        
        # Calculate stats
        duration = time.time() - start_time
        stats = {
            'duration': duration,
            'memory': {
                'current': current / 10**6,  # MB
                'peak': peak / 10**6,        # MB
                'profile': mem_usage
            }
        }
        
        # Log top memory users
        logger.debug(f"Memory profile for {request.endpoint}:")
        top_stats = snapshot.statistics('lineno')
        for stat in top_stats[:3]:
            logger.debug(str(stat))
        
        # Store stats in g for access in after_request
        g.profile_stats = stats
        
        return f(*args, **kwargs)
    return wrapped

class Profiler:
    """Context manager for profiling code blocks."""
    def __init__(self, name):
        self.name = name
        self.pr = cProfile.Profile()
    
    def __enter__(self):
        self.pr.enable()
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.pr.disable()
        duration = time.time() - self.start_time
        
        s = io.StringIO()
        ps = pstats.Stats(self.pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        logger.debug(f"Profile for {self.name}:")
        logger.debug(f"Duration: {duration:.4f}s")
        logger.debug(f"Stats:\n{s.getvalue()}")

def setup_profiling(app):
    """Configure profiling for the application."""
    if app.debug:
        # Profile all requests in debug mode
        app.before_request(start_request_profiling)
        app.after_request(end_request_profiling)

def start_request_profiling():
    """Start profiling a request."""
    g.start_time = time.time()
    g.pr = cProfile.Profile()
    g.pr.enable()

def end_request_profiling(response):
    """End profiling a request and log results."""
    if hasattr(g, 'pr'):
        g.pr.disable()
        duration = time.time() - g.start_time
        
        s = io.StringIO()
        ps = pstats.Stats(g.pr, stream=s).sort_stats('cumulative')
        ps.print_stats()
        
        logger.debug(f"Profile for {request.endpoint}:")
        logger.debug(f"Duration: {duration:.4f}s")
        logger.debug(f"Stats:\n{s.getvalue()}")
    
    return response 