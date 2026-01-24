"""Core subpackage for Kernel Installer GUI - business logic."""

from .distro import DistroDetector
from .kernel import KernelManager
from .profiles import KernelProfile, KERNEL_PROFILES
from .notifications import NotificationManager

__all__ = ['DistroDetector', 'KernelManager', 'KernelProfile', 'KERNEL_PROFILES', 'NotificationManager']
