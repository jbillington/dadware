"""HTML report generator with UX improvements."""

import os
import json
import datetime
import webbrowser
from urllib.parse import quote
from scanners.grading import (
    grade_free_space,
    grade_home_folders_ratio,
    grade_home_folders_clutter,
    grade_library_size,
    calculate_composite_storage_grade,
    score_to_letter,
    format_size as format_size_grading
)


def format_size(bytes):
    """Format bytes into human-readable size."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if bytes < 1024.0:
            return f"{bytes:.1f} {unit}"
        bytes /= 1024.0
    return f"{bytes:.1f} PB"


def get_status_emoji(status):
    """Get emoji for status."""
    if status == 'critical':
        return '🔴'
    elif status == 'warn':
        return '🟡'
    else:
        return '🟢'


def get_status_text(status):
    """Get status text."""
    if status == 'critical':
        return 'needs attention'
    elif status == 'warn':
        return 'stable but cluttered'
    else:
        return 'all good'


def get_storage_color_class(free_percent):
    """Get color class based on free storage percentage."""
    if free_percent < 10:
        return 'critical'
    elif free_percent < 20:
        return 'warn'
    else:
        return 'ok'


def get_folder_color(index):
    """Get distinct color for folder bar."""
    colors = [
        '#4A90E2',  # Blue
        '#50C878',  # Green
        '#FF6B6B',  # Red
        '#FFA500',  # Orange
        '#9B59B6',  # Purple
        '#1ABC9C',  # Teal
        '#E74C3C',  # Dark Red
        '#3498DB',  # Light Blue
        '#2ECC71',  # Light Green
        '#F39C12',  # Dark Orange
    ]
    return colors[index % len(colors)]


def render_html(scan_data, personality_data, report_path):
    """Generate HTML report with UX improvements and save to file."""
    scan_type = scan_data.get('scan_type', 'unknown')
    status = personality_data.get('status', 'ok')
    comments = personality_data.get('comments', [])
    tips = personality_data.get('tips', [])
    
    now = datetime.datetime.now()
    date_str = now.strftime('%B %d, %Y %H:%M')
    
    # Get volume info for storage overview
    volume_info = {}
    if scan_type == 'storage':
        volume_info = scan_data.get('volume_info', {})
        free_percent = volume_info.get('free_percent', 0)
        used_percent = volume_info.get('used_percent', 0)
        storage_status_class = get_storage_color_class(free_percent)
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dad's Report Card - {now.strftime('%b %d, %Y')}</title>
    <style>
        * {{
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }}
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
        }}
        .container {{
            max-width: 1200px;
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
            font-size: 2em;
            margin-bottom: 10px;
        }}
        .meta {{
            color: #666;
            font-size: 0.9em;
        }}
        
        /* Storage Overview Section */
        .storage-overview {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .storage-overview h2 {{
            color: white;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .storage-stats {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }}
        .storage-stat {{
            flex: 1;
            min-width: 150px;
        }}
        .storage-stat-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }}
        .storage-stat-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .storage-stat-percent {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .storage-stat-size {{
            font-size: 0.7em;
            font-weight: normal;
            opacity: 0.9;
            margin-left: 8px;
        }}
        .progress-bar-container {{
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 15px 0;
            position: relative;
        }}
        .progress-bar {{
            height: 100%;
            background: linear-gradient(90deg, #6bcf7f 0%, #ffd93d 50%, #ff6b6b 100%);
            transition: width 0.5s ease;
            display: flex;
            align-items: center;
            justify-content: flex-end;
            padding-right: 10px;
            color: #333;
            font-weight: bold;
            font-size: 0.9em;
        }}
        
        .permission-warning {{
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .permission-warning h3 {{
            color: #856404;
            margin-top: 0;
            margin-bottom: 10px;
        }}
        .permission-warning p {{
            color: #856404;
            margin: 5px 0;
        }}
        .permission-warning ul {{
            color: #856404;
            margin: 10px 0 10px 20px;
        }}
        .permission-warning li {{
            margin: 5px 0;
        }}
        .permission-warning .permission-status {{
            font-weight: bold;
            margin-bottom: 10px;
        }}
        .personality {{
            background: #f9f9f9;
            border-left: 4px solid #333;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }}
        .personality h2 {{
            font-size: 1.2em;
            margin-bottom: 10px;
        }}
        .personality p {{
            font-style: italic;
            color: #555;
        }}
        
        section {{
            margin: 30px 0;
        }}
        h2 {{
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
        }}
        h3 {{
            font-size: 1.2em;
            margin: 20px 0 10px 0;
            color: #555;
        }}
        
        /* Folder Bar Chart - Single Horizontal Bar */
        .folder-chart-container {{
            margin: 30px 0;
        }}
        .folder-bar-header {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 15px;
        }}
        .folder-bar-label {{
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }}
        .folder-bar-summary {{
            font-family: 'Monaco', 'Courier New', monospace;
            color: #666;
            font-size: 0.95em;
        }}
        .folder-bar-wrapper {{
            background: #e9ecef;
            border-radius: 8px;
            height: 50px;
            overflow: hidden;
            position: relative;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
        }}
        .folder-bar-segment {{
            height: 100%;
            position: relative;
            transition: all 0.2s ease;
            border-right: 1px solid rgba(255,255,255,0.3);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 0 6px;
            overflow: hidden;
        }}
        .folder-bar-segment:hover {{
            opacity: 0.85;
            transform: scaleY(1.08);
            z-index: 10;
            box-shadow: 0 0 8px rgba(0,0,0,0.3);
        }}
        .folder-bar-segment.active {{
            opacity: 0.9;
            box-shadow: inset 0 0 12px rgba(0,0,0,0.4);
        }}
        .folder-bar-segment:last-child {{
            border-right: none;
        }}
        /* Text inside segments */
        .segment-label {{
            color: white;
            font-size: 0.7em;
            font-weight: 600;
            text-align: center;
            white-space: nowrap;
            overflow: hidden;
            text-overflow: ellipsis;
            width: 100%;
            text-shadow: 0 1px 2px rgba(0,0,0,0.3);
            line-height: 1.2;
        }}
        .segment-label-name {{
            display: block;
            font-weight: 600;
        }}
        .segment-label-size {{
            display: block;
            font-size: 0.85em;
            font-weight: 400;
            opacity: 0.95;
            font-family: 'Monaco', 'Courier New', monospace;
            margin-top: 1px;
        }}
        .folder-bar-expanded {{
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 3px solid #4A90E2;
            border-radius: 4px;
            display: none;
        }}
        .folder-bar-expanded.active {{
            display: block;
        }}
        .subfolders-list {{
            margin: 15px 0;
        }}
        .subfolder-item {{
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .subfolder-name {{
            font-weight: 500;
            color: #555;
        }}
        .subfolder-size {{
            font-family: 'Monaco', 'Courier New', monospace;
            color: #666;
            font-size: 0.9em;
        }}
        .folder-files-list {{
            margin: 15px 0;
        }}
        .folder-file-item {{
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .folder-file-name {{
            color: #0066cc;
            text-decoration: none;
        }}
        .folder-file-name:hover {{
            text-decoration: underline;
        }}
        .see-all-link {{
            display: block;
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            color: #0066cc;
            text-decoration: none;
            border: 1px dashed #0066cc;
            border-radius: 4px;
            transition: all 0.2s ease;
        }}
        .see-all-link:hover {{
            background: #0066cc;
            color: white;
        }}
        
        /* Top Files with Folder Names */
        table {{
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }}
        th {{
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            cursor: pointer;
            user-select: none;
        }}
        th:hover {{
            background: #555;
        }}
        td {{
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }}
        tr:hover {{
            background: #f9f9f9;
        }}
        .file-name-cell {{
            padding: 12px;
        }}
        .file-name-primary {{
            font-weight: 600;
            font-size: 1em;
            color: #333;
            display: block;
        }}
        .file-name-primary a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .file-name-primary a:hover {{
            text-decoration: underline;
        }}
        .file-folder-name {{
            font-size: 0.85em;
            color: #666;
            margin-top: 4px;
            font-style: italic;
        }}
        .file-folder-name a {{
            color: #0066cc;
            text-decoration: none;
        }}
        .file-folder-name a:hover {{
            text-decoration: underline;
        }}
        .size {{
            font-family: 'Monaco', 'Courier New', monospace;
            text-align: right;
        }}
        button, .button-link {{
            background: #0066cc;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            text-decoration: none;
            display: inline-block;
        }}
        button:hover, .button-link:hover {{
            background: #0052a3;
        }}
        .copy-success {{
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border: 1px solid #c3e6cb;
        }}
        .copy-instructions {{
            font-family: 'Monaco', 'Courier New', monospace;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
            font-size: 0.9em;
        }}
        footer {{
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
        }}
        .tips {{
            background: #fff3cd;
            padding: 15px;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .tips ul {{
            margin-left: 20px;
            margin-top: 10px;
        }}
        .tips li {{
            margin: 5px 0;
        }}
        
        /* Report Card Styles */
        .report-card {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }}
        .report-card h2 {{
            color: white;
            margin-bottom: 20px;
            font-size: 1.8em;
        }}
        .overall-grade {{
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
        }}
        .overall-grade-letter {{
            font-size: 4em;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }}
        .overall-grade-score {{
            font-size: 1.2em;
            opacity: 0.9;
        }}
        .storage-metrics {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }}
        .metric-item {{
            text-align: center;
        }}
        .metric-label {{
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }}
        .metric-value {{
            font-size: 1.5em;
            font-weight: bold;
        }}
        .grade-breakdown {{
            margin: 20px 0;
        }}
        .grade-row {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            margin: 8px 0;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
        }}
        .grade-label {{
            font-size: 1.1em;
            font-weight: 500;
        }}
        .grade-display {{
            display: flex;
            align-items: center;
            gap: 15px;
        }}
        .grade-letter {{
            font-size: 2em;
            font-weight: bold;
            min-width: 50px;
            text-align: center;
        }}
        .grade-score {{
            font-size: 1em;
            opacity: 0.9;
        }}
        .grade-letter.A {{
            color: #6bcf7f;
        }}
        .grade-letter.B {{
            color: #ffd93d;
        }}
        .grade-letter.C {{
            color: #ffa500;
        }}
        .grade-letter.D {{
            color: #ff6b6b;
        }}
        .grade-letter.F {{
            color: #e74c3c;
        }}
        .library-grades {{
            margin-top: 15px;
            padding-left: 20px;
        }}
        .library-grade-item {{
            padding: 8px 12px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        .library-grade-label {{
            font-size: 0.95em;
        }}
        .library-grade-display {{
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .library-grade-letter {{
            font-size: 1.3em;
            font-weight: bold;
        }}
        .library-grade-size {{
            font-size: 0.85em;
            opacity: 0.8;
            font-family: 'Monaco', 'Courier New', monospace;
        }}
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DAD'S REPORT CARD</h1>
            <p class="meta">Dad Ware v0.1  |  {date_str}</p>
        </header>
"""
    
    # Report Card Section (replaces Storage Overview)
    if scan_type == 'storage' and volume_info:
        volume = scan_data.get('volume', 'Unknown')
        used_bytes = volume_info.get('used_bytes', 0)
        free_percent = volume_info.get('free_percent', 0)
        used_percent = volume_info.get('used_percent', 0)
        
        # Get metrics
        metrics = scan_data.get('metrics', {})
        sum_top_10_folders = metrics.get('sum_top_10_folders_human', '0 B')
        sum_top_25_files = metrics.get('sum_top_25_files_human', '0 B')
        reclaimable_percent = metrics.get('reclaimable_percent', 0)
        
        # Calculate grades
        free_space_grade = grade_free_space(free_percent)
        home_folders_total = scan_data.get('home_folders_total_bytes', 0)
        home_folders_ratio_grade = grade_home_folders_ratio(home_folders_total, used_bytes)
        
        # Grade home folders clutter separately (Downloads, Desktop, etc.)
        top_folders = scan_data.get('top_folders', [])
        home_folders_clutter_grade = grade_home_folders_clutter(top_folders)
        
        # Grade Mac libraries
        mac_libraries = scan_data.get('mac_libraries', {})
        library_grades = {}
        library_scores = []
        
        library_types = {
            'photos': 'Photos',
            'music': 'Music',
            'messages': 'Messages',
            'mail': 'Mail',
            'time_machine': 'Time Machine',
            'creative': 'Creative Apps'
        }
        
        for lib_type, lib_name in library_types.items():
            lib_data = mac_libraries.get(lib_type, {})
            if lib_type in ['photos', 'music', 'time_machine', 'creative']:
                lib_size = lib_data.get('total_size_bytes', 0)
            else:
                lib_size = lib_data.get('size_bytes', 0)
            
            if lib_size > 0:
                grade = grade_library_size(lib_size, lib_type, used_bytes)
                library_grades[lib_type] = {
                    'name': lib_name,
                    'grade': grade,
                    'size': format_size(lib_size)
                }
                library_scores.append(grade['score'])
        
        # Calculate average library grade
        avg_library_score = sum(library_scores) / len(library_scores) if library_scores else 0
        avg_library_grade = {
            'letter': score_to_letter(avg_library_score),
            'score': avg_library_score
        }
        
        # Calculate composite grade (excluding home folders clutter - shown separately)
        component_grades = {
            'free_space': free_space_grade,
            'home_folders_ratio': home_folders_ratio_grade,
            'mac_libraries': avg_library_grade
        }
        weights = {
            'free_space': 0.4,
            'home_folders_ratio': 0.3,
            'mac_libraries': 0.3
        }
        composite_grade = calculate_composite_storage_grade(component_grades, weights)
        
        # Get overall grade comment
        overall_comment = "Excellent!" if composite_grade['score'] >= 90 else \
                          "Good job!" if composite_grade['score'] >= 80 else \
                          "Room for improvement" if composite_grade['score'] >= 70 else \
                          "Needs work" if composite_grade['score'] >= 60 else \
                          "Critical issues"
        
        html += f"""
        <section class="report-card">
            <h2>📊 Storage Report Card - {volume}</h2>
            
            <div class="overall-grade">
                <div class="overall-grade-letter grade-letter.{composite_grade['letter']}">{composite_grade['letter']}</div>
                <div class="overall-grade-score">{composite_grade['score']:.0f}/100 - {overall_comment}</div>
            </div>
            
            <div class="storage-metrics">
                <div class="metric-item">
                    <div class="metric-label">Top 10 Folders</div>
                    <div class="metric-value">{sum_top_10_folders}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Top 25 Files</div>
                    <div class="metric-value">{sum_top_25_files}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Reclaimable</div>
                    <div class="metric-value">{reclaimable_percent:.1f}%</div>
                </div>
            </div>
            <p style="text-align: center; margin-top: 10px; opacity: 0.9; font-size: 0.9em;">
                You can free up {reclaimable_percent:.1f}% of used space by deleting or offloading your top 25 largest files
            </p>
            
            <div class="grade-breakdown">
                <h3 style="color: white; margin-bottom: 15px; font-size: 1.2em;">Grade Breakdown</h3>
                
                <div class="grade-row">
                    <div class="grade-label">Free Space</div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter.{free_space_grade['letter']}">{free_space_grade['letter']}</div>
                        <div class="grade-score">{free_space_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">Home Folders Ratio</div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter.{home_folders_ratio_grade['letter']}">{home_folders_ratio_grade['letter']}</div>
                        <div class="grade-score">{home_folders_ratio_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">Home Folders Clutter</div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter.{home_folders_clutter_grade['letter']}">{home_folders_clutter_grade['letter']}</div>
                        <div class="grade-score">{home_folders_clutter_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">Mac App Libraries</div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter.{avg_library_grade['letter']}">{avg_library_grade['letter']}</div>
                        <div class="grade-score">{avg_library_grade['score']:.0f}/100</div>
                    </div>
                </div>
"""
        
        # Build library grades HTML separately to avoid nested f-string issues
        library_grades_html = ""
        if library_grades:
            library_items = []
            for lib_data in library_grades.values():
                lib_name = lib_data['name']
                lib_letter = lib_data['grade']['letter']
                lib_size = lib_data['size']
                library_items.append(f'''
                        <div class="library-grade-item">
                            <div class="library-grade-label">{lib_name}</div>
                            <div class="library-grade-display">
                                <div class="library-grade-letter grade-letter.{lib_letter}">{lib_letter}</div>
                                <div class="library-grade-size">{lib_size}</div>
                            </div>
                        </div>
                        ''')
            library_grades_html = f'''
                <div class="library-grades">
                    {''.join(library_items)}
                </div>
                '''
        
        html += library_grades_html + """
            </div>
        </section>
"""
    
    # Permission warning section
    if scan_type == 'storage':
        permission_status = scan_data.get('permission_status', {})
        if permission_status and not permission_status.get('has_access', True):
            missing = permission_status.get('missing_permissions', [])
            if missing:
                libs = ", ".join(m.title() for m in missing)
                html += f"""
        <section class="permission-warning">
            <h3>⚠️ Permission Notice</h3>
            <p class="permission-status">Full Disk Access required for: {libs}</p>
            <p>Protected libraries show 0 bytes without permission. To grant access:</p>
            <ul>
                <li>Open <strong>System Settings</strong> → <strong>Privacy & Security</strong></li>
                <li>Scroll to <strong>Full Disk Access</strong></li>
                <li>Click the lock icon and enter your password</li>
                <li>Click <strong>+</strong> and add <strong>Terminal.app</strong> (or your IDE)</li>
                <li>Make sure the checkbox is checked ✅</li>
                <li>Restart Terminal/IDE and run the scan again</li>
            </ul>
            <p><em>Note: If you're running from Cursor, VS Code, or another IDE, add that application instead of Terminal.</em></p>
        </section>
"""
    
    # Personality section
    if comments:
        html += """
        <section class="personality">
            <h2>💬 Dad says:</h2>
"""
        for comment in comments:
            html += f'            <p>"{comment}"</p>\n'
        html += "        </section>\n"
    
    # Top Folders - Two Separate Bars: Home Folders and Other Folders
    if scan_type == 'storage':
        top_folders = scan_data.get('top_folders', [])
        if top_folders:
            # Identify home folders
            home_folder_names = ['Downloads', 'Desktop', 'Documents', 'Movies', 'Music', 'Pictures', 'Library']
            
            # Separate folders into home and non-home
            home_folder_segments = []
            non_home_folder_segments = []
            home_folder_total_bytes = 0
            non_home_folder_total_bytes = 0
            
            for idx, folder in enumerate(top_folders):
                path_display = folder.get('path_display', '') or folder.get('path', '')
                folder_name = os.path.basename(path_display)
                # Also check the raw path
                raw_path = folder.get('path', '')
                
                # Check if this is a home folder
                # Match if folder name matches, or if path contains the home folder name
                is_home_folder = False
                for home_name in home_folder_names:
                    # Check folder name
                    if folder_name == home_name:
                        is_home_folder = True
                        break
                    # Check if path contains the home folder name (case-insensitive)
                    if home_name.lower() in path_display.lower() or home_name.lower() in raw_path.lower():
                        is_home_folder = True
                        break
                
                size_bytes = folder.get('size_bytes', 0)
                seg = {
                    'idx': idx,
                    'folder': folder,
                    'color': get_folder_color(idx)
                }
                
                if is_home_folder:
                    home_folder_segments.append(seg)
                    home_folder_total_bytes += size_bytes
                else:
                    non_home_folder_segments.append(seg)
                    non_home_folder_total_bytes += size_bytes
            
            # Calculate widths for home folders
            for seg in home_folder_segments:
                size_bytes = seg['folder'].get('size_bytes', 0)
                seg['width'] = (size_bytes / home_folder_total_bytes) * 100 if home_folder_total_bytes > 0 else 0
            
            # Limit non-home folders to top 10 and calculate widths
            top_10_non_home = non_home_folder_segments[:10]
            top_10_non_home_total = sum(seg['folder'].get('size_bytes', 0) for seg in top_10_non_home)
            for seg in top_10_non_home:
                size_bytes = seg['folder'].get('size_bytes', 0)
                seg['width'] = (size_bytes / top_10_non_home_total) * 100 if top_10_non_home_total > 0 else 0
            
            html += """
        <section>
            <div class="folder-chart-container">
"""
            
            # Home Folders Bar (First Bar)
            if home_folder_segments:
                html += """
                <div class="folder-bar-header">
                    <h2>Home Folders</h2>
                </div>
                <div class="folder-bar-wrapper" id="homeFolderBar">
"""
                for seg in home_folder_segments:
                    folder = seg['folder']
                    full_path = folder.get('path', '')
                    path_display = folder.get('path_display', full_path)
                    size = folder.get('size_human', '0 B')
                    folder_id = f"home_folder_{seg['idx']}"
                    
                    # If path is not absolute, construct it from volume
                    if not os.path.isabs(full_path):
                        volume = scan_data.get('volume', '')
                        full_path = os.path.join(volume, full_path.lstrip('/'))
                        full_path = os.path.normpath(full_path)
                    
                    html += f"""
                    <div class="folder-bar-segment" 
                         style="width: {seg['width']}%; background: {seg['color']};"
                         onclick="toggleFolder('{folder_id}')"
                         title="{path_display} - {size}">
                        <div class="segment-label">
                            <span class="segment-label-name">{path_display}</span>
                            <span class="segment-label-size">{size}</span>
                        </div>
                    </div>
"""
                html += """
                </div>
"""
            
            # Other Folders Bar (Second Bar - Top 10)
            if top_10_non_home:
                html += """
                <div class="folder-bar-header" style="margin-top: 30px;">
                    <h2>Other Folders</h2>
                </div>
                <div class="folder-bar-wrapper" id="otherFolderBar">
"""
                for seg in top_10_non_home:
                    folder = seg['folder']
                    full_path = folder.get('path', '')
                    path_display = folder.get('path_display', full_path)
                    size = folder.get('size_human', '0 B')
                    folder_id = f"folder_{seg['idx']}"
                    
                    # If path is not absolute, construct it from volume
                    if not os.path.isabs(full_path):
                        volume = scan_data.get('volume', '')
                        full_path = os.path.join(volume, full_path.lstrip('/'))
                        full_path = os.path.normpath(full_path)
                    
                    html += f"""
                    <div class="folder-bar-segment" 
                         style="width: {seg['width']}%; background: {seg['color']};"
                         onclick="toggleFolder('{folder_id}')"
                         title="{path_display} - {size}">
                        <div class="segment-label">
                            <span class="segment-label-name">{path_display}</span>
                            <span class="segment-label-size">{size}</span>
                        </div>
                    </div>
"""
                html += """
                </div>
"""
                # Add note if there are more than 10 non-home folders
                if len(non_home_folder_segments) > 10:
                    html += """
                <p style="text-align: center; color: #666; font-size: 0.9em; margin-top: 10px; font-style: italic;">
                    Only top 10 other folders displayed
                </p>
"""
            
            html += """
            </div>
"""
            
            # Generate expanded details for home folders
            for seg in home_folder_segments:
                folder = seg['folder']
                full_path = folder.get('path', '')
                path_display = folder.get('path_display', full_path)
                subfolders = folder.get('subfolders', [])
                top_files = folder.get('top_files', [])
                folder_id = f"home_folder_{seg['idx']}"
                folder_color = seg['color']
                
                # If path is not absolute, construct it from volume
                if not os.path.isabs(full_path):
                    volume = scan_data.get('volume', '')
                    full_path = os.path.join(volume, full_path.lstrip('/'))
                    full_path = os.path.normpath(full_path)
                
                html += f"""
            <div class="folder-bar-expanded" id="{folder_id}" style="border-left-color: {folder_color};">
                <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.3em; display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 20px; height: 20px; background: {folder_color}; border-radius: 4px; flex-shrink: 0;"></span>
                    <span style="color: {folder_color}; font-weight: 600;">{path_display}</span>
                </h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 15px; font-family: 'Monaco', 'Courier New', monospace;">
                    {full_path}
                </p>
"""
                
                # Subfolders
                if subfolders:
                    html += """
                <h4>Subfolders</h4>
                <div class="subfolders-list">
"""
                    for subfolder in subfolders[:5]:
                        html += f"""
                    <div class="subfolder-item">
                        <span class="subfolder-name">{subfolder.get('path_display', subfolder.get('path', ''))}</span>
                        <span class="subfolder-size">{subfolder.get('size_human', '0 B')}</span>
                    </div>
"""
                    html += """
                </div>
"""
                
                # Top Files
                if top_files:
                    html += f"""
                <h4>Top Files in {path_display}</h4>
                <div class="folder-files-list">
"""
                    for file_info in top_files[:10]:
                        file_path = file_info.get('path', '')
                        file_size = file_info.get('size_human', '0 B')
                        file_url = f"file://{quote(file_path)}"
                        file_name = os.path.basename(file_path)
                        html += f"""
                    <div class="folder-file-item">
                        <a href="{file_url}" class="folder-file-name" title="Click to view">{file_name}</a>
                        <span class="subfolder-size">{file_size}</span>
                    </div>
"""
                    
                    # Show "View all files" link if there are more files
                    if len(top_files) > 10:
                        all_files_id = f"all_files_{folder_id}"
                        html += f"""
                    <a href="#" class="see-all-link" onclick="event.preventDefault(); showAllFilesInFolder('{all_files_id}', {len(top_files)}); return false;">
                        View all {len(top_files)} files in {path_display} →
                    </a>
                    <div id="{all_files_id}" style="display: none; margin-top: 10px;">
"""
                        for file_info in top_files[10:]:
                            file_path = file_info.get('path', '')
                            file_size = file_info.get('size_human', '0 B')
                            file_url = f"file://{quote(file_path)}"
                            file_name = os.path.basename(file_path)
                            html += f"""
                        <div class="folder-file-item">
                            <a href="{file_url}" class="folder-file-name" title="Click to view">{file_name}</a>
                            <span class="subfolder-size">{file_size}</span>
                        </div>
"""
                        html += """
                    </div>
"""
                    
                    html += """
                </div>
"""
                
                html += """
            </div>
"""
            
            # Generate expanded details for other folders (top 10)
            for seg in top_10_non_home:
                folder = seg['folder']
                full_path = folder.get('path', '')
                path_display = folder.get('path_display', full_path)
                subfolders = folder.get('subfolders', [])
                top_files = folder.get('top_files', [])
                folder_id = f"folder_{seg['idx']}"
                folder_color = seg['color']
                
                # If path is not absolute, construct it from volume
                if not os.path.isabs(full_path):
                    volume = scan_data.get('volume', '')
                    full_path = os.path.join(volume, full_path.lstrip('/'))
                    full_path = os.path.normpath(full_path)
                
                html += f"""
            <div class="folder-bar-expanded" id="{folder_id}" style="border-left-color: {folder_color};">
                <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.3em; display: flex; align-items: center; gap: 10px;">
                    <span style="display: inline-block; width: 20px; height: 20px; background: {folder_color}; border-radius: 4px; flex-shrink: 0;"></span>
                    <span style="color: {folder_color}; font-weight: 600;">{path_display}</span>
                </h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 15px; font-family: 'Monaco', 'Courier New', monospace;">
                    {full_path}
                </p>
"""
                
                # Subfolders
                if subfolders:
                    html += """
                <h4>Subfolders</h4>
                <div class="subfolders-list">
"""
                    for subfolder in subfolders[:5]:  # Top 5 subfolders
                        subfolder_name = subfolder.get('path_display', subfolder.get('path', ''))
                        subfolder_size = subfolder.get('size_human', '0 B')
                        html += f"""
                    <div class="subfolder-item">
                        <span class="subfolder-name">📁 {subfolder_name}</span>
                        <span class="subfolder-size">{subfolder_size}</span>
                    </div>
"""
                    html += """
                </div>
"""
                
                # Top 10 Files
                if top_files:
                    html += f"""
                <h4>Top Files in {path_display}</h4>
                <div class="folder-files-list">
"""
                    for file_info in top_files[:10]:  # Top 10 files
                        file_path = file_info.get('path', '')
                        file_name = os.path.basename(file_path)
                        file_size = file_info.get('size_human', '0 B')
                        file_url = f"file://{quote(file_path)}"
                        html += f"""
                    <div class="folder-file-item">
                        <a href="{file_url}" class="folder-file-name" onclick="event.stopPropagation();">{file_name}</a>
                        <span class="subfolder-size">{file_size}</span>
                    </div>
"""
                    html += """
                </div>
"""
                    
                    # "See All Files" link - always show if there are files, expand inline
                    if len(top_files) > 0:
                        # Always show link, even if showing all files already
                        files_shown = min(10, len(top_files))
                        if len(top_files) > 10:
                            link_text = f"View all {len(top_files)} files in {path_display} →"
                        else:
                            # Even if showing all, still show link to make it clear
                            link_text = f"View all {len(top_files)} files in {path_display} →"
                        
                        html += f"""
                <a href="#" class="see-all-link" onclick="event.stopPropagation(); showAllFilesInFolder('{folder_id}'); return false;">
                    {link_text}
                </a>
                <div id="{folder_id}_all_files" style="display: none; margin-top: 15px;">
                    <h4>All Files ({len(top_files)} total)</h4>
                    <div class="folder-files-list">
"""
                        # Show ALL files in the expanded view (not just beyond 10)
                        for file_info in top_files:
                            file_path = file_info.get('path', '')
                            file_name = os.path.basename(file_path)
                            file_size = file_info.get('size_human', '0 B')
                            file_url = f"file://{quote(file_path)}"
                            html += f"""
                        <div class="folder-file-item">
                            <a href="{file_url}" class="folder-file-name" onclick="event.stopPropagation();">{file_name}</a>
                            <span class="subfolder-size">{file_size}</span>
                        </div>
"""
                        html += """
                    </div>
                </div>
"""
                
                html += """
            </div>
"""
            
            html += """
        </section>
"""
    
    # Top Files with Folder Names (UPDATED - Top 25)
    if scan_type == 'storage':
        top_files = scan_data.get('top_files', [])
        if top_files:
            # Calculate sum of top 25
            top_25_files = top_files[:25]
            total_top_25_bytes = sum(f.get('size_bytes', 0) for f in top_25_files)
            total_top_25_human = format_size(total_top_25_bytes)
            
            html += f"""
        <section>
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h2>Top Largest Files</h2>
                <span style="font-family: 'Monaco', 'Courier New', monospace; color: #666; font-size: 0.95em;">
                    Top 25: {total_top_25_human} total
                </span>
            </div>
            <table id="filesTable" data-showing-all="false">
                <thead>
                    <tr>
                        <th onclick="sortTable('filesTable', 0)">File ↕</th>
                        <th onclick="sortTable('filesTable', 1)">Size ↕</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
"""
            # Add all files to table, but hide rows beyond 25
            for idx, file_info in enumerate(top_files):
                path = file_info.get('path', '')
                size = file_info.get('size_human', '0 B')
                size_bytes = file_info.get('size_bytes', 0)
                file_url = f"file://{quote(path)}"
                basename = os.path.basename(path)
                folder_path = os.path.dirname(path)
                folder_name = os.path.basename(folder_path) if folder_path else 'Root'
                
                # Escape single quotes for JavaScript
                escaped_file_path = path.replace("'", "\\'")
                escaped_folder_path = folder_path.replace("'", "\\'")
                
                # Hide rows beyond top 25 initially
                display_style = '' if idx < 25 else 'display: none;'
                
                html += f"""
                    <tr style="{display_style}">
                        <td class="file-name-cell">
                            <span class="file-name-primary">
                                <a href="{file_url}" title="Click to view in browser">{basename}</a>
                            </span>
                            <span class="file-folder-name">
                                📁 in <a href="#" onclick="event.preventDefault(); revealInFinder('{escaped_folder_path}'); return false;">{folder_name}</a>
                            </span>
                        </td>
                        <td class="size" data-size="{size_bytes}">{size}</td>
                        <td><button onclick="revealInFinder('{escaped_file_path}')" title="Copy command to open in Finder">Reveal in Finder</button></td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
"""
            # Add "See All Files" link if there are more than 25
            if len(top_files) > 25:
                html += f"""
            <div style="text-align: center; margin-top: 20px;">
                <a href="#" class="see-all-link" onclick="showAllFiles('allFiles')" style="display: inline-block;">
                    View all {len(top_files)} files →
                </a>
            </div>
"""
            html += """
        </section>
"""
    
    # Tips
    if tips:
        html += """
        <section class="tips">
            <h3>💡 Quick Wins:</h3>
            <ul>
"""
        for tip in tips:
            html += f"                <li>{tip}</li>\n"
        html += """
            </ul>
        </section>
"""
    
    # Footer
    html += """
        <footer>
            <h3>💡 What to do next:</h3>
            <ul>
                <li>Click folder bars to see subfolders and top files</li>
                <li>Click "Reveal in Finder" button - it will copy a command to your clipboard</li>
                <li>Open Terminal (Cmd+Space, type "Terminal") and paste (Cmd+V), then press Enter</li>
                <li>Finder will open with the file/folder selected</li>
                <li>Delete files manually (send to Trash)</li>
                <li>Start with largest items - easiest wins</li>
            </ul>
            <p style="margin-top: 20px; color: #666; font-size: 0.9em;">
                <strong>Note:</strong> This tool is read-only. You must delete files manually from Finder. Trash = safe undo.<br>
                <strong>Tip:</strong> You can also right-click file links and select "Open in Finder" if your browser supports it.
            </p>
        </footer>
    </div>
    
    <script>
        function toggleFolder(folderId) {
            const expanded = document.getElementById(folderId);
            if (expanded) {
                const isActive = expanded.classList.contains('active');
                
                // Close all other folders
                document.querySelectorAll('.folder-bar-expanded').forEach(el => {
                    el.classList.remove('active');
                });
                document.querySelectorAll('.folder-bar-segment').forEach(el => {
                    el.classList.remove('active');
                });
                
                // Toggle this folder
                if (!isActive) {
                    expanded.classList.add('active');
                    // Find and highlight corresponding segment
                    const segment = document.querySelector(`[onclick*="'${folderId}'"]`);
                    if (segment && segment.classList.contains('folder-bar-segment')) {
                        segment.classList.add('active');
                    }
                    // Scroll to expanded section
                    expanded.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                }
            }
        }
        
        function showAllFilesInFolder(folderId) {
            const allFilesDiv = document.getElementById(folderId + '_all_files');
            if (allFilesDiv) {
                const isVisible = allFilesDiv.style.display !== 'none';
                allFilesDiv.style.display = isVisible ? 'none' : 'block';
                
                // Update link text
                const link = event.target.closest('a');
                if (link) {
                    if (isVisible) {
                        link.textContent = link.textContent.replace('Hide', 'View all');
                    } else {
                        link.textContent = link.textContent.replace('View all', 'Hide');
                    }
                }
                
                // Scroll to the expanded section
                if (!isVisible) {
                    setTimeout(() => {
                        allFilesDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                    }, 100);
                }
            }
        }
        
        function showAllFiles(sectionId) {
            // For the main "Top Largest Files" section, show all files
            const table = document.getElementById('filesTable');
            if (table) {
                const tbody = table.querySelector('tbody');
                const allRows = Array.from(tbody.querySelectorAll('tr'));
                
                // Check if we're showing all or just top 25
                const showingAll = table.dataset.showingAll === 'true';
                
                if (showingAll) {
                    // Show only top 25
                    allRows.forEach((row, idx) => {
                        row.style.display = idx < 25 ? '' : 'none';
                    });
                    table.dataset.showingAll = 'false';
                    const link = event.target.closest('a');
                    if (link) {
                        link.textContent = link.textContent.replace('Hide', 'View all');
                    }
                } else {
                    // Show all files
                    allRows.forEach(row => {
                        row.style.display = '';
                    });
                    table.dataset.showingAll = 'true';
                    const link = event.target.closest('a');
                    if (link) {
                        const totalFiles = allRows.length;
                        link.textContent = `Hide additional files (showing all ${totalFiles})`;
                    }
                }
            }
        }
        
        function sortTable(tableId, colIndex) {
            const table = document.getElementById(tableId);
            const tbody = table.querySelector('tbody');
            const rows = Array.from(tbody.querySelectorAll('tr'));
            const isNumeric = colIndex === 1; // Size column
            
            // Determine sort direction
            const currentOrder = table.dataset.sortOrder || 'asc';
            const newOrder = currentOrder === 'asc' ? 'desc' : 'asc';
            table.dataset.sortOrder = newOrder;
            
            rows.sort((a, b) => {
                const aVal = a.cells[colIndex].textContent.trim();
                const bVal = b.cells[colIndex].textContent.trim();
                
                if (isNumeric) {
                    // Extract numeric value from data-size attribute or text
                    const aNum = parseFloat(a.cells[colIndex].getAttribute('data-size') || aVal.replace(/[^0-9.]/g, ''));
                    const bNum = parseFloat(b.cells[colIndex].getAttribute('data-size') || bVal.replace(/[^0-9.]/g, ''));
                    return newOrder === 'asc' ? aNum - bNum : bNum - aNum;
                } else {
                    return newOrder === 'asc' 
                        ? aVal.localeCompare(bVal)
                        : bVal.localeCompare(aVal);
                }
            });
            
            // Update table
            rows.forEach(row => tbody.appendChild(row));
            
            // Update header arrows
            const headers = table.querySelectorAll('th');
            headers.forEach((h, i) => {
                if (i === colIndex) {
                    h.textContent = h.textContent.replace(/ ↕| ↑| ↓/g, '') + (newOrder === 'asc' ? ' ↑' : ' ↓');
                } else {
                    h.textContent = h.textContent.replace(/ ↕| ↑| ↓/g, '') + ' ↕';
                }
            });
        }
        
        function revealInFinder(path) {
            const cmd = `open -R "${path}"`;
            
            // Copy to clipboard
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(cmd).then(() => {
                    showCopySuccess(cmd);
                }).catch(() => {
                    fallbackCopy(cmd);
                });
            } else {
                fallbackCopy(cmd);
            }
        }
        
        function fallbackCopy(cmd) {
            const textarea = document.createElement('textarea');
            textarea.value = cmd;
            textarea.style.position = 'fixed';
            textarea.style.opacity = '0';
            document.body.appendChild(textarea);
            textarea.select();
            try {
                document.execCommand('copy');
                showCopySuccess(cmd);
            } catch (e) {
                alert('Could not copy to clipboard. Please copy manually:\\n' + cmd);
            }
            document.body.removeChild(textarea);
        }
        
        function showCopySuccess(cmd) {
            // Remove any existing success message
            const existing = document.getElementById('copy-success-message');
            if (existing) {
                existing.remove();
            }
            
            // Create success message
            const successDiv = document.createElement('div');
            successDiv.id = 'copy-success-message';
            successDiv.className = 'copy-success';
            successDiv.innerHTML = `
                <strong>✓ Command copied to clipboard!</strong><br>
                <div class="copy-instructions">
                    Press Cmd+V in Terminal, then press Enter to open Finder.
                </div>
                <small>Command: <code>` + cmd + `</code></small>
            `;
            
            // Insert at top of page
            const container = document.querySelector('.container');
            if (container) {
                container.insertBefore(successDiv, container.firstChild);
                
                // Scroll to top
                window.scrollTo({ top: 0, behavior: 'smooth' });
                
                // Remove after 10 seconds
                setTimeout(() => {
                    successDiv.remove();
                }, 10000);
            }
        }
    </script>
</body>
</html>
"""
    
    # Write to file
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)
    
    return report_path

