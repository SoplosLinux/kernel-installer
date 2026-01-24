#!/usr/bin/env python3
"""
Kernel Installer GUI - Launcher
Copyright (C) 2025 Sergi Perich <info@soploslinux.com>

Run this script to start the Kernel Installer GUI.
"""

import sys
import os
import signal
import atexit
import shutil

# Handle cleanup on exit
def cleanup_pycache():
    """Remove all __pycache__ directories in the project."""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    for root, dirs, files in os.walk(base_dir):
        if "__pycache__" in dirs:
            pycache_path = os.path.join(root, "__pycache__")
            try:
                shutil.rmtree(pycache_path)
            except Exception:
                pass

# Register cleanup for normal exit
atexit.register(cleanup_pycache)

# Handle Ctrl+C and other termination signals
def signal_handler(sig, frame):
    cleanup_pycache()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Add package directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from kernel_installer_gui.app import KernelInstallerApp

if __name__ == "__main__":
    app = KernelInstallerApp()
    sys.exit(app.run(sys.argv))
