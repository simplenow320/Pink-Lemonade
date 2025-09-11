#!/usr/bin/env python3
"""
Deployment script to work around .replit configuration issues.
This script ensures proper deployment setup for Replit Autoscale.
"""

import os
import sys
import subprocess
import signal


def cleanup_ports():
    """Kill any processes that might be using conflicting ports."""
    try:
        # Kill any existing gunicorn processes
        subprocess.run(["pkill", "-f", "gunicorn"], capture_output=True)
        print("Cleaned up existing processes")
    except Exception as e:
        print(f"Cleanup warning: {e}")


def start_production_server():
    """Start the server with production-optimized settings for deployment."""
    
    # Cleanup any conflicting processes
    cleanup_ports()
    
    # Production command optimized for Replit Autoscale deployment
    cmd = [
        "gunicorn",
        "--bind", "0.0.0.0:5000",
        "--workers", "1",  # Single worker for Autoscale
        "--timeout", "120",
        "--worker-class", "sync",
        "--max-requests", "1000",
        "--max-requests-jitter", "100",
        "--preload",  # Preload app for faster startup
        "--worker-tmp-dir", "/dev/shm",  # Use RAM for worker files
        "main:app"
    ]
    
    print("Starting deployment-optimized server...")
    print(f"Command: {' '.join(cmd)}")
    
    # Handle graceful shutdown
    def signal_handler(sig, frame):
        print("\nShutting down gracefully...")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # Start the server
        process = subprocess.Popen(cmd)
        process.wait()
    except Exception as e:
        print(f"Error starting server: {e}")
        sys.exit(1)


if __name__ == "__main__":
    start_production_server()