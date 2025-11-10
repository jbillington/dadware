"""Dad personality engine - generates witty, helpful comments."""

import os


def add_personality(scan_data):
    """Add dad personality comments based on scan results."""
    comments = []
    tips = []
    status = 'ok'
    
    scan_type = scan_data.get('scan_type')
    
    if scan_type == 'storage':
        # Check Downloads folder
        downloads_size = 0
        downloads_path = None
        for folder in scan_data.get('top_folders', []):
            folder_path = folder.get('path', '') or folder.get('path_display', '')
            folder_name = os.path.basename(folder_path) if folder_path else ''
            # Check if this is Downloads folder (case-insensitive)
            if 'Downloads' in folder_path or folder_path.endswith('Downloads') or folder_name == 'Downloads':
                downloads_size = folder.get('size_bytes', 0)
                downloads_path = folder_path
                break
        
        if downloads_size > 10 * 1024**3:  # >10GB
            comments.append("downloads looks like a garage shelf. time to label a box.")
            status = 'warn'
            tips.append(f"Start with {downloads_path or 'Downloads'} folder")
        elif downloads_size > 5 * 1024**3:  # >5GB
            comments.append("downloads is getting crowded. regular cleanup day?")
            status = 'warn'
            tips.append(f"Review {downloads_path or 'Downloads'} folder")
        
        # Check Desktop
        desktop_size = 0
        desktop_path = None
        for folder in scan_data.get('top_folders', []):
            folder_path = folder.get('path', '')
            if 'Desktop' in folder_path or folder_path.endswith('Desktop'):
                desktop_size = folder.get('size_bytes', 0)
                desktop_path = folder_path
                break
        
        if desktop_size > 5 * 1024**3:  # >5GB
            comments.append("desktop isn't meant to be storage. it's a desk, not a storage unit.")
            if status == 'ok':
                status = 'warn'
            tips.append(f"Clean up {desktop_path or 'Desktop'} folder")
        
        # Check free space
        volume_info = scan_data.get('volume_info', {})
        used_percent = volume_info.get('used_percent', 0)
        free_percent = 100 - used_percent
        
        if free_percent < 10:
            comments.append("living on the edge. let's back away from the cliff.")
            status = 'critical'
            tips.append("Free up space urgently - system may slow down")
        elif free_percent < 20:
            if not comments:  # Don't override more specific comments
                comments.append("getting tight. time to make some room.")
            if status == 'ok':
                status = 'warn'
        
        # Check for large files
        top_files = scan_data.get('top_files', [])
        if top_files:
            largest = top_files[0]
            largest_size_gb = largest.get('size_bytes', 0) / (1024**3)
            if largest_size_gb > 5:
                if not comments:
                    tips.append(f"Review large file: {os.path.basename(largest.get('path', ''))} ({largest.get('size_human', '')})")
        
        # Default positive comment if everything is fine
        if not comments and status == 'ok':
            comments.append("looks fine. don't mess with success.")
    
    elif scan_type == 'cpu':
        top_processes = scan_data.get('top_processes', [])
        
        chrome_cpu = 0
        photoanalysisd_running = False
        
        for proc in top_processes:
            name = proc.get('name', '').lower()
            cpu = proc.get('cpu_percent', 0)
            
            if 'chrome' in name or 'chromium' in name:
                chrome_cpu = max(chrome_cpu, cpu)
            if 'photoanalysisd' in name:
                photoanalysisd_running = True
                if cpu > 20:
                    comments.append("photoanalysisd is doing its thing. mac's version of 'I'm organizing.'")
                    status = 'warn'
        
        if chrome_cpu > 50:
            comments.append("lots of tabs. lots of fans. cause ↔ effect.")
            status = 'warn'
            tips.append("Close unused browser tabs to reduce CPU usage")
        
        if not comments:
            comments.append("cpu looks reasonable. nothing to worry about.")
    
    # Limit to 1-2 comments
    final_comments = comments[:2] if comments else ["everything looks good."]
    
    return {
        'comments': final_comments,
        'status': status,
        'tips': tips[:5]  # Limit to 5 tips
    }

