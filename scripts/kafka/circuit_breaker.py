#!/usr/bin/env python3
"""
Circuit Breaker for Kafka ingestion pipeline

This module implements the circuit breaker pattern to prevent cascading failures
in the Kafka ingestion pipeline.
"""
import os
import json
import time
import logging
import threading
import redis
from enum import Enum
from datetime import datetime, timedelta
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("circuit-breaker")

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation, requests allowed
    OPEN = "open"      # Circuit is open, requests blocked
    HALF_OPEN = "half_open"  # Testing if service is back online

class CircuitBreaker:
    """Circuit breaker implementation"""
    
    def __init__(
        self,
        name,
        failure_threshold=5,
        recovery_timeout=30,
        timeout_multiplier=2,
        max_timeout=300,
        half_open_success_threshold=3,
        redis_url=None
    ):
        """Initialize the circuit breaker"""
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.timeout_multiplier = timeout_multiplier
        self.max_timeout = max_timeout
        self.half_open_success_threshold = half_open_success_threshold
        
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._last_failure_time = None
        self._last_state_change_time = datetime.now()
        self._current_timeout = recovery_timeout
        self._lock = threading.RLock()
        
        # Redis connection for distributed state
        self._redis = None
        if redis_url:
            try:
                self._redis = redis.from_url(redis_url)
                logger.info(f"Connected to Redis at {redis_url}")
            except Exception as e:
                logger.error(f"Error connecting to Redis: {e}")
                logger.warning("Falling back to local state storage")
        
        # Load state from persistent storage
        self._load_state()
    
    def _get_state_file_path(self):
        """Get the path to the state file"""
        state_dir = Path.home() / ".circuit_breaker"
        state_dir.mkdir(exist_ok=True)
        return state_dir / f"{self.name}_state.json"
    
    def _load_state(self):
        """Load state from persistent storage"""
        try:
            if self._redis:
                # Load from Redis
                state_json = self._redis.get(f"circuit_breaker:{self.name}")
                if state_json:
                    state = json.loads(state_json)
                    self._update_state_from_dict(state)
            else:
                # Load from file
                state_file = self._get_state_file_path()
                if state_file.exists():
                    with open(state_file, "r") as f:
                        state = json.load(f)
                        self._update_state_from_dict(state)
        except Exception as e:
            logger.error(f"Error loading circuit breaker state: {e}")
    
    def _save_state(self):
        """Save state to persistent storage"""
        try:
            state = {
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "last_failure_time": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "last_state_change_time": self._last_state_change_time.isoformat(),
                "current_timeout": self._current_timeout
            }
            
            if self._redis:
                # Save to Redis
                self._redis.set(f"circuit_breaker:{self.name}", json.dumps(state))
                # Set expiration to avoid stale state
                self._redis.expire(f"circuit_breaker:{self.name}", 86400)  # 24 hours
            else:
                # Save to file
                state_file = self._get_state_file_path()
                with open(state_file, "w") as f:
                    json.dump(state, f)
        except Exception as e:
            logger.error(f"Error saving circuit breaker state: {e}")
    
    def _update_state_from_dict(self, state):
        """Update state from dictionary"""
        try:
            self._state = CircuitState(state.get("state", CircuitState.CLOSED.value))
            self._failure_count = state.get("failure_count", 0)
            self._success_count = state.get("success_count", 0)
            
            last_failure_time = state.get("last_failure_time")
            if last_failure_time:
                self._last_failure_time = datetime.fromisoformat(last_failure_time)
            
            last_state_change_time = state.get("last_state_change_time")
            if last_state_change_time:
                self._last_state_change_time = datetime.fromisoformat(last_state_change_time)
            
            self._current_timeout = state.get("current_timeout", self.recovery_timeout)
        except Exception as e:
            logger.error(f"Error updating circuit breaker state: {e}")
    
    def allow_request(self):
        """Check if a request is allowed"""
        with self._lock:
            now = datetime.now()
            
            if self._state == CircuitState.CLOSED:
                return True
            
            if self._state == CircuitState.OPEN:
                # Check if recovery timeout has elapsed
                if self._last_failure_time and now - self._last_failure_time > timedelta(seconds=self._current_timeout):
                    logger.info(f"Circuit {self.name} transitioning from OPEN to HALF_OPEN after {self._current_timeout}s timeout")
                    self._state = CircuitState.HALF_OPEN
                    self._success_count = 0
                    self._last_state_change_time = now
                    self._save_state()
                    return True
                return False
            
            if self._state == CircuitState.HALF_OPEN:
                # In HALF_OPEN state, allow limited requests to test if service is back
                return True
            
            return False
    
    def record_success(self):
        """Record a successful request"""
        with self._lock:
            if self._state == CircuitState.CLOSED:
                # Reset failure count on success in closed state
                if self._failure_count > 0:
                    self._failure_count = 0
                    self._save_state()
                return
            
            if self._state == CircuitState.HALF_OPEN:
                self._success_count += 1
                
                # If enough successes, close the circuit
                if self._success_count >= self.half_open_success_threshold:
                    logger.info(f"Circuit {self.name} transitioning from HALF_OPEN to CLOSED after {self._success_count} successes")
                    self._state = CircuitState.CLOSED
                    self._failure_count = 0
                    self._success_count = 0
                    self._current_timeout = self.recovery_timeout  # Reset timeout
                    self._last_state_change_time = datetime.now()
                    self._save_state()
                else:
                    # Save state for each success in half-open state
                    self._save_state()
    
    def record_failure(self):
        """Record a failed request"""
        with self._lock:
            now = datetime.now()
            self._last_failure_time = now
            
            if self._state == CircuitState.CLOSED:
                self._failure_count += 1
                
                # If too many failures, open the circuit
                if self._failure_count >= self.failure_threshold:
                    logger.warning(f"Circuit {self.name} transitioning from CLOSED to OPEN after {self._failure_count} failures")
                    self._state = CircuitState.OPEN
                    self._last_state_change_time = now
                    self._save_state()
                else:
                    # Save state for each failure in closed state
                    self._save_state()
                return
            
            if self._state == CircuitState.HALF_OPEN:
                # Any failure in half-open state opens the circuit again
                logger.warning(f"Circuit {self.name} transitioning from HALF_OPEN to OPEN after failure")
                self._state = CircuitState.OPEN
                self._success_count = 0
                
                # Increase timeout exponentially
                self._current_timeout = min(
                    self._current_timeout * self.timeout_multiplier,
                    self.max_timeout
                )
                
                self._last_state_change_time = now
                self._save_state()
                return
            
            if self._state == CircuitState.OPEN:
                # Update last failure time
                self._save_state()
    
    def get_state(self):
        """Get the current state of the circuit breaker"""
        with self._lock:
            return {
                "name": self.name,
                "state": self._state.value,
                "failure_count": self._failure_count,
                "success_count": self._success_count,
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self._current_timeout,
                "last_failure": self._last_failure_time.isoformat() if self._last_failure_time else None,
                "last_state_change": self._last_state_change_time.isoformat(),
                "half_open_success_threshold": self.half_open_success_threshold
            }
    
    def reset(self):
        """Reset the circuit breaker to closed state"""
        with self._lock:
            logger.info(f"Manually resetting circuit {self.name} to CLOSED state")
            self._state = CircuitState.CLOSED
            self._failure_count = 0
            self._success_count = 0
            self._current_timeout = self.recovery_timeout
            self._last_state_change_time = datetime.now()
            self._save_state()
    
    def force_open(self):
        """Force the circuit breaker to open state"""
        with self._lock:
            logger.info(f"Manually forcing circuit {self.name} to OPEN state")
            self._state = CircuitState.OPEN
            self._failure_count = self.failure_threshold
            self._success_count = 0
            self._last_failure_time = datetime.now()
            self._last_state_change_time = datetime.now()
            self._save_state()

if __name__ == "__main__":
    # Example usage
    cb = CircuitBreaker(name="test")
    
    # Simulate failures
    for i in range(10):
        if cb.allow_request():
            print(f"Request {i} allowed")
            if i < 7:  # First 7 requests fail
                cb.record_failure()
            else:
                cb.record_success()
        else:
            print(f"Request {i} blocked by circuit breaker")
        
        time.sleep(1)
