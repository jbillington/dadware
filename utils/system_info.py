"""System information collector for Mac."""

import subprocess
import platform
import os
import re
import sys

# Import diagnostic logging from main module if available
try:
    from yourdad import DIAGNOSTIC_LOGGING
except ImportError:
    DIAGNOSTIC_LOGGING = False

def log_subprocess_call(location, cmd, **kwargs):
    """Log subprocess call for diagnostics."""
    if DIAGNOSTIC_LOGGING:
        print(f"\n[DIAGNOSTIC] {location}: About to call subprocess.run()", file=sys.stderr)
        print(f"[DIAGNOSTIC] Command: {cmd}", file=sys.stderr)
        print(f"[DIAGNOSTIC] Command type: {type(cmd)}", file=sys.stderr)
        if isinstance(cmd, (list, tuple)):
            print(f"[DIAGNOSTIC] Command length: {len(cmd)}", file=sys.stderr)
            for i, arg in enumerate(cmd):
                print(f"[DIAGNOSTIC]   Arg[{i}]: {repr(arg)} (type: {type(arg).__name__})", file=sys.stderr)
        print(f"[DIAGNOSTIC] Additional args: {kwargs}", file=sys.stderr)
        sys.stderr.flush()


def run_command(cmd):
    """Run a shell command and return output."""
    # Defensive check: cmd must be valid
    if not cmd:
        return None
    
    # Ensure cmd is a list (not None, not empty)
    if isinstance(cmd, str):
        # String commands are handled by shell=True
        pass
    elif not isinstance(cmd, (list, tuple)):
        return None
    
    try:
        log_subprocess_call("run_command()", cmd)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=5,
            shell=isinstance(cmd, str)
        )
        if result.returncode == 0:
            return result.stdout.strip()
        return None
    except (TypeError, ValueError, subprocess.TimeoutExpired, FileNotFoundError) as e:
        return None
    except Exception:
        return None


def get_mac_model():
    """Get Mac model name and identifier."""
    # Get model name (e.g., "MacBook Pro")
    model_name = run_command(['sysctl', '-n', 'hw.model'])

    # Get more readable model info from system_profiler
    model_info = run_command(['system_profiler', 'SPHardwareDataType'])

    readable_name = None
    model_id = None
    year = None

    if model_info:
        # Extract "Model Name: MacBook Pro"
        name_match = re.search(r'Model Name:\s*(.+)', model_info)
        if name_match:
            readable_name = name_match.group(1).strip()

        # Extract "Model Identifier: MacBookPro16,1"
        id_match = re.search(r'Model Identifier:\s*(.+)', model_info)
        if id_match:
            model_id = id_match.group(1).strip()

        # Extract year from model identifier or chip name
        # Try to get year from "Chip: Apple M1 Pro" or similar
        chip_match = re.search(r'Chip:\s*(.+)', model_info)
        if chip_match:
            chip_name = chip_match.group(1).strip()
            # Estimate year based on chip (rough approximation)
            if 'M3' in chip_name:
                year = '2023-2024'
            elif 'M2' in chip_name:
                year = '2022-2023'
            elif 'M1' in chip_name:
                year = '2020-2021'

    return {
        'model_name': readable_name or model_name or 'Unknown Mac',
        'model_identifier': model_id or model_name or 'Unknown',
        'year': year or 'Unknown'
    }


def get_cpu_info():
    """Get CPU/processor information."""
    cpu_brand = run_command(['sysctl', '-n', 'machdep.cpu.brand_string'])
    cpu_cores = run_command(['sysctl', '-n', 'hw.ncpu'])
    cpu_physical_cores = run_command(['sysctl', '-n', 'hw.physicalcpu'])

    # For Apple Silicon, get chip name
    chip_name = None
    if platform.processor() == 'arm':
        model_info = run_command(['system_profiler', 'SPHardwareDataType'])
        if model_info:
            chip_match = re.search(r'Chip:\s*(.+)', model_info)
            if chip_match:
                chip_name = chip_match.group(1).strip()

    return {
        'brand': chip_name or cpu_brand or 'Unknown CPU',
        'total_cores': cpu_cores or 'Unknown',
        'physical_cores': cpu_physical_cores or 'Unknown',
        'architecture': platform.processor() or platform.machine()
    }


def get_memory_info():
    """Get RAM information."""
    # Total memory in bytes
    mem_bytes = run_command(['sysctl', '-n', 'hw.memsize'])
    total_gb = None
    if mem_bytes:
        try:
            total_gb = int(mem_bytes) / (1024**3)
        except:
            pass

    # Get memory type/speed from system_profiler
    memory_info = run_command(['system_profiler', 'SPMemoryDataType'])
    memory_type = None
    memory_speed = None

    if memory_info:
        type_match = re.search(r'Type:\s*(.+)', memory_info)
        if type_match:
            memory_type = type_match.group(1).strip()

        speed_match = re.search(r'Speed:\s*(.+)', memory_info)
        if speed_match:
            memory_speed = speed_match.group(1).strip()

    return {
        'total_gb': f"{total_gb:.0f}" if total_gb else 'Unknown',
        'type': memory_type or 'Unknown',
        'speed': memory_speed or 'Unknown'
    }


def get_storage_info():
    """Get storage information."""
    storage_info = run_command(['system_profiler', 'SPStorageDataType'])

    drives = []
    if storage_info:
        # Try to extract drive info
        # This is a simplified version - system_profiler output can be complex
        size_matches = re.findall(r'Capacity:\s*(.+)', storage_info)
        for size in size_matches:
            drives.append(size.strip())

    return {
        'drives': drives if drives else ['Unknown']
    }


def get_os_info():
    """Get macOS version information."""
    # Get macOS version
    os_version = platform.mac_ver()[0]

    # Get build version
    build = run_command(['sw_vers', '-buildVersion'])

    # Get product name (e.g., "macOS Sonoma")
    product_name = run_command(['sw_vers', '-productName'])

    # Map version to name (rough mapping)
    version_names = {
        '15': 'Sequoia',
        '14': 'Sonoma',
        '13': 'Ventura',
        '12': 'Monterey',
        '11': 'Big Sur',
        '10.15': 'Catalina',
        '10.14': 'Mojave',
        '10.13': 'High Sierra'
    }

    version_name = None
    for v, name in version_names.items():
        if os_version.startswith(v):
            version_name = name
            break

    return {
        'version': os_version or 'Unknown',
        'version_name': version_name or product_name or 'macOS',
        'build': build or 'Unknown'
    }


def get_system_info():
    """
    Collect comprehensive system information.
    Returns dict with all system specs.
    """
    mac_model = get_mac_model()
    cpu = get_cpu_info()
    memory = get_memory_info()
    storage = get_storage_info()
    os_info = get_os_info()

    return {
        'model': mac_model,
        'cpu': cpu,
        'memory': memory,
        'storage': storage,
        'os': os_info,
        'hostname': platform.node(),
        'username': os.getenv('USER', 'Unknown')
    }


def format_system_info(system_info):
    """Format system info for display."""
    lines = []

    model = system_info.get('model', {})
    lines.append(f"Computer: {model.get('model_name', 'Unknown Mac')}")
    lines.append(f"Model ID: {model.get('model_identifier', 'Unknown')}")
    if model.get('year') != 'Unknown':
        lines.append(f"Year: {model.get('year', 'Unknown')}")

    cpu = system_info.get('cpu', {})
    lines.append(f"Processor: {cpu.get('brand', 'Unknown')}")
    lines.append(f"Cores: {cpu.get('total_cores', 'Unknown')} total ({cpu.get('physical_cores', 'Unknown')} physical)")
    lines.append(f"Architecture: {cpu.get('architecture', 'Unknown')}")

    memory = system_info.get('memory', {})
    lines.append(f"RAM: {memory.get('total_gb', 'Unknown')} GB {memory.get('type', '')}")
    if memory.get('speed') != 'Unknown':
        lines.append(f"RAM Speed: {memory.get('speed', '')}")

    storage = system_info.get('storage', {})
    drives = storage.get('drives', [])
    if drives:
        for idx, drive in enumerate(drives, 1):
            lines.append(f"Storage {idx}: {drive}")

    os_info = system_info.get('os', {})
    lines.append(f"OS: {os_info.get('version_name', 'macOS')} {os_info.get('version', '')}")
    lines.append(f"Build: {os_info.get('build', 'Unknown')}")

    return '\n'.join(lines)
