"""
Retry Handler with Exponential Backoff

Handles retry logic for transient failures with configurable exponential backoff.
"""
import logging
import time
from typing import Callable, TypeVar, Optional
from functools import wraps

logger = logging.getLogger(__name__)

T = TypeVar('T')


class RetryHandler:
    """
    Handles retry logic with exponential backoff for transient failures.
    """
    
    def __init__(
        self,
        max_attempts: int = 3,
        initial_delay: float = 2.0,
        backoff_factor: float = 2.0,
        max_delay: float = 60.0
    ):
        """
        Initialize retry handler
        
        Args:
            max_attempts: Maximum number of retry attempts
            initial_delay: Initial delay in seconds
            backoff_factor: Multiplier for exponential backoff
            max_delay: Maximum delay cap in seconds
        """
        self.max_attempts = max_attempts
        self.initial_delay = initial_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
    
    def calculate_delay(self, attempt: int) -> float:
        """
        Calculate delay for given attempt using exponential backoff
        
        Args:
            attempt: Current attempt number (0-indexed)
            
        Returns:
            Delay in seconds
        """
        delay = self.initial_delay * (self.backoff_factor ** attempt)
        return min(delay, self.max_delay)
    
    def retry(
        self,
        func: Callable[..., T],
        *args,
        **kwargs
    ) -> Optional[T]:
        """
        Execute function with retry logic
        
        Args:
            func: Function to execute
            *args: Positional arguments for function
            **kwargs: Keyword arguments for function
            
        Returns:
            Function result or None if all retries exhausted
        """
        last_exception = None
        
        for attempt in range(self.max_attempts):
            try:
                result = func(*args, **kwargs)
                if attempt > 0:
                    logger.info(f"Retry succeeded on attempt {attempt + 1}")
                return result
            except Exception as e:
                last_exception = e
                if attempt < self.max_attempts - 1:
                    delay = self.calculate_delay(attempt)
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_attempts} failed: {e}. "
                        f"Retrying in {delay}s..."
                    )
                    time.sleep(delay)
                else:
                    logger.error(
                        f"All {self.max_attempts} attempts failed. Last error: {e}",
                        exc_info=True
                    )
        
        return None


def with_retry(
    max_attempts: int = 3,
    initial_delay: float = 2.0,
    backoff_factor: float = 2.0,
    max_delay: float = 60.0
):
    """
    Decorator for adding retry logic to functions
    
    Args:
        max_attempts: Maximum number of retry attempts
        initial_delay: Initial delay in seconds
        backoff_factor: Multiplier for exponential backoff
        max_delay: Maximum delay cap in seconds
    """
    def decorator(func: Callable[..., T]) -> Callable[..., Optional[T]]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Optional[T]:
            handler = RetryHandler(max_attempts, initial_delay, backoff_factor, max_delay)
            return handler.retry(func, *args, **kwargs)
        return wrapper
    return decorator
