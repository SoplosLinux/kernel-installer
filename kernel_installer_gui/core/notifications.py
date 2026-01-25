"""
System notifications for Kernel Installer GUI.
Uses libnotify for transient desktop notifications.
"""

import gi
gi.require_version('Notify', '0.7')
from gi.repository import Notify, GLib
from ..locale.i18n import _


class NotificationManager:
    """
    Manages desktop notifications for the Kernel Installer.
    
    Uses libnotify to ensure notifications are transient and disappear automatically.
    """
    
    def __init__(self, application=None):
        """
        Initialize the notification manager.
        """
        self._initialized = False
        # libnotify doesn't strictly need the app instance for simple notifications,
        # but we keep the structure for compatibility.
        self._app = application
        try:
            self._initialized = Notify.init("kernel-installer")
        except Exception as e:
            print(f"Failed to initialize libnotify: {e}")
    
    def set_application(self, application) -> None:
        """Set the application instance."""
        self._app = application
    
    def send(self, title: str, body: str, icon: str = "kernel-installer",
             priority: str = "normal") -> None:
        """
        Send a transient desktop notification using libnotify.
        
        Args:
            title: Notification title
            body: Notification body text
            icon: Icon name
            priority: 'low', 'normal', 'high'
        """
        if not self._initialized:
            print(f"[Notification] {title}: {body}")
            return
        
        # Priority mapping for Notify
        urgency_map = {
            'low': Notify.Urgency.LOW,
            'normal': Notify.Urgency.NORMAL,
            'high': Notify.Urgency.CRITICAL,
        }
        
        notification = Notify.Notification.new(title, body, icon)
        notification.set_urgency(urgency_map.get(priority, Notify.Urgency.NORMAL))
        
        # Set timeout to ensure it disappears (milliseconds)
        # Most notification servers ignore this and use their own defaults for normal/low,
        # but specifying it helps in some environments.
        notification.set_timeout(5000) 
        
        try:
            notification.show()
        except Exception as e:
            print(f"Error showing notification: {e}")
    
    def notify_new_kernel_available(self, version: str) -> None:
        """Notify that a new kernel version is available."""
        self.send(
            title=_("New kernel version available"),
            body=_("Linux %(version)s is available for download.") % {'version': version},
            icon="software-update-available",
            priority="normal"
        )
    
    def notify_download_complete(self, version: str) -> None:
        """Notify that kernel download is complete."""
        self.send(
            title=_("Download complete"),
            body=_("Linux %(version)s has been downloaded successfully.") % {'version': version},
            icon="emblem-downloads",
            priority="low"
        )
    
    def notify_build_complete(self, version: str, success: bool) -> None:
        """Notify that kernel build is complete."""
        if success:
            self.send(
                title=_("Build complete"),
                body=_("Linux %(version)s has been compiled and installed successfully.") % {'version': version},
                icon="emblem-ok-symbolic",
                priority="normal"
            )
        else:
            self.send(
                title=_("Build error"),
                body=_("Compilation of Linux %(version)s has failed.") % {'version': version},
                icon="dialog-error",
                priority="high"
            )
    
    def notify_reboot_required(self) -> None:
        """Notify that a reboot is required."""
        self.send(
            title=_("Reboot required"),
            body=_("Reboot the system to use the new kernel."),
            icon="system-reboot",
            priority="normal"
        )



# Global notification manager instance
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
