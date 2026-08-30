#!/usr/bin/env python3
"""Generate HTML README with Dad Ware branding."""

import os
import sys
from datetime import datetime

def generate_html_readme(output_path):
    """Generate HTML README file with Dad Ware branding."""
    
    now = datetime.now()
    date_str = now.strftime('%B %d, %Y')
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dad Ware - Installation & Usage Guide</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }}
        .container {{
            max-width: 1000px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }}
        header {{
            border-bottom: 3px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }}
        h1 {{
            font-size: 2.5em;
            margin-bottom: 10px;
            color: #333;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
        }}
        
        .hero-section {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 40px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .hero-section h2 {{
            color: white;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .hero-section p {{
            font-size: 1.1em;
            line-height: 1.8;
            opacity: 0.95;
        }}
        
        .personality {{
            background: #f9f9f9;
            border-left: 4px solid #333;
            padding: 20px;
            margin: 30px 0;
            border-radius: 4px;
        }}
        .personality h2 {{
            font-size: 1.3em;
            margin-bottom: 15px;
            color: #333;
        }}
        .personality p {{
            font-style: italic;
            color: #555;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            font-size: 1.05em;
            line-height: 1.8;
        }}
        
        section {{
            margin: 40px 0;
        }}
        h2 {{
            font-size: 1.8em;
            margin-bottom: 20px;
            color: #333;
            border-bottom: 2px solid #e0e0e0;
            padding-bottom: 10px;
        }}
        h3 {{
            font-size: 1.3em;
            margin: 25px 0 15px 0;
            color: #555;
        }}
        
        .warning-box {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .warning-box h3 {{
            color: #856404;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .warning-box p {{
            color: #856404;
            margin: 8px 0;
        }}
        .warning-box ul {{
            color: #856404;
            margin: 10px 0 10px 20px;
        }}
        .warning-box li {{
            margin: 5px 0;
        }}
        
        .info-box {{
            background: #e7f3ff;
            border-left: 4px solid #2196F3;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .info-box h3 {{
            color: #0d47a1;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .info-box p {{
            color: #1565c0;
            margin: 8px 0;
        }}
        
        .success-box {{
            background: #d4edda;
            border-left: 4px solid #28a745;
            padding: 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .success-box h3 {{
            color: #155724;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .success-box p {{
            color: #155724;
            margin: 8px 0;
        }}
        
        code {{
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            color: #c7254e;
        }}
        
        pre {{
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 20px;
            border-radius: 6px;
            overflow-x: auto;
            margin: 15px 0;
            font-family: 'Monaco', 'Courier New', monospace;
            font-size: 0.9em;
            line-height: 1.5;
        }}
        
        .step {{
            background: #f9f9f9;
            border-left: 4px solid #667eea;
            padding: 15px 20px;
            margin: 15px 0;
            border-radius: 4px;
        }}
        .step-number {{
            display: inline-block;
            background: #667eea;
            color: white;
            width: 30px;
            height: 30px;
            border-radius: 50%;
            text-align: center;
            line-height: 30px;
            font-weight: bold;
            margin-right: 10px;
        }}
        
        ul, ol {{
            margin: 15px 0 15px 25px;
        }}
        li {{
            margin: 8px 0;
            line-height: 1.7;
        }}
        
        .footer {{
            margin-top: 50px;
            padding-top: 20px;
            border-top: 2px solid #e0e0e0;
            text-align: center;
            color: #666;
            font-style: italic;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>Dad Ware</h1>
            <p class="meta">Mac Cleanup Tool - Installation & Usage Guide</p>
            <p class="meta">Last Updated: {date_str}</p>
        </header>
        
        <div class="hero-section">
            <h2>What is Dad Ware?</h2>
            <p>
                Dad Ware scans your Mac's storage and memory, then gives you a report card with letter grades, 
                dad-style commentary, and actionable tips for freeing up space. It's a read-only tool that never 
                deletes files - you're always in control.
            </p>
        </div>
        
        <div class="personality">
            <h2>💬 From Dad</h2>
            <p>
                "look, i know you're busy. but your mac is running slow because it's full of stuff. 
                this tool will show you what's taking up space so you can decide what to clean up. 
                it won't delete anything - that's your call. just run it and see what it finds."
            </p>
        </div>
        
        <section>
            <h2>🚀 Quick Start</h2>
            
            <div class="step">
                <span class="step-number">1</span>
                <strong>Download and Extract</strong>
                <p style="margin-top: 10px;">
                    Download the ZIP file and double-click to extract it. You'll see a folder with:
                </p>
                <ul>
                    <li><code>askdad</code> - The executable file</li>
                    <li><code>README.html</code> - This file (instructions)</li>
                    <li><code>README.md</code> - Markdown version (if you have a markdown viewer)</li>
                </ul>
            </div>
            
            <div class="warning-box">
                <h3>⚠️ First Run - Security Warning</h3>
                <p>On first run, macOS may show a security warning. Here's how to fix it:</p>
                <p><strong>Option 1 (Easiest):</strong></p>
                <ol>
                    <li>Right-click the <code>askdad</code> file</li>
                    <li>Select <strong>Open</strong></li>
                    <li>Click <strong>Open</strong> in the security dialog</li>
                    <li>This only needs to be done once</li>
                </ol>
                <p style="margin-top: 15px;"><strong>Option 2 (Terminal):</strong></p>
                <pre>xattr -d com.apple.quarantine askdad</pre>
            </div>
            
            <div class="step">
                <span class="step-number">2</span>
                <strong>Make It Executable</strong>
                <p style="margin-top: 10px;">
                    Open Terminal and navigate to the folder, then run:
                </p>
                <pre>cd ~/Downloads/askdad  # (or wherever you extracted it)
chmod +x askdad</pre>
            </div>
            
            <div class="step">
                <span class="step-number">3</span>
                <strong>Run Your First Scan</strong>
                <p style="margin-top: 10px;">Try one of these commands:</p>
                <pre># Scan storage (find large files and folders)
./askdad

# Scan CPU and RAM usage
./askdad cpu

# Scan both (opens both reports)
./askdad all</pre>
                <p style="margin-top: 10px;">
                    The HTML report will open automatically in your browser!
                </p>
            </div>
        </section>
        
        <section>
            <h2>📋 Commands</h2>
            
            <h3>Storage Scan</h3>
            <p>Find large files and folders taking up space:</p>
            <pre>./askdad</pre>
            
            <h3>CPU/RAM Scan</h3>
            <p>See what's using your memory:</p>
            <pre>./askdad cpu</pre>
            
            <h3>Combined Scan</h3>
            <p>Run both scans at once:</p>
            <pre>./askdad all</pre>
        </section>
        
        <section>
            <h2>🔐 Permissions (Optional)</h2>
            
            <div class="info-box">
                <h3>Full Disk Access</h3>
                <p>
                    To scan Photos, Messages, and Mail libraries, you need <strong>Full Disk Access</strong>:
                </p>
                <ol>
                    <li>Open <strong>System Settings</strong> → <strong>Privacy & Security</strong></li>
                    <li>Scroll to <strong>Full Disk Access</strong></li>
                    <li>Click the lock icon and enter your password</li>
                    <li>Click <strong>+</strong> and add <strong>Terminal.app</strong></li>
                    <li>Make sure the checkbox is checked ✅</li>
                    <li>Restart Terminal</li>
                </ol>
                <p style="margin-top: 15px;">
                    <strong>Note:</strong> The scan will work without permissions, but protected libraries will show 0 bytes.
                </p>
            </div>
        </section>
        
        <section>
            <h2>📁 Report Locations</h2>
            <p>Reports are automatically saved to:</p>
            <pre>~/.dadware/reports/</pre>
            <p>This is a hidden folder in your home directory. Each scan creates an HTML report that opens in your browser automatically.</p>
        </section>
        
        <section>
            <h2>🔧 Troubleshooting</h2>
            
            <h3>"Permission denied"</h3>
            <p>Make sure you made the file executable:</p>
            <pre>chmod +x askdad</pre>
            
            <h3>Security warning</h3>
            <p>Right-click the file → <strong>Open</strong> (first time only)</p>
            
            <h3>"No such file or directory"</h3>
            <p>Make sure you're in the right folder:</p>
            <pre>cd ~/Downloads/askdad  # (or wherever you extracted it)</pre>
        </section>
        
        <section>
            <h2>🛡️ Safety & Disclaimer</h2>
            
            <div class="success-box">
                <h3>✅ Read-Only by Design</h3>
                <p>
                    This tool never deletes files. It only scans and reports. You control what gets deleted.
                </p>
            </div>
            
            <div class="warning-box" style="margin-top: 20px;">
                <h3>⚠️ Important</h3>
                <p>
                    This software provides reports and information about what is taking up space on your computer. 
                    It does NOT provide advice about what to delete or archive. <strong>You must determine, at your 
                    own discretion, what files or folders to delete or archive from your computer.</strong> The authors 
                    are not responsible for any data loss or consequences resulting from decisions you make based on 
                    information provided by this software.
                </p>
            </div>
        </section>
        
        <section>
            <h2>📄 License</h2>
            
            <div class="info-box">
                <h3>MIT License</h3>
                <p><strong>Copyright (c) 2025 John Billington</strong></p>
                <p style="margin-top: 15px;">
                    Permission is hereby granted, free of charge, to any person obtaining a copy of this software 
                    and associated documentation files (the "Software"), to deal in the Software without restriction, 
                    including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, 
                    and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, 
                    subject to the following conditions:
                </p>
                <p style="margin-top: 10px;">
                    The above copyright notice and this permission notice shall be included in all copies or substantial 
                    portions of the Software.
                </p>
                <p style="margin-top: 15px; font-weight: bold;">
                    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, including but not 
                    limited to the warranties of merchantability, fitness for a particular purpose and noninfringement. 
                    In no event shall the authors or copyright holders be liable for any claim, damages or other liability, 
                    whether in an action of contract, tort or otherwise, arising from, out of or in connection with the 
                    Software or the use or other dealings in the Software.
                </p>
            </div>
        </section>
        
        <div class="footer">
            <p><strong>Made with ❤️ by a dad who's tired of explaining disk space</strong></p>
            <p style="margin-top: 10px;">Copyright (c) 2025 John Billington</p>
        </div>
    </div>
</body>
</html>
"""
    
    # Write HTML file
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    print(f"HTML README generated: {output_path}")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        output_path = sys.argv[1]
    else:
        output_path = 'README.html'
    
    generate_html_readme(output_path)

