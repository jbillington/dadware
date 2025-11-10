"""CPU and RAM scanner."""

import subprocess
import re


def scan_cpu():
    """Scan CPU and RAM usage, return structured data."""
    try:
        # Run ps aux to get process info
        result = subprocess.run(
            ['ps', 'aux'],
            capture_output=True,
            text=True,
            timeout=5
        )
        
        if result.returncode != 0:
            return None
        
        processes = []
        lines = result.stdout.strip().split('\n')
        
        # Skip header line
        for line in lines[1:]:
            parts = line.split(None, 10)  # Split on whitespace, max 11 parts
            if len(parts) < 11:
                continue
            
            try:
                # ps aux format: USER PID %CPU %MEM VSZ RSS TT STAT START TIME COMMAND
                cpu_percent = float(parts[2])
                mem_percent = float(parts[3])
                rss_kb = int(parts[5])  # Resident Set Size in KB
                command = parts[10]
                
                # Extract process name (first part of command)
                process_name = command.split()[0] if command else 'Unknown'
                # Remove path, keep just name
                process_name = process_name.split('/')[-1]
                
                processes.append({
                    'name': process_name,
                    'cpu_percent': cpu_percent,
                    'memory_percent': mem_percent,
                    'memory_mb': rss_kb / 1024.0,  # Convert KB to MB
                    'command': command
                })
            except (ValueError, IndexError):
                continue
        
        # Sort by CPU usage
        processes.sort(key=lambda x: x['cpu_percent'], reverse=True)
        top_processes = processes[:5]  # Top 5
        
        # Get system memory info (using vm_stat would be better, but simpler for POC)
        try:
            mem_result = subprocess.run(
                ['sysctl', 'hw.memsize'],
                capture_output=True,
                text=True,
                timeout=2
            )
            total_memory_bytes = 0
            if mem_result.returncode == 0:
                match = re.search(r'(\d+)', mem_result.stdout)
                if match:
                    total_memory_bytes = int(match.group(1))
        except:
            total_memory_bytes = 0
        
        return {
            'scan_type': 'cpu',
            'top_processes': top_processes,
            'total_memory_bytes': total_memory_bytes,
            'total_memory_gb': total_memory_bytes / (1024**3) if total_memory_bytes > 0 else 0
        }
    
    except subprocess.TimeoutExpired:
        return None
    except Exception as e:
        return None

