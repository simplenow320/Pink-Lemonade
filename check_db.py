#!/usr/bin/env python3
"""
Database Verification Tool for GrantFlow

This script checks the database connection and configuration.
"""

import os
import sys
import argparse
from urllib.parse import urlparse
import importlib.util

def check_database_url(url):
    """Check if the database URL is valid and parse it."""
    if not url:
        return False, "DATABASE_URL environment variable not set", None
    
    parsed = urlparse(url)
    
    if parsed.scheme == 'sqlite':
        db_type = 'sqlite'
        db_info = {
            'path': parsed.path.lstrip('/'),
            'exists': os.path.exists(parsed.path.lstrip('/')) if parsed.path else False
        }
    elif parsed.scheme == 'postgresql':
        db_type = 'postgresql'
        try:
            # Extract connection details
            username = parsed.username
            password = parsed.password
            hostname = parsed.hostname
            port = parsed.port or 5432
            database = parsed.path.lstrip('/')
            
            db_info = {
                'username': username,
                'hostname': hostname,
                'port': port,
                'database': database
            }
        except Exception as e:
            return False, f"Failed to parse PostgreSQL URL: {e}", None
    else:
        return False, f"Unsupported database scheme: {parsed.scheme}", None
    
    return True, f"Database URL is valid ({db_type})", {'type': db_type, 'info': db_info}

def check_required_packages(db_type):
    """Check if the required packages for the database type are installed."""
    if db_type == 'sqlite':
        # Sqlite is included in Python standard library
        return True, "SQLite support is available in Python"
    
    if db_type == 'postgresql':
        spec = importlib.util.find_spec('psycopg2')
        if spec is None:
            return False, "psycopg2 (PostgreSQL driver) is not installed"
        return True, "PostgreSQL driver (psycopg2) is installed"
    
    return False, f"Unknown database type: {db_type}"

def check_database_connection(db_type, db_info):
    """Check if the database connection works."""
    if db_type == 'sqlite':
        try:
            import sqlite3
            conn = sqlite3.connect(db_info['path'])
            conn.close()
            return True, f"Successfully connected to SQLite database at {db_info['path']}"
        except Exception as e:
            return False, f"Failed to connect to SQLite database: {e}"
    
    if db_type == 'postgresql':
        try:
            import psycopg2
            conn_string = f"host='{db_info['hostname']}' port='{db_info['port']}' dbname='{db_info['database']}' user='{db_info['username']}'"
            if 'password' in db_info and db_info['password']:
                conn_string += f" password='{db_info['password']}'"
            
            conn = psycopg2.connect(conn_string)
            conn.close()
            return True, f"Successfully connected to PostgreSQL database at {db_info['hostname']}:{db_info['port']}/{db_info['database']}"
        except Exception as e:
            return False, f"Failed to connect to PostgreSQL database: {e}"
    
    return False, f"Unknown database type: {db_type}"

def check_tables(db_type, db_info):
    """Check if the required tables exist in the database."""
    if db_type == 'sqlite':
        try:
            import sqlite3
            conn = sqlite3.connect(db_info['path'])
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            conn.close()
            return True, f"Found {len(tables)} tables in SQLite database: {', '.join([t[0] for t in tables])}" if tables else "No tables found in SQLite database"
        except Exception as e:
            return False, f"Failed to check tables in SQLite database: {e}"
    
    if db_type == 'postgresql':
        try:
            import psycopg2
            conn_string = f"host='{db_info['hostname']}' port='{db_info['port']}' dbname='{db_info['database']}' user='{db_info['username']}'"
            if 'password' in db_info and db_info['password']:
                conn_string += f" password='{db_info['password']}'"
            
            conn = psycopg2.connect(conn_string)
            cursor = conn.cursor()
            cursor.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public';")
            tables = cursor.fetchall()
            conn.close()
            return True, f"Found {len(tables)} tables in PostgreSQL database: {', '.join([t[0] for t in tables])}" if tables else "No tables found in PostgreSQL database"
        except Exception as e:
            return False, f"Failed to check tables in PostgreSQL database: {e}"
    
    return False, f"Unknown database type: {db_type}"

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='Check database connection and setup for GrantFlow')
    parser.add_argument('--url', type=str, help='Database URL (if not provided, will use DATABASE_URL from environment)')
    parser.add_argument('--create-tables', action='store_true', help='Create tables if they do not exist')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose output')
    
    args = parser.parse_args()
    
    # Get database URL
    db_url = args.url or os.environ.get('DATABASE_URL')
    
    print("GrantFlow Database Verification Tool")
    print("===================================\n")
    
    # Check database URL
    url_valid, url_message, db_details = check_database_url(db_url)
    print(f"Database URL: {'✓' if url_valid else '✗'} {url_message}")
    
    if not url_valid or db_details is None:
        print("\nPlease check the DATABASE_URL environment variable or provide it with --url")
        sys.exit(1)
    
    db_type = db_details['type']
    db_info = db_details['info']
    
    # Check required packages
    pkg_ok, pkg_message = check_required_packages(db_type)
    print(f"Required Packages: {'✓' if pkg_ok else '✗'} {pkg_message}")
    
    if not pkg_ok:
        print("\nPlease install the required packages for database support")
        sys.exit(1)
    
    # Check database connection
    conn_ok, conn_message = check_database_connection(db_type, db_info)
    print(f"Database Connection: {'✓' if conn_ok else '✗'} {conn_message}")
    
    if not conn_ok:
        print("\nPlease check your database configuration and connection")
        sys.exit(1)
    
    # Check tables
    tables_ok, tables_message = check_tables(db_type, db_info)
    print(f"Database Tables: {tables_message}")
    
    # Summary
    print("\nDatabase Verification Summary:")
    if url_valid and pkg_ok and conn_ok:
        print("✓ Database configuration is valid and connection works")
        if 'No tables found' not in tables_message:
            print("✓ Database has tables")
        else:
            print("! No tables found in database")
            if args.create_tables:
                print("  Attempting to create tables...")
                try:
                    from app import db
                    db.create_all()
                    print("✓ Tables created successfully")
                except Exception as e:
                    print(f"✗ Failed to create tables: {e}")
            else:
                print("  Run with --create-tables to create the database schema")
    else:
        print("✗ Database verification failed")
    
    print("\nFor more information about database setup, see README.md")
    
if __name__ == "__main__":
    main()