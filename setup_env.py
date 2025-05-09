#!/usr/bin/env python3
"""
Setup Environment Script for GrantFlow

This script initializes the environment by:
1. Copying .env.example to .env if it doesn't exist
2. Prompting for required values
3. Validating the values
4. Saving the updated .env file

Usage:
  ./setup_env.py           # Interactive mode with prompts
  ./setup_env.py --non-interactive  # Use default values without prompts
  ./setup_env.py --help    # Show help message
"""

import os
import re
import sys
import shutil
import secrets
import argparse
from urllib.parse import urlparse

# Validation functions
def validate_database_url(url):
    """Validate the database URL."""
    if not url:
        return False, "Database URL cannot be empty"
    
    parsed = urlparse(url)
    if parsed.scheme not in ['sqlite', 'postgresql']:
        return False, "Database URL must start with sqlite:// or postgresql://"
    
    return True, "Database URL is valid"

def validate_session_secret(secret):
    """Validate the session secret."""
    if not secret or secret == "your_secret_key_here":
        return False, "Session secret cannot be empty or the default value"
    
    if len(secret) < 16:
        return False, "Session secret should be at least 16 characters long"
    
    return True, "Session secret is valid"

def validate_openai_api_key(key):
    """Validate the OpenAI API key format."""
    if not key or key == "your_openai_api_key_here":
        # Special case for non-interactive mode - we'll allow this to pass
        # but print a warning
        if key == "your_openai_api_key_here":
            print("WARNING: Using default OpenAI API key placeholder. AI features will not work.")
            return True, "OpenAI API key is a placeholder"
        return False, "OpenAI API key cannot be empty"
    
    if not key.startswith("sk-") or len(key) < 20:
        return False, "OpenAI API key should start with 'sk-' and be at least 20 characters"
    
    return True, "OpenAI API key format is valid"

def generate_session_secret():
    """Generate a secure random session secret."""
    return secrets.token_hex(24)  # 48 character hex string

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Setup environment variables for GrantFlow')
    parser.add_argument('--non-interactive', action='store_true', 
                        help='Run in non-interactive mode (use defaults)')
    parser.add_argument('--force', '-f', action='store_true',
                        help='Force overwrite of existing .env file')
    parser.add_argument('--database-url', type=str,
                        help='Set the DATABASE_URL environment variable')
    parser.add_argument('--session-secret', type=str,
                        help='Set the SESSION_SECRET environment variable')
    parser.add_argument('--openai-api-key', type=str,
                        help='Set the OPENAI_API_KEY environment variable')
    
    return parser.parse_args()

def main():
    """Main function to set up the environment."""
    args = parse_arguments()
    
    env_example_path = '.env.example'
    env_path = '.env'
    
    # Check if .env.example exists
    if not os.path.exists(env_example_path):
        print(f"Error: {env_example_path} does not exist.")
        sys.exit(1)
    
    # Load .env.example content
    with open(env_example_path, 'r') as f:
        env_example_content = f.read()
    
    # Check if .env exists
    if os.path.exists(env_path):
        if args.force:
            proceed_with_overwrite = True
        elif args.non_interactive:
            print(f"{env_path} already exists. Use --force to overwrite.")
            sys.exit(0)
        else:
            overwrite = input(f"{env_path} already exists. Overwrite? (y/n): ")
            proceed_with_overwrite = overwrite.lower() == 'y'
            
        if not proceed_with_overwrite:
            print("Setup cancelled.")
            sys.exit(0)
    
    # Copy .env.example to .env if it doesn't exist or we're overwriting
    if not os.path.exists(env_path) or args.force:
        shutil.copy2(env_example_path, env_path)
        print(f"Created {env_path} from {env_example_path}")
    
    # Load current .env content
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Parse env vars
    env_vars = {}
    for line in env_example_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        var_match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line)
        if var_match:
            key, default_value = var_match.groups()
            env_vars[key] = default_value
    
    # Extract current values from .env
    current_values = {}
    for line in env_content.splitlines():
        var_match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line.strip())
        if var_match:
            key, value = var_match.groups()
            current_values[key] = value
    
    # Now prompt for each value and validate, or use provided arguments
    new_env_content = []
    for line in env_example_content.splitlines():
        line = line.strip()
        new_line = line
        
        if not line or line.startswith('#'):
            new_env_content.append(line)
            continue
        
        var_match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line)
        if var_match:
            key, default_value = var_match.groups()
            
            # Use command line arg if provided
            if key == 'DATABASE_URL' and args.database_url:
                new_value = args.database_url
            elif key == 'SESSION_SECRET' and args.session_secret:
                new_value = args.session_secret
            elif key == 'OPENAI_API_KEY' and args.openai_api_key:
                new_value = args.openai_api_key
            # Use existing value if available
            elif key in current_values and current_values[key] != default_value:
                new_value = current_values[key]
            # Generate a secure session secret
            elif key == 'SESSION_SECRET' and (default_value == 'your_secret_key_here' or not default_value):
                new_value = generate_session_secret()
                print(f"Generated secure SESSION_SECRET")
            # Use default for non-interactive mode
            elif args.non_interactive:
                new_value = default_value
            # Prompt for value in interactive mode
            else:
                prompt_value = current_values.get(key, default_value)
                
                if key == 'DATABASE_URL':
                    print("\nDatabase Configuration")
                    new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                    valid, message = validate_database_url(new_value)
                    while not valid:
                        print(f"Validation failed: {message}")
                        new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                        valid, message = validate_database_url(new_value)
                
                elif key == 'SESSION_SECRET':
                    print("\nFlask Configuration")
                    if prompt_value == 'your_secret_key_here':
                        prompt_value = generate_session_secret()
                        print(f"Generated new secure session secret")
                    
                    new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                    valid, message = validate_session_secret(new_value)
                    while not valid:
                        print(f"Validation failed: {message}")
                        if new_value == 'your_secret_key_here':
                            new_value = generate_session_secret()
                            print(f"Generated new secure session secret: {new_value}")
                        else:
                            new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                        valid, message = validate_session_secret(new_value)
                
                elif key == 'OPENAI_API_KEY':
                    print("\nOpenAI Configuration")
                    new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                    valid, message = validate_openai_api_key(new_value)
                    while not valid:
                        print(f"Validation failed: {message}")
                        new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                        valid, message = validate_openai_api_key(new_value)
                
                else:
                    new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
            
            # Validate the values
            if key == 'DATABASE_URL':
                valid, message = validate_database_url(new_value)
                if not valid and not args.non_interactive:
                    print(f"Error: {message}")
                    sys.exit(1)
                
            elif key == 'SESSION_SECRET':
                valid, message = validate_session_secret(new_value)
                if not valid:
                    if args.non_interactive or args.session_secret:
                        print(f"Error: {message}")
                        sys.exit(1)
                    else:
                        new_value = generate_session_secret()
                        print(f"Generated secure session secret: {new_value}")
                
            elif key == 'OPENAI_API_KEY':
                valid, message = validate_openai_api_key(new_value)
                if not valid and not args.non_interactive:
                    print(f"Error: {message}")
                    sys.exit(1)
            
            new_line = f"{key}={new_value}"
        
        new_env_content.append(new_line)
    
    # Write updated content back to .env
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_env_content))
    
    print(f"\n{env_path} has been updated successfully.")
    print("Environment setup complete.")

if __name__ == "__main__":
    main()