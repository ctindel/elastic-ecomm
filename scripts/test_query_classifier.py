#!/usr/bin/env python3
"""
Run tests for the query classifier
"""
import os
import sys
import unittest
from pathlib import Path

# Add project root to Python path
project_root = str(Path(__file__).parent.parent.absolute())
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def run_tests():
    """Run the query classifier tests"""
    # Get the test directory
    test_dir = os.path.join(project_root, "tests", "query_classifier")
    
    # Discover and run tests
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern="test_*.py")
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Return success or failure
    return result.wasSuccessful()

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
