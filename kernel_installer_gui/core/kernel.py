"""
Kernel manager for downloading, compiling, and installing kernels.
"""

import os
import sys
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
        self._cancel_requested = False
    
    def cancel_operation(self) -> None:
        """Request cancellation of the current operation."""
        self._cancel_requested = True
    
    def _is_cancelled(self) -> bool:
        """Check if cancellation was requested."""
        return self._cancel_requested

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
            # The label (mainline, stable, etc.) might be inside a tag or classes
            row_pattern = re.compile(
                r'<tr[^>]*>\s*<td[^>]*>\s*(\w+):?</td>\s*<td[^>]*>\s*<strong>([0-9]+\.[0-9]+(?:\.[0-9]+)?(?:-rc\d+)?)</strong>',
                re.IGNORECASE | re.DOTALL
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
                
                # Mainline/RC versions use snapshot from torvalds tree
                if kernel_type == 'mainline' or '-rc' in version:
                    url = f"https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/snapshot/linux-{version}.tar.gz"
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

    def check_build_dependencies(self) -> List[str]:
        """
        Check if all required build tools are installed.
        
        Returns:
            List of missing tools/packages
        """
        import shutil
        missing = []
        
        # Use exhaustive list from distro detector
        required_packages = self._distro.get_required_packages()
        
        for pkg in required_packages:
            # For commands, we check with which
            if pkg in ['make', 'gcc', 'g++', 'flex', 'bison', 'bc', 'wget', 'tar', 'rsync', 'pahole', 'cpio', 'pkg-config', 'fakeroot', 'curl', 'git', 'stdbuf', 'openssl']:
                if not shutil.which(pkg):
                    missing.append(pkg)
            else:
                # For libraries (on Debian-like), we could check with dpkg -l or similar
                # But to keep it cross-distro and simple, we'll assume command-check is primary
                # and maybe adds light library check logic if needed.
                # For now, if it's not a known command, we'll skip direct check here 
                # or assume it's part of a group check.
                pass
        
        return missing

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
        if '-rc' in version:
            # Use snapshot from git.kernel.org for RC/Mainline
            url = f"https://git.kernel.org/pub/scm/linux/kernel/git/torvalds/linux.git/snapshot/linux-{version}.tar.gz"
            extension = "tar.gz"
        else:
            url = f"{self.KERNEL_CDN_URL}/v{major}.x/linux-{version}.tar.xz"
            extension = "tar.xz"
            
        tarball = os.path.join(self._build_dir, f"linux-{version}.{extension}")
        
        self._report_progress(_("Downloading linux-%(version)s.%(ext)s...") % {'version': version, 'ext': extension}, 5)
        
        # Download using wget for progress
        cmd = f'wget -O "{tarball}" "{url}"'
        result = run_command(cmd, cwd=self._build_dir)
        
        if result.returncode != 0:
            self._report_progress(_("Download error: %(error)s") % {'error': result.stderr}, -1)
            return False
        
        self._report_progress(_("Download complete. Extracting..."), 15)
        
        source_dir = os.path.join(self._build_dir, f"linux-{version}")
        
        # 1. Clean old sources and artifacts to ensure a fresh start
        if os.path.exists(source_dir):
            self._report_progress(_("Removing old source directory..."), 16)
            shutil.rmtree(source_dir)
            
        # Also remove old tarballs and packages for THIS version to avoid conflicts
        import glob
        old_artifacts = [
            tarball,
            os.path.join(self._build_dir, f"linux-image-{version}*.deb"),
            os.path.join(self._build_dir, f"linux-headers-{version}*.deb"),
            os.path.join(self._build_dir, f"linux-libc-dev-{version}*.deb"),
            os.path.join(self._build_dir, f"linux-image-{version}*.rpm"),
            os.path.join(self._build_dir, f"linux-{version}*.rpm")
        ]
        for pattern in old_artifacts:
            for f in glob.glob(pattern):
                try:
                    if os.path.isfile(f):
                        os.remove(f)
                except Exception:
                    pass
            
        # 2. Extract
        self._report_progress(_("Extracting linux-%(version)s...") % {'version': version}, 17)
        cmd = f'tar -xf "{tarball}"'
        result = run_command(cmd, cwd=self._build_dir)
        
        if result.returncode != 0:
            self._report_progress(_("Extraction error: %(error)s") % {'error': result.stderr}, -1)
            return False
            
        # 3. Verify extraction
        if not os.path.exists(os.path.join(source_dir, "Makefile")):
            self._report_progress(_("Error: Extraction failed (Makefile not found in %s)") % source_dir, -1)
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
        
        # Make scripts/config executable
        run_command("chmod +x scripts/config", cwd=source_dir)
        
        # Use scripts/config instead of sed (much more robust)
        run_command(f"./scripts/config --set-str LOCALVERSION \"{full_tag}\"", cwd=source_dir)
        
        # 4. Disable system trusted keys that cause build failure on Debian/Ubuntu
        # Force it with sed first, then scripts/config to be extra sure
        run_command("sed -i 's/CONFIG_SYSTEM_TRUSTED_KEYS=.*/CONFIG_SYSTEM_TRUSTED_KEYS=\"\"/' .config", cwd=source_dir)
        run_command("sed -i 's/CONFIG_SYSTEM_REVOCATION_KEYS=.*/CONFIG_SYSTEM_REVOCATION_KEYS=\"\"/' .config", cwd=source_dir)
        run_command("./scripts/config --set-str SYSTEM_TRUSTED_KEYS \"\"", cwd=source_dir)
        run_command("./scripts/config --set-str SYSTEM_REVOCATION_KEYS \"\"", cwd=source_dir)
        
        # 5. Disable DEBUG_INFO_BTF to avoid pahole errors
        run_command("sed -i 's/CONFIG_DEBUG_INFO_BTF=y/CONFIG_DEBUG_INFO_BTF=n/' .config", cwd=source_dir)
        run_command("./scripts/config --disable DEBUG_INFO_BTF", cwd=source_dir)
        
        # 6. Disable module signing to avoid cert issues
        run_command("./scripts/config --disable MODULE_SIG", cwd=source_dir)
        
        # Verbose verification for debugging
        print("\n--- DEBUG: Kernel Config Patch State ---", file=sys.stderr)
        for flag in ['CONFIG_SYSTEM_TRUSTED_KEYS', 'CONFIG_SYSTEM_REVOCATION_KEYS', 'CONFIG_DEBUG_INFO_BTF', 'CONFIG_MODULE_SIG']:
            check = run_command(f"grep {flag} .config", cwd=source_dir)
            print(f"DEBUG: {check.stdout.strip() or flag + ' is NOT SET'}", file=sys.stderr)
        print("---------------------------------------\n", file=sys.stderr)
        
        self._report_progress(_("Running make olddefconfig..."), 28)
        
        # Run olddefconfig (non-interactive)
        cmd = 'make olddefconfig'
        result = run_command_with_callback(cmd, cwd=source_dir)
        
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
            # Ensure we have a clean environment and use standard bindeb-pkg
            cmd = f'make -j{cpu_count} bindeb-pkg'
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
        
        exit_code = run_command_with_callback(cmd, cwd=source_dir, 
                                            line_callback=line_callback,
                                            stop_check=self._is_cancelled)
        
        if self._is_cancelled():
            self._report_progress(_("Build cancelled by user."), -1)
            self.cleanup_build_files()
            return False
        
        if exit_code != 0:
            error_msg = _("Build error (Exit code: %(code)d)") % {'code': exit_code}
            self._report_progress(error_msg, -1)
            # Try to report some relevant error lines
            self._report_progress(_("Check the terminal output for details or try installing missing dependencies and rebuilding."), -1)
            return False
        
        # For Arch, also build modules
        if distro_info.family == DistroFamily.ARCH:
            self._report_progress(_("Compiling modules..."), 85)
            cmd = f'make -j{cpu_count} modules'
            exit_code = run_command_with_callback(cmd, cwd=source_dir, 
                                                line_callback=line_callback,
                                                stop_check=self._is_cancelled)
                                                
            if self._is_cancelled():
                return False
                
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
        custom = getattr(self, '_custom_name', 'custom')
        full_tag = f"-{custom}-{profile.suffix}"
        source_dir = os.path.join(self._build_dir, f"linux-{version}")
        kernel_version = f"{version}{full_tag}"
        
        cmds = []
        
        if distro_info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU):
            self._report_progress(_("Preparing .deb packages installation..."), 93)
            cmds.append(f'dpkg -i {self._build_dir}/linux-image-{version}*.deb')
            cmds.append(f'dpkg -i {self._build_dir}/linux-headers-{version}*.deb 2>/dev/null || true')
            
        elif distro_info.family == DistroFamily.FEDORA:
            self._report_progress(_("Preparing RPM packages installation..."), 93)
            rpm_path = os.path.expanduser("~/rpmbuild/RPMS/x86_64/")
            cmds.append(f'rpm -ivh {rpm_path}kernel-{version}*.rpm')
                
        elif distro_info.family == DistroFamily.ARCH:
            self._report_progress(_("Preparing direct installation..."), 93)
            cmds.append(f'cd {source_dir} && make modules_install')
            cmds.append(f'cd {source_dir} && make install')
        
        # Regenerate initramfs
        initramfs_cmd = self._distro.get_initramfs_update_command(kernel_version)
        cmds.append(initramfs_cmd)
        
        # Update bootloader
        bootloader_cmd = self._distro.get_bootloader_update_command()
        cmds.append(bootloader_cmd)
        
        # Combine all commands into a single privileged call
        self._report_progress(_("Finalizing installation (may require password)..."), 95)
        full_cmd = " && ".join(cmds)
        result = run_privileged(full_cmd)
        
        if result.returncode != 0:
            self._report_progress(_("Installation error: %(error)s") % {'error': result.stderr or result.stdout}, -1)
            return False
        
        # Save to history
        self._save_to_history(version, profile)
        
        self._report_progress(_("Installation complete!"), 100)
        return True
    
    def full_install(self, version: str, profile: KernelProfile, custom_name: str = "", cleanup: bool = False) -> bool:
        """
        Perform full kernel installation: download, configure, build, install.
        
        Args:
            version: Kernel version
            profile: KernelProfile to use
            custom_name: Custom name/suffix for the kernel
            cleanup: Whether to remove build files after success
            
        Returns:
            True if all steps successful
        """
        # Store custom name for use in configure and install
        self._custom_name = custom_name or "custom"
        self._cancel_requested = False
        
        if not self.download_kernel(version):
            return False
        
        if self._is_cancelled():
            return False
        
        if not self.configure_kernel(version, profile):
            return False
            
        if self._is_cancelled():
            return False
        
        if not self.build_kernel(version):
            return False
            
        if self._is_cancelled():
            return False
        
        if not self.install_kernel(version, profile):
            return False
            
        if cleanup:
            self._report_progress(_("Cleaning up build files..."), 100)
            self.cleanup_build_files()
        
        return True
    
    def _get_history_path(self) -> str:
        """Get path to history file."""
        return os.path.join(Path.home(), self.HISTORY_FILE)
    
    def _save_to_history(self, version: str, profile: KernelProfile) -> None:
        """Save installation to history."""
        history = self.get_installation_history()
        
        custom = getattr(self, '_custom_name', 'custom')
        full_version = f"{version}-{custom}-{profile.suffix}"
        
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

    def remove_kernel(self, kernel_version: str) -> bool:
        """
        Remove an installed kernel from the system.
        
        Args:
            kernel_version: Full version string (e.g. 6.13.0-custom-minimal)
            
        Returns:
            True if successful
        """
        self._report_progress(_("Removing kernel %(version)s...") % {'version': kernel_version}, 0)
        
        # 1. Get remove command
        remove_cmd = self._distro.get_kernel_remove_command(kernel_version)
        self._report_progress(_("Uninstalling packages/files..."), 20)
        
        result = run_privileged(remove_cmd)
        if result.returncode != 0:
            self._report_progress(_("Error removing kernel: %(error)s") % {'error': result.stderr}, -1)
            return False
            
        # 2. Update bootloader
        self._report_progress(_("Updating bootloader..."), 60)
        bootloader_cmd = self._distro.get_bootloader_update_command()
        result = run_privileged(bootloader_cmd)
        
        if result.returncode != 0:
            self._report_progress(_("Warning: Error updating bootloader during removal"), -1)
            
        # 3. Remove from history
        self._report_progress(_("Updating history..."), 90)
        history = self.get_installation_history()
        updated_history = [k for k in history if k.version != kernel_version]
        
        # Save updated history
        try:
            with open(self._get_history_path(), 'w') as f:
                json.dump([
                    {
                        'version': k.version,
                        'profile': k.profile,
                        'installed_date': k.installed_date
                    }
                    for k in updated_history
                ], f, indent=2)
        except Exception as e:
            print(f"Error updating history after removal: {e}")
            
        self._report_progress(_("Kernel removed successfully."), 100)
        return True
