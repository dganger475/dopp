import time
import functools
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)

def rate_limit(max_retries: int = 3, delay: float = 1.0) -> Callable:
    """
    Decorator to handle rate limiting with exponential backoff.
    
    Args:
        max_retries (int): Maximum number of retry attempts
        delay (float): Initial delay between retries in seconds
        
    Returns:
        Callable: Decorated function with rate limiting
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            retries = 0
            while retries < max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if "rate limit" in str(e).lower() or "too many requests" in str(e).lower():
                        retries += 1
                        if retries == max_retries:
                            logger.error(f"Max retries ({max_retries}) exceeded for rate limit")
                            raise
                        wait_time = delay * (2 ** retries)  # Exponential backoff
                        logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry {retries}/{max_retries}")
                        time.sleep(wait_time)
                    else:
                        raise
            return None
        return wrapper
    return decorator 