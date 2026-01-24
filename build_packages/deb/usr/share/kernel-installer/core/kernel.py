"""
Kernel manager for downloading, compiling, and installing kernels.
"""

import os
import re
import json
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Callable
from pathlib import Path

from .distro import DistroDetector, DistroFamily
from .profiles import KernelProfile, ProfileType
from ..utils.system import (
    run_command, run_command_with_callback, run_privileged,
    get_build_directory, ensure_directory, get_cpu_count
)
from ..locale.i18n import _


@dataclass
class KernelVersion:
    """Represents a kernel version available for download."""
    version: str
    url: str
    is_latest: bool = False
    is_longterm: bool = False
    is_mainline: bool = False  # Release candidate
    released: Optional[str] = None


@dataclass 
class InstalledKernel:
    """Represents an installed kernel in history."""
    version: str
    profile: str
    installed_date: str
    is_current: bool = False


class KernelManager:
    """
    Manages kernel operations: fetching versions, downloading,
    compiling, and installing.
    """
    
    KERNEL_ORG_URL = "https://www.kernel.org/"
    KERNEL_CDN_URL = "https://cdn.kernel.org/pub/linux/kernel"
    TAG = "-lexi-amd64"
    HISTORY_FILE = ".kernel_installer_history.json"
    
    def __init__(self):
        self._distro = DistroDetector()
        self._build_dir = get_build_directory()
        self._progress_callback: Optional[Callable[[str, int], None]] = None
        self._current_version: Optional[str] = None
    
    def set_progress_callback(self, callback: Callable[[str, int], None]) -> None:
        """
        Set a callback for progress updates.
        
        Args:
            callback: Function receiving (message, percent)
        """
        self._progress_callback = callback
    
    def _report_progress(self, message: str, percent: int = -1) -> None:
        """Report progress to callback if set."""
        if self._progress_callback:
            self._progress_callback(message, percent)
    
    def fetch_available_versions(self) -> List[KernelVersion]:
        """
        Fetch available kernel versions from kernel.org.
        
        Returns:
            List of KernelVersion objects
        """
        versions = []
        
        try:
            # Fetch kernel.org page
            req = urllib.request.Request(
                self.KERNEL_ORG_URL,
                headers={'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Kernel-Installer/1.0'}
            )
            with urllib.request.urlopen(req, timeout=30) as response:
                html = response.read().decode('utf-8')
            
            # Find the releases table
            # Pattern to match each row: <tr>...<td>TYPE:</td>...<strong>VERSION</strong>...</tr>
            # We look for the version in the strong tag after each kernel type
            
            # Find all table rows with kernel info
            row_pattern = re.compile(
                r'<tr[^>]*>.*?<td>(\w+):</td>.*?<strong>([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-rc\d+)?)</strong>',
                re.DOTALL
            )
            
            seen_versions = set()
            first_stable = True
            
            for match in row_pattern.finditer(html):
                kernel_type = match.group(1).lower()
                version = match.group(2)
                
                if version in seen_versions:
                    continue
                seen_versions.add(version)
                
                major = version.split('.')[0]
                
                # Mainline (RC) versions have different URL format
                if '-rc' in version:
                    url = f"{self.KERNEL_CDN_URL}/v{major}.x/testing/linux-{version}.tar.xz"
                else:
                    url = f"{self.KERNEL_CDN_URL}/v{major}.x/linux-{version}.tar.xz"
                
                if kernel_type == 'mainline':
                    versions.append(KernelVersion(
                        version=version,
                        url=url,
                        is_latest=False,
                        is_longterm=False,
                        is_mainline=True
                    ))
                elif kernel_type == 'stable':
                    is_latest = first_stable
                    first_stable = False
                    versions.append(KernelVersion(
                        version=version,
                        url=url,
                        is_latest=is_latest,
                        is_longterm=False
                    ))
                elif kernel_type == 'longterm':
                    versions.append(KernelVersion(
                        version=version,
                        url=url,
                        is_latest=False,
                        is_longterm=True
                    ))
            
            # Sort: mainline first (experimental), then latest stable, then LTS
            versions.sort(key=lambda v: (
                not v.is_mainline,  # Mainline first
                not v.is_latest,    # Then latest stable
                not v.is_longterm,  # Then LTS
                [-int(x) for x in re.findall(r'\d+', v.version)]
            ))
                    
        except Exception as e:
            print(f"Error fetching kernel versions: {e}")
            import traceback
            traceback.print_exc()
        
        return versions
    
    def get_latest_version(self) -> Optional[str]:
        """Get the latest stable kernel version."""
        versions = self.fetch_available_versions()
        for v in versions:
            if v.is_latest:
                return v.version
        return versions[0].version if versions else None
    
    def get_current_kernel(self) -> str:
        """Get the currently running kernel version."""
        result = run_command("uname -r")
        return result.stdout.strip() if result.returncode == 0 else "Unknown"
    
    def download_kernel(self, version: str) -> bool:
        """
        Download a kernel tarball.
        
        Args:
            version: Kernel version to download
            
        Returns:
            True if successful
        """
        self._report_progress(_("Preparing download for Linux %(version)s...") % {'version': version}, 0)
        
        # Ensure build directory exists
        if not ensure_directory(self._build_dir):
            self._report_progress(_("Error: Could not create build directory"), -1)
            return False
        
        major = version.split('.')[0]
        url = f"{self.KERNEL_CDN_URL}/v{major}.x/linux-{version}.tar.xz"
        tarball = os.path.join(self._build_dir, f"linux-{version}.tar.xz")
        
        self._report_progress(_("Downloading linux-%(version)s.tar.xz...") % {'version': version}, 5)
        
        # Download using wget for progress
        cmd = f'wget -O "{tarball}" "{url}"'
        result = run_command(cmd, cwd=self._build_dir)
        
        if result.returncode != 0:
            self._report_progress(_("Download error: %(error)s") % {'error': result.stderr}, -1)
            return False
        
        self._report_progress(_("Download complete. Extracting..."), 15)
        
        # Extract
        cmd = f'tar -xf "{tarball}"'
        result = run_command(cmd, cwd=self._build_dir)
        
        if result.returncode != 0:
            self._report_progress(_("Extraction error: %(error)s") % {'error': result.stderr}, -1)
            return False
        
        self._report_progress(_("Extraction complete."), 20)
        self._current_version = version
        return True
    
    def configure_kernel(self, version: str, profile: KernelProfile) -> bool:
        """
        Configure the kernel with a given profile.
        
        Args:
            version: Kernel version
            profile: KernelProfile to apply
            
        Returns:
            True if successful
        """
        source_dir = os.path.join(self._build_dir, f"linux-{version}")
        config_path = os.path.join(source_dir, ".config")
        
        self._report_progress(_("Copying current kernel configuration..."), 22)
        
        # Copy current kernel config
        cmd = f'cp /boot/config-$(uname -r) .config'
        result = run_command(cmd, cwd=source_dir)
        
        if result.returncode != 0:
            # Try alternative location
            cmd = 'zcat /proc/config.gz > .config 2>/dev/null || cp /boot/config-* .config 2>/dev/null'
            result = run_command(cmd, cwd=source_dir)
        
        self._report_progress(_("Applying profile: %(profile)s...") % {'profile': profile.name}, 25)
        
        # Apply profile settings
        try:
            profile.apply_to_config(config_path)
        except Exception as e:
            self._report_progress(_("Warning applying profile: %(error)s") % {'error': e}, -1)
        
        # Set local version tag (use custom name if set)
        custom = getattr(self, '_custom_name', 'custom')
        profile_suffix = profile.suffix  # Clean suffix like 'gaming', 'lowlatency', 'minimal'
        full_tag = f"-{custom}-{profile_suffix}"
        cmd = f"sed -i 's/^CONFIG_LOCALVERSION=.*/CONFIG_LOCALVERSION=\"{full_tag}\"/' .config"
        run_command(cmd, cwd=source_dir)
        
        self._report_progress(_("Running make oldconfig..."), 28)
        
        # Run oldconfig to handle new options
        cmd = 'yes "" | make oldconfig'
        result = run_command(cmd, cwd=source_dir)
        
        self._report_progress(_("Configuration complete."), 30)
        return True
    
    def build_kernel(self, version: str) -> bool:
        """
        Build the kernel with progress tracking.
        
        Args:
            version: Kernel version to build
            
        Returns:
            True if successful
        """
        source_dir = os.path.join(self._build_dir, f"linux-{version}")
        cpu_count = get_cpu_count()
        
        self._report_progress(_("Compiling kernel with %(cores)d cores...") % {'cores': cpu_count}, 30)
        
        # Count source files for progress estimation
        result = run_command(f"find {source_dir} -name '*.c' | wc -l")
        total_files = int(result.stdout.strip()) if result.returncode == 0 else 20000
        total_files = int(total_files * 0.85)  # Adjust estimate
        
        compiled_count = 0
        
        def line_callback(line: str) -> None:
            nonlocal compiled_count
            if ' CC ' in line or ' LD ' in line or ' AR ' in line:
                compiled_count += 1
                percent = min(30 + int((compiled_count / total_files) * 60), 90)
                self._report_progress(line[:80], percent)
        
        # Build command depends on distro family
        distro_info = self._distro.detect()
        
        if distro_info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU):
            # Build .deb packages
            self._report_progress(_("Generating .deb packages..."), 32)
            cmd = f'LC_ALL=C fakeroot make -j{cpu_count} bindeb-pkg'
        elif distro_info.family == DistroFamily.FEDORA:
            # Build RPM packages
            self._report_progress(_("Generating RPM packages..."), 32)
            cmd = f'make -j{cpu_count} rpm-pkg'
        elif distro_info.family == DistroFamily.ARCH:
            # Arch uses direct installation
            self._report_progress(_("Compiling for direct installation..."), 32)
            cmd = f'make -j{cpu_count}'
        else:
            # Fallback: generic make
            cmd = f'make -j{cpu_count}'
        
        exit_code = run_command_with_callback(cmd, cwd=source_dir, line_callback=line_callback)
        
        if exit_code != 0:
            self._report_progress(_("Build error"), -1)
            return False
        
        # For Arch, also build modules
        if distro_info.family == DistroFamily.ARCH:
            self._report_progress(_("Compiling modules..."), 85)
            cmd = f'make -j{cpu_count} modules'
            exit_code = run_command_with_callback(cmd, cwd=source_dir, line_callback=line_callback)
            if exit_code != 0:
                self._report_progress(_("Error compiling modules"), -1)
                return False
        
        self._report_progress(_("Build complete."), 90)
        return True
    
    def install_kernel(self, version: str, profile: KernelProfile) -> bool:
        """
        Install the compiled kernel.
        
        Args:
            version: Kernel version
            profile: Profile used for compilation
            
        Returns:
            True if successful
        """
        self._report_progress(_("Installing kernel..."), 92)
        
        distro_info = self._distro.detect()
        full_tag = f"{self.TAG}-{profile.name.lower()}"
        source_dir = os.path.join(self._build_dir, f"linux-{version}")
        kernel_version = f"{version}{full_tag}"
        
        if distro_info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU):
            # Install .deb packages
            self._report_progress(_("Installing .deb packages..."), 93)
            cmd = f'dpkg -i {self._build_dir}/linux-image-{version}*.deb'
            result = run_privileged(cmd)
            
            if result.returncode != 0:
                self._report_progress(_("Installation error: %(error)s") % {'error': result.stderr}, -1)
                return False
            
            # Install headers if exists
            cmd = f'dpkg -i {self._build_dir}/linux-headers-{version}*.deb 2>/dev/null || true'
            run_privileged(cmd)
            
        elif distro_info.family == DistroFamily.FEDORA:
            # Install RPM packages
            self._report_progress(_("Installing RPM packages..."), 93)
            rpm_path = os.path.expanduser("~/rpmbuild/RPMS/x86_64/")
            cmd = f'rpm -ivh {rpm_path}kernel-{version}*.rpm'
            result = run_privileged(cmd)
            
            if result.returncode != 0:
                self._report_progress(_("RPM installation error: %(error)s") % {'error': result.stderr}, -1)
                return False
                
        elif distro_info.family == DistroFamily.ARCH:
            # Arch: Direct installation using make
            self._report_progress(_("Installing modules..."), 93)
            cmd = f'make modules_install'
            result = run_privileged(f'sh -c "cd {source_dir} && {cmd}"')
            
            if result.returncode != 0:
                self._report_progress(_("Module installation error: %(error)s") % {'error': result.stderr}, -1)
                return False
            
            self._report_progress(_("Installing kernel..."), 94)
            cmd = f'make install'
            result = run_privileged(f'sh -c "cd {source_dir} && {cmd}"')
            
            if result.returncode != 0:
                self._report_progress(_("Kernel installation error: %(error)s") % {'error': result.stderr}, -1)
                return False
        
        # Regenerate initramfs
        self._report_progress(_("Regenerating initramfs..."), 95)
        initramfs_cmd = self._distro.get_initramfs_update_command(kernel_version)
        result = run_privileged(initramfs_cmd)
        
        if result.returncode != 0:
            self._report_progress(_("Warning: Error regenerating initramfs"), -1)
        
        # Update bootloader
        self._report_progress(_("Updating bootloader..."), 97)
        bootloader_cmd = self._distro.get_bootloader_update_command()
        result = run_privileged(bootloader_cmd)
        
        if result.returncode != 0:
            self._report_progress(_("Warning: Error updating bootloader"), -1)
        
        # Save to history
        self._save_to_history(version, profile)
        
        self._report_progress(_("Installation complete!"), 100)
        return True
    
    def full_install(self, version: str, profile: KernelProfile, custom_name: str = "") -> bool:
        """
        Perform full kernel installation: download, configure, build, install.
        
        Args:
            version: Kernel version
            profile: KernelProfile to use
            custom_name: Custom name/suffix for the kernel
            
        Returns:
            True if all steps successful
        """
        # Store custom name for use in configure and install
        self._custom_name = custom_name or "custom"
        
        if not self.download_kernel(version):
            return False
        
        if not self.configure_kernel(version, profile):
            return False
        
        if not self.build_kernel(version):
            return False
        
        if not self.install_kernel(version, profile):
            return False
        
        return True
    
    def _get_history_path(self) -> str:
        """Get path to history file."""
        return os.path.join(Path.home(), self.HISTORY_FILE)
    
    def _save_to_history(self, version: str, profile: KernelProfile) -> None:
        """Save installation to history."""
        history = self.get_installation_history()
        
        full_version = f"{version}{self.TAG}-{profile.name.lower()}"
        
        history.insert(0, InstalledKernel(
            version=full_version,
            profile=profile.name,
            installed_date=datetime.now().isoformat()
        ))
        
        # Keep only last 20 entries
        history = history[:20]
        
        # Save to file
        try:
            with open(self._get_history_path(), 'w') as f:
                json.dump([
                    {
                        'version': k.version,
                        'profile': k.profile,
                        'installed_date': k.installed_date
                    }
                    for k in history
                ], f, indent=2)
        except Exception as e:
            print(f"Error saving history: {e}")
    
    def get_installation_history(self) -> List[InstalledKernel]:
        """Get list of previously installed kernels."""
        history = []
        current = self.get_current_kernel()
        
        try:
            path = self._get_history_path()
            if os.path.exists(path):
                with open(path, 'r') as f:
                    data = json.load(f)
                    for item in data:
                        history.append(InstalledKernel(
                            version=item['version'],
                            profile=item['profile'],
                            installed_date=item['installed_date'],
                            is_current=(item['version'] == current)
                        ))
        except Exception as e:
            print(f"Error loading history: {e}")
        
        return history
    
    def cleanup_build_files(self) -> bool:
        """Remove build directory and temporary files."""
        try:
            import shutil
            if os.path.exists(self._build_dir):
                shutil.rmtree(self._build_dir)
            return True
        except Exception as e:
            print(f"Error cleaning up: {e}")
            return False
