"""
System notifications for Kernel Installer GUI.
Uses Gio.Notification for desktop notifications.
"""

import gi
gi.require_version('Gio', '2.0')
from gi.repository import Gio, GLib
from ..locale.i18n import _


class NotificationManager:
    """
    Manages desktop notifications for the Kernel Installer.
    
    Uses GNotification for cross-desktop compatibility.
    """
    
    def __init__(self, application: Gio.Application = None):
        """
        Initialize the notification manager.
        
        Args:
            application: The GtkApplication instance (required for notifications)
        """
        self._app = application
    
    def set_application(self, application: Gio.Application) -> None:
        """Set the application instance after initialization."""
        self._app = application
    
    def send(self, title: str, body: str, icon: str = "dialog-information",
             priority: str = "normal") -> None:
        """
        Send a desktop notification.
        
        Args:
            title: Notification title
            body: Notification body text
            icon: Icon name (from icon theme)
            priority: 'low', 'normal', 'high', or 'urgent'
        """
        if not self._app:
            print(f"[Notification] {title}: {body}")
            return
        
        notification = Gio.Notification.new(title)
        notification.set_body(body)
        notification.set_icon(Gio.ThemedIcon.new(icon))
        
        # Set priority
        priority_map = {
            'low': Gio.NotificationPriority.LOW,
            'normal': Gio.NotificationPriority.NORMAL,
            'high': Gio.NotificationPriority.HIGH,
            'urgent': Gio.NotificationPriority.URGENT,
        }
        notification.set_priority(priority_map.get(priority, Gio.NotificationPriority.NORMAL))
        
        self._app.send_notification(None, notification)
    
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
                priority="high"
            )
        else:
            self.send(
                title=_("Build error"),
                body=_("Compilation of Linux %(version)s has failed.") % {'version': version},
                icon="dialog-error",
                priority="urgent"
            )
    
    def notify_reboot_required(self) -> None:
        """Notify that a reboot is required."""
        self.send(
            title=_("Reboot required"),
            body=_("Reboot the system to use the new kernel."),
            icon="system-reboot",
            priority="high"
        )


# Global notification manager instance
_notification_manager = None


def get_notification_manager() -> NotificationManager:
    """Get the global notification manager instance."""
    global _notification_manager
    if _notification_manager is None:
        _notification_manager = NotificationManager()
    return _notification_manager
