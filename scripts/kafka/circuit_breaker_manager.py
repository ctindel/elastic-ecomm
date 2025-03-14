#!/usr/bin/env python3
"""
Circuit Breaker Manager for Kafka ingestion pipeline

This module provides a centralized manager for circuit breakers used in the
Kafka ingestion pipeline to prevent cascading failures.
"""
import os
import sys
import json
import time
import logging
import threading
from pathlib import Path

# Add project root to path
project_root = str(Path(__file__).parent.parent.parent)
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from scripts.kafka.circuit_breaker import CircuitBreaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger("circuit-breaker-manager")

class CircuitBreakerManager:
    """Manager for circuit breakers"""
    
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Singleton pattern to ensure only one manager instance"""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(CircuitBreakerManager, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance
    
    def __init__(self):
        """Initialize the circuit breaker manager"""
        if self._initialized:
            return
        
        self._initialized = True
        self._circuit_breakers = {}
        
        # Default circuit breaker configurations
        self._default_configs = {
            "kafka": {
                "failure_threshold": 5,
                "recovery_timeout": 30,
                "timeout_multiplier": 2,
                "max_timeout": 300,
                "half_open_success_threshold": 3
            },
            "elasticsearch": {
                "failure_threshold": 3,
                "recovery_timeout": 15,
                "timeout_multiplier": 2,
                "max_timeout": 120,
                "half_open_success_threshold": 2
            },
            "ollama": {
                "failure_threshold": 3,
                "recovery_timeout": 20,
                "timeout_multiplier": 2,
                "max_timeout": 180,
                "half_open_success_threshold": 2
            },
            "redis": {
                "failure_threshold": 3,
                "recovery_timeout": 10,
                "timeout_multiplier": 2,
                "max_timeout": 60,
                "half_open_success_threshold": 2
            }
        }
        
        # Initialize circuit breakers
        self._init_circuit_breakers()
    
    def _init_circuit_breakers(self):
        """Initialize circuit breakers with default configurations"""
        for name, config in self._default_configs.items():
            self._circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=config["failure_threshold"],
                recovery_timeout=config["recovery_timeout"],
                timeout_multiplier=config["timeout_multiplier"],
                max_timeout=config["max_timeout"],
                half_open_success_threshold=config["half_open_success_threshold"]
            )
    
    def get_circuit_breaker(self, name):
        """Get a circuit breaker by name"""
        if name not in self._circuit_breakers:
            # Create a new circuit breaker with default configuration
            if name in self._default_configs:
                config = self._default_configs[name]
            else:
                # Use kafka config as default
                config = self._default_configs["kafka"]
            
            self._circuit_breakers[name] = CircuitBreaker(
                name=name,
                failure_threshold=config["failure_threshold"],
                recovery_timeout=config["recovery_timeout"],
                timeout_multiplier=config["timeout_multiplier"],
                max_timeout=config["max_timeout"],
                half_open_success_threshold=config["half_open_success_threshold"]
            )
        
        return self._circuit_breakers[name]
    
    def get_all_circuit_breakers(self):
        """Get all circuit breakers"""
        return self._circuit_breakers
    
    def get_all_states(self):
        """Get the state of all circuit breakers"""
        states = {}
        for name, cb in self._circuit_breakers.items():
            states[name] = cb.get_state()
        return states
    
    def reset_all(self):
        """Reset all circuit breakers"""
        for cb in self._circuit_breakers.values():
            cb.reset()
    
    def reset_circuit_breaker(self, name):
        """Reset a specific circuit breaker"""
        if name in self._circuit_breakers:
            self._circuit_breakers[name].reset()
            return True
        return False

if __name__ == "__main__":
    # Example usage
    manager = CircuitBreakerManager()
    
    # Get circuit breakers
    kafka_cb = manager.get_circuit_breaker("kafka")
    es_cb = manager.get_circuit_breaker("elasticsearch")
    
    # Print states
    print(json.dumps(manager.get_all_states(), indent=2))
