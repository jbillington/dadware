#!/usr/bin/env python3
"""Quick script to open HTML report in browser."""

import os
import sys
import webbrowser
from pathlib import Path

def main():
    # Default to the sample report
    if len(sys.argv) > 1:
        html_file = sys.argv[1]
    else:
        html_file = 'test-reports/sample_report_improved.html'
    
    # Get absolute path
    script_dir = Path(__file__).parent
    html_path = script_dir / html_file
    
    if not html_path.exists():
        print(f"Error: {html_path} not found")
        print(f"\nAvailable reports:")
        reports_dir = script_dir / 'test-reports'
        if reports_dir.exists():
            for f in sorted(reports_dir.glob('*.html')):
                print(f"  - {f.name}")
        return 1
    
    # Open in browser
    file_url = f"file://{html_path.absolute()}"
    webbrowser.open(file_url)
    print(f"✅ Opened in browser: {file_url}")
    
    return 0

if __name__ == '__main__':
    sys.exit(main())

