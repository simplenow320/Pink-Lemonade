#!/usr/bin/env python3
"""
Pink Lemonade Brand Compliance Audit
Scans for unapproved colors and logo placement violations
"""

import os
import re
import json
from pathlib import Path
from collections import defaultdict

# Approved Pink Lemonade brand colors
APPROVED_COLORS = {
    # Matte Pink
    '#db2777', '#be185d', '#9f1239', '#881337', '#831843',
    'rgb(219, 39, 119)', 'rgb(190, 24, 93)', 'rgb(159, 18, 57)',
    'rgba(219, 39, 119', 'rgba(190, 24, 93', 'rgba(159, 18, 57',
    
    # White
    '#fff', '#ffffff', 'white', 
    'rgb(255, 255, 255)', 'rgba(255, 255, 255',
    '#fafafa', '#f9fafb', '#f3f4f6',
    
    # Grey 
    '#gray', '#grey', '#333', '#666', '#999', '#ccc', '#ddd', '#eee',
    '#111', '#222', '#444', '#555', '#777', '#888', '#aaa', '#bbb',
    '#1f2937', '#374151', '#4b5563', '#6b7280', '#9ca3af', '#d1d5db', '#e5e7eb', '#f3f4f6',
    'gray', 'grey', 'rgb(107, 114, 128)', 'rgb(156, 163, 175)',
    
    # Black
    '#000', '#000000', 'black',
    'rgb(0, 0, 0)', 'rgba(0, 0, 0',
    
    # Transparent
    'transparent', 'none', 'inherit', 'initial', 'currentColor',
    'rgba(0, 0, 0, 0)', 'rgba(255, 255, 255, 0)'
}

# Additional allowed CSS color properties
SYSTEM_COLORS = {
    'auto', 'unset', 'revert', 'initial', 'inherit', 'currentcolor',
    'buttonface', 'canvas', 'field', 'fieldtext', 'graytext', 'highlight',
    'highlighttext', 'linktext', 'visitedtext', 'windowframe', 'window'
}

# Color patterns to find
COLOR_PATTERNS = [
    r'#[0-9a-fA-F]{3,8}\b',  # Hex colors
    r'rgb\([^)]+\)',          # RGB colors
    r'rgba\([^)]+\)',         # RGBA colors
    r'hsl\([^)]+\)',          # HSL colors
    r'hsla\([^)]+\)',         # HSLA colors
]

# CSS properties that contain colors
COLOR_PROPERTIES = [
    'color:', 'background-color:', 'background:', 'border-color:',
    'border-top-color:', 'border-right-color:', 'border-bottom-color:', 'border-left-color:',
    'outline-color:', 'text-decoration-color:', 'box-shadow:', 'text-shadow:',
    'fill:', 'stroke:', 'stop-color:', 'flood-color:', 'lighting-color:'
]

class BrandAuditor:
    def __init__(self):
        self.violations = []
        self.logo_locations = []
        self.files_scanned = 0
        self.total_violations = 0
        
    def is_approved_color(self, color):
        """Check if a color is in the approved palette"""
        color_lower = color.lower().strip()
        
        # Remove semicolons and quotes
        color_lower = color_lower.replace(';', '').replace('"', '').replace("'", '')
        
        # Check if it's a system color or approved color
        if color_lower in SYSTEM_COLORS:
            return True
            
        # Check approved colors
        for approved in APPROVED_COLORS:
            if color_lower.startswith(approved.lower()):
                return True
        
        # Check for CSS variables (custom properties)
        if color_lower.startswith('var(--'):
            return True
            
        return False
    
    def scan_file_for_colors(self, filepath):
        """Scan a file for color violations"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            return
        
        file_violations = []
        
        # Check each line for color properties
        for line_num, line in enumerate(lines, 1):
            line_lower = line.lower()
            
            # Skip comments
            if '/*' in line or '//' in line or '<!--' in line:
                continue
            
            # Check for color properties
            for prop in COLOR_PROPERTIES:
                if prop in line_lower:
                    # Extract the color value
                    parts = line.split(prop)
                    if len(parts) > 1:
                        value = parts[1].split(';')[0].strip()
                        if value and not self.is_approved_color(value):
                            file_violations.append({
                                'line': line_num,
                                'property': prop,
                                'value': value,
                                'code': line.strip()
                            })
            
            # Check for hex colors in inline styles
            if 'style=' in line_lower:
                hex_matches = re.findall(r'#[0-9a-fA-F]{3,8}\b', line)
                for hex_color in hex_matches:
                    if not self.is_approved_color(hex_color):
                        file_violations.append({
                            'line': line_num,
                            'property': 'inline style',
                            'value': hex_color,
                            'code': line.strip()[:100]
                        })
        
        if file_violations:
            self.violations.append({
                'file': filepath,
                'violations': file_violations
            })
            self.total_violations += len(file_violations)
    
    def scan_for_logo(self, filepath):
        """Check for logo occurrences in a file"""
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
        except:
            return
        
        # Look for logo references
        logo_patterns = [
            r'logo\.(png|jpg|jpeg|svg|gif)',
            r'pink-lemonade-logo',
            r'brand-logo',
            r'company-logo',
            r'<img[^>]*logo[^>]*>',
            r'src=["\'][^"\']*logo[^"\']*["\']'
        ]
        
        for line_num, line in enumerate(lines, 1):
            for pattern in logo_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    self.logo_locations.append({
                        'file': filepath,
                        'line': line_num,
                        'code': line.strip()[:100]
                    })
    
    def scan_directory(self, directory):
        """Scan all relevant files in a directory"""
        extensions = ['.html', '.css', '.js', '.jsx', '.ts', '.tsx']
        
        for root, dirs, files in os.walk(directory):
            # Skip node_modules and hidden directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
            
            for file in files:
                if any(file.endswith(ext) for ext in extensions):
                    filepath = os.path.join(root, file)
                    self.files_scanned += 1
                    self.scan_file_for_colors(filepath)
                    self.scan_for_logo(filepath)
    
    def generate_report(self):
        """Generate the brand compliance report"""
        report = []
        report.append("# Pink Lemonade Brand Compliance Audit Report")
        report.append(f"\n**Date:** {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Files Scanned:** {self.files_scanned}")
        report.append(f"**Total Violations:** {self.total_violations}")
        report.append(f"**Logo Occurrences:** {len(self.logo_locations)}")
        
        # Color violations
        report.append("\n## Color Violations\n")
        if self.violations:
            report.append("### Files with Unapproved Colors:\n")
            for file_data in self.violations:
                report.append(f"\n#### {file_data['file']}")
                report.append(f"**Violations: {len(file_data['violations'])}**\n")
                for v in file_data['violations'][:10]:  # Show first 10
                    report.append(f"- Line {v['line']}: `{v['property']}` = `{v['value']}`")
                    report.append(f"  ```")
                    report.append(f"  {v['code']}")
                    report.append(f"  ```")
                if len(file_data['violations']) > 10:
                    report.append(f"- ... and {len(file_data['violations']) - 10} more violations")
        else:
            report.append("✅ **No color violations found!** All colors comply with brand guidelines.")
        
        # Logo placement
        report.append("\n## Logo Placement Audit\n")
        if self.logo_locations:
            if len(self.logo_locations) == 1:
                report.append("✅ **Logo appears once** (compliant)")
            else:
                report.append(f"⚠️ **Logo appears {len(self.logo_locations)} times** (should appear only once)")
            
            report.append("\n### Logo Locations:\n")
            for loc in self.logo_locations:
                report.append(f"- {loc['file']} (Line {loc['line']})")
                report.append(f"  ```")
                report.append(f"  {loc['code']}")
                report.append(f"  ```")
        else:
            report.append("⚠️ **No logo found** - Logo should appear once in landing hero")
        
        # Brand compliance summary
        report.append("\n## Compliance Summary\n")
        report.append("### Approved Brand Palette:")
        report.append("- **Matte Pink:** #db2777, #be185d, #9f1239")
        report.append("- **White:** #ffffff, #fafafa")
        report.append("- **Grey:** #6b7280, #9ca3af, #d1d5db")
        report.append("- **Black:** #000000")
        
        if self.total_violations == 0 and len(self.logo_locations) == 1:
            report.append("\n## ✅ BRAND COMPLIANT")
            report.append("All files pass brand compliance checks!")
        else:
            report.append("\n## ❌ BRAND VIOLATIONS DETECTED")
            report.append("Please fix the violations listed above.")
        
        return "\n".join(report)


def main():
    print("=" * 60)
    print("PINK LEMONADE BRAND COMPLIANCE AUDIT")
    print("=" * 60)
    
    auditor = BrandAuditor()
    
    # Get the absolute path to the project root
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # Scan app directories with absolute paths
    directories = [
        os.path.join(project_root, 'app', 'templates'),
        os.path.join(project_root, 'app', 'static')
    ]
    
    for directory in directories:
        if os.path.exists(directory):
            print(f"Scanning {directory}...")
            auditor.scan_directory(directory)
        else:
            print(f"Directory not found: {directory}")
    
    # Generate and save report
    report = auditor.generate_report()
    
    # Save to file in current directory
    report_path = os.path.join(current_dir, 'BRAND_REPORT.md')
    with open(report_path, 'w') as f:
        f.write(report)
    
    print(f"\nFiles scanned: {auditor.files_scanned}")
    print(f"Color violations: {auditor.total_violations}")
    print(f"Logo occurrences: {len(auditor.logo_locations)}")
    print(f"\nReport saved to: {report_path}")
    
    return auditor.total_violations == 0 and len(auditor.logo_locations) <= 1


if __name__ == "__main__":
    compliant = main()
    exit(0 if compliant else 1)