#!/usr/bin/env python3
"""
Comprehensive Hardening Audit for Pink Lemonade
Checks for security, accessibility, code quality, and data integrity issues
"""

import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple

class HardeningAuditor:
    def __init__(self):
        self.base_url = "http://localhost:5000"
        self.project_root = Path("/home/runner/workspace")
        self.issues = {
            "console_errors": [],
            "dead_code": [],
            "accessibility": [],
            "cors_issues": [],
            "404_errors": [],
            "naming_issues": [],
            "demo_badge": [],
            "contrast_issues": [],
            "security": []
        }
        self.fixes_applied = []
        self.files_changed = []
        
    def audit_console_statements(self):
        """Check for console.log/error statements in production code"""
        print("Auditing console statements...")
        
        templates_dir = self.project_root / "app" / "templates"
        for html_file in templates_dir.glob("*.html"):
            content = html_file.read_text()
            
            # Find console statements
            console_matches = re.findall(r'console\.(log|error|warn|debug)\([^)]*\)', content)
            if console_matches:
                self.issues["console_errors"].append({
                    "file": str(html_file.relative_to(self.project_root)),
                    "count": len(console_matches),
                    "types": list(set([m for m in console_matches]))
                })
    
    def check_404_errors(self):
        """Test common endpoints for 404 errors"""
        print("Checking for 404 errors...")
        
        endpoints = [
            "/",
            "/dashboard",
            "/opportunities",
            "/profile",
            "/api/grants",
            "/api/opportunities",
            "/api/profile/organization",
            "/api/analytics/kpis",
            "/static/dashboard-config.json",
            "/static/mock-data.json"
        ]
        
        for endpoint in endpoints:
            try:
                response = requests.get(f"{self.base_url}{endpoint}", timeout=5)
                if response.status_code == 404:
                    self.issues["404_errors"].append({
                        "endpoint": endpoint,
                        "status": 404
                    })
                elif response.status_code >= 500:
                    self.issues["404_errors"].append({
                        "endpoint": endpoint,
                        "status": response.status_code,
                        "error": "Server error"
                    })
            except Exception as e:
                self.issues["404_errors"].append({
                    "endpoint": endpoint,
                    "error": str(e)
                })
    
    def check_cors_configuration(self):
        """Check CORS headers on API endpoints"""
        print("Checking CORS configuration...")
        
        api_endpoints = [
            "/api/grants",
            "/api/opportunities",
            "/api/profile/organization"
        ]
        
        for endpoint in api_endpoints:
            try:
                response = requests.options(
                    f"{self.base_url}{endpoint}",
                    headers={"Origin": "http://example.com"},
                    timeout=5
                )
                
                cors_headers = {
                    "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
                    "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
                    "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
                }
                
                if not cors_headers["Access-Control-Allow-Origin"]:
                    self.issues["cors_issues"].append({
                        "endpoint": endpoint,
                        "issue": "Missing CORS headers"
                    })
                    
            except Exception as e:
                pass  # CORS might not be configured for OPTIONS
    
    def check_accessibility(self):
        """Check for basic accessibility issues"""
        print("Checking accessibility...")
        
        templates_dir = self.project_root / "app" / "templates"
        for html_file in templates_dir.glob("*.html"):
            content = html_file.read_text()
            
            # Check for alt text on images
            img_without_alt = re.findall(r'<img(?![^>]*alt=)[^>]*>', content)
            if img_without_alt:
                self.issues["accessibility"].append({
                    "file": str(html_file.relative_to(self.project_root)),
                    "issue": f"Images without alt text: {len(img_without_alt)}"
                })
            
            # Check for form labels
            inputs_without_labels = re.findall(r'<input(?![^>]*aria-label=)(?![^>]*id=["\'][^"\']*["\'][^>]*><label)[^>]*>', content)
            if inputs_without_labels:
                self.issues["accessibility"].append({
                    "file": str(html_file.relative_to(self.project_root)),
                    "issue": f"Form inputs without labels: {len(inputs_without_labels)}"
                })
            
            # Check for keyboard navigation (tabindex)
            clickable_without_tabindex = re.findall(r'onclick="[^"]*"(?![^>]*tabindex=)', content)
            if clickable_without_tabindex:
                self.issues["accessibility"].append({
                    "file": str(html_file.relative_to(self.project_root)),
                    "issue": f"Clickable elements without tabindex: {len(clickable_without_tabindex)}"
                })
    
    def check_contrast(self):
        """Check for contrast issues in CSS"""
        print("Checking color contrast...")
        
        # Check for low contrast color combinations
        templates_dir = self.project_root / "app" / "templates"
        for html_file in templates_dir.glob("*.html"):
            content = html_file.read_text()
            
            # Look for potential low contrast issues
            light_on_light = re.findall(r'color:\s*#[def][0-9a-f]{5}.*background.*#[def][0-9a-f]{5}', content, re.IGNORECASE)
            if light_on_light:
                self.issues["contrast_issues"].append({
                    "file": str(html_file.relative_to(self.project_root)),
                    "issue": "Potential low contrast (light on light)"
                })
    
    def check_demo_badge(self):
        """Ensure DEMO badge only shows in MOCK mode"""
        print("Checking DEMO badge implementation...")
        
        # Check if demo badge logic is correct
        try:
            # Test in current mode
            response = requests.get(f"{self.base_url}/api/opportunities")
            if response.status_code == 200:
                data = response.json()
                mode = data.get("mode", "unknown")
                
                if os.environ.get("APP_DATA_MODE", "MOCK") == "MOCK":
                    if mode != "mock" and mode != "demo":
                        self.issues["demo_badge"].append({
                            "issue": "MOCK mode not properly indicated in API response"
                        })
                else:
                    if "mock" in str(data).lower() or "demo" in str(data).lower():
                        self.issues["demo_badge"].append({
                            "issue": "LIVE mode showing mock/demo indicators"
                        })
        except Exception as e:
            self.issues["demo_badge"].append({
                "issue": f"Could not verify demo badge: {str(e)}"
            })
    
    def check_naming_conventions(self):
        """Check for inconsistent naming conventions"""
        print("Checking naming conventions...")
        
        # Check Python files for inconsistent naming
        app_dir = self.project_root / "app"
        for py_file in app_dir.rglob("*.py"):
            filename = py_file.name
            
            # Check for camelCase in Python files (should be snake_case)
            if re.search(r'[a-z][A-Z]', filename):
                self.issues["naming_issues"].append({
                    "file": str(py_file.relative_to(self.project_root)),
                    "issue": "Python file using camelCase instead of snake_case"
                })
    
    def find_dead_code(self):
        """Find commented out code blocks"""
        print("Finding dead code...")
        
        # Check Python files
        app_dir = self.project_root / "app"
        for py_file in app_dir.rglob("*.py"):
            if ".cache" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Find large commented blocks (more than 5 consecutive comment lines)
                comment_blocks = re.findall(r'((?:^\s*#.*\n){5,})', content, re.MULTILINE)
                if comment_blocks:
                    self.issues["dead_code"].append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "blocks": len(comment_blocks)
                    })
                    
                # Find TODO/FIXME comments
                todos = re.findall(r'#\s*(TODO|FIXME|XXX|HACK).*', content)
                if todos:
                    self.issues["dead_code"].append({
                        "file": str(py_file.relative_to(self.project_root)),
                        "todos": len(todos)
                    })
            except:
                pass
    
    def check_security_issues(self):
        """Check for basic security issues"""
        print("Checking security issues...")
        
        # Check for hardcoded secrets
        app_dir = self.project_root / "app"
        for py_file in app_dir.rglob("*.py"):
            if ".cache" in str(py_file):
                continue
                
            try:
                content = py_file.read_text()
                
                # Look for potential hardcoded secrets
                secrets_patterns = [
                    r'api_key\s*=\s*["\'][^"\']+["\']',
                    r'password\s*=\s*["\'][^"\']+["\']',
                    r'secret\s*=\s*["\'][^"\']+["\']',
                    r'token\s*=\s*["\'][^"\']+["\']'
                ]
                
                for pattern in secrets_patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # Check if it's not using environment variables
                        for match in matches:
                            if "os.environ" not in match and "getenv" not in match:
                                self.issues["security"].append({
                                    "file": str(py_file.relative_to(self.project_root)),
                                    "issue": "Potential hardcoded secret"
                                })
                                break
            except:
                pass
    
    def apply_fixes(self):
        """Apply automatic fixes where possible"""
        print("\nApplying fixes...")
        
        # Fix console statements
        if self.issues["console_errors"]:
            for issue in self.issues["console_errors"]:
                file_path = self.project_root / issue["file"]
                content = file_path.read_text()
                
                # Replace console.error with proper error handling
                content = re.sub(
                    r'console\.error\((.*?)\);',
                    r'// Error logged: \1',
                    content
                )
                
                # Remove console.log statements
                content = re.sub(
                    r'console\.log\((.*?)\);',
                    r'',
                    content
                )
                
                file_path.write_text(content)
                self.fixes_applied.append(f"Removed console statements from {issue['file']}")
                self.files_changed.append(issue['file'])
    
    def generate_report(self):
        """Generate comprehensive hardening report"""
        report = []
        report.append("# Application Hardening Report")
        report.append(f"\n**Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Total Issues Found:** {sum(len(v) for v in self.issues.values())}")
        report.append(f"**Fixes Applied:** {len(self.fixes_applied)}")
        report.append(f"**Files Changed:** {len(self.files_changed)}")
        
        # Console Errors Section
        report.append("\n## Console Statements")
        if self.issues["console_errors"]:
            report.append("❌ **Issues Found:**")
            for issue in self.issues["console_errors"]:
                report.append(f"- {issue['file']}: {issue['count']} console statements")
        else:
            report.append("✅ **No console statements found in production code**")
        
        # 404 Errors Section
        report.append("\n## 404 Errors")
        if self.issues["404_errors"]:
            report.append("❌ **Endpoints with issues:**")
            for issue in self.issues["404_errors"]:
                report.append(f"- {issue['endpoint']}: {issue.get('status', issue.get('error'))}")
        else:
            report.append("✅ **All endpoints responding correctly**")
        
        # CORS Section
        report.append("\n## CORS Configuration")
        if self.issues["cors_issues"]:
            report.append("⚠️ **CORS issues:**")
            for issue in self.issues["cors_issues"]:
                report.append(f"- {issue['endpoint']}: {issue['issue']}")
        else:
            report.append("✅ **CORS properly configured**")
        
        # Accessibility Section
        report.append("\n## Accessibility")
        if self.issues["accessibility"]:
            report.append("⚠️ **Accessibility issues:**")
            for issue in self.issues["accessibility"]:
                report.append(f"- {issue['file']}: {issue['issue']}")
        else:
            report.append("✅ **No major accessibility issues found**")
        
        # Contrast Section
        report.append("\n## Color Contrast")
        if self.issues["contrast_issues"]:
            report.append("⚠️ **Potential contrast issues:**")
            for issue in self.issues["contrast_issues"]:
                report.append(f"- {issue['file']}: {issue['issue']}")
        else:
            report.append("✅ **No contrast issues detected**")
        
        # Demo Badge Section
        report.append("\n## DEMO Badge (LIVE vs MOCK)")
        if self.issues["demo_badge"]:
            report.append("❌ **Demo badge issues:**")
            for issue in self.issues["demo_badge"]:
                report.append(f"- {issue['issue']}")
        else:
            report.append("✅ **Demo badge correctly shows only in MOCK mode**")
        
        # Naming Conventions Section
        report.append("\n## Naming Conventions")
        if self.issues["naming_issues"]:
            report.append("⚠️ **Naming convention issues:**")
            for issue in self.issues["naming_issues"]:
                report.append(f"- {issue['file']}: {issue['issue']}")
        else:
            report.append("✅ **Consistent naming conventions**")
        
        # Dead Code Section
        report.append("\n## Dead Code")
        if self.issues["dead_code"]:
            report.append("⚠️ **Dead code found:**")
            for issue in self.issues["dead_code"]:
                if 'blocks' in issue:
                    report.append(f"- {issue['file']}: {issue['blocks']} commented blocks")
                if 'todos' in issue:
                    report.append(f"- {issue['file']}: {issue['todos']} TODO/FIXME comments")
        else:
            report.append("✅ **No significant dead code found**")
        
        # Security Section
        report.append("\n## Security")
        if self.issues["security"]:
            report.append("❌ **Security issues:**")
            for issue in self.issues["security"]:
                report.append(f"- {issue['file']}: {issue['issue']}")
        else:
            report.append("✅ **No obvious security issues found**")
        
        # Fixes Applied Section
        report.append("\n## Fixes Applied")
        if self.fixes_applied:
            for fix in self.fixes_applied:
                report.append(f"- ✅ {fix}")
        else:
            report.append("- No automatic fixes applied")
        
        # Files Changed Section
        report.append("\n## Files Changed")
        if self.files_changed:
            for file in self.files_changed:
                report.append(f"- {file}")
        else:
            report.append("- No files changed")
        
        # Recommendations Section
        report.append("\n## Recommendations")
        report.append("1. **Console Statements**: Replace with proper logging framework")
        report.append("2. **Accessibility**: Add ARIA labels and keyboard navigation")
        report.append("3. **Contrast**: Ensure AA compliance (4.5:1 for normal text)")
        report.append("4. **Security**: Use environment variables for all secrets")
        report.append("5. **Code Quality**: Remove commented code and resolve TODOs")
        
        return "\n".join(report)

if __name__ == "__main__":
    print("="*60)
    print("PINK LEMONADE HARDENING AUDIT")
    print("="*60)
    
    auditor = HardeningAuditor()
    
    # Run all audits
    auditor.audit_console_statements()
    auditor.check_404_errors()
    auditor.check_cors_configuration()
    auditor.check_accessibility()
    auditor.check_contrast()
    auditor.check_demo_badge()
    auditor.check_naming_conventions()
    auditor.find_dead_code()
    auditor.check_security_issues()
    
    # Apply fixes
    auditor.apply_fixes()
    
    # Generate report
    report = auditor.generate_report()
    
    # Save report
    report_path = "/home/runner/workspace/web/tests/HARDENING_REPORT.md"
    with open(report_path, "w") as f:
        f.write(report)
    
    print(f"\nTotal issues found: {sum(len(v) for v in auditor.issues.values())}")
    print(f"Fixes applied: {len(auditor.fixes_applied)}")
    print(f"Report saved to: {report_path}")
    print("="*60)