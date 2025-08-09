#!/usr/bin/env python3
"""
Simple test runner script for Pink Lemonade
"""

import subprocess
import sys
import os

def run_tests():
    """Run pytest with quiet output"""
    # Set Python path to current directory
    env = os.environ.copy()
    env["PYTHONPATH"] = os.getcwd()
    
    try:
        result = subprocess.run(
            ["pytest", "-q"],
            capture_output=False,
            text=True,
            env=env
        )
        return result.returncode
    except FileNotFoundError:
        print("pytest not found. Running simple test instead...")
        result = subprocess.run(
            ["python", "test_scraper_simple.py"],
            capture_output=False,
            text=True,
            env=env
        )
        return result.returncode

if __name__ == "__main__":
    sys.exit(run_tests())