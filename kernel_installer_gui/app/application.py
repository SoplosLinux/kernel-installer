"""
GTK Application class for Kernel Installer.
Handles application lifecycle, theme detection, and CSS loading.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, Gdk, Gio, GLib

import os
from pathlib import Path

from .main_window import KernelInstallerWindow
from ..core.notifications import get_notification_manager
from ..core.kernel import KernelManager
from ..locale.i18n import _


class KernelInstallerApp(Gtk.Application):
    """Main GTK Application for Kernel Installer."""
    
    APP_ID = "org.soploslinux.kernelinstaller"
    
    def __init__(self):
        super().__init__(
            application_id=self.APP_ID,
            flags=Gio.ApplicationFlags.FLAGS_NONE
        )
        
        self._window = None
        self._kernel_manager = KernelManager()
    
    def do_startup(self) -> None:
        """Called when application starts."""
        Gtk.Application.do_startup(self)
        
        # Load CSS
        self._load_css()
        
        # Setup actions first
        self._setup_actions()
        
        # Setup keyboard shortcuts after actions
        self._setup_accelerators()
        
        # Setup notification manager
        notifier = get_notification_manager()
        notifier.set_application(self)
    
    def do_activate(self) -> None:
        """Called when application is activated."""
        if not self._window:
            self._window = KernelInstallerWindow(self)
            # Connect key press event for shortcuts
            self._window.connect('key-press-event', self._on_key_press)
        
        self._window.present()
    
    def _on_key_press(self, widget, event) -> bool:
        """Handle key press events for shortcuts."""
        keyval = event.keyval
        state = event.state & Gtk.accelerator_get_default_mod_mask()
        
        # Ctrl+Q or Ctrl+W to quit
        if state == Gdk.ModifierType.CONTROL_MASK:
            if keyval in (Gdk.KEY_q, Gdk.KEY_Q, Gdk.KEY_w, Gdk.KEY_W):
                self.quit()
                return True
        
        # F5 to refresh
        if keyval == Gdk.KEY_F5:
            if self._window:
                self._window.refresh_versions()
            return True
        
        # Escape to close dialogs or go back
        if keyval == Gdk.KEY_Escape:
            # Could be used for canceling
            pass
        
        return False
    
    def _setup_accelerators(self) -> None:
        """Setup keyboard shortcuts."""
        # These are for menu display, actual handling is in _on_key_press
        self.set_accels_for_action("app.quit", ["<Control>q", "<Control>w"])
        self.set_accels_for_action("app.refresh", ["F5"])
    
    def _load_css(self) -> None:
        """Load and apply CSS styles."""
        css_provider = Gtk.CssProvider()
        
        # Try to load from package data directory
        css_paths = [
            Path(__file__).parent.parent / "data" / "style.css",
            Path("/usr/share/kernel-installer/style.css"),
            Path.home() / ".config" / "kernel-installer" / "style.css",
        ]
        
        css_content = self._get_default_css()
        
        for path in css_paths:
            if path.exists():
                try:
                    css_provider.load_from_path(str(path))
                    css_content = None
                    break
                except Exception:
                    continue
        
        if css_content:
            css_provider.load_from_data(css_content.encode())
        
        # Apply to screen
        screen = Gdk.Screen.get_default()
        Gtk.StyleContext.add_provider_for_screen(
            screen,
            css_provider,
            Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
        )
    
    def _get_default_css(self) -> str:
        """Get default CSS styles that adapt to light/dark themes."""
        return '''
/* Kernel Installer GUI Styles */
/* Uses GTK3 theme variables for automatic light/dark adaptation */

/* Profile Cards */
.profile-card {
    padding: 12px;
    border-radius: 12px;
    border: 2px solid alpha(@theme_fg_color, 0.1);
    background: alpha(@theme_bg_color, 0.5);
    transition: all 200ms ease;
    min-width: 160px;
}

.profile-card:hover {
    border-color: alpha(@theme_selected_bg_color, 0.5);
    background: alpha(@theme_selected_bg_color, 0.1);
}

.profile-card:checked {
    border-color: @theme_selected_bg_color;
    background: alpha(@theme_selected_bg_color, 0.15);
    box-shadow: 0 0 0 3px alpha(@theme_selected_bg_color, 0.2);
}

.profile-name {
    font-weight: bold;
    font-size: 1.1em;
}

.profile-description {
    font-size: 0.9em;
    opacity: 0.8;
}

/* Section Headers */
.section-header {
    font-weight: bold;
    font-size: 1.05em;
    opacity: 0.9;
}

/* Install Button */
.install-button {
    padding: 12px 24px;
    font-size: 1.1em;
    font-weight: bold;
    border-radius: 8px;
}

/* History List */
.history-list {
    background: transparent;
}

.history-list row {
    border-radius: 6px;
    margin: 2px 0;
}

.history-list row:hover {
    background: alpha(@theme_fg_color, 0.05);
}

.current-kernel {
    font-weight: bold;
}

.profile-badge {
    padding: 2px 8px;
    border-radius: 4px;
    font-size: 0.85em;
    background: alpha(@theme_selected_bg_color, 0.2);
}

/* Load Indicator */
.load-percentage {
    font-size: 1.5em;
    font-weight: bold;
}

/* Level Bar Colors */
levelbar block.low {
    background-color: #4caf50;
}

levelbar block.high {
    background-color: #ff9800;
}

levelbar block.full {
    background-color: #f44336;
}

/* Dim Labels */
.dim-label {
    opacity: 0.7;
    font-size: 0.9em;
}

/* Error Text */
.error {
    color: #f44336;
}

/* Progress Bar */
progressbar progress {
    border-radius: 4px;
}

progressbar trough {
    border-radius: 4px;
}
'''
    
    def _setup_actions(self) -> None:
        """Setup application actions for menu."""
        # Quit action
        quit_action = Gio.SimpleAction.new("quit", None)
        quit_action.connect("activate", self._on_quit)
        self.add_action(quit_action)
        
        # Refresh action
        refresh_action = Gio.SimpleAction.new("refresh", None)
        refresh_action.connect("activate", self._on_refresh)
        self.add_action(refresh_action)
        
        # About action
        about_action = Gio.SimpleAction.new("about", None)
        about_action.connect("activate", self._on_about)
        self.add_action(about_action)
        
        # Cleanup action
        cleanup_action = Gio.SimpleAction.new("cleanup", None)
        cleanup_action.connect("activate", self._on_cleanup)
        self.add_action(cleanup_action)
    
    def _on_quit(self, action: Gio.SimpleAction, param) -> None:
        """Quit the application."""
        self.quit()
    
    def _on_refresh(self, action: Gio.SimpleAction, param) -> None:
        """Refresh kernel versions."""
        if self._window:
            self._window.refresh_versions()
    
    def _on_about(self, action: Gio.SimpleAction, param) -> None:
        """Show about dialog."""
        about = Gtk.AboutDialog(transient_for=self._window, modal=True)
        about.set_program_name(_("Kernel Installer"))
        about.set_version("1.0.0")
        about.set_comments(
            _("A graphical interface for downloading, compiling and installing the Linux kernel with optimized profiles.")
        )
        about.set_authors([
            "Sergi Perich <info@soploslinux.com>",
            "Alexia Michelle <alexia@goldendoglinux.org>"
        ])
        about.set_copyright("© 2025 Sergi Perich & Alexia Michelle")
        about.set_license_type(Gtk.License.GPL_3_0)
        about.set_website("https://github.com/SoplosLinux/kernell-installer")
        about.set_website_label("GitHub")
        about.set_logo_icon_name("kernel-installer")
        
        about.run()
        about.destroy()
    
    def _on_cleanup(self, action: Gio.SimpleAction, param) -> None:
        """Clean up build files."""
        dialog = Gtk.MessageDialog(
            transient_for=self._window,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Clean build files?")
        )
        dialog.format_secondary_text(
            _("All temporary files in ~/kernel_build will be deleted.\n"
            "This will free up disk space.")
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            if self._kernel_manager.cleanup_build_files():
                self._show_info(_("Build files deleted."))
            else:
                self._show_error(_("Error cleaning files."))
    
    def _show_info(self, message: str) -> None:
        """Show info dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self._window,
            modal=True,
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
    
    def _show_error(self, message: str) -> None:
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self._window,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=message
        )
        dialog.run()
        dialog.destroy()
