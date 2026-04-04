#!/usr/bin/env python3
"""Generate a sample report from JSON file for UX testing."""

import json
import os
import sys
from renderers.html import render_html
from personality.yourdad import add_personality
from scanners.mac_libraries import scan_all_mac_libraries

def main():
    # Load sample JSON
    json_path = 'test-reports/sample_storage_2025-11-09_14-23.json'
    
    if not os.path.exists(json_path):
        print(f"Error: {json_path} not found")
        return 1
    
    with open(json_path, 'r') as f:
        manifest = json.load(f)
    
    # Extract scan data and personality
    scan_data = manifest['scan_results']['storage']
    
    # Scan Mac app libraries (this was missing!)
    print("→ scanning Mac app libraries...")
    mac_libraries = scan_all_mac_libraries()
    scan_data['mac_libraries'] = mac_libraries
    
    # Re-run personality with updated scan data
    personality_data = add_personality(scan_data)
    
    # Generate report
    report_path = 'test-reports/sample_report_improved.html'
    render_html(scan_data, personality_data, report_path)
    
    print(f"✅ Generated sample report: {report_path}")
    print(f"   Open in browser: file://{os.path.abspath(report_path)}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

