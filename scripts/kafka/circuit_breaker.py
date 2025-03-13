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
    """Circuit breaker implementation for Kafka consumers"""
    def __init__(
        self,
        name,
        failure_threshold=5,
        recovery_timeout=60,
        state_file=None
    ):
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
