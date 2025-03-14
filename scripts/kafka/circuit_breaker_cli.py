#!/usr/bin/env python3
"""
Command-line interface for the circuit breaker manager.

This script provides a CLI for viewing and managing circuit breakers.
"""

import argparse
import json
import logging
import sys
import time
from tabulate import tabulate

from scripts.kafka.circuit_breaker_manager import CircuitBreakerManager
from scripts.kafka.circuit_breaker import CircuitBreakerState

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('circuit-breaker-cli')

def format_metrics(metrics):
    """Format circuit breaker metrics for display"""
    rows = []
    for name, data in metrics.items():
        state = data['state']
        state_color = {
            CircuitBreakerState.CLOSED: '\033[92m',  # Green
            CircuitBreakerState.OPEN: '\033[91m',    # Red
            CircuitBreakerState.HALF_OPEN: '\033[93m'  # Yellow
        }.get(state, '')
        reset = '\033[0m'
        
        rows.append([
            name,
            f"{state_color}{state}{reset}",
            f"{data['failure_count']}/{data['total_count']}",
            f"{data['failure_rate']:.2%}",
            data['last_failure'] or 'N/A',
            data['last_state_change'] or 'N/A'
        ])
    
    return tabulate(
        rows,
        headers=['Name', 'State', 'Failures/Total', 'Failure Rate', 'Last Failure', 'Last State Change'],
        tablefmt='pretty'
    )

def main():
    parser = argparse.ArgumentParser(description='Circuit Breaker CLI')
    parser.add_argument('--redis-host', default='localhost', help='Redis host')
    parser.add_argument('--redis-port', type=int, default=6379, help='Redis port')
    parser.add_argument('--redis-db', type=int, default=0, help='Redis DB')
    
    subparsers = parser.add_subparsers(dest='command', help='Command')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show circuit breaker status')
    status_parser.add_argument('--json', action='store_true', help='Output in JSON format')
    status_parser.add_argument('--watch', action='store_true', help='Watch mode (continuous updates)')
    status_parser.add_argument('--interval', type=int, default=5, help='Watch interval in seconds')
    
    # Reset command
    reset_parser = subparsers.add_parser('reset', help='Reset a circuit breaker')
    reset_parser.add_argument('name', help='Circuit breaker name to reset')
    
    args = parser.parse_args()
    
    # Create circuit breaker manager
    manager = CircuitBreakerManager(
        redis_host=args.redis_host,
        redis_port=args.redis_port,
        redis_db=args.redis_db
    )
    
    if args.command == 'status':
        if args.watch:
            try:
                while True:
                    metrics = manager.get_all_metrics()
                    if not metrics:
                        print("No circuit breakers found.")
                    else:
                        if args.json:
                            print(json.dumps(metrics, indent=2))
                        else:
                            print("\033c", end="")  # Clear screen
                            print(format_metrics(metrics))
                            print(f"\nUpdated: {time.strftime('%Y-%m-%d %H:%M:%S')}")
                            print("Press Ctrl+C to exit")
                    time.sleep(args.interval)
            except KeyboardInterrupt:
                print("\nExiting watch mode")
        else:
            metrics = manager.get_all_metrics()
            if not metrics:
                print("No circuit breakers found.")
            else:
                if args.json:
                    print(json.dumps(metrics, indent=2))
                else:
                    print(format_metrics(metrics))
    
    elif args.command == 'reset':
        # Get the circuit breaker
        cb = manager.get_circuit_breaker(args.name)
        
        # Reset to closed state
        cb.set_state(CircuitBreakerState.CLOSED)
        
        print(f"Circuit breaker '{args.name}' has been reset to CLOSED state.")
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
