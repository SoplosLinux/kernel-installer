#!/usr/bin/env python3
"""
Kernel Installer GUI - Launcher
Copyright (C) 2026 Sergi Perich <info@soploslinux.com>

Run this script to start the Kernel Installer GUI.
"""

import sys
import os
import signal
import atexit
import shutil
import argparse

# Handle cleanup on exit
def cleanup_pycache():
    """Remove all __pycache__ directories in the project."""
    try:
        # Check if __file__ exists (it might be gone during atexit/traceback)
        curr_file = globals().get('__file__') or sys.argv[0]
        base_dir = os.path.dirname(os.path.abspath(curr_file))
        for root, dirs, files in os.walk(base_dir):
            if "__pycache__" in dirs:
                pycache_path = os.path.join(root, "__pycache__")
                try:
                    shutil.rmtree(pycache_path)
                except Exception:
                    pass
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

import gi
gi.require_version('Gtk', '3.0')
gi.require_version('Gdk', '3.0')
from gi.repository import GLib, Gdk, Gtk

# Force identity association for panel icons (Soplos Standard)
GLib.set_prgname('kernel-installer')
GLib.set_application_name('Kernel Installer')
if hasattr(Gdk, 'set_program_class'):
    Gdk.set_program_class('kernel-installer')
Gtk.Window.set_default_icon_name('kernel-installer')

from kernel_installer_gui.app import KernelInstallerApp



if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kernel Installer GUI Launcher")
    parser.add_argument("--force", action="store_true", help="Force a new instance (allows seeing terminal output even if another instance is running)")
    args, unknown = parser.parse_known_args()
    
    print("--- Kernel Installer: Starting CLI Launcher ---", file=sys.stderr, flush=True)
    if args.force:
        print("NOTE: Forcing new instance. Multiple windows may appear.", file=sys.stderr, flush=True)
        
    try:
        app = KernelInstallerApp(force_new=args.force)
        status = app.run([sys.argv[0]] + unknown)
        print(f"--- Kernel Installer: Process finished with status {status} ---", file=sys.stderr, flush=True)
        sys.exit(status)
    except Exception as e:
        print(f"CRITICAL ERROR: {e}", file=sys.stderr, flush=True)
        import traceback
        traceback.print_exc()
        sys.exit(1)
