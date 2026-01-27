#!/usr/bin/env python3
"""
Setup script for Kernel Installer GUI.
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_path = Path(__file__).parent / "README.md"
long_description = ""
if readme_path.exists():
    long_description = readme_path.read_text(encoding="utf-8")

setup(
    name="kernel-installer-gui",
    version="1.0.2",
    author="Sergi Perich",
    author_email="info@soploslinux.com",
    description="GTK3 GUI for downloading, compiling and installing Linux kernels",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/SoplosLinux/kernel-installer",
    license="GPL-3.0",
    
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "kernel_installer_gui": [
            "data/*.css",
            "data/*.desktop",
            "data/*.xml",
            "assets/icons/org.soplos.kernel-installer*.png",
            "locale/*/LC_MESSAGES/*.mo",
        ],
    },
    
    python_requires=">=3.9",
    install_requires=[
        "PyGObject>=3.40",
    ],
    
    entry_points={
        "console_scripts": [
            "kernel-installer-gui=kernel_installer_gui.main:main",
        ],
        "gui_scripts": [
            "kernel-installer=kernel_installer_gui.main:main",
        ],
    },
    
    data_files=[
        ("share/applications", ["kernel_installer_gui/data/org.soplos.kernel-installer.desktop"]),
        ("share/metainfo", ["kernel_installer_gui/data/org.soplos.kernel-installer.metainfo.xml"]),
        ("share/kernel-installer", ["kernel_installer_gui/data/style.css"]),
        ("share/icons/hicolor/48x48/apps", ["kernel_installer_gui/assets/icons/org.soplos.kernel-installer-48.png"]),
        ("share/icons/hicolor/128x128/apps", ["kernel_installer_gui/assets/icons/org.soplos.kernel-installer-128.png"]),
        ("share/icons/hicolor/256x256/apps", ["kernel_installer_gui/assets/icons/org.soplos.kernel-installer-256.png"]),
    ],
    
    classifiers=[
        "Development Status :: 4 - Beta",
        "Environment :: X11 Applications :: GTK",
        "Intended Audience :: End Users/Desktop",
        "Intended Audience :: System Administrators",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Operating System :: POSIX :: Linux",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Topic :: System :: Operating System Kernels :: Linux",
        "Topic :: System :: Systems Administration",
    ],
    
    keywords="kernel linux compile install gtk gui",
)
