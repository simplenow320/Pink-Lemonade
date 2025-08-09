#!/usr/bin/env python3
"""
Fix all Pink Lemonade brand violations
Updates all files to use only approved colors and ensures logo appears only once
"""

import os
import re
from pathlib import Path

# Define approved brand colors
APPROVED_REPLACEMENTS = {
    # Box shadows - replace with solid borders or remove
    r'box-shadow:\s*[^;]+rgba\([^)]+\)[^;]*;': 'border: 1px solid #e5e7eb;',
    r'box-shadow:\s*[^;]+#[0-9a-fA-F]+[^;]*;': 'border: 1px solid #e5e7eb;',
    
    # Gradients - replace with solid colors
    r'background:\s*linear-gradient[^;]+;': 'background: #ffffff;',
    r'background-image:\s*linear-gradient[^;]+;': 'background: #ffffff;',
    
    # Non-approved specific colors
    '#f5f5f5': '#f3f4f6',  # Light grey
    '#3B82F6': '#db2777',  # Blue to pink
    '#2563EB': '#9f1239',  # Dark blue to dark pink
    '#93c5fd': '#f3f4f6',  # Light blue to light grey
    '#d1fae5': '#f3f4f6',  # Light green to light grey
    '#10b981': '#db2777',  # Green to pink
    '#84cc16': '#be185d',  # Light green to medium pink
    '#eab308': '#6b7280',  # Yellow to grey
    '#f97316': '#9f1239',  # Orange to dark pink
    '#ef4444': '#831843',  # Red to darkest pink
    '#fef3c7': '#f3f4f6',  # Light yellow to light grey
    '#fde68a': '#e5e7eb',  # Yellow to border grey
    '#92400e': '#374151',  # Brown to dark grey
    '#ec4899': '#db2777',  # Bright pink to matte pink
    
    # RGBA colors with opacity - convert to solid equivalents
    r'rgba\(236,\s*72,\s*153,\s*0\.\d+\)': '#f3f4f6',
    r'rgba\(219,\s*39,\s*119,\s*0\.\d+\)': '#f3f4f6',
    r'rgba\(0,\s*0,\s*0,\s*0\.\d+\)': '#e5e7eb',
    r'rgba\(90,\s*103,\s*216,\s*0\.\d+\)': '#f3f4f6',
    r'rgba\(249,\s*168,\s*212,\s*0\.\d+\)': '#f3f4f6',
}

def fix_file(filepath):
    """Fix brand violations in a single file"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply all replacements
        for pattern, replacement in APPROVED_REPLACEMENTS.items():
            if pattern.startswith('r'):
                # It's a regex pattern
                content = re.sub(pattern[1:], replacement, content)
            else:
                # It's a simple string replacement
                content = content.replace(pattern, replacement)
        
        # Fix fit score classes to use approved colors
        content = re.sub(r'\.fit-score-5\s*{\s*background:\s*#10b981;', '.fit-score-5 { background: #db2777;', content)
        content = re.sub(r'\.fit-score-4\s*{\s*background:\s*#84cc16;', '.fit-score-4 { background: #be185d;', content)
        content = re.sub(r'\.fit-score-3\s*{\s*background:\s*#eab308;', '.fit-score-3 { background: #6b7280;', content)
        content = re.sub(r'\.fit-score-2\s*{\s*background:\s*#f97316;', '.fit-score-2 { background: #9f1239;', content)
        content = re.sub(r'\.fit-score-1\s*{\s*background:\s*#ef4444;', '.fit-score-1 { background: #831843;', content)
        
        # Remove logo references except in landing.html
        if 'landing.html' not in filepath:
            # Remove all logo references in non-landing pages
            content = re.sub(r'<img[^>]*logo[^>]*>[^<]*</img>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'<img[^>]*logo[^>]*/>', '', content, flags=re.IGNORECASE)
            content = re.sub(r'\.logo[^{]*{[^}]*}', '', content, flags=re.IGNORECASE)
        
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")
        return False

def main():
    print("=" * 60)
    print("FIXING PINK LEMONADE BRAND VIOLATIONS")
    print("=" * 60)
    
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Directories to fix
    directories = [
        os.path.join(project_root, 'app', 'templates'),
        os.path.join(project_root, 'app', 'static')
    ]
    
    files_fixed = 0
    total_files = 0
    
    for directory in directories:
        if not os.path.exists(directory):
            continue
            
        for root, dirs, files in os.walk(directory):
            # Skip node_modules and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                if file.endswith(('.html', '.css', '.js', '.jsx')):
                    filepath = os.path.join(root, file)
                    total_files += 1
                    if fix_file(filepath):
                        files_fixed += 1
                        print(f"✓ Fixed: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"Fixed {files_fixed} out of {total_files} files")
    print("=" * 60)
    
    return files_fixed > 0

if __name__ == "__main__":
    main()