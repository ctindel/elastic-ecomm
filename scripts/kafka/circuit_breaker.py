#!/usr/bin/env python3
"""
Circuit breaker implementation for Kafka consumers
This prevents overloading Ollama with too many requests
"""
import os
import sys
import time
import json
import logging
import threading
from enum import Enum
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "CLOSED"  # Normal operation, requests flow through
    OPEN = "OPEN"      # Circuit is open, requests are blocked
    HALF_OPEN = "HALF_OPEN"  # Testing if the circuit can be closed again

class CircuitBreaker:
    """
    Circuit breaker implementation for Kafka consumers
    
    This prevents overloading Ollama with too many requests
    """
    def __init__(
        self,
        name,
        failure_threshold=5,
        recovery_timeout=60,
        state_file=None
    ):
        """
        Initialize the circuit breaker
        
        Args:
            name: Name of the circuit breaker
            failure_threshold: Number of failures before opening the circuit
            recovery_timeout: Time in seconds before trying to close the circuit again
            state_file: Path to the state file
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state_file = state_file or f"/tmp/circuit_breaker_{name}.json"
        
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0
        self.lock = threading.RLock()
        
        # Load state from file if it exists
        self._load_state()
    
    def _load_state(self):
        """Load the circuit breaker state from file"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, "r") as f:
                    state_data = json.load(f)
                
                self.state = CircuitState(state_data.get("state", CircuitState.CLOSED.value))
                self.failure_count = state_data.get("failure_count", 0)
                self.last_failure_time = state_data.get("last_failure_time", 0)
                
                logger.info(f"Loaded circuit breaker state: {self.state.value}")
        
        except Exception as e:
            logger.error(f"Error loading circuit breaker state: {str(e)}")
    
    def _save_state(self):
        """Save the circuit breaker state to file"""
        try:
            state_data = {
                "name": self.name,
                "state": self.state.value,
                "failure_count": self.failure_count,
                "last_failure_time": self.last_failure_time
            }
            
            with open(self.state_file, "w") as f:
                json.dump(state_data, f)
        
        except Exception as e:
            logger.error(f"Error saving circuit breaker state: {str(e)}")
