#!/usr/bin/env python3
"""
Circuit Breaker Implementation for E-Commerce Search Demo

This module implements a circuit breaker pattern to prevent system overload
during failures and provide graceful degradation.
"""

import json
import logging
import time
from collections import deque
from datetime import datetime, timedelta
from threading import Lock
import redis

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('circuit-breaker')

class CircuitBreakerState:
    """Enum for circuit breaker states"""
    CLOSED = 'CLOSED'  # Normal operation, requests flow through
    OPEN = 'OPEN'      # Circuit is open, requests are blocked
    HALF_OPEN = 'HALF_OPEN'  # Testing if the circuit can be closed again

class CircuitBreaker:
    """Circuit breaker implementation for Kafka consumer"""
    
    def __init__(self, name, redis_client=None,
                 failure_threshold=0.3,  # 30% failure rate
                 window_size=300,  # 5 minutes in seconds
                 reset_timeout=900,  # 15 minutes in seconds
                 half_open_requests=5):  # Number of requests to try when half-open
        """Initialize the circuit breaker"""
        self.name = name
        self.redis = redis_client
        self.failure_threshold = failure_threshold
        self.window_size = window_size
        self.reset_timeout = reset_timeout
        self.half_open_requests = half_open_requests
        
        # Redis keys
        self._init_redis_keys()
        
        # Initialize state if using Redis
        if self.redis:
            self._init_redis_state()
    
    def _init_redis_keys(self):
        """Initialize Redis key names"""
        prefix = f"ecommerce:circuit_breaker:{self.name}"
        self.state_key = f"{prefix}:state"
        self.last_failure_key = f"{prefix}:last_failure"
        self.failures_key = f"{prefix}:failures"
        self.successes_key = f"{prefix}:successes"
        self.half_open_count_key = f"{prefix}:half_open_count"
        self.last_state_change_key = f"{prefix}:last_state_change"
    
    def _init_redis_state(self):
        """Initialize Redis state if not exists"""
        if not self.redis.exists(self.state_key):
            self.redis.set(self.state_key, CircuitBreakerState.CLOSED)
            self.redis.set(self.last_state_change_key, int(time.time()))
            self.redis.delete(self.failures_key)
            self.redis.delete(self.successes_key)
    
    def get_state(self):
        """Get the current state of the circuit breaker"""
        if self.redis:
            state = self.redis.get(self.state_key)
            return state.decode('utf-8') if state else CircuitBreakerState.CLOSED
        return CircuitBreakerState.CLOSED
    
    def set_state(self, state):
        """Set the state of the circuit breaker"""
        if self.redis:
            current_state = self.get_state()
            if current_state != state:
                self.redis.set(self.state_key, state)
                self.redis.set(self.last_state_change_key, int(time.time()))
                logger.info(f"Circuit breaker '{self.name}' changed state from {current_state} to {state}")
                
                # Reset counters on state change
                if state == CircuitBreakerState.HALF_OPEN:
                    self.redis.set(self.half_open_count_key, 0)
    
    def record_success(self):
        """Record a successful operation"""
        current_time = int(time.time())
        
        if self.redis:
            state = self.get_state()
            
            if state == CircuitBreakerState.CLOSED:
                # Add success to the window
                self.redis.zadd(self.successes_key, {str(current_time): current_time})
                
                # Remove old events outside the window
                self._clean_old_events()
                
            elif state == CircuitBreakerState.HALF_OPEN:
                # In half-open state, increment success counter
                count = self.redis.incr(self.half_open_count_key)
                
                # If we've had enough successful requests, close the circuit
                if count >= self.half_open_requests:
                    self.set_state(CircuitBreakerState.CLOSED)
                    self.redis.delete(self.failures_key)
                    self.redis.delete(self.successes_key)
    
    def record_failure(self):
        """Record a failed operation"""
        current_time = int(time.time())
        
        if self.redis:
            self.redis.set(self.last_failure_key, current_time)
            state = self.get_state()
            
            if state == CircuitBreakerState.CLOSED:
                # Add failure to the window
                self.redis.zadd(self.failures_key, {str(current_time): current_time})
                
                # Remove old events outside the window
                self._clean_old_events()
                
                # Check if we need to open the circuit
                failure_count = self.redis.zcard(self.failures_key)
                success_count = self.redis.zcard(self.successes_key)
                total = failure_count + success_count
                
                if total > 0 and failure_count / total >= self.failure_threshold:
                    self.set_state(CircuitBreakerState.OPEN)
                    
            elif state == CircuitBreakerState.HALF_OPEN:
                # Any failure in half-open state opens the circuit again
                self.set_state(CircuitBreakerState.OPEN)
    
    def _clean_old_events(self):
        """Remove events outside the window"""
        if self.redis:
            current_time = int(time.time())
            min_time = current_time - self.window_size
            
            # Remove old successes
            self.redis.zremrangebyscore(self.successes_key, 0, min_time)
            
            # Remove old failures
            self.redis.zremrangebyscore(self.failures_key, 0, min_time)
    
    def allow_request(self):
        """Check if a request should be allowed through the circuit breaker"""
        if not self.redis:
            return True
            
        current_time = int(time.time())
        state = self.get_state()
        
        if state == CircuitBreakerState.CLOSED:
            return True
            
        elif state == CircuitBreakerState.OPEN:
            # Check if enough time has passed to try again
            last_state_change = int(self.redis.get(self.last_state_change_key) or 0)
            if current_time - last_state_change >= self.reset_timeout:
                # Transition to half-open state
                self.set_state(CircuitBreakerState.HALF_OPEN)
                return True
            return False
            
        elif state == CircuitBreakerState.HALF_OPEN:
            # In half-open state, allow a limited number of requests
            count = int(self.redis.get(self.half_open_count_key) or 0)
            return count < self.half_open_requests
            
        return True
