#!/usr/bin/env python3
"""
Production-ready startup script for the Flask application.
This script starts Gunicorn without the --reload flag for faster boot times
and better production deployment compatibility.
"""

import os
import subprocess
import sys


def main():
    """Start the application with production-optimized settings."""
    
    # Production Gunicorn command without --reload for faster startup
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--reuse-port",
        "--workers", "2",
        "--timeout", "120",
        "--worker-class", "sync",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "main:app"
    ]
    
    print("Starting production server...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nShutting down gracefully...")
        sys.exit(0)
    except subprocess.CalledProcessError as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()