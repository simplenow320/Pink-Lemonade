"""
HTTP Utilities for GrantFlow

This module provides utilities for making HTTP requests with automatic retries,
backoff, and rate limiting to improve stability of the scraping process.
"""

import logging
import time
import random
import requests
from functools import wraps
from typing import Dict, Any, Optional, Callable, TypeVar, Union, List

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for return type
T = TypeVar('T')

class RateLimiter:
    """Rate limiter to prevent overwhelming servers with requests"""
    
    def __init__(self, requests_per_minute: int = 20):
        """
        Initialize the rate limiter
        
        Args:
            requests_per_minute: Maximum number of requests allowed per minute
        """
        self.requests_per_minute = requests_per_minute
        self.interval = 60 / self.requests_per_minute  # Time between requests in seconds
        self.last_request_time = 0
        
    def wait(self):
        """Wait if necessary to maintain the rate limit"""
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        
        if time_since_last_request < self.interval:
            sleep_time = self.interval - time_since_last_request
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

# Create a global rate limiter for all requests
global_rate_limiter = RateLimiter()

def with_retry(
    max_retries: int = 3, 
    backoff_factor: float = 1.5,
    retry_status_codes: List[int] = [429, 500, 502, 503, 504],
    rate_limiter: Optional[RateLimiter] = global_rate_limiter
) -> Callable:
    """
    Decorator that adds retry capability to functions making HTTP requests
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Factor to increase wait time between retries
        retry_status_codes: List of HTTP status codes that should trigger a retry
        rate_limiter: Rate limiter to use, defaults to the global rate limiter
        
    Returns:
        Decorated function with retry capability
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @wraps(func)
        def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(max_retries + 1):  # +1 for the initial attempt
                try:
                    # Wait if needed to respect rate limits
                    if rate_limiter:
                        rate_limiter.wait()
                        
                    # Call the original function
                    return func(*args, **kwargs)
                    
                except requests.exceptions.RequestException as e:
                    last_exception = e
                    
                    # Don't retry if we've reached max retries or if it's not a retryable error
                    if attempt >= max_retries:
                        logger.error(f"Max retries ({max_retries}) reached for request: {e}")
                        break
                        
                    # Check if status code is in retryable list
                    if hasattr(e, 'response') and e.response is not None and hasattr(e.response, 'status_code') and e.response.status_code not in retry_status_codes:
                        logger.warning(f"Non-retryable status code {e.response.status_code}: {e}")
                        break
                        
                    # Calculate wait time with exponential backoff and jitter
                    wait_time = backoff_factor ** attempt + random.uniform(0, 1)
                    logger.warning(f"Request failed (attempt {attempt+1}/{max_retries+1}), retrying in {wait_time:.2f}s: {e}")
                    time.sleep(wait_time)
                    
                except Exception as e:
                    # For non-request exceptions, log and raise immediately
                    logger.error(f"Non-request exception in HTTP request: {e}")
                    raise
                    
            # If we've exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception
                
            # This should never happen, but to satisfy the type checker
            return func(*args, **kwargs)
                
        return wrapper
    return decorator

@with_retry()
def fetch_url(url: str, headers: Optional[Dict[str, str]] = None, timeout: int = 30) -> requests.Response:
    """
    Fetch a URL with automatic retries and rate limiting
    
    Args:
        url: The URL to fetch
        headers: Optional HTTP headers
        timeout: Request timeout in seconds
        
    Returns:
        The HTTP response
        
    Raises:
        requests.exceptions.RequestException: If the request fails after all retries
    """
    if headers is None:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
    return requests.get(url, headers=headers, timeout=timeout)

def extract_main_content(url: str) -> str:
    """
    Extract the main text content from a URL using trafilatura
    
    Args:
        url: The URL to extract content from
        
    Returns:
        The extracted text content
        
    Raises:
        Exception: If content extraction fails
    """
    try:
        import trafilatura
        
        # Fetch the URL with retries
        response = fetch_url(url)
        
        # Check if the request was successful
        if response.status_code != 200:
            logger.warning(f"Failed to fetch URL {url}: Status code {response.status_code}")
            return ""
            
        # Extract the main content
        downloaded = response.text
        text = trafilatura.extract(downloaded)
        
        if not text:
            logger.warning(f"No content extracted from {url}")
            return ""
            
        return text
        
    except Exception as e:
        logger.error(f"Error extracting content from {url}: {str(e)}")
        return ""