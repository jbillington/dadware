"""HTML report generator with UX improvements."""

import os
import json
import datetime
import webbrowser
from urllib.parse import quote
# Absolute import of the stdlib `html` module. This file is itself named
# `renderers/html.py`, so `import html` alone would be dangerously ambiguous
# to a reader (Python 3 absolute imports do resolve it to the stdlib, not to
# this module - verified with `python -c "import html; html.escape"` run from
# this package). We still import only the `escape` function under an alias
# rather than binding the name `html`, because every render_*() function
# below uses a local variable named `html` as its string accumulator; a
# bare `import html` would be shadowed by that local variable inside those
# functions and `html.escape(...)` would fail with AttributeError.
from html import escape as escape_html
from scanners.grading import (
    grade_free_space,
    grade_home_folders_ratio,
    grade_home_folders_clutter,
    grade_library_size,
    calculate_composite_storage_grade,
    score_to_letter,
)
from utils.formatters import format_size, get_status_emoji, get_status_text
from utils.path_utils import folder_label, left_out_note
from utils.permissions import FDA_SETTINGS_URL
from utils.system_info import get_system_info
from utils.version import VERSION
from utils import promo
from utils.llm_prompt import generate_llm_prompt
from utils.memory import memory_summary, AVAILABLE_NOTE, APPS_NOTE


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


REPORT_CSS = """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: #f5f5f5;
            padding: 20px;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 30px;
        }
        header {
            border-bottom: 3px solid #333;
            padding-bottom: 20px;
            margin-bottom: 30px;
        }
        h1 {
            font-size: 2em;
            margin-bottom: 10px;
        }
        .meta {
            color: #666;
            font-size: 0.9em;
        }
        
        /* Storage Overview Section */
        .storage-overview {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .storage-overview h2 {
            color: white;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .storage-stats {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
            flex-wrap: wrap;
            gap: 15px;
        }
        .storage-stat {
            flex: 1;
            min-width: 150px;
        }
        .storage-stat-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 5px;
        }
        .storage-stat-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        .storage-stat-percent {
            font-size: 1.5em;
            font-weight: bold;
        }
        .storage-stat-size {
            font-size: 0.7em;
            font-weight: normal;
            opacity: 0.9;
            margin-left: 8px;
        }
        .progress-bar-container {
            background: rgba(255,255,255,0.2);
            border-radius: 10px;
            height: 30px;
            overflow: hidden;
            margin: 15px 0;
            position: relative;
        }
        .progress-bar {
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
        }
        
        .permission-warning {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .permission-warning h3 {
            color: #856404;
            margin-top: 0;
            margin-bottom: 10px;
        }
        .permission-warning p {
            color: #856404;
            margin: 5px 0;
        }
        .permission-warning ul {
            color: #856404;
            margin: 10px 0 10px 20px;
        }
        .permission-warning li {
            margin: 5px 0;
        }
        .permission-warning .permission-status {
            font-weight: bold;
            margin-bottom: 10px;
        }
        .personality {
            background: #f9f9f9;
            border-left: 4px solid #333;
            padding: 15px 20px;
            margin: 20px 0;
            border-radius: 4px;
        }
        .personality h2 {
            font-size: 1.2em;
            margin-bottom: 10px;
        }
        .personality p {
            font-style: italic;
            color: #555;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }
        
        section {
            margin: 30px 0;
        }
        h2 {
            font-size: 1.5em;
            margin-bottom: 15px;
            color: #333;
        }
        h3 {
            font-size: 1.2em;
            margin: 20px 0 10px 0;
            color: #555;
        }
        
        /* Folder Bar Chart - Single Horizontal Bar */
        .folder-chart-container {
            margin: 30px 0;
        }
        .folder-bar-header {
            display: flex;
            align-items: center;
            justify-content: flex-start;
            gap: 14px;
            margin-bottom: 30px;
        }
        /* The heading's own bottom margin sat inside the flex row and pushed
           its text above the hint's centre line; the header carries the space. */
        .folder-bar-header h2 {
            margin-bottom: 0;
        }
        .folder-bar-hint {
            display: inline-flex;
            align-items: center;
            gap: 5px;
            font-size: 0.8em;
            color: #000;
        }
        .folder-bar-hint svg {
            width: 14px;
            height: 14px;
            flex: none;
        }
        .folder-bar-label {
            font-weight: 600;
            font-size: 1.1em;
            color: #333;
        }
        .folder-bar-summary {
            font-family: 'Monaco', 'Courier New', monospace;
            color: #666;
            font-size: 0.95em;
        }
        .folder-bar-wrapper {
            background: #e9ecef;
            border-radius: 8px;
            height: 50px;
            overflow: hidden;
            position: relative;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            display: flex;
        }
        .folder-bar-segment {
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
        }
        .folder-bar-segment:hover {
            opacity: 0.85;
            transform: scaleY(1.08);
            z-index: 10;
            box-shadow: 0 0 8px rgba(0,0,0,0.3);
        }
        .folder-bar-segment.active {
            opacity: 0.9;
            box-shadow: inset 0 0 12px rgba(0,0,0,0.4);
        }
        .folder-bar-segment:last-child {
            border-right: none;
        }
        /* Text inside segments */
        .segment-label {
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
        }
        .segment-label-name {
            display: block;
            font-weight: 600;
        }
        .segment-label-size {
            display: block;
            font-size: 0.85em;
            font-weight: 400;
            opacity: 0.95;
            font-family: 'Monaco', 'Courier New', monospace;
            margin-top: 1px;
        }
        .folder-bar-expanded {
            margin-top: 15px;
            padding: 15px;
            background: #f8f9fa;
            border-left: 3px solid #4A90E2;
            border-radius: 4px;
            display: none;
        }
        .folder-bar-expanded.active {
            display: block;
        }
        .subfolders-list {
            margin: 15px 0;
        }
        .subfolder-item {
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .subfolder-name {
            font-weight: 500;
            color: #555;
        }
        .subfolder-size {
            font-family: 'Monaco', 'Courier New', monospace;
            color: #666;
            font-size: 0.9em;
        }
        .folder-files-list {
            margin: 15px 0;
        }
        .folder-file-item {
            padding: 8px 12px;
            margin: 5px 0;
            background: white;
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .folder-file-name {
            color: #0066cc;
            text-decoration: none;
        }
        .folder-file-name:hover {
            text-decoration: underline;
        }
        .see-all-link {
            display: block;
            margin-top: 15px;
            padding: 10px;
            text-align: center;
            color: #0066cc;
            text-decoration: none;
            border: 1px dashed #0066cc;
            border-radius: 4px;
            transition: all 0.2s ease;
        }
        .see-all-link:hover {
            background: #0066cc;
            color: white;
        }
        
        /* Top Files with Folder Names */
        table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        th {
            background: #333;
            color: white;
            padding: 12px;
            text-align: left;
            cursor: pointer;
            user-select: none;
        }
        th:hover {
            background: #555;
        }
        td {
            padding: 10px 12px;
            border-bottom: 1px solid #ddd;
        }
        tr:hover {
            background: #f9f9f9;
        }
        .file-name-cell {
            padding: 12px;
        }
        .file-name-primary {
            font-weight: 600;
            font-size: 1em;
            color: #333;
            display: block;
        }
        .file-name-primary a {
            color: #0066cc;
            text-decoration: none;
        }
        .file-name-primary a:hover {
            text-decoration: underline;
        }
        .file-folder-name {
            font-size: 0.85em;
            color: #666;
            margin-top: 4px;
            font-style: italic;
            font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
            -webkit-font-smoothing: antialiased;
            -moz-osx-font-smoothing: grayscale;
            text-rendering: optimizeLegibility;
        }
        .file-folder-name a {
            color: #0066cc;
            text-decoration: none;
        }
        .file-folder-name a:hover {
            text-decoration: underline;
        }
        .size {
            font-family: 'Monaco', 'Courier New', monospace;
            text-align: right;
        }
        button, .button-link {
            background: #0066cc;
            color: white;
            border: none;
            padding: 6px 12px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 0.9em;
            text-decoration: none;
            display: inline-block;
        }
        button:hover, .button-link:hover {
            background: #0052a3;
        }
        .copy-success {
            background: #d4edda;
            color: #155724;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
            border: 1px solid #c3e6cb;
        }
        .copy-instructions {
            font-family: 'Monaco', 'Courier New', monospace;
            background: #f8f9fa;
            padding: 8px;
            border-radius: 4px;
            margin: 5px 0;
            font-size: 0.9em;
        }
        footer {
            margin-top: 40px;
            padding-top: 20px;
            border-top: 2px solid #ddd;
        }
        .personality .dad-tips {
            margin: 12px 0 0 20px;
            color: #333;
        }
        .personality .dad-tips li {
            margin: 5px 0;
        }
        .personality .next-steps-link {
            font-style: normal;
            margin-top: 12px;
        }
        
        /* Report Card Styles */
        .report-card {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 8px;
            margin: 20px 0;
            box-shadow: 0 4px 15px rgba(0,0,0,0.1);
        }
        .report-card h2 {
            color: white;
            margin-bottom: 20px;
            font-size: 1.8em;
        }
        .overall-grade {
            text-align: center;
            margin: 30px 0;
            padding: 20px;
            background: rgba(255,255,255,0.15);
            border-radius: 8px;
        }
        .overall-grade-letter {
            font-size: 4em;
            font-weight: bold;
            margin: 10px 0;
            text-shadow: 2px 2px 4px rgba(0,0,0,0.3);
        }
        .overall-grade-score {
            font-size: 1.2em;
            opacity: 0.9;
        }
        .storage-headline {
            text-align: center;
            font-size: 1.15em;
            margin-top: 6px;
            opacity: 0.95;
        }
        .cache-explainer {
            color: #666;
            margin: 0 0 15px 0;
            padding-left: 20px;
            line-height: 1.65;
        }
        .cache-explainer li {
            margin-bottom: 8px;
        }
        .cache-explainer strong {
            color: #444;
        }
        .storage-aside {
            text-align: center;
            margin-top: 6px;
            opacity: 0.75;
            font-size: 0.85em;
        }
        .metric-link {
            color: inherit;
            text-decoration: none;
            border-bottom: 1px dotted rgba(255,255,255,0.6);
        }
        .metric-link:hover {
            border-bottom-style: solid;
        }
        .storage-metrics {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 20px 0;
            padding: 20px;
            background: rgba(255,255,255,0.1);
            border-radius: 8px;
        }
        .metric-item {
            text-align: center;
        }
        .metric-label {
            font-size: 0.9em;
            opacity: 0.9;
            margin-bottom: 8px;
        }
        .metric-value {
            font-size: 1.5em;
            font-weight: bold;
        }
        .grade-breakdown {
            margin: 20px 0;
        }
        .grade-row {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px 15px;
            margin: 8px 0;
            background: rgba(255,255,255,0.1);
            border-radius: 6px;
        }
        .grade-label {
            font-size: 1.1em;
            font-weight: 500;
        }
        .grade-note {
            font-size: 0.75em;
            font-weight: 400;
            opacity: 0.75;
            margin-top: 2px;
        }
        .grade-display {
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .grade-letter {
            font-size: 2em;
            font-weight: bold;
            min-width: 50px;
            text-align: center;
        }
        .grade-score {
            font-size: 1em;
            opacity: 0.9;
        }
        .grade-letter-A {
            color: #6bcf7f;
        }
        .grade-letter-B {
            color: #ffd93d;
        }
        .grade-letter-C {
            color: #ffa500;
        }
        .grade-letter-D {
            color: #ff6b6b;
        }
        .grade-letter-F {
            color: #e74c3c;
        }
        .library-grades {
            margin-top: 15px;
            padding-left: 20px;
        }
        .library-grade-advice {
            flex-basis: 100%;
            font-size: 0.8em;
            opacity: 0.85;
            margin-top: 6px;
            line-height: 1.35;
        }
        .library-grade-item {
            flex-wrap: wrap;
            padding: 8px 12px;
            margin: 5px 0;
            background: rgba(255,255,255,0.05);
            border-radius: 4px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .library-grade-label {
            font-size: 0.95em;
        }
        .library-grade-display {
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .library-grade-letter {
            font-size: 1.3em;
            font-weight: bold;
        }
        .library-grade-size {
            font-size: 0.85em;
            opacity: 0.8;
            font-family: 'Monaco', 'Courier New', monospace;
        }
"""


REPORT_JS = """        function copyPromptToClipboard() {
            const textarea = document.getElementById('llmPrompt');
            const status = document.getElementById('copyStatus');

            // Select and copy
            textarea.select();
            textarea.setSelectionRange(0, 99999); // For mobile devices

            try {
                document.execCommand('copy');

                // Show success message
                status.style.opacity = '1';
                setTimeout(() => {
                    status.style.opacity = '0';
                }, 2000);

                // Deselect
                window.getSelection().removeAllRanges();
            } catch (err) {
                alert('Failed to copy. Please manually select and copy the text.');
            }
        }

        function copyPromoCommand() {
            const field = document.getElementById('promoCommand');
            const status = document.getElementById('promoCopyStatus');
            field.select();
            try {
                document.execCommand('copy');
                status.style.opacity = '1';
                setTimeout(() => { status.style.opacity = '0'; }, 2000);
                window.getSelection().removeAllRanges();
            } catch (err) {
                alert('Failed to copy. Please select the command and copy it.');
            }
        }

        // Show (and copy) the prompt with or without the largest-files list.
        function syncPromptFileNames() {
            const box = document.getElementById('includeFileNames');
            if (!box) { return; }
            const source = document.getElementById(box.checked ? 'llmPromptFull' : 'llmPromptNoFiles');
            document.getElementById('llmPrompt').value = source.value;
        }
        window.addEventListener('DOMContentLoaded', syncPromptFileNames);

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
            // Handle both ID patterns: folderId directly or with _all_files suffix
            let allFilesDiv = document.getElementById(folderId);
            if (!allFilesDiv) {
                // Try with _all_files suffix (for other folders pattern)
                allFilesDiv = document.getElementById(folderId + '_all_files');
            }
            
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
"""


def render_document_head(now):
    """Doctype, head (with inline CSS), body-open, container-open, header."""
    date_str = now.strftime('%B %d, %Y %H:%M')
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dad's Report Card - {now.strftime('%b %d, %Y')}</title>
    <style>
{REPORT_CSS}    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>DAD'S REPORT CARD</h1>
            <p class="meta">Ask Dad v{VERSION}  |  {date_str}</p>
        </header>
"""
    return html


# What to do about a big library. Ask Dad never deletes anything on its own
# and does not name files to delete; these point at the app's own settings,
# which is where the owner makes the call.
LIBRARY_ADVICE = {
    'photos': "In Photos, Settings > iCloud > Optimize Mac Storage keeps full-size "
              "originals in iCloud and smaller copies here.",
    'mail': "In Mail, Settings > Accounts can stop downloading attachments automatically, "
            "and Mailbox > Rebuild fixes a bloated mailbox.",
    'music': "In Music, Settings > Files shows where the library lives; downloaded "
             "songs can be removed and streamed instead.",
}


def render_report_card(scan_data):
    """Storage Report Card section: overall + per-metric grade breakdown."""
    scan_type = scan_data.get('scan_type', 'unknown')
    volume_info = scan_data.get('volume_info', {}) if scan_type == 'storage' else {}
    html = ""
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
        # The old "Reclaimable %" summed the top 25 files, which on a real
        # Mac included Xcode.app and a Docker disk - a number that points at
        # things nobody should delete. The Trash is the one pile that is
        # already marked for deletion, so it is the one we state.
        trash = scan_data.get('trash') or {}
        if trash.get('permission_denied') or not trash:
            trash_stat = 'Needs Full Disk Access' if trash else 'Not measured'
        else:
            trash_stat = trash.get('total_size_human') or '0 B'
        
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
            'creative': 'Creative Apps'
        }
        
        # Check overall scan status
        scan_status = mac_libraries.get('scan_status', 'complete')
        
        for lib_type, lib_name in library_types.items():
            lib_data = mac_libraries.get(lib_type, {})
            lib_status = lib_data.get('status', 'complete')
            
            if lib_type in ['photos', 'music', 'creative']:
                lib_size = lib_data.get('total_size_bytes', 0)
            else:
                lib_size = lib_data.get('size_bytes', 0)
            
            # Show library if it has size, if it was skipped/interrupted, or if
            # it came back empty only because we lack permission to read it -
            # an invisible zero is exactly what made the grade look complete.
            # Only when a library scan actually ran. With --no-mac-libraries
            # there is nothing to be blocked from, and "needs Full Disk Access"
            # would be the wrong explanation for a section the user turned off.
            blocked = bool(mac_libraries) and lib_type in (
                (scan_data.get('permission_status') or {}).get('missing_permissions') or []
            )
            if lib_size > 0 or lib_status != 'complete' or blocked:
                if lib_type == 'messages' and lib_size > 0:
                    # Messages is the user's own history: a big one is not a
                    # problem to fix, and an F for it reads as scolding. Show
                    # the size, leave it out of the grade.
                    grade = {'letter': '-', 'score': 0}
                elif lib_size > 0:
                    grade = grade_library_size(lib_size, lib_type, used_bytes)
                else:
                    # No grade for skipped/interrupted libraries
                    grade = {'letter': '-', 'score': 0}
                
                library_grades[lib_type] = {
                    'name': lib_name,
                    'grade': grade,
                    'size': (format_size(lib_size) + (' (not graded)' if lib_type == 'messages' else ''))
                            if lib_size > 0 else 'N/A',
                    'status': lib_status,
                    'reason': lib_data.get('reason', '')
                }
                if lib_size > 0 and lib_type != 'messages':
                    library_scores.append(grade['score'])
        
        # Calculate average library grade (only from completed scans with size > 0)
        avg_library_score = sum(library_scores) / len(library_scores) if library_scores else 0
        avg_library_grade = {
            'letter': score_to_letter(avg_library_score) if library_scores else '-',
            'score': avg_library_score
        }
        
        # A library that never ran is left out of the average above rather than
        # averaged in as a zero, so a truncated scan does not drag the score
        # down - it quietly shrinks the evidence behind it. Scoring that subset
        # as though all six libraries had been measured is the dishonest part:
        # on the Aug 24 run the grade came from Photos, Music and Messages
        # alone and still carried its full 0.2 of the composite. Don't grade
        # what wasn't measured - drop the component and let the weights
        # renormalize, so the composite reflects only what the scan actually saw.
        libraries_incomplete = any(
            info.get('status') not in ('complete', None)
            for info in library_grades.values()
        )

        # A library blocked by Full Disk Access does NOT report an error - it
        # reports status 'complete' with zero bytes, because the scanner simply
        # finds nothing at a path it cannot read. So the status check above
        # sails straight past it, and the average gets computed from whatever
        # is left. On a Mac without FDA that means Photos, Messages and Mail
        # all silently drop out and the grade comes from Music alone: one
        # library, scored A, presented as though it covered them all.
        missing_permissions = set(
            (scan_data.get('permission_status') or {}).get('missing_permissions') or []
        )
        # Only libraries that came back *silently* empty. One that already
        # reported 'error' or 'skipped' is telling the truth about itself and
        # keeps its own status - the problem being fixed here is the library
        # that claims success while having measured nothing.
        blocked_and_empty = {
            lib_type for lib_type, info in library_grades.items()
            if lib_type in missing_permissions
            and info.get('size') == 'N/A'
            and info.get('status') == 'complete'
        }
        if blocked_and_empty:
            libraries_incomplete = True
            for lib_type in blocked_and_empty:
                library_grades[lib_type]['status'] = 'no-permission'
                library_grades[lib_type]['reason'] = 'needs Full Disk Access'

        libraries_scored = bool(library_scores) and not libraries_incomplete
        
        # Nothing in the report explained what any of these measured. A
        # reader could see "Home Folders Ratio: A" and have no idea what was
        # graded, which makes an A meaningless and a D unactionable. Each line
        # says what it looks at and what share of the grade it carries, so the
        # numbers add up in the open rather than in docs/GRADING.md.
        library_title = ("Mac Apps: Photos, Music, & Mail (15% of grade)"
                         if libraries_scored else
                         "Mac Apps: Photos, Music, & Mail (not counted in grade)")
        component_notes = {
            'free_space': "A nearly full disk can make your Mac sluggish, and it is the "
                          "part of the grade you can change fastest.",
            'home_folders_ratio': "These are your files you saved",
            'home_folders_clutter': "This is all the junk in Downloads and on your Desktop.",
            'mac_libraries': "These are harder to reduce in size, but there are strategies.",
        }

        # The breakdown row has to agree with the composite. Showing a letter
        # for a component that was dropped invites the reader to add it up and
        # get a different answer than we did.
        if libraries_scored:
            library_row_letter = avg_library_grade['letter']
            library_row_score = f"{avg_library_grade['score']:.0f}/100"
            library_row_note = f'<div class="grade-note">{component_notes["mac_libraries"]}</div>'
        else:
            library_row_letter = '-'
            library_row_score = 'not scored'
            if blocked_and_empty:
                reason = 'needs Full Disk Access to measure - not counted toward the overall grade'
            elif library_grades:
                reason = 'scan incomplete - not counted toward the overall grade'
            else:
                reason = 'not scanned - not counted toward the overall grade'
            library_row_note = (
                f'<div class="grade-note">{component_notes["mac_libraries"]} {reason}</div>')
        
        # Home folders clutter counts toward the composite as of Aug 24, 2026.
        # It was computed and displayed but excluded, so a user could score an F
        # on Downloads and Desktop and watch the big letter at the top not move
        # at all. It is also the one component measuring something a reader can
        # act on in ten minutes, which is the whole promise of the report.
        component_grades = {
            'free_space': free_space_grade,
            'home_folders_ratio': home_folders_ratio_grade,
            'home_folders_clutter': home_folders_clutter_grade,
        }
        weights = {
            'free_space': 0.5,
            'home_folders_ratio': 0.15,
            'home_folders_clutter': 0.2,
        }
        if libraries_scored:
            component_grades['mac_libraries'] = avg_library_grade
            weights['mac_libraries'] = 0.15
        # Renormalize to 1.0. Without this, dropping a component silently
        # subtracts its weight from the top-line score instead of
        # redistributing it - which is also what --no-mac-libraries used to do,
        # costing 20 points for a flag that only means "don't look here".
        total_weight = sum(weights.values())
        weights = {k: v / total_weight for k, v in weights.items()}
        composite_grade = calculate_composite_storage_grade(component_grades, weights)
        
        # Get overall grade comment
        overall_comment = "Excellent!" if composite_grade['score'] >= 90 else \
                          "Good job!" if composite_grade['score'] >= 80 else \
                          "Room for improvement" if composite_grade['score'] >= 70 else \
                          "Needs work" if composite_grade['score'] >= 60 else \
                          "Critical issues"
        
        # How full the disk actually is. The card graded Free Space without
        # ever printing the number it graded, which is the one figure a
        # storage tool most owes the reader.
        total_human = volume_info.get('total_human', '0 B')
        used_human = volume_info.get('used_human', '0 B')
        free_human = volume_info.get('free_human', '0 B')
        storage_headline = escape_html(
            f"{used_human} used of {total_human}, {free_human} free ({free_percent:.0f}%)"
        )

        html += f"""
        <section class="report-card">
            <h2>📊 Storage Report Card - {escape_html(volume)}</h2>
            
            <div class="overall-grade">
                <div class="overall-grade-letter grade-letter-{composite_grade['letter']}">{composite_grade['letter']}</div>
                <div class="overall-grade-score">{composite_grade['score']:.0f}/100 - {overall_comment}</div>
            </div>

            <div class="storage-headline">{storage_headline}</div>

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
                    <div class="metric-label">In the Trash</div>
                    <div class="metric-value">{escape_html(trash_stat)}</div>
                </div>
            </div>
            
            <div class="grade-breakdown">
                <h3 style="color: white; margin-bottom: 15px; font-size: 1.2em;">Grade Breakdown</h3>
                
                <div class="grade-row">
                    <div class="grade-label">Free Space (50% of grade)<div class="grade-note">{component_notes['free_space']}</div></div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter-{free_space_grade['letter']}">{free_space_grade['letter']}</div>
                        <div class="grade-score">{free_space_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">Home Folders Ratio (15% of grade)<div class="grade-note">{component_notes['home_folders_ratio']}</div></div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter-{home_folders_ratio_grade['letter']}">{home_folders_ratio_grade['letter']}</div>
                        <div class="grade-score">{home_folders_ratio_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">Clutter (20% of grade)<div class="grade-note">{component_notes['home_folders_clutter']}</div></div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter-{home_folders_clutter_grade['letter']}">{home_folders_clutter_grade['letter']}</div>
                        <div class="grade-score">{home_folders_clutter_grade['score']:.0f}/100</div>
                    </div>
                </div>
                
                <div class="grade-row">
                    <div class="grade-label">{escape_html(library_title)}{library_row_note}</div>
                    <div class="grade-display">
                        <div class="grade-letter grade-letter-{library_row_letter}">{library_row_letter}</div>
                        <div class="grade-score">{library_row_score}</div>
                    </div>
                </div>
"""
        
        # Build library grades HTML separately to avoid nested f-string issues
        library_grades_html = ""
        if library_grades:
            library_items = []
            for lib_key, lib_data in library_grades.items():
                lib_name = lib_data['name']
                lib_letter = lib_data['grade']['letter']
                lib_size = lib_data['size']
                lib_status = lib_data.get('status', 'complete')
                lib_reason = lib_data.get('reason', '')
                
                # Add status indicator
                status_badge = ""
                if lib_status == 'skipped':
                    status_badge = f'<span style="display: inline-block; font-size: 0.8em; margin-left: 8px; padding: 1px 8px; border-radius: 10px; background: #eeeeee; color: #555555;">(skipped: {escape_html(lib_reason)})</span>'
                elif lib_status == 'error':
                    status_badge = '<span style="display: inline-block; font-size: 0.8em; margin-left: 8px; padding: 1px 8px; border-radius: 10px; background: #fde8e8; color: #b71c1c;">(error)</span>'
                elif lib_status == 'interrupted':
                    status_badge = '<span style="display: inline-block; font-size: 0.8em; margin-left: 8px; padding: 1px 8px; border-radius: 10px; background: #fff3cd; color: #8a4b00;">(interrupted)</span>'
                elif lib_status == 'no-permission':
                    status_badge = '<span style="display: inline-block; font-size: 0.8em; margin-left: 8px; padding: 1px 8px; border-radius: 10px; background: #fff3cd; color: #8a4b00;">(needs Full Disk Access)</span>'
                
                # A grade without an action is a scolding: a D or F gets one
                # line on what the owner can do about it, in the same
                # read-only voice as the snapshot section.
                advice = LIBRARY_ADVICE.get(lib_key) if lib_letter in ('D', 'F') else None
                advice_html = (
                    f'<div class="library-grade-advice">{escape_html(advice)}</div>'
                    if advice else ''
                )

                library_items.append(f'''
                        <div class="library-grade-item">
                            <div class="library-grade-label">{lib_name}{status_badge}</div>
                            <div class="library-grade-display">
                                <div class="library-grade-letter grade-letter-{lib_letter}">{lib_letter}</div>
                                <div class="library-grade-size">{lib_size}</div>
                            </div>
                            {advice_html}
                        </div>
                        ''')
            library_grades_html = f'''
                <div class="library-grades">
                    {''.join(library_items)}
                </div>
                '''
        
        # Add overall scan status notice if partial or interrupted
        if scan_status != 'complete' and mac_libraries:
            status_notice = ""
            if scan_status == 'partial':
                interrupted = mac_libraries.get('interrupted_scans', [])
                if interrupted:
                    status_notice = f'<div style="margin-top: 15px; padding: 10px; background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; border-radius: 4px;"><strong>⚠️ Partial Scan:</strong> Some libraries were skipped due to time limits: {", ".join(interrupted)}</div>'
                else:
                    status_notice = '<div style="margin-top: 15px; padding: 10px; background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; border-radius: 4px;"><strong>⚠️ Partial Scan:</strong> Some libraries were skipped due to time limits</div>'
            elif scan_status == 'interrupted':
                status_notice = '<div style="margin-top: 15px; padding: 10px; background: #ffebee; color: #b71c1c; border-left: 4px solid #d32f2f; border-radius: 4px;"><strong>⚠️ Scan Interrupted:</strong> Library scan was interrupted. Results may be incomplete.</div>'
            
            if status_notice:
                library_grades_html += status_notice
        
        html += library_grades_html + """
            </div>
        </section>
"""
    return html


def render_volume_summary(scan_data):
    """Plain summary for a drive that is not the one the home folder is on.

    No letter grade. Three of the four graded components measure the home
    folder and the Mac's app libraries, which are not on this drive at all,
    and Free Space alone is a number the reader can already see - a letter
    computed from it adds a verdict where the user asked a question: what is
    on this drive?
    """
    volume_info = scan_data.get('volume_info', {}) or {}
    volume = scan_data.get('volume', 'Unknown')
    metrics = scan_data.get('metrics', {}) or {}

    total_human = volume_info.get('total_human', '0 B')
    used_human = volume_info.get('used_human', '0 B')
    free_human = volume_info.get('free_human', '0 B')
    free_percent = volume_info.get('free_percent', 0)

    headline = escape_html(
        f"{used_human} used of {total_human}, {free_human} free ({free_percent:.0f}%)"
    )
    folders_total = escape_html(metrics.get('sum_top_10_folders_human', '0 B'))
    files_total = escape_html(metrics.get('sum_top_25_files_human', '0 B'))

    return f"""
        <section class="report-card">
            <h2>💾 Volume Report - {escape_html(volume)}</h2>

            <div class="storage-headline">{headline}</div>

            <p class="storage-aside">
                This is a drive, not your startup disk, so there is no grade and no
                report card.
            </p>

            <div class="storage-metrics">
                <div class="metric-item">
                    <div class="metric-label">Top 10 Folders</div>
                    <div class="metric-value">{folders_total}</div>
                </div>
                <div class="metric-item">
                    <div class="metric-label">Top 25 Files</div>
                    <div class="metric-value">{files_total}</div>
                </div>
            </div>
        </section>
"""


def render_permission_warning(scan_data):
    """Honest-denial notices: denied folders and missing Full Disk Access.

    Implements the tier matrix from PERMISSIONS-PLAN.md — anything the scan
    couldn't see says so, with the fix path. Never a silent zero.
    """
    scan_type = scan_data.get('scan_type', 'unknown')
    html = ""
    if scan_type == 'storage':
        permission_status = scan_data.get('permission_status', {})

        # Auto-prompt tier: folders macOS asked about and the user declined.
        folders = permission_status.get('folders') or {}
        denied_folders = [name for name, info in folders.items()
                          if isinstance(info, dict) and info.get('status') == 'denied']
        if denied_folders:
            names = ", ".join(escape_html(name) for name in denied_folders)
            html += f"""
        <section class="permission-warning">
            <h3>🚪 Folders I couldn't check</h3>
            <p class="permission-status">No access to: {names}</p>
            <p>You told macOS not to let me look there. That's fine, and nothing is broken.
               Those folders are left out of the numbers above rather than counted as zero.
               If you change your mind: <strong>System Settings</strong> →
               <strong>Privacy &amp; Security</strong> → <strong>Files &amp; Folders</strong>,
               then run the scan again.</p>
        </section>
"""

        # The Trash, when macOS would not let us measure it. It has no row
        # in the folder chart in that case - a bar cannot show "unknown" -
        # so its absence is stated here rather than left to look like an
        # empty Trash.
        trash = scan_data.get('trash') or {}
        if trash.get('permission_denied'):
            html += """
        <section class="permission-warning">
            <h3>🗑️ I couldn't measure your Trash</h3>
            <p class="permission-status">Full Disk Access required for: Trash</p>
            <p>Deleted files still take up space until the Trash is emptied. macOS won't
               let me look in there yet, so the Trash is missing from the folders above
               rather than counted as zero. Granting Full Disk Access below fixes it on
               the next scan.</p>
        </section>
"""

        # FDA tier: protected libraries need the manual toggle.
        if permission_status and not permission_status.get('has_access', True):
            missing = permission_status.get('missing_permissions', [])
            if missing:
                libs = ", ".join(m.title() for m in missing)
                html += f"""
        <section class="permission-warning">
            <h3>⚠️ Permission Notice</h3>
            <p class="permission-status">Full Disk Access required for: {libs}</p>
            <p>Can't see those libraries yet. They're marked "needs Full Disk Access" above.
               To grant access:</p>
            <ul>
                <li><a href="{FDA_SETTINGS_URL}">Open the Full Disk Access settings pane</a>
                    (or: <strong>System Settings</strong> → <strong>Privacy & Security</strong> →
                    <strong>Full Disk Access</strong>)</li>
                <li>Click the lock icon and enter your password</li>
                <li>Click <strong>+</strong> and add <strong>Terminal.app</strong> (or your IDE)</li>
                <li>Make sure the checkbox is checked ✅</li>
                <li>Restart Terminal/IDE and run the scan again</li>
            </ul>
            <p><em>Note: If you're running Ask Dad from Cursor, VS Code, or another IDE, add that application instead of Terminal.</em></p>
        </section>
"""
    return html


def render_personality(comments, tips=()):
    """"Dad says" quote block, with the quick-win tips as a short list at its end.

    The tips used to sit in their own yellow "Quick Wins" box; they are Dad's
    advice, so they live in his section now. The section also carries the link
    down to Next Steps.
    """
    html = ""
    if comments or tips:
        html += """
        <section class="personality">
            <h2>💬 Dad says:</h2>
"""
        for comment in comments:
            html += f'            <p>"{escape_html(comment)}"</p>\n'
        if tips:
            html += '            <ul class="dad-tips">\n'
            for tip in tips:
                html += f"                <li>{escape_html(tip)}</li>\n"
            html += "            </ul>\n"
        html += '            <p class="next-steps-link"><a href="#next-steps">View next steps</a></p>\n'
        html += "        </section>\n"
    return html


def render_left_out_note(folder):
    """One line under a Library row saying what its number leaves out."""
    note = left_out_note(folder)
    if not note:
        return ""
    return (f'                <p class="left-out-note" style="color: #666; font-size: 0.9em; '
            f'margin-bottom: 15px;">{escape_html(note)}</p>\n')


def render_folder_chart(scan_data, split_home=True):
    """Home/Other folder bar charts plus their expandable detail panels.

    `split_home=False` puts every folder in one bar titled "Folders". A drive
    that is not the startup disk has no home folders, and the split is by
    folder *name* - a "Documents" folder on a thumb drive is not your
    Documents folder, and filing it under "Home Folders" would say it was.
    """
    scan_type = scan_data.get('scan_type', 'unknown')
    html = ""
    # Top Folders - Two Separate Bars: Home Folders and Other Folders
    if scan_type == 'storage':
        top_folders = scan_data.get('top_folders', [])
        if top_folders:
            # Identify home folders
            # Which bar a folder belongs in is decided by where it lives,
            # not by its name. The old test was a list of seven names, so a
            # folder in home that wasn't on it went to "Other Folders" - or,
            # further upstream, was dropped from the report altogether.
            # The scan records the home it walked; falling back to this
            # machine's home keeps older manifests rendering.
            home_dir = scan_data.get('home_path') or os.path.expanduser('~')
            
            # Separate folders into home and non-home
            home_folder_segments = []
            non_home_folder_segments = []
            home_folder_total_bytes = 0
            non_home_folder_total_bytes = 0
            
            for idx, folder in enumerate(top_folders):
                path_display = folder.get('path_display', '') or folder.get('path', '')
                raw_path = folder.get('path', '')

                is_home_folder = bool(split_home) and raw_path.startswith(home_dir)

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
            
            # Limit home folders to top 10 and calculate widths
            # Sort by size first
            home_folder_segments.sort(key=lambda seg: seg['folder'].get('size_bytes', 0), reverse=True)
            top_10_home = home_folder_segments[:10]
            top_10_home_total = sum(seg['folder'].get('size_bytes', 0) for seg in top_10_home)
            for seg in top_10_home:
                size_bytes = seg['folder'].get('size_bytes', 0)
                seg['width'] = (size_bytes / top_10_home_total) * 100 if top_10_home_total > 0 else 0
            
            # Limit non-home folders to top 10 and calculate widths
            # Sort by size first
            non_home_folder_segments.sort(key=lambda seg: seg['folder'].get('size_bytes', 0), reverse=True)
            top_10_non_home = non_home_folder_segments[:10]
            top_10_non_home_total = sum(seg['folder'].get('size_bytes', 0) for seg in top_10_non_home)
            for seg in top_10_non_home:
                size_bytes = seg['folder'].get('size_bytes', 0)
                seg['width'] = (size_bytes / top_10_non_home_total) * 100 if top_10_non_home_total > 0 else 0
            
            html += """
        <section>
            <div class="folder-chart-container">
"""
            
            # Home Folders Bar (First Bar - Top 10)
            if top_10_home:
                html += """
                <div class="folder-bar-header">
                    <h2>Top 10 Home Folders</h2>
                    <span class="folder-bar-hint"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" stroke="#000" stroke-width="1.5"/><circle cx="8" cy="4.8" r="1" fill="#000"/><rect x="7.2" y="7" width="1.6" height="5" rx="0.6" fill="#000"/></svg>Click each folder to view its top items</span>
                </div>
                <div class="folder-bar-wrapper" id="homeFolderBar">
"""
                for seg in top_10_home:
                    folder = seg['folder']
                    full_path = folder.get('path', '')
                    path_display = escape_html(folder.get('path_display', full_path))
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
            
            # Other Folders Bar (Second Bar - Top 10). With no home bar above
            # it there is nothing for it to be "other" than, so it is just
            # "Folders" and loses the spacing that separated the two.
            if top_10_non_home:
                second_bar_heading = "Top 10 Other Folders" if split_home else "Folders"
                second_bar_style = ' style="margin-top: 30px;"' if split_home else ''
                html += f"""
                <div class="folder-bar-header"{second_bar_style}>
                    <h2>{second_bar_heading}</h2>
                    <span class="folder-bar-hint"><svg viewBox="0 0 16 16" aria-hidden="true"><circle cx="8" cy="8" r="7" fill="none" stroke="#000" stroke-width="1.5"/><circle cx="8" cy="4.8" r="1" fill="#000"/><rect x="7.2" y="7" width="1.6" height="5" rx="0.6" fill="#000"/></svg>Click each folder to view its top items</span>
                </div>
                <div class="folder-bar-wrapper" id="otherFolderBar">
"""
                for seg in top_10_non_home:
                    folder = seg['folder']
                    full_path = folder.get('path', '')
                    path_display = escape_html(folder_label(folder, home_dir))
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
            
            html += """
            </div>
"""
            
            # Generate expanded details for home folders (top 10)
            for seg in top_10_home:
                folder = seg['folder']
                full_path = folder.get('path', '')
                path_display = escape_html(folder_label(folder, home_dir))
                # A 0.0 B row says nothing; drop empty subfolders.
                subfolders = [sf for sf in folder.get('subfolders', []) if sf.get('size_bytes')]
                top_files = folder.get('top_files', [])
                folder_id = f"home_folder_{seg['idx']}"
                folder_color = seg['color']
                
                # If path is not absolute, construct it from volume
                if not os.path.isabs(full_path):
                    volume = scan_data.get('volume', '')
                    full_path = os.path.join(volume, full_path.lstrip('/'))
                    full_path = os.path.normpath(full_path)
                full_path = escape_html(full_path)

                folder_size = folder.get('size_human', '0 B')
                html += f"""
            <div class="folder-bar-expanded" id="{folder_id}" style="border-left-color: {folder_color};">
                <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.3em; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
                    <span style="display: flex; align-items: center; gap: 10px;">
                        <span style="display: inline-block; width: 20px; height: 20px; background: {folder_color}; border-radius: 4px; flex-shrink: 0;"></span>
                        <span style="color: {folder_color}; font-weight: 600;">{path_display}</span>
                    </span>
                    <span style="color: {folder_color}; font-weight: 600; font-size: 1.3em;">{folder_size}</span>
                </h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 15px; font-family: 'Monaco', 'Courier New', monospace;">
                    {full_path}
                </p>
"""
                html += render_left_out_note(folder)
                
                # Subfolders
                if subfolders:
                    html += """
                <h4>Subfolders</h4>
                <div class="subfolders-list">
"""
                    for subfolder in subfolders[:5]:
                        html += f"""
                    <div class="subfolder-item">
                        <span class="subfolder-name">{escape_html(subfolder.get('path_display', subfolder.get('path', '')))}</span>
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
                        file_name = escape_html(os.path.basename(file_path))
                        html += f"""
                    <div class="folder-file-item">
                        <a href="{file_url}" class="folder-file-name" title="Click to view">{file_name}</a>
                        <span class="subfolder-size">{file_size}</span>
                    </div>
"""
                    
                    # Show "View all files" link if there are more files
                    if len(top_files) > 10:
                        all_files_id = f"{folder_id}_all_files"
                        html += f"""
                    <a href="#" class="see-all-link" onclick="event.preventDefault(); showAllFilesInFolder('{all_files_id}'); return false;">
                        View all {len(top_files)} files in {path_display} →
                    </a>
                    <div id="{all_files_id}" style="display: none; margin-top: 10px;">
"""
                        for file_info in top_files[10:]:
                            file_path = file_info.get('path', '')
                            file_size = file_info.get('size_human', '0 B')
                            file_url = f"file://{quote(file_path)}"
                            file_name = escape_html(os.path.basename(file_path))
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
                path_display = escape_html(folder_label(folder, home_dir))
                # A 0.0 B row says nothing; drop empty subfolders.
                subfolders = [sf for sf in folder.get('subfolders', []) if sf.get('size_bytes')]
                top_files = folder.get('top_files', [])
                folder_id = f"folder_{seg['idx']}"
                folder_color = seg['color']
                
                # If path is not absolute, construct it from volume
                if not os.path.isabs(full_path):
                    volume = scan_data.get('volume', '')
                    full_path = os.path.join(volume, full_path.lstrip('/'))
                    full_path = os.path.normpath(full_path)
                full_path = escape_html(full_path)

                folder_size = folder.get('size_human', '0 B')
                html += f"""
            <div class="folder-bar-expanded" id="{folder_id}" style="border-left-color: {folder_color};">
                <h3 style="margin-top: 0; margin-bottom: 15px; font-size: 1.3em; display: flex; align-items: center; justify-content: space-between; gap: 10px;">
                    <span style="display: flex; align-items: center; gap: 10px;">
                        <span style="display: inline-block; width: 20px; height: 20px; background: {folder_color}; border-radius: 4px; flex-shrink: 0;"></span>
                        <span style="color: {folder_color}; font-weight: 600;">{path_display}</span>
                    </span>
                    <span style="color: {folder_color}; font-weight: 600; font-size: 1.3em;">{folder_size}</span>
                </h3>
                <p style="color: #666; font-size: 0.9em; margin-bottom: 15px; font-family: 'Monaco', 'Courier New', monospace;">
                    {full_path}
                </p>
"""
                html += render_left_out_note(folder)
                
                # Subfolders
                if subfolders:
                    html += """
                <h4>Subfolders</h4>
                <div class="subfolders-list">
"""
                    for subfolder in subfolders[:5]:  # Top 5 subfolders
                        subfolder_name = escape_html(subfolder.get('path_display', subfolder.get('path', '')))
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
                        file_name = escape_html(os.path.basename(file_path))
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
                            file_name = escape_html(os.path.basename(file_path))
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
    return html


def render_top_files_table(scan_data):
    """Sortable "Top Largest Files" table."""
    scan_type = scan_data.get('scan_type', 'unknown')
    html = ""
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
                <h2>Top Largest Files &amp; Apps</h2>
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
                basename = escape_html(os.path.basename(path))
                folder_path = os.path.dirname(path)
                folder_name = escape_html(os.path.basename(folder_path) if folder_path else 'Root')

                # Build safe JS string literals for the onclick handlers below.
                # json.dumps() produces a correctly-escaped JS string literal
                # (handles quotes/backslashes/control chars), and escape_html()
                # then neutralizes that literal's own double-quotes so it can't
                # break out of the double-quoted HTML `onclick="..."` attribute
                # it's embedded in. html.escape() alone would NOT be enough
                # here since the value also has to survive being parsed as a
                # JS string, not just as HTML attribute text.
                escaped_file_path = escape_html(json.dumps(path))
                escaped_folder_path = escape_html(json.dumps(folder_path))

                # Hide rows beyond top 25 initially
                display_style = '' if idx < 25 else 'display: none;'

                html += f"""
                    <tr style="{display_style}">
                        <td class="file-name-cell">
                            <span class="file-name-primary">
                                <a href="{file_url}" title="Click to view in browser">{basename}</a>
                            </span>
                            <span class="file-folder-name">
                                📁 in <a href="#" onclick="event.preventDefault(); revealInFinder({escaped_folder_path}); return false;">{folder_name}</a>
                            </span>
                        </td>
                        <td class="size" data-size="{size_bytes}">{size}</td>
                        <td><button onclick="revealInFinder({escaped_file_path})" title="Copy command to open in Finder">Reveal in Finder</button></td>
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
    return html


def render_hidden_caches(scan_data):
    """"Hidden App Storage" table - the piles under ~/Library/Caches and Logs.

    Returns '' when the scan carries no hidden-cache data (an older manifest,
    or a scan where the section found nothing), so reports that predate this
    section render exactly as they did before.

    Every app name and path here comes off disk, so both go through
    escape_html(), and the Finder paths additionally through json.dumps()
    for the JS-literal context - same rule as the files table above.
    """
    if scan_data.get('scan_type') != 'storage':
        return ""

    hidden = scan_data.get('hidden_caches') or {}
    entries = hidden.get('entries') or []
    if not entries:
        return ""

    total_human = hidden.get('total_size_human', '0 B')
    folder_count = hidden.get('folder_count', 0)
    listed_bytes = sum(entry.get('size_bytes', 0) for entry in entries)
    remainder = max(0, hidden.get('total_size_bytes', 0) - listed_bytes)

    html = f"""
        <section id="hidden-caches">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h2>Hidden App Storage</h2>
                <span style="font-family: 'Monaco', 'Courier New', monospace; color: #666; font-size: 0.95em;">
                    {total_human} across {folder_count} folders
                </span>
            </div>
            <p style="color: #666; margin-bottom: 12px;">
                This is where a chunk of your disk went. It is hidden from Finder, and not all
                of it is the same kind of thing: most is cache an app can rebuild, but some
                folders (like <code>.local</code>) hold programs and settings. If you don't
                know what a folder is, leave it alone.
            </p>
            <ul class="cache-explainer">
                <li>Clearing a cache is like deleting a copy of something the app can get
                    again. It's temporary relief, but the bloat will return.</li>
                <li>Clearing a cache is a safe way to get space back today - just don't
                    expect it to stay gone.</li>
                <li>Dragging an app to the Trash leaves its cache behind, so if you're
                    getting rid of an app, those leftovers are the ones worth a look.</li>
            </ul>
            <table id="hiddenCachesTable">
                <thead>
                    <tr>
                        <th onclick="sortTable('hiddenCachesTable', 0)">App ↕</th>
                        <th onclick="sortTable('hiddenCachesTable', 1)">Size ↕</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody>
"""

    for entry in entries:
        app_name = escape_html(entry.get('app_name', 'Unknown'))
        folder_name = entry.get('folder_name', '')
        path = entry.get('path', '')
        size = entry.get('size_human', '0 B')
        size_bytes = entry.get('size_bytes', 0)
        note = entry.get('note', '')
        escaped_path = escape_html(json.dumps(path))

        # Show the raw folder name under the friendly one only when they
        # differ, so 'Firefox' doesn't get a redundant second line.
        secondary = ""
        if folder_name and folder_name != entry.get('app_name'):
            secondary = f"""
                            <span class="file-folder-name">{escape_html(folder_name)}</span>"""
        if note:
            secondary += f"""
                            <span class="file-folder-name">⚠️ {escape_html(note)}</span>"""

        html += f"""
                    <tr>
                        <td class="file-name-cell">
                            <span class="file-name-primary">{app_name}</span>{secondary}
                        </td>
                        <td class="size" data-size="{size_bytes}">{size}</td>
                        <td><button onclick="revealInFinder({escaped_path})" title="Copy command to open in Finder">Reveal in Finder</button></td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
"""

    if remainder > 0:
        html += f"""
            <p style="color: #666; margin-top: 15px;">
                Plus {format_size(remainder)} in smaller caches not listed individually.
            </p>
"""

    if hidden.get('permission_denied'):
        html += """
            <p style="color: #666; margin-top: 15px;">
                ⚠️ Some cache folders are protected by macOS, so those sizes may be
                incomplete. Granting Full Disk Access lets Ask Dad see all of them.
            </p>
"""

    if hidden.get('scan_status') == 'partial':
        html += """
            <p style="color: #666; margin-top: 15px;">
                ⚠️ This scan ran out of time before measuring every folder, so the
                total above is a floor, not the whole story.
            </p>
"""

    html += """
        </section>
"""
    return html


def render_snapshots(scan_data):
    """"Local Snapshots" section - why deleting things didn't free up space.

    Returns '' when the scan carries no snapshot data or found none worth
    explaining, so older reports render unchanged.

    Deliberately reports no sizes. APFS snapshots share blocks, so a
    per-snapshot size has no single true value, and macOS exposes no
    purgeable total to any command-line tool (verified Aug 2026). Saying so
    plainly beats printing a number we'd have to invent.
    """
    if scan_data.get('scan_type') != 'storage':
        return ""

    snapshot_data = scan_data.get('snapshots') or {}
    if snapshot_data.get('status') != 'complete':
        return ""

    snapshots = snapshot_data.get('snapshots') or []
    count = snapshot_data.get('count', 0)
    if not count:
        return ""

    oldest_age = snapshot_data.get('oldest_age_days')
    stale_count = snapshot_data.get('stale_count', 0)
    os_update_count = snapshot_data.get('os_update_count', 0)

    plural = 's' if count != 1 else ''
    headline = f"{count} local snapshot{plural}"
    if oldest_age is not None:
        if oldest_age == 0:
            headline += ", the oldest from today"
        elif oldest_age == 1:
            headline += ", the oldest from yesterday"
        else:
            headline += f", the oldest {oldest_age} days old"

    # Fresh snapshots are Time Machine working correctly; stale ones are the
    # story. Never scold someone for a system doing its job.
    if stale_count:
        explanation = (
            "Time Machine keeps about a day of these and usually tidies up after itself. "
            "Yours have been sitting longer than that, which normally means macOS hasn't "
            "needed the space back yet."
        )
    else:
        explanation = (
            "That's Time Machine working exactly as intended. It keeps about a day's worth "
            "and clears them out on its own. Nothing to do here."
        )

    html = f"""
        <section id="local-snapshots">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 15px;">
                <h2>Local Snapshots</h2>
                <span style="font-family: 'Monaco', 'Courier New', monospace; color: #666; font-size: 0.95em;">
                    {escape_html(headline)}
                </span>
            </div>
            <p style="color: #666; margin-bottom: 15px;">
                A snapshot is a local Time Machine backup kept on the same drive. {explanation}
            </p>
            <table id="snapshotsTable">
                <thead>
                    <tr>
                        <th>Taken</th>
                        <th>Age</th>
                        <th>macOS can reclaim it</th>
                    </tr>
                </thead>
                <tbody>
"""

    for snapshot in snapshots:
        created = snapshot.get('created') or ''
        # '2026-03-08T15:02:55' -> '2026-03-08 15:02'
        when = created.replace('T', ' ')[:16] if created else 'Unknown'
        age_days = snapshot.get('age_days')
        if age_days is None:
            age = 'Unknown'
        elif age_days == 0:
            age = 'Today'
        elif age_days == 1:
            age = '1 day'
        else:
            age = f'{age_days} days'

        purgeable = snapshot.get('purgeable')
        if purgeable is True:
            reclaim = 'Yes'
        elif purgeable is False:
            reclaim = 'No'
        else:
            reclaim = 'Unknown'

        html += f"""
                    <tr>
                        <td>{escape_html(when)}</td>
                        <td>{escape_html(age)}</td>
                        <td>{escape_html(reclaim)}</td>
                    </tr>
"""

    html += """
                </tbody>
            </table>
"""

    # The honest bit. macOS shows a purgeable figure in Finder that no
    # command-line tool can read, so say that rather than invent one.
    html += """
            <p style="color: #666; margin-top: 20px;">
                There's no honest way to determine the size of these snapshots.
            </p>
"""

    if os_update_count:
        html += f"""
            <p style="color: #666; margin-top: 15px;">
                There {'is' if os_update_count == 1 else 'are'} also {os_update_count} system update
                snapshot{'s' if os_update_count != 1 else ''} that belong to macOS. Best to leave
                these be.
            </p>
"""

    if stale_count:
        html += """
            <p style="color: #666; margin-top: 15px;">
                <strong>You can get some space back today</strong> by connecting your Time Machine
                drive and letting a backup finish.
            </p>
            <p style="color: #666; margin-top: 10px;">
                If you're in a hurry, this Terminal command asks macOS to thin them out:
            </p>
            <pre style="background: #f5f5f5; padding: 12px; border-radius: 6px; overflow-x: auto;"><code>tmutil thinlocalsnapshots / 9999999999 4</code></pre>
            <p style="color: #666; margin-top: 10px;">
                And if you don't use Time Machine, turn off Automatic Backup in System Settings
                so your Mac stops making these.
            </p>
"""

    html += """
        </section>
"""
    return html


def render_cpu_section(scan_data):
    """CPU/RAM snapshot: memory overview, process stats, memory hogs, top CPU."""
    scan_type = scan_data.get('scan_type', 'unknown')
    html = ""
    # CPU & Memory Section
    if scan_type == 'cpu':
        memory_hogs = scan_data.get('memory_hogs', [])
        top_processes = scan_data.get('top_processes', [])
        # Every RAM figure comes from utils.memory, the same numbers the
        # terminal and the AI prompt print.
        mem = memory_summary(scan_data)
        pressure_level = mem['pressure']
        pressure_busy = pressure_level in ('medium', 'high')

        # Memory Overview Section
        if mem['total_bytes'] > 0:
            used_percent = mem['used_percent'] or 0
            used_percent_html = (f' <span style="font-size: 0.7em;">({mem["used_percent_text"]})</span>'
                                 if mem['used_percent_text'] else '')
            swap_html = (f" &middot; Swap in use: {mem['swap_used_text']}"
                         if mem['swap_used_bytes'] is not None else '')

            # Determine pressure color
            pressure_color = '#e74c3c' if pressure_level == 'high' else '#f39c12' if pressure_level == 'medium' else '#2ecc71' if pressure_level == 'low' else '#95a5a6'
            pressure_emoji = '🔴' if pressure_level == 'high' else '🟡' if pressure_level == 'medium' else '🟢' if pressure_level == 'low' else '⚪'

            html += f"""
        <section>
            <h2>🔥 CPU & RAM Snapshot</h2>

            <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 25px; border-radius: 8px; margin: 20px 0;">
                <h3 style="color: white; margin-top: 0; margin-bottom: 15px;">Memory Overview</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-bottom: 15px;">
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Total RAM</div>
                        <div style="font-size: 1.8em; font-weight: bold;">{mem['total_text']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Used</div>
                        <div style="font-size: 1.8em; font-weight: bold;">{mem['used_text']}{used_percent_html}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Available <span style="font-size: 0.85em;">({AVAILABLE_NOTE})</span></div>
                        <div style="font-size: 1.8em; font-weight: bold;">{mem['available_text']}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; opacity: 0.9;">Memory Pressure</div>
                        <div style="font-size: 1.8em; font-weight: bold;">
                            <span style="background: {pressure_color}; padding: 5px 15px; border-radius: 20px; display: inline-block;">
                                {pressure_emoji} {pressure_level}
                            </span>
                        </div>
                    </div>
                </div>

                <!-- Memory Usage Bar -->
                <div style="margin-top: 20px;">
                    <div style="background: rgba(255,255,255,0.2); border-radius: 10px; height: 30px; overflow: hidden; position: relative;">
                        <div style="background: {pressure_color}; height: 100%; width: {used_percent:.1f}%; transition: width 0.3s ease; display: flex; align-items: center; justify-content: center; color: white; font-weight: bold; font-size: 0.9em;">
                            {used_percent:.0f}% Used
                        </div>
                    </div>
                </div>
                <p style="margin: 15px 0 0 0; font-size: 0.9em; opacity: 0.9;">
                    Free (not used at all): {mem['free_text']} &middot; Memory used by apps: {mem['apps_text']} (approx., {APPS_NOTE}){swap_html}
                </p>
            </div>
"""

        # Process Metrics Section (if available)
        process_metrics = scan_data.get('process_metrics', {})
        if process_metrics:
            total_procs = process_metrics.get('total_processes', 0)
            procs_100mb = process_metrics.get('processes_over_100mb', 0)
            procs_500mb = process_metrics.get('processes_over_500mb', 0)
            procs_1gb = process_metrics.get('processes_over_1gb', 0)
            avg_mem = process_metrics.get('avg_memory_mb', 0)
            
            html += f"""
            <div style="background: #f8f9fa; padding: 20px; border-radius: 8px; margin: 20px 0;">
                <h3 style="margin-top: 0;">Process Statistics</h3>
                <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr)); gap: 15px;">
                    <div>
                        <div style="font-size: 0.9em; color: #666;">Total Processes</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{total_procs:,}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #666;">Over 100 MB</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{procs_100mb}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #666;">Over 500 MB</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{procs_500mb}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #666;">Over 1 GB</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{procs_1gb}</div>
                    </div>
                    <div>
                        <div style="font-size: 0.9em; color: #666;">Avg Memory/Process</div>
                        <div style="font-size: 1.5em; font-weight: bold;">{avg_mem:.0f} MB</div>
                    </div>
                </div>
"""
            
            # Memory Distribution Analysis
            small_mb = process_metrics.get('small_processes_mb', 0)
            medium_mb = process_metrics.get('medium_processes_mb', 0)
            large_mb = process_metrics.get('large_processes_mb', 0)
            small_count = process_metrics.get('small_processes_count', 0)
            
            if small_mb > 0 or medium_mb > 0 or large_mb > 0:
                small_gb = small_mb / 1024.0
                medium_gb = medium_mb / 1024.0
                large_gb = large_mb / 1024.0
                total_categorized = small_mb + medium_mb + large_mb
                
                html += f"""
                <div style="margin-top: 20px; padding-top: 20px; border-top: 1px solid #ddd;">
                    <h4 style="margin-top: 0; color: #333;">Memory Distribution</h4>
                    <p style="color: #666; font-size: 0.9em; margin-bottom: 15px;">
                        Where your memory is going: many small processes vs few large ones
                    </p>
                    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px;">
                        <div style="background: #e8f5e9; padding: 15px; border-radius: 6px;">
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Small Processes (&lt;100 MB)</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: #2e7d32;">{small_gb:.1f} GB</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">{small_count:,} processes</div>
                        </div>
                        <div style="background: #fff3e0; padding: 15px; border-radius: 6px;">
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Medium (100-500 MB)</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: #e65100;">{medium_gb:.1f} GB</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">{procs_100mb - procs_500mb} processes</div>
                        </div>
                        <div style="background: #ffebee; padding: 15px; border-radius: 6px;">
                            <div style="font-size: 0.85em; color: #666; margin-bottom: 5px;">Large (&ge;500 MB)</div>
                            <div style="font-size: 1.3em; font-weight: bold; color: #c62828;">{large_gb:.1f} GB</div>
                            <div style="font-size: 0.85em; color: #666; margin-top: 5px;">{procs_500mb} processes</div>
                        </div>
                    </div>
"""
                
                # Add insight about memory distribution
                if small_count > 400 and small_gb > 5:
                    html += """
                    <div style="margin-top: 15px; padding: 12px; background: #fff3cd; color: #856404; border-left: 4px solid #ffc107; border-radius: 4px;">
                        <strong>💡 Insight:</strong> You have many small processes using memory. This is normal, but if memory pressure is high, 
                        consider closing apps you're not using - even small processes add up.
                    </div>
"""
                elif large_gb > (small_gb + medium_gb):
                    html += """
                    <div style="margin-top: 15px; padding: 12px; background: #ffebee; border-left: 4px solid #f44336; border-radius: 4px;">
                        <strong>💡 Insight:</strong> A few large processes are using most of your memory. Focus on closing the biggest apps first.
                    </div>
"""
                
                html += """
                </div>
            </div>
"""

        # Memory Hogs Section
        if memory_hogs:
            html += f"""
            <h3 style="margin-top: 30px;">Apps Using Most Memory</h3>
            <p style="color: #666; font-size: 0.9em;">Approximate: {APPS_NOTE}, so these add up to more than the RAM in use.</p>
            <table>
                <thead>
                    <tr>
                        <th>App Name</th>
                        <th>Memory used by this app</th>
                        <th>Processes</th>
                    </tr>
                </thead>
                <tbody>
"""
            for hog in memory_hogs[:20]:  # Top 20 (increased from 10)
                name = escape_html(hog.get('name', 'Unknown'))
                mem_mb = hog.get('total_mb', 0)
                mem_gb = mem_mb / 1024.0
                process_count = hog.get('process_count', 1)

                # Format memory
                if mem_gb >= 1:
                    mem_display = f"{mem_gb:.1f} GB"
                else:
                    mem_display = f"{mem_mb:.0f} MB"

                # Color code based on size
                if mem_gb >= 3:
                    row_style = 'background-color: rgba(231, 76, 60, 0.1);'  # Red tint for high usage
                elif mem_gb >= 1:
                    row_style = 'background-color: rgba(243, 156, 18, 0.1);'  # Orange tint
                else:
                    row_style = ''

                html += f"""
                    <tr style="{row_style}">
                        <td><strong>{name}</strong></td>
                        <td class="size">{mem_display}</td>
                        <td>{process_count} process{'es' if process_count > 1 else ''}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
"""

        # Browser Tabs Memory Advice Section (if Safari or Chrome are using memory)
        chrome_hog = next((h for h in memory_hogs if h.get('name') == 'Chrome'), None)
        safari_hog = next((h for h in memory_hogs if h.get('name') == 'Safari'), None)
        
        # Tab advice only when macOS reports memory pressure; with pressure
        # normal, closing tabs fixes nothing.
        if (chrome_hog or safari_hog) and pressure_busy:
            chrome_mem_gb = chrome_hog.get('total_mb', 0) / 1024.0 if chrome_hog else 0
            safari_mem_gb = safari_hog.get('total_mb', 0) / 1024.0 if safari_hog else 0
            chrome_procs = chrome_hog.get('process_count', 0) if chrome_hog else 0
            safari_procs = safari_hog.get('process_count', 0) if safari_hog else 0
            
            # Show section if either browser is using significant memory (>0.5GB) or has many processes
            if chrome_mem_gb > 0.5 or safari_mem_gb > 0.5 or chrome_procs > 5 or safari_procs > 5:
                html += """
            <div style="background: linear-gradient(135deg, #ff6b6b 0%, #ee5a6f 100%); color: white; padding: 25px; border-radius: 8px; margin: 30px 0; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h3 style="color: white; margin-top: 0; margin-bottom: 15px;">🌐 Browser Tabs & Memory</h3>
                <div style="background: rgba(255,255,255,0.15); padding: 20px; border-radius: 6px; margin-bottom: 15px;">
                    <p style="margin: 0 0 15px 0; font-size: 1.1em; line-height: 1.6;">
                        <strong>Each browser tab uses 100-300MB of memory.</strong> The more tabs you have open, the more memory your browser uses.
                    </p>
"""
                if chrome_hog and chrome_mem_gb > 0.5:
                    html += f"""
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 6px; margin-bottom: 10px;">
                        <strong>Chrome:</strong> Using {chrome_mem_gb:.1f}GB across {chrome_procs} processes
                        <ul style="margin: 10px 0 0 0; padding-left: 25px; line-height: 1.8;">
                            <li>Close tabs you're not actively using</li>
                            <li>Use bookmarks instead of keeping tabs open</li>
                            <li>Consider a tab suspender extension (pauses unused tabs)</li>
                            <li>Each tab = 100-300MB of memory</li>
                        </ul>
                    </div>
"""
                if safari_hog and safari_mem_gb > 0.5:
                    html += f"""
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 6px; margin-bottom: 10px;">
                        <strong>Safari:</strong> Using {safari_mem_gb:.1f}GB across {safari_procs} processes
                        <ul style="margin: 10px 0 0 0; padding-left: 25px; line-height: 1.8;">
                            <li>Close tabs you're not actively viewing</li>
                            <li>Use Reading List or bookmarks to save pages</li>
                            <li>Each tab/page = 100-200MB of memory</li>
                            <li>Right-click tabs → Close Other Tabs (keeps only current)</li>
                        </ul>
                    </div>
"""
                html += """
                    <div style="background: rgba(255,255,255,0.2); padding: 15px; border-radius: 6px; margin-top: 15px;">
                        <strong>💡 Quick Tips:</strong>
                        <ul style="margin: 10px 0 0 0; padding-left: 25px; line-height: 1.8;">
                            <li><strong>Bookmark it:</strong> If you'll need it later, bookmark it instead of keeping the tab open</li>
                            <li><strong>Close unused tabs:</strong> If you haven't looked at a tab in 10 minutes, close it</li>
                            <li><strong>One window rule:</strong> Try to keep all tabs in one browser window</li>
                            <li><strong>Restart browser:</strong> If memory is high, quit and reopen your browser</li>
                        </ul>
                    </div>
                </div>
            </div>
"""

        # Top Individual Memory Processes Section (show individual processes, not just grouped apps)
        top_memory_processes = scan_data.get('top_memory_processes', [])
        if top_memory_processes:
            html += """
            <h3 style="margin-top: 30px;">Top Individual Processes by Memory</h3>
            <p style="color: #666; font-size: 0.9em;">Individual processes sorted by memory usage (not grouped by app)</p>
            <table>
                <thead>
                    <tr>
                        <th>Process Name</th>
                        <th>Memory</th>
                        <th>CPU %</th>
                    </tr>
                </thead>
                <tbody>
"""
            for proc in top_memory_processes[:30]:  # Top 30 individual processes (increased for many small processes)
                name = proc.get('name', 'Unknown')
                mem_mb = proc.get('memory_mb', 0)
                mem_gb = mem_mb / 1024.0
                cpu_percent = proc.get('cpu_percent', 0)
                
                # Format memory
                if mem_gb >= 1:
                    mem_display = f"{mem_gb:.1f} GB"
                else:
                    mem_display = f"{mem_mb:.0f} MB"
                
                # Color code based on size
                if mem_gb >= 1:
                    row_style = 'background-color: rgba(231, 76, 60, 0.1);'  # Red tint
                elif mem_mb >= 500:
                    row_style = 'background-color: rgba(243, 156, 18, 0.1);'  # Orange tint
                else:
                    row_style = ''
                
                # Truncate long names (before escaping, so entities aren't split mid-truncation)
                display_name = name[:40] + '...' if len(name) > 40 else name
                display_name = escape_html(display_name)
                
                html += f"""
                    <tr style="{row_style}">
                        <td><code>{display_name}</code></td>
                        <td class="size">{mem_display}</td>
                        <td>{cpu_percent:.1f}%</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
"""

        # Top CPU Processes Section
        if top_processes:
            html += """
            <h3 style="margin-top: 30px;">Top CPU Usage</h3>
            <table>
                <thead>
                    <tr>
                        <th>Process Name</th>
                        <th>CPU %</th>
                        <th>Memory</th>
                    </tr>
                </thead>
                <tbody>
"""
            for proc in top_processes[:10]:  # Top 10
                name = escape_html(proc.get('name', 'Unknown'))
                cpu = proc.get('cpu_percent', 0)
                mem_mb = proc.get('memory_mb', 0)

                # Format memory
                if mem_mb >= 1024:
                    mem_display = f"{mem_mb/1024:.1f} GB"
                else:
                    mem_display = f"{mem_mb:.0f} MB"

                # Color code based on CPU usage
                if cpu >= 50:
                    row_style = 'background-color: rgba(231, 76, 60, 0.1);'  # Red tint
                elif cpu >= 20:
                    row_style = 'background-color: rgba(243, 156, 18, 0.1);'  # Orange tint
                else:
                    row_style = ''

                html += f"""
                    <tr style="{row_style}">
                        <td><strong>{name}</strong></td>
                        <td>{cpu:.1f}%</td>
                        <td class="size">{mem_display}</td>
                    </tr>
"""
            html += """
                </tbody>
            </table>
        </section>
"""
    return html


def render_next_steps(scan_type):
    """"NEXT STEPS" 1990s-report-card-styled instructions block."""
    html = ""
    # What to do next section (1990s report card style)
    html += """
        <section id="next-steps" style="margin-top: 40px; border: 3px solid #333; background: #fff; box-shadow: 2px 2px 0 #333;">
            <div style="background: #333; color: #fff; padding: 15px; border-bottom: 3px solid #333;">
                <h3 style="margin: 0; font-family: 'Courier New', monospace; font-size: 1.4em; letter-spacing: 1px; color: #fff;">📋 NEXT STEPS</h3>
            </div>
            <div style="padding: 25px; background: #fffef7; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;">
"""

    if scan_type == 'storage':
        html += """
                <ol style="line-height: 2; margin: 0; padding-left: 25px; color: #333;">
                    <li><strong>Click folder bars</strong> above to see subfolders and top files</li>
                    <li><strong>Click "Reveal in Finder"</strong> button - copies command to clipboard</li>
                    <li><strong>Open Terminal</strong> (Cmd+Space, type "Terminal") and paste (Cmd+V), press Enter</li>
                    <li><strong>Finder opens</strong> with the file/folder selected</li>
                    <li><strong>Delete files manually</strong> (send to Trash for safe undo)</li>
                    <li><strong>Start with largest items</strong> - easiest wins first</li>
                </ol>
                <div style="margin-top: 20px; padding: 15px; background: #f0f0f0; border-left: 4px solid #333;">
                    <p style="margin: 0; color: #555; font-size: 0.95em; line-height: 1.6;">
                        <strong>⚠️ Important:</strong> Ask Dad does not delete files for you, you must delete files manually from Finder. Don't empty Trash until you are sure you want it gone for good.
                    </p>
                </div>
"""
    elif scan_type == 'cpu':
        html += """
                <ol style="line-height: 2; margin: 0; padding-left: 25px; color: #333;">
                    <li><strong>Check memory pressure</strong> - <span style="color: #2ecc71;">🟢 low</span> means macOS is coping fine, even if "Used" looks high</li>
                    <li><strong>If it's <span style="color: #f39c12;">🟡 medium</span> or <span style="color: #e74c3c;">🔴 high</span>, quit apps you're not using</strong> - Right-click app in Dock → Quit</li>
                    <li><strong>Reduce browser tabs</strong> - Only worth it when pressure is up; each tab holds memory</li>
                    <li><strong>Restart if it stays slow</strong> - Only if pressure stays medium or high</li>
                </ol>
                <div style="margin-top: 20px; padding: 15px; background: #f0f0f0; border-left: 4px solid #333;">
                    <p style="margin: 0; color: #555; font-size: 0.95em; line-height: 1.6;">
                        <strong>ℹ️ Note:</strong> This is a snapshot of your system. Re-run <code>askdad cpu</code> anytime to check updated status.
                    </p>
                    <p style="margin: 10px 0 0 0; color: #555; font-size: 0.95em; line-height: 1.6;">
                        <strong>🔒 Privacy:</strong> The .json file saved next to this report holds every process's full command line, which can include your user name and folder paths. Don't share it; the AI prompt below leaves command lines out.
                    </p>
                </div>
"""

    html += """
            </div>
        </section>
"""
    return html


def render_ai_prompt_section(llm_prompt, llm_prompt_no_files=None):
    """"Ask AI About This Report" section. The footer is render_footer().

    `llm_prompt_no_files` is the same prompt without the largest-files list.
    When it differs, a checkbox (off by default) lets the reader add the
    file names back into what they copy; private is the default.
    """
    file_names_control = ""
    if llm_prompt_no_files and llm_prompt_no_files != llm_prompt:
        file_names_control = f"""
                    <label style="display: block; margin-bottom: 15px; color: #555; font-size: 0.9em; cursor: pointer;">
                        <input type="checkbox" id="includeFileNames" onchange="syncPromptFileNames()">
                        Include my largest file names. Off by default to keep them private.
                    </label>
                    <textarea id="llmPromptFull" hidden>{escape_html(llm_prompt)}</textarea>
                    <textarea id="llmPromptNoFiles" hidden>{escape_html(llm_prompt_no_files)}</textarea>
"""
    html = ""
    html += f"""
        <section style="margin-top: 30px; border: 3px solid #667eea; border-radius: 12px; padding: 0; overflow: hidden;">
            <details style="cursor: pointer;" open>
                <summary style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; font-size: 1.3em; font-weight: bold; cursor: pointer; user-select: none;">
                    💬 Ask AI About This Report
                </summary>
                <div style="padding: 25px; background: #f8f9fa;">
                    <p style="margin-top: 0; margin-bottom: 20px; color: #555; font-size: 1.05em; line-height: 1.6;">
                        <strong>Get personalized advice from AI:</strong> Copy the prompt below and paste it into ChatGPT, Claude, or any AI assistant.
                        The prompt includes all your system specs and scan results, so the AI can give you specific recommendations for <em>your</em> Mac.
                    </p>

                    <div style="margin-bottom: 15px;">
                        <button onclick="copyPromptToClipboard()" style="background: #667eea; color: white; border: none; padding: 12px 24px; font-size: 1em; border-radius: 6px; cursor: pointer; font-weight: bold; box-shadow: 0 2px 8px rgba(102, 126, 234, 0.3); transition: all 0.2s;">
                            📋 Copy Prompt to Clipboard
                        </button>
                        <span id="copyStatus" style="margin-left: 15px; color: #2ecc71; font-weight: bold; opacity: 0; transition: opacity 0.3s;">✓ Copied!</span>
                    </div>
{file_names_control}
                    <textarea id="llmPrompt" readonly style="width: 100%; height: 400px; font-family: 'Monaco', 'Courier New', monospace; font-size: 0.85em; padding: 20px; border: 2px solid #ddd; border-radius: 8px; background: white; color: #333; resize: vertical; line-height: 1.5;">{escape_html(llm_prompt_no_files if file_names_control else llm_prompt)}</textarea>

                    <div style="margin-top: 20px; padding: 15px; background: #e8f4f8; border-left: 4px solid #667eea; border-radius: 4px;">
                        <p style="margin: 0; color: #555; font-size: 0.95em;">
                            <strong>💡 Tip:</strong> Once you have the plan, you can ask follow-up questions like:
                        </p>
                        <ul style="margin: 10px 0 0 0; padding-left: 20px; color: #666; font-size: 0.9em;">
                            <li>"Walk me through step 3."</li>
                            <li>"What would you leave out of this plan?"</li>
                            <li>"What can I archive instead of moving to the Trash?"</li>
                        </ul>
                    </div>
                </div>
            </details>
        </section>
"""
    return html


def render_scan_promo(scan_type):
    """Small card pointing at the other scan: CPU from storage, storage from CPU.

    A report cannot launch a command, so it shows one with a Copy button.
    Not called for a drive report: a thumb-drive report is not the place to
    talk about the Mac's memory.
    """
    command = promo.promo_command(scan_type)
    if command is None:
        return ""
    if scan_type == 'storage':
        lead = "Your Mac has a memory and CPU report too."
    else:
        lead = "Your Mac has a storage report too."
    return f"""
        <section id="other-scan" style="margin-top: 30px; padding: 20px 25px; border: 2px solid #ddd; border-radius: 12px; background: #fff;">
            <p style="margin: 0 0 12px 0; color: #333; font-size: 1.05em;"><strong>{escape_html(lead)}</strong> In Terminal, run:</p>
            <div style="display: flex; align-items: center; gap: 12px; flex-wrap: wrap;">
                <input id="promoCommand" type="text" readonly value="{escape_html(command)}" size="{len(command) + 2}" style="font-family: 'Monaco', 'Courier New', monospace; font-size: 1em; padding: 8px 12px; border: 2px solid #ddd; border-radius: 6px; background: #f8f9fa; color: #333;">
                <button onclick="copyPromoCommand()" style="background: #667eea; color: white; border: none; padding: 9px 18px; font-size: 0.95em; border-radius: 6px; cursor: pointer; font-weight: bold;">📋 Copy</button>
                <span id="promoCopyStatus" style="color: #2ecc71; font-weight: bold; opacity: 0; transition: opacity 0.3s;">✓ Copied!</span>
            </div>
        </section>
"""


def render_footer():
    """Page footer with the feedback invitation, plus the container close.

    The address is visible text beside the link: some browsers have no mail
    handler, and a link that does nothing must not be the only way to find it.
    """
    email = escape_html(promo.FEEDBACK_EMAIL)
    return f"""
        <footer style="margin-top: 40px; padding-top: 20px; border-top: 2px solid #ddd; text-align: center; color: #999; font-size: 0.85em;">
            <p id="feedback" style="color: #555; font-size: 1.1em;">{escape_html(promo.FEEDBACK_INVITE)}<br>
                <a href="{escape_html(promo.feedback_mailto())}" style="color: #667eea;">{email}</a></p>
            <p>Ask Dad v{VERSION}, a DadWare joint. Happy cleaning</p>
        </footer>
    </div>
"""


def render_scripts():
    """Inline <script> block plus closing </body></html>."""
    html = ""
    html += """
    <script>
"""
    html += REPORT_JS
    html += """    </script>
</body>
</html>
"""
    return html



def render_html(scan_data, personality_data, report_path):
    """Generate HTML report with UX improvements and save to file."""
    scan_type = scan_data.get('scan_type', 'unknown')
    comments = personality_data.get('comments', [])
    tips = personality_data.get('tips', [])

    now = datetime.datetime.now()

    system_info = get_system_info()
    llm_prompt = generate_llm_prompt(scan_data, personality_data, system_info)
    llm_prompt_no_files = generate_llm_prompt(scan_data, personality_data, system_info,
                                              include_file_names=False)

    if scan_data.get('scan_scope') == 'other_volume':
        # A drive report is a different report, not the Mac report with
        # sections switched off. Every section it does carry is the same
        # function the full report calls - what changes is which ones are
        # asked for, so neither report is a pile of conditionals about the
        # other. Absent: the report card and its grades, the permission
        # notices, the app caches and the snapshots - all of them describing
        # the startup disk.
        html = render_document_head(now)
        html += render_volume_summary(scan_data)
        html += render_folder_chart(scan_data, split_home=False)
        html += render_top_files_table(scan_data)
        html += render_next_steps(scan_type)
        html += render_ai_prompt_section(llm_prompt, llm_prompt_no_files)
        html += render_footer()
        html += render_scripts()
    else:
        html = render_document_head(now)
        html += render_report_card(scan_data)
        html += render_permission_warning(scan_data)
        html += render_personality(comments, tips)
        html += render_folder_chart(scan_data)
        html += render_top_files_table(scan_data)
        html += render_hidden_caches(scan_data)
        html += render_snapshots(scan_data)
        html += render_cpu_section(scan_data)
        html += render_next_steps(scan_type)
        html += render_ai_prompt_section(llm_prompt, llm_prompt_no_files)
        html += render_scan_promo(scan_type)
        html += render_footer()
        html += render_scripts()

    # Write to file
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(html)

    return report_path
