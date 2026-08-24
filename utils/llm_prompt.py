"""LLM prompt generator for AI consultation about scan results."""

from utils.system_info import format_system_info


def generate_llm_prompt(scan_data, personality_data, system_info):
    """
    Generate a comprehensive prompt for LLM consultation.

    Args:
        scan_data: Scan results (storage or CPU)
        personality_data: Dad's comments and tips
        system_info: System specifications

    Returns:
        Formatted prompt string ready for LLM
    """
    scan_type = scan_data.get('scan_type', 'unknown')

    if scan_type == 'storage':
        return generate_storage_prompt(scan_data, personality_data, system_info)
    elif scan_type == 'cpu':
        return generate_cpu_prompt(scan_data, personality_data, system_info)
    else:
        return generate_generic_prompt(scan_data, personality_data, system_info)


def generate_storage_prompt(scan_data, personality_data, system_info):
    """Generate prompt for storage scan results."""

    volume_info = scan_data.get('volume_info', {})
    top_folders = scan_data.get('top_folders', [])[:10]
    top_files = scan_data.get('top_files', [])[:10]
    mac_libraries = scan_data.get('mac_libraries', {})

    # Format volume info
    total = volume_info.get('total_human', '0 B')
    used = volume_info.get('used_human', '0 B')
    free = volume_info.get('free_human', '0 B')
    used_percent = volume_info.get('used_percent', 0)

    # Format top folders
    folders_text = ""
    for idx, folder in enumerate(top_folders, 1):
        path = folder.get('path_display') or folder.get('path', '')
        size = folder.get('size_human', '0 B')
        folders_text += f"{idx}. {path}: {size}\n"

    # Format top files
    files_text = ""
    for idx, file_info in enumerate(top_files, 1):
        import os
        path = file_info.get('path', '')
        basename = os.path.basename(path)
        size = file_info.get('size_human', '0 B')
        files_text += f"{idx}. {basename}: {size}\n"

    # Format Mac libraries
    libraries_text = ""
    for lib_type, lib_name in [('photos', 'Photos'), ('music', 'Music'),
                                ('messages', 'Messages'), ('mail', 'Mail')]:
        lib_data = mac_libraries.get(lib_type, {})
        if lib_type in ['photos', 'music']:
            size = lib_data.get('total_size_human', '0 B')
        else:
            size = lib_data.get('size_human', '0 B')
        if size != '0 B':
            libraries_text += f"- {lib_name}: {size}\n"

    # Format dad's assessment
    comments = personality_data.get('comments', [])
    status = personality_data.get('status', 'ok')
    status_emoji = '🔴' if status == 'critical' else '🟡' if status == 'warn' else '🟢'

    dad_text = '\n'.join(f'"{comment}"' for comment in comments)

    # Format tips
    tips = personality_data.get('tips', [])
    tips_text = '\n'.join(f"• {tip}" for tip in tips)

    prompt = f"""I need help understanding my Mac's storage situation. Here's a detailed scan of my system:

═══════════════════════════════════════
SYSTEM SPECIFICATIONS
═══════════════════════════════════════
{format_system_info(system_info)}

═══════════════════════════════════════
STORAGE STATUS
═══════════════════════════════════════
Volume: {scan_data.get('volume', 'Unknown')}
Total Capacity: {total}
Used: {used} ({used_percent:.0f}%)
Available: {free}
Status: {status_emoji} {status.upper()}

═══════════════════════════════════════
LARGEST FOLDERS
═══════════════════════════════════════
{folders_text.strip()}

═══════════════════════════════════════
LARGEST FILES
═══════════════════════════════════════
{files_text.strip()}
"""

    if libraries_text:
        prompt += f"""
═══════════════════════════════════════
MAC APP LIBRARIES
═══════════════════════════════════════
{libraries_text.strip()}
"""

    # Hidden caches: absent from older scan data, so the block is conditional
    # and prompts generated from a pre-hidden-caches scan are unchanged.
    hidden = scan_data.get('hidden_caches') or {}
    cache_entries = hidden.get('entries') or []
    if cache_entries:
        caches_text = '\n'.join(
            f"- {entry.get('app_name', 'Unknown')}: {entry.get('size_human', '0 B')} ({entry.get('path', '')})"
            for entry in cache_entries[:15]
        )
        prompt += f"""
═══════════════════════════════════════
HIDDEN APP CACHES
═══════════════════════════════════════
These live under ~/Library/Caches and ~/Library/Logs, which Finder hides and
the main scan above excludes. Total: {hidden.get('total_size_human', '0 B')} across {hidden.get('folder_count', 0)} folders.

{caches_text}
"""

    snapshot_data = scan_data.get('snapshots') or {}
    if snapshot_data.get('status') == 'complete' and snapshot_data.get('count'):
        oldest = snapshot_data.get('oldest_age_days')
        prompt += f"""
═══════════════════════════════════════
LOCAL APFS SNAPSHOTS
═══════════════════════════════════════
{snapshot_data['count']} local Time Machine snapshot(s) on this drive"""
        if oldest is not None:
            prompt += f", oldest {oldest} days old"
        prompt += f""".
{snapshot_data.get('stale_count', 0)} older than macOS's usual ~24h retention.
{snapshot_data.get('os_update_count', 0)} system update snapshot(s), which are not user-reclaimable.

Note: macOS does not expose per-snapshot sizes or a purgeable-space total to
command-line tools, so no size is given here. Snapshots share storage via
copy-on-write, which is why free space can stay flat after deleting files.
"""

    prompt += f"""
═══════════════════════════════════════
ADVISOR'S ASSESSMENT
═══════════════════════════════════════
{dad_text}
"""

    if tips_text:
        prompt += f"""
Quick Wins Suggested:
{tips_text}
"""

    prompt += """
═══════════════════════════════════════
MY QUESTIONS
═══════════════════════════════════════
Based on this storage scan:

1. What should I focus on cleaning up first?
2. Are any of these files/folders safe to delete?
3. Which folders are taking up the most space unnecessarily?
4. Do I need to upgrade my storage, or can I free up enough space?
5. Are there any red flags in my storage usage?
6. What's a healthy amount of free space to maintain?

Please provide specific, actionable recommendations for my Mac model and usage patterns.
"""

    return prompt


def generate_cpu_prompt(scan_data, personality_data, system_info):
    """Generate prompt for CPU/memory scan results."""

    total_mem_gb = scan_data.get('total_memory_gb', 0)
    total_used_gb = scan_data.get('total_used_gb', 0)
    memory_pressure = scan_data.get('memory_pressure', {})
    memory_hogs = scan_data.get('memory_hogs', [])
    top_processes = scan_data.get('top_processes', [])
    top_memory_processes = scan_data.get('top_memory_processes', [])
    process_metrics = scan_data.get('process_metrics', {})
    all_processes = scan_data.get('all_processes', [])

    # Format memory overview
    used_percent = (total_used_gb / total_mem_gb * 100) if total_mem_gb > 0 else 0
    pressure_level = memory_pressure.get('pressure', 'low') if memory_pressure else 'low'
    free_gb = memory_pressure.get('free_gb', 0) if memory_pressure else 0
    pressure_emoji = '🔴' if pressure_level == 'high' else '🟡' if pressure_level == 'medium' else '🟢'

    # Format memory hogs (show more - top 30)
    hogs_text = ""
    for idx, hog in enumerate(memory_hogs[:30], 1):
        name = hog.get('name', 'Unknown')
        mem_mb = hog.get('total_mb', 0)
        mem_gb = mem_mb / 1024.0
        process_count = hog.get('process_count', 1)

        if mem_gb >= 1:
            mem_display = f"{mem_gb:.1f} GB"
        else:
            mem_display = f"{mem_mb:.0f} MB"

        hogs_text += f"{idx}. {name}: {mem_display}"
        if process_count > 1:
            hogs_text += f" ({process_count} processes)"
        hogs_text += "\n"

    # Format top CPU processes
    cpu_text = ""
    for idx, proc in enumerate(top_processes[:15], 1):
        name = proc.get('name', 'Unknown')
        cpu = proc.get('cpu_percent', 0)
        mem_mb = proc.get('memory_mb', 0)

        if mem_mb >= 1024:
            mem_display = f"{mem_mb/1024:.1f} GB"
        else:
            mem_display = f"{mem_mb:.0f} MB"

        cpu_text += f"{idx}. {name}: {cpu:.1f}% CPU, {mem_display} RAM\n"
    
    # Format top individual memory processes (not grouped)
    memory_procs_text = ""
    for idx, proc in enumerate(top_memory_processes[:30], 1):
        name = proc.get('name', 'Unknown')
        mem_mb = proc.get('memory_mb', 0)
        cpu = proc.get('cpu_percent', 0)
        mem_percent = proc.get('memory_percent', 0)
        
        if mem_mb >= 1024:
            mem_display = f"{mem_mb/1024:.1f} GB"
        else:
            mem_display = f"{mem_mb:.0f} MB"
        
        memory_procs_text += f"{idx}. {name}: {mem_display} ({mem_percent:.1f}% of RAM), {cpu:.1f}% CPU\n"
    
    # Format process metrics
    metrics_text = ""
    if process_metrics:
        total_procs = process_metrics.get('total_processes', 0)
        procs_100mb = process_metrics.get('processes_over_100mb', 0)
        procs_500mb = process_metrics.get('processes_over_500mb', 0)
        procs_1gb = process_metrics.get('processes_over_1gb', 0)
        avg_mem = process_metrics.get('avg_memory_mb', 0)
        small_mb = process_metrics.get('small_processes_mb', 0)
        medium_mb = process_metrics.get('medium_processes_mb', 0)
        large_mb = process_metrics.get('large_processes_mb', 0)
        small_count = process_metrics.get('small_processes_count', 0)
        
        metrics_text = f"""Total Processes: {total_procs:,}
Processes over 100 MB: {procs_100mb}
Processes over 500 MB: {procs_500mb}
Processes over 1 GB: {procs_1gb}
Average Memory per Process: {avg_mem:.0f} MB

Memory Distribution:
- Small processes (<100 MB): {small_count:,} processes using {small_mb/1024:.1f} GB
- Medium processes (100-500 MB): {procs_100mb - procs_500mb} processes using {medium_mb/1024:.1f} GB
- Large processes (≥500 MB): {procs_500mb} processes using {large_mb/1024:.1f} GB
"""

    # Format dad's assessment
    comments = personality_data.get('comments', [])
    status = personality_data.get('status', 'ok')
    status_emoji = '🔴' if status == 'critical' else '🟡' if status == 'warn' else '🟢'

    dad_text = '\n'.join(f'"{comment}"' for comment in comments)

    # Format tips
    tips = personality_data.get('tips', [])
    tips_text = '\n'.join(f"• {tip}" for tip in tips)

    prompt = f"""I'm experiencing performance issues on my Mac and need help understanding what's going on. Here's a detailed snapshot of my system:

═══════════════════════════════════════
SYSTEM SPECIFICATIONS
═══════════════════════════════════════
{format_system_info(system_info)}

═══════════════════════════════════════
MEMORY STATUS
═══════════════════════════════════════
Total RAM: {total_mem_gb:.1f} GB
Used: {total_used_gb:.1f} GB ({used_percent:.0f}%)
Free: {free_gb:.1f} GB
Memory Pressure: {pressure_emoji} {pressure_level.upper()}
Status: {status_emoji} {status.upper()}

═══════════════════════════════════════
PROCESS STATISTICS
═══════════════════════════════════════
{metrics_text.strip()}

═══════════════════════════════════════
APPS USING MOST MEMORY (Grouped)
═══════════════════════════════════════
{hogs_text.strip()}

═══════════════════════════════════════
TOP INDIVIDUAL PROCESSES BY MEMORY
═══════════════════════════════════════
{memory_procs_text.strip()}

═══════════════════════════════════════
TOP CPU USAGE
═══════════════════════════════════════
{cpu_text.strip()}

═══════════════════════════════════════
ADVISOR'S ASSESSMENT
═══════════════════════════════════════
{dad_text}
"""

    if tips_text:
        prompt += f"""
Quick Wins Suggested:
{tips_text}
"""

    # Add detailed process list if available (for deep analysis)
    if all_processes:
        detailed_procs_text = "\n═══════════════════════════════════════\n"
        detailed_procs_text += "ALL PROCESSES (Detailed List)\n"
        detailed_procs_text += "═══════════════════════════════════════\n"
        detailed_procs_text += "Complete list of all processes sorted by memory usage:\n\n"
        
        for idx, proc in enumerate(all_processes[:100], 1):  # Top 100 processes
            name = proc.get('name', 'Unknown')
            mem_mb = proc.get('memory_mb', 0)
            cpu = proc.get('cpu_percent', 0)
            mem_percent = proc.get('memory_percent', 0)
            command = proc.get('command', '')
            
            # Truncate very long commands
            if len(command) > 150:
                command = command[:147] + '...'
            
            if mem_mb >= 1024:
                mem_display = f"{mem_mb/1024:.2f} GB"
            else:
                mem_display = f"{mem_mb:.0f} MB"
            
            detailed_procs_text += f"{idx}. {name}\n"
            detailed_procs_text += f"   Memory: {mem_display} ({mem_percent:.2f}% of RAM), CPU: {cpu:.1f}%\n"
            if command and command != name:
                detailed_procs_text += f"   Command: {command}\n"
            detailed_procs_text += "\n"
        
        if len(all_processes) > 100:
            detailed_procs_text += f"\n... and {len(all_processes) - 100} more processes (see full export for complete list)\n"
        
        prompt += detailed_procs_text

    prompt += f"""
═══════════════════════════════════════
MY QUESTIONS
═══════════════════════════════════════
Based on this performance scan:

1. Is my memory pressure level concerning? Should I be worried?
2. Which apps should I quit to improve performance immediately?
3. Is {total_mem_gb:.0f} GB RAM enough for my usage, or should I upgrade?
4. Are any of these processes abnormal or problematic?
5. What's causing my Mac to feel slow/show memory warnings?
6. Should I restart my Mac, or is there a better solution?
7. Are there any long-term changes I should make to prevent this?
8. Can you identify any specific processes that are using more memory than they should?
9. Are there any processes I should investigate further or be concerned about?

Please provide specific, actionable recommendations based on my Mac model and the processes running. 
If you see any unusual processes or patterns, please point them out.
"""

    return prompt


def generate_generic_prompt(scan_data, personality_data, system_info):
    """Generate generic prompt when scan type is unknown."""

    comments = personality_data.get('comments', [])
    dad_text = '\n'.join(f'"{comment}"' for comment in comments)

    prompt = f"""I ran a system scan on my Mac and need help understanding the results:

═══════════════════════════════════════
SYSTEM SPECIFICATIONS
═══════════════════════════════════════
{format_system_info(system_info)}

═══════════════════════════════════════
ADVISOR'S ASSESSMENT
═══════════════════════════════════════
{dad_text}

═══════════════════════════════════════
MY QUESTIONS
═══════════════════════════════════════
1. What do these results mean for my Mac's health?
2. Should I take any action based on these findings?
3. Are there any concerning issues I should address?

Please provide specific recommendations for my Mac model.
"""

    return prompt
