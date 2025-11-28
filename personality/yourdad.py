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
            comments.append("desktop isn't meant to be storage. it's a desk, not a box of junk.")
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
        memory_hogs = scan_data.get('memory_hogs', [])
        memory_pressure = scan_data.get('memory_pressure', {})
        total_mem_gb = scan_data.get('total_memory_gb', 0)
        total_used_gb = scan_data.get('total_used_gb', 0)

        chrome_cpu = 0
        photoanalysisd_running = False

        # Check CPU usage
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

        # Check memory pressure
        pressure_level = memory_pressure.get('pressure', 'low') if memory_pressure else 'low'
        free_gb = memory_pressure.get('free_gb', 0) if memory_pressure else 0
        used_percent = (total_used_gb / total_mem_gb * 100) if total_mem_gb > 0 else 0

        if pressure_level == 'high' or used_percent > 95:
            comments.append("memory's maxed out. that's why you're seeing warnings.")
            status = 'critical'
            tips.append("Close apps you're not using right now - start with the biggest memory hogs")
            tips.append("Quit browser tabs you're not actively viewing")
            tips.append("Check Activity Monitor to see what's using memory")
            if len(memory_hogs) > 0:
                top_hog = memory_hogs[0]
                tips.append(f"Priority: Close {top_hog.get('name', 'apps')} if not needed ({top_hog.get('total_mb', 0)/1024:.1f} GB)")
        elif pressure_level == 'medium' or used_percent > 85:
            comments.append("memory's getting tight. close some apps before it complains.")
            if status == 'ok':
                status = 'warn'
            tips.append("Quit apps you're not actively using")
            if len(memory_hogs) >= 3:
                tips.append(f"Multiple apps using memory: {', '.join([h['name'] for h in memory_hogs[:3]])}")
            tips.append("Close unused browser tabs to free up memory")

        # Check for specific memory hogs
        chrome_mem = None
        safari_mem = None
        messages_mem = None

        for hog in memory_hogs:
            name = hog.get('name', '')
            mem_mb = hog.get('total_mb', 0)
            mem_gb = mem_mb / 1024.0
            process_count = hog.get('process_count', 1)

            if name == 'Chrome':
                chrome_mem = {'gb': mem_gb, 'count': process_count}
                if mem_gb > 3:
                    comments.append(f"chrome's using {mem_gb:.1f}GB across {process_count} processes. each tab is a memory buffet.")
                    if status == 'ok':
                        status = 'warn'
                    tips.append("Chrome: Close tabs or use tab suspender extensions")
                    tips.append("Chrome: Each tab uses 100-300MB - close tabs you're not actively using")
                    tips.append("Chrome: Use bookmarks instead of keeping tabs open - saves memory")
                    if process_count > 10:
                        tips.append(f"Chrome: You have {process_count} Chrome processes running - that's a lot of tabs/extensions")
                elif mem_gb > 1:
                    # Even moderate Chrome usage gets tips
                    tips.append("Chrome: Each browser tab uses memory - close tabs you're not using")
                    if process_count > 5:
                        tips.append(f"Chrome: {process_count} processes detected - consider closing unused tabs")
            elif name == 'Safari':
                safari_mem = {'gb': mem_gb, 'count': process_count}
                if mem_gb > 2:
                    comments.append(f"safari's using {mem_gb:.1f}GB. tabs add up faster than you think.")
                    if status == 'ok':
                        status = 'warn'
                    tips.append("Safari: Close tabs you're not using")
                    tips.append("Safari: Each tab uses 100-200MB - bookmark pages instead of keeping tabs open")
                    tips.append("Safari: Use Reading List or bookmarks to save pages without keeping tabs open")
                    if process_count > 8:
                        tips.append(f"Safari: {process_count} WebKit processes detected - that's a lot of open tabs/pages")
                elif mem_gb > 0.5:
                    # Even moderate Safari usage gets tips
                    tips.append("Safari: Browser tabs consume memory - close tabs you're not actively viewing")
                    if process_count > 3:
                        tips.append(f"Safari: {process_count} processes running - each tab/page uses memory")
            elif name == 'Messages':
                messages_mem = {'gb': mem_gb}
                if mem_gb > 1:
                    comments.append(f"messages is using {mem_gb:.1f}GB. years of conversations aren't free.")
                    if status == 'ok':
                        status = 'warn'
                    tips.append("Messages: Consider archiving old conversations or clearing attachments")

        # Check for "many small processes" scenario
        process_metrics = scan_data.get('process_metrics', {})
        if process_metrics:
            total_procs = process_metrics.get('total_processes', 0)
            small_count = process_metrics.get('small_processes_count', 0)
            small_mb = process_metrics.get('small_processes_mb', 0)
            small_gb = small_mb / 1024.0
            
            # If many small processes using significant total memory
            if small_count > 400 and small_gb > 5 and pressure_level in ['medium', 'high']:
                comments.append(f"{small_count:,} small processes using {small_gb:.1f}GB. death by a thousand cuts.")
                if status == 'ok':
                    status = 'warn'
                tips.append("Many small processes are using memory - quit apps you're not using")
                tips.append("Even small processes add up - restart your Mac to clear memory cruft")
        
        # If multiple memory hogs, give general advice
        if len(memory_hogs) >= 3 and pressure_level in ['medium', 'high']:
            if not any('chrome' in c.lower() or 'safari' in c.lower() or 'messages' in c.lower() or 'small processes' in c.lower() for c in comments):
                hog_names = ', '.join([h['name'] for h in memory_hogs[:3]])
                comments.append(f"{hog_names} are all fighting for memory. pick your battles.")
                tips.append("Quit apps you're not actively using to free up memory")

        # General tips about browser tabs and memory
        if chrome_mem or safari_mem:
            if not any('tab' in tip.lower() for tip in tips):
                # Add general tab advice if not already covered
                tips.append("Browser tabs: Each open tab uses 100-300MB of memory")
                tips.append("Tip: Use bookmarks or Reading List instead of keeping many tabs open")
        
        # General tip about memory management
        if pressure_level in ['medium', 'high']:
            tips.append("Restart your Mac if problems persist - clears memory cruft")
            if chrome_mem or safari_mem:
                tips.append("Close browser tabs first - they're often the biggest memory users")

        if not comments:
            comments.append("cpu and memory look reasonable. nothing to worry about.")
    
    # Limit to 1-2 comments
    final_comments = comments[:2] if comments else ["everything looks good."]
    
    return {
        'comments': final_comments,
        'status': status,
        'tips': tips[:5]  # Limit to 5 tips
    }

