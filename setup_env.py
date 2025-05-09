#!/usr/bin/env python3
"""
Setup Environment Script for GrantFlow

This script initializes the environment by:
1. Copying .env.example to .env if it doesn't exist
2. Prompting for required values
3. Validating the values
4. Saving the updated .env file
"""

import os
import re
import sys
import shutil
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
        return False, "OpenAI API key cannot be empty or the default value"
    
    if not key.startswith("sk-") or len(key) < 20:
        return False, "OpenAI API key should start with 'sk-' and be at least 20 characters"
    
    return True, "OpenAI API key format is valid"

def main():
    """Main function to set up the environment."""
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
        overwrite = input(f"{env_path} already exists. Overwrite? (y/n): ")
        if overwrite.lower() != 'y':
            print("Setup cancelled.")
            sys.exit(0)
    else:
        # Copy .env.example to .env
        shutil.copy2(env_example_path, env_path)
        print(f"Created {env_path} from {env_example_path}")
    
    # Load current .env content
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    # Parse and prompt for values
    env_vars = {}
    for line in env_example_content.splitlines():
        line = line.strip()
        if not line or line.startswith('#'):
            continue
        
        var_match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', line)
        if var_match:
            key, default_value = var_match.groups()
            env_vars[key] = default_value
    
    # Now prompt for each value and validate
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
            
            # Extract current value from .env if it exists
            current_value = None
            for env_line in env_content.splitlines():
                env_var_match = re.match(r'^([A-Za-z0-9_]+)=(.*)$', env_line.strip())
                if env_var_match and env_var_match.group(1) == key:
                    current_value = env_var_match.group(2)
                    break
            
            # Use current value or default
            if current_value and current_value != default_value:
                prompt_value = current_value
            else:
                prompt_value = default_value
            
            # Prompt for value
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
                new_value = input(f"{key} [{prompt_value}]: ") or prompt_value
                valid, message = validate_session_secret(new_value)
                while not valid:
                    print(f"Validation failed: {message}")
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
            
            new_line = f"{key}={new_value}"
        
        new_env_content.append(new_line)
    
    # Write updated content back to .env
    with open(env_path, 'w') as f:
        f.write('\n'.join(new_env_content))
    
    print(f"\n{env_path} has been updated successfully.")
    print("Environment setup complete.")

if __name__ == "__main__":
    main()