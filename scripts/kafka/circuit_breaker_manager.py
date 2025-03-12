#!/usr/bin/env python3
"""
Circuit Breaker Manager for E-Commerce Search Demo

This module provides a centralized manager for circuit breakers
across different document types and ingestion stages.
"""

import json
import logging
import os
import redis
from typing import Dict, Optional
from .circuit_breaker import CircuitBreaker, InMemoryCircuitBreaker

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('circuit-breaker-manager')

class CircuitBreakerManager:
    """Manager for multiple circuit breakers in the ingestion pipeline"""
    
    def __init__(self, use_redis=True, redis_client=None):
        """Initialize the circuit breaker manager"""
        self.use_redis = use_redis
        self.redis_client = redis_client
        self.breakers: Dict[str, CircuitBreaker] = {}
        
        # Initialize breakers for each document type
        self._init_breakers()
    
    def _init_breakers(self):
        """Initialize circuit breakers for all document types"""
        document_types = [
            'products',
            'product-images',
            'personas',
            'queries'
        ]
        
        for doc_type in document_types:
            # Create breakers for different stages
            for stage in ['ingestion', 'vectorization']:
                breaker_name = f"{doc_type}_{stage}"
                if self.use_redis:
                    if self.redis_client:
                        self.breakers[breaker_name] = CircuitBreaker(breaker_name, self.redis_client)
                    else:
                        # Create a new Redis client
                        from app.config.settings import REDIS_HOST, REDIS_PORT
                        redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT)
                        self.breakers[breaker_name] = CircuitBreaker(breaker_name, redis_client)
                else:
                    self.breakers[breaker_name] = InMemoryCircuitBreaker(breaker_name)
    
    def get_breaker(self, doc_type: str, stage: str) -> Optional[CircuitBreaker]:
        """Get a circuit breaker for a specific document type and stage"""
        breaker_name = f"{doc_type}_{stage}"
        return self.breakers.get(breaker_name)
    
    def record_success(self, doc_type: str, stage: str):
        """Record a successful operation for a document type and stage"""
        breaker = self.get_breaker(doc_type, stage)
        if breaker:
            breaker.record_success()
    
    def record_failure(self, doc_type: str, stage: str):
        """Record a failed operation for a document type and stage"""
        breaker = self.get_breaker(doc_type, stage)
        if breaker:
            breaker.record_failure()
    
    def allow_request(self, doc_type: str, stage: str) -> bool:
        """Check if a request should be allowed for a document type and stage"""
        breaker = self.get_breaker(doc_type, stage)
        return breaker.allow_request() if breaker else True
    
    def get_all_metrics(self) -> Dict[str, dict]:
        """Get metrics for all circuit breakers"""
        return {
            name: breaker.get_metrics()
            for name, breaker in self.breakers.items()
        }
    
    def get_metrics(self, doc_type: str, stage: str) -> Optional[dict]:
        """Get metrics for a specific circuit breaker"""
        breaker = self.get_breaker(doc_type, stage)
        return breaker.get_metrics() if breaker else None

# Global instance for convenience
_manager = None

def get_manager(use_redis=True, redis_client=None) -> CircuitBreakerManager:
    """Get the global circuit breaker manager instance"""
    global _manager
    if _manager is None:
        _manager = CircuitBreakerManager(use_redis=use_redis, redis_client=redis_client)
    return _manager
