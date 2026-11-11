"""Dad personality engine - generates witty, helpful comments."""

import os

from utils.path_utils import find_folder


def add_personality(scan_data):
    """Add dad personality comments based on scan results."""
    comments = []
    # Informational notes - where the disk went, not a verdict on it. Kept
    # apart from `comments` because the verdict is capped at two lines, and
    # these must not win that slot off a real finding (or lose to one: a
    # 20 GB cache total is worth saying either way).
    info_comments = []
    tips = []
    status = 'ok'
    
    scan_type = scan_data.get('scan_type')
    
    if scan_type == 'storage':
        # Check Downloads folder
        downloads_size = 0
        downloads_path = None
        downloads_folder = find_folder(scan_data.get('top_folders', []), 'Downloads')
        if downloads_folder is not None:
            downloads_size = downloads_folder.get('size_bytes', 0)
            downloads_path = downloads_folder.get('path', '') or downloads_folder.get('path_display', '')

        if downloads_size > 10 * 1000**3:  # >10 GB
            comments.append("Hey Downloads looks like a total mess. Time to do some organization in there.")
            status = 'warn'
            tips.append(f"Start with {downloads_path or 'Downloads'} folder")
        elif downloads_size > 5 * 1000**3:  # >5 GB
            comments.append("Found some fatties in Downloads. You need a cleanup day.")
            status = 'warn'
            tips.append(f"Review {downloads_path or 'Downloads'} folder")
        
        # Check Desktop
        desktop_size = 0
        desktop_path = None
        desktop_folder = find_folder(scan_data.get('top_folders', []), 'Desktop')
        if desktop_folder is not None:
            desktop_size = desktop_folder.get('size_bytes', 0)
            desktop_path = desktop_folder.get('path', '') or desktop_folder.get('path_display', '')

        if desktop_size > 5 * 1000**3:  # >5 GB
            comments.append("Desktop has some hefty files staring you right in the face!")
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
            comments.append("This puppy looks fine! I'm proud of how tidy you are.")

        # The Trash is the one thing here that is both the user's doing and
        # the user's to fix in a minute, so unlike the caches and snapshots
        # below it earns a real tip. Status is still left alone: a full Trash
        # already shows up in the free-space number that set the status.
        trash = scan_data.get('trash') or {}
        trash_bytes = trash.get('total_size_bytes', 0)
        trash_human = trash.get('total_size_human', '')
        trash_oldest = trash.get('oldest_age_days')
        if trash_bytes > 5 * 1000**3:
            info_comments.append(
                f"there's {trash_human} sitting in your trash. you took the bag out, "
                "you just left it by the door.")
            tips.append(f"Empty the Trash - {trash_human} comes back immediately")
        elif trash_bytes > 1000**3:
            if trash_oldest is not None and trash_oldest >= 30:
                info_comments.append(
                    f"{trash_human} in the trash, oldest bit of it {trash_oldest} days "
                    "old. it's not going anywhere on its own.")
            else:
                info_comments.append(
                    f"{trash_human} in the trash. easiest space you'll get back today.")
            tips.append("Empty the Trash (Finder → right-click Trash → Empty Trash)")
        if trash.get('permission_denied'):
            tips.append(
                "Grant Full Disk Access so I can measure your Trash next time")

        # Hidden caches and snapshots come last, deliberately, so they add to
        # the verdict instead of replacing it - a clean disk still gets to
        # hear "looks fine" before being told where the rest of it went.
        #
        # Neither of these ever touches `status` and neither produces a tip.
        # Caches are not graded (docs/GRADING.md): an app filling a cache is
        # an app working, and the space comes back on its own. Saying "warn"
        # about it would be scolding someone for something that isn't their
        # fault and that they can't permanently fix.
        hidden = scan_data.get('hidden_caches') or {}
        cache_bytes = hidden.get('total_size_bytes', 0)
        cache_human = hidden.get('total_size_human', '')
        if cache_bytes > 20 * 1000**3:
            info_comments.append(
                # "Separately", not "of that": caches sit outside the folder
                # totals above (the Nov 7 wording fix on main).
                f"Separately, {cache_human} is tucked away in hidden app folders. Most of it "
                "is cache that will come back after you clear it, but some folders hold programs or settings, "
                "so check what a folder is before you touch it.")
        elif cache_bytes > 5 * 1000**3:
            info_comments.append(
                f"{cache_human} is eaten up by app caches but they just fill back "
                "up over time. That's apps being apps.")

        snapshots = scan_data.get('snapshots') or {}
        if snapshots.get('status') == 'complete' and snapshots.get('count'):
            snap_count = snapshots['count']
            stale_count = snapshots.get('stale_count', 0)
            oldest_days = snapshots.get('oldest_age_days')
            copies = "copy" if snap_count == 1 else "copies"
            if stale_count and oldest_days:
                info_comments.append(
                    f"your mac's been holding {snap_count} {copies} of itself from "
                    f"Time Machine. Oldest one {oldest_days} days back. "
                    "sentimental, but expensive.")
            elif stale_count:
                info_comments.append(
                    f"your mac's been holding on to {snap_count} old {copies} of itself. "
                    "sentimental, but expensive.")
    
    elif scan_type == 'cpu':
        top_processes = scan_data.get('top_processes', [])
        memory_hogs = scan_data.get('memory_hogs', [])
        memory_pressure = scan_data.get('memory_pressure', {})
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

        # Check memory pressure. This is the kernel's reading (scanners/cpu.py),
        # and the only thing that decides whether memory is a problem: a
        # "used" figure near 100% is normal on a Mac, which keeps RAM busy.
        pressure_level = memory_pressure.get('pressure', 'unknown') if memory_pressure else 'unknown'
        pressure_busy = pressure_level in ('medium', 'high')

        if pressure_level == 'high':
            comments.append("memory's maxed out. macOS says it's under real pressure.")
            status = 'critical'
            tips.append("Quit apps you're not using right now - start with the biggest ones")
            if len(memory_hogs) > 0:
                top_hog = memory_hogs[0]
                tips.append(f"Quitting {top_hog.get('name', 'the biggest app')} may free up to about "
                            f"{top_hog.get('total_mb', 0)/1024:.1f} GB")
            tips.append("Check Activity Monitor to see what's using memory")
        elif pressure_level == 'medium':
            comments.append("memory's getting busy. quit what you're not using before it complains.")
            if status == 'ok':
                status = 'warn'
            tips.append("Quit apps you're not actively using")
            if len(memory_hogs) >= 3:
                tips.append(f"Biggest apps right now: {', '.join([h['name'] for h in memory_hogs[:3]])}")
        elif pressure_level == 'low':
            comments.append("memory looks fine. macOS is just using what it has.")
        else:
            comments.append("couldn't get a memory pressure reading from macOS, so i'm not guessing.")

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
                    if status == 'ok' and pressure_busy:
                        status = 'warn'
                    if pressure_busy:
                        tips.append("Chrome: Close tabs or use tab suspender extensions")
                        tips.append("Chrome: Each tab uses 100-300MB - close tabs you're not actively using")
                        tips.append("Chrome: Use bookmarks instead of keeping tabs open - saves memory")
                        if process_count > 10:
                            tips.append(f"Chrome: You have {process_count} Chrome processes running - that's a lot of tabs/extensions")
                elif mem_gb > 1 and pressure_busy:
                    # Even moderate Chrome usage gets tips
                    tips.append("Chrome: Each browser tab uses memory - close tabs you're not using")
                    if process_count > 5:
                        tips.append(f"Chrome: {process_count} processes detected - consider closing unused tabs")
            elif name == 'Safari':
                safari_mem = {'gb': mem_gb, 'count': process_count}
                if mem_gb > 2:
                    comments.append(f"safari's using {mem_gb:.1f}GB. tabs add up faster than you think.")
                    if status == 'ok' and pressure_busy:
                        status = 'warn'
                    if pressure_busy:
                        tips.append("Safari: Close tabs you're not using")
                        tips.append("Safari: Each tab uses 100-200MB - bookmark pages instead of keeping tabs open")
                        tips.append("Safari: Use Reading List or bookmarks to save pages without keeping tabs open")
                        if process_count > 8:
                            tips.append(f"Safari: {process_count} WebKit processes detected - that's a lot of open tabs/pages")
                elif mem_gb > 0.5 and pressure_busy:
                    # Even moderate Safari usage gets tips
                    tips.append("Safari: Browser tabs consume memory - close tabs you're not actively viewing")
                    if process_count > 3:
                        tips.append(f"Safari: {process_count} processes running - each tab/page uses memory")
            elif name == 'Messages':
                messages_mem = {'gb': mem_gb}
                if mem_gb > 1:
                    comments.append(f"messages is using {mem_gb:.1f}GB. years of conversations aren't free.")
                    if status == 'ok' and pressure_busy:
                        status = 'warn'
                    if pressure_busy:
                        tips.append("Messages: Consider archiving old conversations or clearing attachments")

        # Check for "many small processes" scenario
        process_metrics = scan_data.get('process_metrics', {})
        if process_metrics:
            total_procs = process_metrics.get('total_processes', 0)
            small_count = process_metrics.get('small_processes_count', 0)
            small_mb = process_metrics.get('small_processes_mb', 0)
            small_gb = small_mb / 1024.0
            
            # If many small processes using significant total memory
            if small_count > 400 and small_gb > 5 and pressure_busy:
                comments.append(f"{small_count:,} small processes using {small_gb:.1f}GB. death by a thousand cuts.")
                if status == 'ok':
                    status = 'warn'
                tips.append("Many small processes are using memory - quit apps you're not using")
                tips.append("Even small processes add up - a restart starts them all fresh")
        
        # If multiple memory hogs, give general advice
        if len(memory_hogs) >= 3 and pressure_busy:
            if not any('chrome' in c.lower() or 'safari' in c.lower() or 'messages' in c.lower() or 'small processes' in c.lower() for c in comments):
                hog_names = ', '.join([h['name'] for h in memory_hogs[:3]])
                comments.append(f"{hog_names} are all fighting for memory. pick your battles.")
                tips.append("Quit apps you're not actively using - it may free up some memory")

        # General tips about browser tabs and memory
        if (chrome_mem or safari_mem) and pressure_busy:
            if not any('tab' in tip.lower() for tip in tips):
                # Add general tab advice if not already covered
                tips.append("Browser tabs: Each open tab uses 100-300MB of memory")
                tips.append("Tip: Use bookmarks or Reading List instead of keeping many tabs open")
        
        # General tip about memory management
        if pressure_busy:
            tips.append("Restart your Mac if it stays slow - it clears out memory apps never gave back")
            if chrome_mem or safari_mem:
                tips.append("Close browser tabs first - they're often the biggest memory users")

        if not comments:
            comments.append("cpu and memory look reasonable. nothing to worry about.")
    
    # The verdict stays capped at two lines - more than that and nobody reads
    # any of them. Informational notes are appended after the cap rather than
    # inside it, so "where did my disk go" never costs you a real finding.
    final_comments = comments[:2] if comments else ["I think this computer is in good shape! Nicely done."]
    final_comments = final_comments + info_comments[:2]
    
    return {
        'comments': final_comments,
        'status': status,
        'tips': tips[:5]  # Limit to 5 tips
    }

