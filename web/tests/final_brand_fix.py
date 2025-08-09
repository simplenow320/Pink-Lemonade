#!/usr/bin/env python3
"""
Final comprehensive brand fix for Pink Lemonade
"""

import os
import re

def fix_all_violations():
    """Fix all brand violations comprehensively"""
    
    # Get project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    templates_dir = os.path.join(project_root, 'app', 'templates')
    
    files_to_fix = {
        'opportunities.html': [
            ('--pink: #ec4899;', '--pink: #db2777;'),
        ],
        'profile.html': [
            ('--pink: #ec4899;', '--pink: #db2777;'),
        ],
        'dashboard.html': [
            ('background-color: r#f3f4f6;', 'background-color: #f3f4f6;'),
            ('box-shadow: 0 2px 8px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 8px 16px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('background: linear-gradient(135deg, var(--pink), var(--pink-dark));', 'background: #db2777;'),
        ],
        'scraper.html': [
            ('box-shadow: 0 2px 5px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('#065f46', '#374151'),
            ('#e0f2fe', '#f3f4f6'),
            ('#075985', '#374151'),
            ('#fee2e2', '#f3f4f6'),
            ('#b91c1c', '#831843'),
            ('#f9f9f9', '#fafafa'),
        ],
        'api-test.html': [
            ('background: linear-gradient(135deg, var(--pink-light) 0%, var(--pink) 100%);', 'background: #db2777;'),
            ('box-shadow: 0 4px 8px rgba(255, 105, 180, 0.2);', 'border: 1px solid #e5e7eb;'),
            ('#4ade80', '#db2777'),
            ('#94a3b8', '#6b7280'),
        ],
        'grants.html': [
            ('background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);', 'background: #f3f4f6;'),
            ('box-shadow: 0 2px 8px rgba(0,0,0,0.1);', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 8px 16px rgba(0,0,0,0.15);', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 0 0 3px rgba(236, 72, 153, 0.1);', 'border: 2px solid #db2777;'),
            ('#d1fae5', '#f3f4f6'),
            ('#fef3c7', '#f3f4f6'),
            ('#fee2e2', '#f3f4f6'),
            ('#10b981', '#db2777'),
            ('#eab308', '#6b7280'),
            ('#ef4444', '#831843'),
            ('#e0f2fe', '#f3f4f6'),
            ('#075985', '#374151'),
        ],
        'crm-dashboard.html': [
            ('background: #ffffff;', 'background: #ffffff;'),
            ('box-shadow: 0 1px 3px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 4px 6px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('background: #ffffff;', 'background: #ffffff;'),
            ('#fef3c7', '#f3f4f6'),
            ('#fee2e2', '#f3f4f6'),
            ('#10b981', '#db2777'),
            ('#f59e0b', '#6b7280'),
            ('#ef4444', '#831843'),
            ('#059669', '#374151'),
        ],
        'applications.html': [
            ('background-color: r#f3f4f6;', 'background-color: #f3f4f6;'),
            ('box-shadow: 0 2px 8px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 0 0 3px r#f3f4f6;', 'border: 2px solid #db2777;'),
            ('background: #ffffff;', 'background: #ffffff;'),
        ],
        'foundation-directory.html': [
            ('background-color: r#f3f4f6;', 'background-color: #f3f4f6;'),
            ('box-shadow: 0 2px 8px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 8px 16px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 0 0 3px r#f3f4f6;', 'border: 2px solid #db2777;'),
        ],
        'discovery.html': [
            ('background: #ffffff;', 'background: #ffffff;'),
            ('box-shadow: 0 1px 3px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
        ],
        'landing.html': [
            ('background: #ffffff;', 'background: #ffffff;'),
            ('box-shadow: 0 4px 6px r#f3f4f6;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 6px 12px r#f3f4f6;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 2px 8px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
            ('box-shadow: 0 8px 16px r#e5e7eb;', 'border: 1px solid #e5e7eb;'),
        ],
    }
    
    # Fix each file
    for filename, replacements in files_to_fix.items():
        filepath = os.path.join(templates_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r') as f:
                content = f.read()
            
            for old, new in replacements:
                content = content.replace(old, new)
            
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"Fixed: {filename}")
    
    # Remove all logo occurrences except in landing.html
    for root, dirs, files in os.walk(templates_dir):
        for file in files:
            if file.endswith('.html') and file != 'landing.html':
                filepath = os.path.join(root, file)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                # Remove logo references
                original = content
                content = re.sub(r'<img[^>]*logo[^>]*>', '', content, flags=re.IGNORECASE)
                content = re.sub(r'Pink Lemonade Logo', '', content, flags=re.IGNORECASE)
                
                if content != original:
                    with open(filepath, 'w') as f:
                        f.write(content)
                    print(f"Removed logos from: {file}")

if __name__ == "__main__":
    fix_all_violations()
    print("Brand fixes applied!")