"""
Distribution detection for Kernel Installer GUI.
Identifies the Linux distribution, bootloader, and initramfs tools.
"""

import os
import shutil
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional
from ..locale.i18n import _


class DistroFamily(Enum):
    """Linux distribution families."""
    DEBIAN = auto()      # Pure Debian and direct derivatives
    UBUNTU = auto()      # Ubuntu and derivatives (Mint, Elementary, Pop)
    FEDORA = auto()      # Fedora, RHEL, CentOS, Rocky, Alma
    ARCH = auto()        # Arch and derivatives
    UNKNOWN = auto()


class Bootloader(Enum):
    """Supported bootloaders."""
    GRUB = auto()           # GRUB2 (most common)
    SYSTEMD_BOOT = auto()   # systemd-boot (gummiboot)
    REFIND = auto()         # rEFInd
    LILO = auto()           # LILO (legacy)
    SYSLINUX = auto()       # Syslinux/Extlinux
    UNKNOWN = auto()


class InitramfsTool(Enum):
    """Initramfs generation tools."""
    INITRAMFS_TOOLS = auto()  # Debian/Ubuntu default
    DRACUT = auto()           # Fedora, RHEL, some Debian
    MKINITCPIO = auto()       # Arch Linux
    UNKNOWN = auto()


@dataclass
class DistroInfo:
    """Information about the detected distribution."""
    id: str
    name: str
    version: str
    family: DistroFamily
    pretty_name: str


@dataclass
class SystemInfo:
    """Complete system information including bootloader and initramfs."""
    distro: DistroInfo
    bootloader: Bootloader
    initramfs_tool: InitramfsTool


# Mapping of distribution IDs to their families
DISTRO_MAP = {
    # Debian family
    'debian': DistroFamily.DEBIAN,
    'devuan': DistroFamily.DEBIAN,
    'mx': DistroFamily.DEBIAN,
    'antix': DistroFamily.DEBIAN,
    'goldendoglinux': DistroFamily.DEBIAN,
    'soplos': DistroFamily.DEBIAN,
    'quirinux': DistroFamily.DEBIAN,
    'etertics': DistroFamily.DEBIAN,
    'goblin': DistroFamily.DEBIAN,
    'gobmis': DistroFamily.DEBIAN,
    'huayra': DistroFamily.DEBIAN,
    
    # Ubuntu/Mint family (need special handling for Secure Boot)
    'ubuntu': DistroFamily.UBUNTU,
    'linuxmint': DistroFamily.UBUNTU,
    'lmde': DistroFamily.DEBIAN,  # LMDE is Debian-based
    'elementary': DistroFamily.UBUNTU,
    'pop': DistroFamily.UBUNTU,
    'zorin': DistroFamily.UBUNTU,
    'neon': DistroFamily.UBUNTU,
    
    # Fedora family
    'fedora': DistroFamily.FEDORA,
    'rhel': DistroFamily.FEDORA,
    'centos': DistroFamily.FEDORA,
    'rocky': DistroFamily.FEDORA,
    'almalinux': DistroFamily.FEDORA,
    'oracle': DistroFamily.FEDORA,
    
    # Arch family
    'arch': DistroFamily.ARCH,
    'manjaro': DistroFamily.ARCH,
    'endeavouros': DistroFamily.ARCH,
    'garuda': DistroFamily.ARCH,
}


class DistroDetector:
    """Detects and provides information about the current Linux distribution."""
    
    def __init__(self):
        self._info: Optional[DistroInfo] = None
        self._bootloader: Optional[Bootloader] = None
        self._initramfs: Optional[InitramfsTool] = None
    
    def detect(self) -> DistroInfo:
        """
        Detect the current Linux distribution.
        
        Returns:
            DistroInfo with distribution details
        """
        if self._info is not None:
            return self._info
        
        os_release = self._parse_os_release()
        
        distro_id = os_release.get('ID', 'unknown').lower()
        distro_name = os_release.get('NAME', 'Unknown')
        distro_version = os_release.get('VERSION_ID', '')
        pretty_name = os_release.get('PRETTY_NAME', distro_name)
        
        # Determine family
        family = DISTRO_MAP.get(distro_id, DistroFamily.UNKNOWN)
        
        # If not found, check ID_LIKE for parent distro
        if family == DistroFamily.UNKNOWN:
            id_like = os_release.get('ID_LIKE', '').lower().split()
            for parent_id in id_like:
                if parent_id in DISTRO_MAP:
                    family = DISTRO_MAP[parent_id]
                    break
        
        self._info = DistroInfo(
            id=distro_id,
            name=distro_name,
            version=distro_version,
            family=family,
            pretty_name=pretty_name
        )
        
        return self._info
    
    def detect_bootloader(self) -> Bootloader:
        """
        Detect the installed bootloader.
        
        Returns:
            Bootloader enum value
        """
        if self._bootloader is not None:
            return self._bootloader
        
        # Check for systemd-boot first (most specific)
        if os.path.exists('/boot/efi/EFI/systemd/systemd-bootx64.efi'):
            self._bootloader = Bootloader.SYSTEMD_BOOT
        elif os.path.exists('/boot/efi/EFI/BOOT/BOOTX64.EFI') and \
             os.path.exists('/boot/loader/loader.conf'):
            self._bootloader = Bootloader.SYSTEMD_BOOT
        # Check for rEFInd
        elif os.path.exists('/boot/efi/EFI/refind'):
            self._bootloader = Bootloader.REFIND
        elif shutil.which('refind-install'):
            if os.path.exists('/boot/refind_linux.conf'):
                self._bootloader = Bootloader.REFIND
        # Check for GRUB2 (most common)
        elif os.path.exists('/boot/grub/grub.cfg') or \
             os.path.exists('/boot/grub2/grub.cfg') or \
             os.path.exists('/etc/default/grub'):
            self._bootloader = Bootloader.GRUB
        # Check for syslinux/extlinux
        elif os.path.exists('/boot/syslinux') or \
             os.path.exists('/boot/extlinux'):
            self._bootloader = Bootloader.SYSLINUX
        # Check for LILO (legacy)
        elif os.path.exists('/etc/lilo.conf'):
            self._bootloader = Bootloader.LILO
        else:
            # Default to GRUB as most common
            self._bootloader = Bootloader.GRUB
        
        return self._bootloader
    
    def detect_initramfs_tool(self) -> InitramfsTool:
        """
        Detect the initramfs generation tool.
        
        Returns:
            InitramfsTool enum value
        """
        if self._initramfs is not None:
            return self._initramfs
        
        # Check for dracut (Fedora, some Debian)
        if shutil.which('dracut'):
            # Verify it's actually used (not just installed)
            if os.path.exists('/etc/dracut.conf') or \
               os.path.exists('/etc/dracut.conf.d'):
                self._initramfs = InitramfsTool.DRACUT
            # Also check if initramfs images are dracut-generated
            elif self._check_dracut_initramfs():
                self._initramfs = InitramfsTool.DRACUT
        
        # Check for mkinitcpio (Arch)
        if self._initramfs is None and shutil.which('mkinitcpio'):
            if os.path.exists('/etc/mkinitcpio.conf'):
                self._initramfs = InitramfsTool.MKINITCPIO
        
        # Check for initramfs-tools (Debian/Ubuntu default)
        if self._initramfs is None and shutil.which('update-initramfs'):
            if os.path.exists('/etc/initramfs-tools'):
                self._initramfs = InitramfsTool.INITRAMFS_TOOLS
        
        # Fallback based on distro family
        if self._initramfs is None:
            info = self.detect()
            if info.family == DistroFamily.ARCH:
                self._initramfs = InitramfsTool.MKINITCPIO
            elif info.family == DistroFamily.FEDORA:
                self._initramfs = InitramfsTool.DRACUT
            else:
                self._initramfs = InitramfsTool.INITRAMFS_TOOLS
        
        return self._initramfs
    
    def _check_dracut_initramfs(self) -> bool:
        """Check if current initramfs was generated by dracut."""
        try:
            # Check for dracut marker in initramfs
            import subprocess
            result = subprocess.run(
                ['lsinitrd', '--list-modules'],
                capture_output=True, text=True
            )
            return result.returncode == 0
        except Exception:
            return False
    
    def get_full_system_info(self) -> SystemInfo:
        """Get complete system information."""
        return SystemInfo(
            distro=self.detect(),
            bootloader=self.detect_bootloader(),
            initramfs_tool=self.detect_initramfs_tool()
        )
    
    def _parse_os_release(self) -> dict:
        """Parse /etc/os-release file."""
        result = {}
        
        for path in ['/etc/os-release', '/usr/lib/os-release']:
            if os.path.exists(path):
                try:
                    with open(path, 'r') as f:
                        for line in f:
                            line = line.strip()
                            if '=' in line:
                                key, value = line.split('=', 1)
                                # Remove quotes
                                value = value.strip('"\'')
                                result[key] = value
                    break
                except Exception:
                    continue
        
        return result
    
    def get_package_manager(self) -> str:
        """Get the package manager command for this distro."""
        info = self.detect()
        
        if info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU):
            return 'apt'
        elif info.family == DistroFamily.FEDORA:
            return 'dnf'
        elif info.family == DistroFamily.ARCH:
            return 'pacman'
        else:
            return 'apt'  # Default fallback
    
    def get_install_command(self, packages: list[str]) -> str:
        """Get the command to install packages."""
        info = self.detect()
        pkg_list = ' '.join(packages)
        
        if info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU):
            return f'apt install -y {pkg_list}'
        elif info.family == DistroFamily.FEDORA:
            return f'dnf install -y {pkg_list}'
        elif info.family == DistroFamily.ARCH:
            return f'pacman -S --noconfirm {pkg_list}'
        else:
            return f'apt install -y {pkg_list}'
    
    def get_bootloader_update_command(self) -> str:
        """Get the command to update the bootloader based on detected bootloader."""
        bootloader = self.detect_bootloader()
        
        if bootloader == Bootloader.GRUB:
            # Check for different GRUB paths
            if os.path.exists('/boot/grub2/grub.cfg'):
                return 'grub2-mkconfig -o /boot/grub2/grub.cfg'
            else:
                return 'update-grub'
        elif bootloader == Bootloader.SYSTEMD_BOOT:
            return 'bootctl update'
        elif bootloader == Bootloader.REFIND:
            return 'refind-mkconfig'
        elif bootloader == Bootloader.LILO:
            return 'lilo'
        elif bootloader == Bootloader.SYSLINUX:
            return 'extlinux-update'
        else:
            return 'update-grub'  # Default fallback
    
    def get_initramfs_update_command(self, kernel_version: str = None) -> str:
        """
        Get the command to regenerate initramfs.
        
        Args:
            kernel_version: Specific kernel version, or None for all
        """
        initramfs = self.detect_initramfs_tool()
        
        if initramfs == InitramfsTool.DRACUT:
            if kernel_version:
                return f'dracut --force /boot/initramfs-{kernel_version}.img {kernel_version}'
            else:
                return 'dracut --regenerate-all --force'
        elif initramfs == InitramfsTool.MKINITCPIO:
            if kernel_version:
                return f'mkinitcpio -k {kernel_version} -g /boot/initramfs-{kernel_version}.img'
            else:
                return 'mkinitcpio -P'
        elif initramfs == InitramfsTool.INITRAMFS_TOOLS:
            if kernel_version:
                return f'update-initramfs -c -k {kernel_version}'
            else:
                return 'update-initramfs -u -k all'
        else:
            return 'update-initramfs -u'
    
    def needs_secure_boot_handling(self) -> bool:
        """Check if this distro needs special Secure Boot certificate handling."""
        info = self.detect()
        return info.family == DistroFamily.UBUNTU
    
    def is_supported(self) -> bool:
        """Check if this distribution is supported."""
        info = self.detect()
        return info.family in (DistroFamily.DEBIAN, DistroFamily.UBUNTU, DistroFamily.FEDORA, DistroFamily.ARCH)
    
    def get_bootloader_name(self) -> str:
        """Get human-readable bootloader name."""
        bootloader = self.detect_bootloader()
        names = {
            Bootloader.GRUB: "GRUB2",
            Bootloader.SYSTEMD_BOOT: "systemd-boot",
            Bootloader.REFIND: "rEFInd",
            Bootloader.LILO: "LILO",
            Bootloader.SYSLINUX: "Syslinux",
            Bootloader.UNKNOWN: _("Unknown")
        }
        return names.get(bootloader, _("Unknown"))
    
    def get_initramfs_name(self) -> str:
        """Get human-readable initramfs tool name."""
        initramfs = self.detect_initramfs_tool()
        names = {
            InitramfsTool.INITRAMFS_TOOLS: "initramfs-tools",
            InitramfsTool.DRACUT: "dracut",
            InitramfsTool.MKINITCPIO: "mkinitcpio",
            InitramfsTool.UNKNOWN: _("Unknown")
        }
        return names.get(initramfs, _("Unknown"))
