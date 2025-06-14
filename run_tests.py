#!/usr/bin/env python3

"""
Test runner for claude-history tool.

Usage:
    python3 run_tests.py              # Run all tests
    python3 run_tests.py unit         # Run only unit tests
    python3 run_tests.py integration  # Run only integration tests
"""

import sys
import unittest


def run_unit_tests():
    """Run unit tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_claude_history')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_integration_tests():
    """Run integration tests."""
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_integration')
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def run_all_tests():
    """Run all tests."""
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add unit tests
    suite.addTests(loader.loadTestsFromName('test_claude_history'))
    
    # Add integration tests
    suite.addTests(loader.loadTestsFromName('test_integration'))
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    return result.wasSuccessful()


def main():
    """Main function to handle command line arguments."""
    if len(sys.argv) > 1:
        test_type = sys.argv[1].lower()
        if test_type == 'unit':
            success = run_unit_tests()
        elif test_type == 'integration':
            success = run_integration_tests()
        else:
            print(f"Unknown test type: {test_type}")
            print("Usage: python3 run_tests.py [unit|integration]")
            sys.exit(1)
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()