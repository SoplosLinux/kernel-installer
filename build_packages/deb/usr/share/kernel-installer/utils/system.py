"""
System utilities for Kernel Installer GUI.
Provides command execution, privilege elevation, and system info.
"""

import subprocess
import os
import shutil


def get_cpu_count() -> int:
    """Get the number of CPU cores available."""
    try:
        return os.cpu_count() or 1
    except Exception:
        return 1


def run_command(cmd: str, cwd: str = None, capture_output: bool = True) -> subprocess.CompletedProcess:
    """
    Run a shell command and return the result.
    
    Args:
        cmd: Command string to execute
        cwd: Working directory for the command
        capture_output: Whether to capture stdout/stderr
    
    Returns:
        CompletedProcess with returncode, stdout, stderr
    """
    return subprocess.run(
        cmd,
        shell=True,
        cwd=cwd,
        capture_output=capture_output,
        text=True
    )


def run_command_with_callback(cmd: str, cwd: str = None, 
                               line_callback=None) -> int:
    """
    Run a command and call a callback for each output line.
    Useful for progress tracking during long operations.
    
    Args:
        cmd: Command string to execute
        cwd: Working directory
        line_callback: Function to call with each line of output
    
    Returns:
        Exit code of the command
    """
    process = subprocess.Popen(
        cmd,
        shell=True,
        cwd=cwd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )
    
    if line_callback:
        for line in iter(process.stdout.readline, ''):
            line_callback(line.rstrip('\n'))
    
    process.wait()
    return process.returncode


def run_privileged(cmd: str) -> subprocess.CompletedProcess:
    """
    Run a command with elevated privileges using pkexec.
    
    Args:
        cmd: Command to run as root
    
    Returns:
        CompletedProcess result
    """
    # Check if pkexec is available
    if shutil.which('pkexec'):
        full_cmd = f'pkexec {cmd}'
    else:
        # Fallback to sudo
        full_cmd = f'sudo {cmd}'
    
    return subprocess.run(
        full_cmd,
        shell=True,
        capture_output=True,
        text=True
    )


def get_home_directory() -> str:
    """Get the user's home directory."""
    return os.path.expanduser('~')


def get_build_directory() -> str:
    """Get the kernel build directory path."""
    return os.path.join(get_home_directory(), 'kernel_build')


def ensure_directory(path: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Returns:
        True if directory exists or was created, False on error
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError:
        return False


def get_load_average() -> tuple[float, float, float]:
    """
    Get system load average (1m, 5m, 15m).
    
    Returns:
        Tuple of (load1, load5, load15)
    """
    try:
        with open('/proc/loadavg', 'r') as f:
            parts = f.read().split()
            return (float(parts[0]), float(parts[1]), float(parts[2]))
    except Exception:
        return (0.0, 0.0, 0.0)
