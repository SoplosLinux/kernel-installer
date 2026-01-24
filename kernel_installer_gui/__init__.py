"""
Kernel Installer GUI Package.
Copyright (C) 2026 Sergi Perich & Alexia Michelle

A GTK3 frontend for downloading, compiling and installing
the latest Linux kernel with optimized profiles.
"""

__version__ = "1.0.0"
__author__ = "Sergi Perich & Alexia Michelle"

# Initialize internationalization
from .locale.i18n import init_i18n, _
init_i18n()
