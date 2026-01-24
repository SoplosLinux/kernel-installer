"""
Main application window for Kernel Installer GUI.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Gio

from ..widgets.profile_selector import ProfileSelector
from ..widgets.version_picker import VersionPicker
from ..widgets.build_progress import BuildProgress
from ..widgets.history_view import HistoryView
from ..core.kernel import KernelManager
from ..core.distro import DistroDetector
from ..core.profiles import KernelProfile
from ..core.notifications import get_notification_manager
from ..locale.i18n import _

import threading


class KernelInstallerWindow(Gtk.ApplicationWindow):
    """Main window for the Kernel Installer application."""
    
    def __init__(self, application: Gtk.Application):
        super().__init__(application=application)
        
        self.set_title("Kernel Installer")
        self.set_default_size(700, 600)
        self.set_position(Gtk.WindowPosition.CENTER)
        self.set_icon_name("kernel-installer")
        
        # Initialize managers
        self._kernel_manager = KernelManager()
        self._distro = DistroDetector()
        self._building = False
        
        # Header bar
        self._create_header_bar()
        
        # Main content
        self._create_content()
        
        # Load initial data
        GLib.idle_add(self._load_initial_data)
    
    def _create_header_bar(self) -> None:
        """Create the header bar with title and actions."""
        header = Gtk.HeaderBar()
        header.set_show_close_button(True)
        header.set_title(_("Kernel Installer"))
        header.set_subtitle(_("by Sergi Perich & Alexia Michelle"))
        
        # App icon managed by window icon setting
        
        # Menu button
        menu_btn = Gtk.MenuButton()
        menu_icon = Gtk.Image.new_from_icon_name("open-menu-symbolic", Gtk.IconSize.BUTTON)
        menu_btn.set_image(menu_icon)
        
        # Create menu
        menu = Gio.Menu()
        menu.append(_("Refresh versions (F5)"), "app.refresh")
        menu.append(_("Clean build files"), "app.cleanup")
        menu.append(_("About"), "app.about")
        menu.append(_("Quit (Ctrl+Q)"), "app.quit")
        menu_btn.set_menu_model(menu)
        
        header.pack_end(menu_btn)
        
        self.set_titlebar(header)
    
    def _create_content(self) -> None:
        """Create the main content area."""
        # Main vertical box with margins
        main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        main_box.set_margin_top(16)
        main_box.set_margin_bottom(16)
        main_box.set_margin_start(24)
        main_box.set_margin_end(24)
        
        # Stack for switching between config and build views
        self._stack = Gtk.Stack()
        self._stack.set_transition_type(Gtk.StackTransitionType.SLIDE_LEFT_RIGHT)
        
        # === Config page ===
        config_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=16)
        
        # Profile selector
        self._profile_selector = ProfileSelector()
        self._profile_selector.connect('profile-changed', self._on_profile_changed)
        config_box.pack_start(self._profile_selector, False, False, 0)
        
        # Separator
        config_box.pack_start(Gtk.Separator(), False, False, 0)
        
        # Version picker
        self._version_picker = VersionPicker(self._kernel_manager)
        config_box.pack_start(self._version_picker, False, False, 0)
        
        # Kernel name entry
        name_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        name_label = Gtk.Label(label=_("Kernel name (suffix)"))
        name_label.set_halign(Gtk.Align.START)
        name_label.get_style_context().add_class('section-header')
        name_box.pack_start(name_label, False, False, 0)
        
        name_row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        self._kernel_name_entry = Gtk.Entry()
        self._kernel_name_entry.set_text("custom")
        self._kernel_name_entry.set_placeholder_text(_("E.g.: gaming, server, my-kernel"))
        self._kernel_name_entry.set_tooltip_text(_("This name will be added to the kernel, e.g.: 6.18.7-custom-gaming"))
        self._kernel_name_entry.set_hexpand(True)
        name_row.pack_start(self._kernel_name_entry, True, True, 0)
        name_box.pack_start(name_row, False, False, 0)
        
        name_hint = Gtk.Label(label=_("Result: 6.x.x-custom-gaming (combined with profile)"))
        name_hint.set_halign(Gtk.Align.START)
        name_hint.get_style_context().add_class('dim-label')
        self._name_hint_label = name_hint
        name_box.pack_start(name_hint, False, False, 0)
        
        # Update hint when name changes
        self._kernel_name_entry.connect('changed', self._on_kernel_name_changed)
        
        config_box.pack_start(name_box, False, False, 0)
        
        # Separator
        config_box.pack_start(Gtk.Separator(), False, False, 0)
        
        # System info - Row 1
        info_box1 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        # Distro info
        distro_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        distro_label = Gtk.Label(label=_("Distribution:"))
        distro_label.set_halign(Gtk.Align.START)
        distro_label.get_style_context().add_class('dim-label')
        distro_box.pack_start(distro_label, False, False, 0)
        
        self._distro_value = Gtk.Label(label=_("Detecting..."))
        self._distro_value.set_halign(Gtk.Align.START)
        distro_box.pack_start(self._distro_value, False, False, 0)
        info_box1.pack_start(distro_box, True, True, 0)
        
        # Current kernel
        kernel_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        kernel_label = Gtk.Label(label=_("Current kernel:"))
        kernel_label.set_halign(Gtk.Align.START)
        kernel_label.get_style_context().add_class('dim-label')
        kernel_box.pack_start(kernel_label, False, False, 0)
        
        self._kernel_value = Gtk.Label(label="...")
        self._kernel_value.set_halign(Gtk.Align.START)
        kernel_box.pack_start(self._kernel_value, False, False, 0)
        info_box1.pack_start(kernel_box, True, True, 0)
        
        config_box.pack_start(info_box1, False, False, 0)
        
        # System info - Row 2 (Bootloader and Initramfs)
        info_box2 = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        
        # Bootloader info
        bootloader_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        bootloader_label = Gtk.Label(label=_("Bootloader:"))
        bootloader_label.set_halign(Gtk.Align.START)
        bootloader_label.get_style_context().add_class('dim-label')
        bootloader_box.pack_start(bootloader_label, False, False, 0)
        
        self._bootloader_value = Gtk.Label(label="...")
        self._bootloader_value.set_halign(Gtk.Align.START)
        bootloader_box.pack_start(self._bootloader_value, False, False, 0)
        info_box2.pack_start(bootloader_box, True, True, 0)
        
        # Initramfs info
        initramfs_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        initramfs_label = Gtk.Label(label=_("Initramfs:"))
        initramfs_label.set_halign(Gtk.Align.START)
        initramfs_label.get_style_context().add_class('dim-label')
        initramfs_box.pack_start(initramfs_label, False, False, 0)
        
        self._initramfs_value = Gtk.Label(label="...")
        self._initramfs_value.set_halign(Gtk.Align.START)
        initramfs_box.pack_start(self._initramfs_value, False, False, 0)
        info_box2.pack_start(initramfs_box, True, True, 0)
        
        config_box.pack_start(info_box2, False, False, 0)
        
        # Install button
        self._install_btn = Gtk.Button(label=_("📥 Download and install kernel"))
        self._install_btn.get_style_context().add_class('suggested-action')
        self._install_btn.get_style_context().add_class('install-button')
        self._install_btn.connect('clicked', self._on_install_clicked)
        config_box.pack_start(self._install_btn, False, False, 8)
        
        # History
        self._history_view = HistoryView(self._kernel_manager)
        config_box.pack_start(self._history_view, False, False, 0)
        
        self._stack.add_named(config_box, "config")
        
        # === Build page ===
        build_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        self._build_progress = BuildProgress()
        build_box.pack_start(self._build_progress, True, True, 0)
        
        # Cancel button
        button_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL)
        button_box.set_halign(Gtk.Align.END)
        
        self._cancel_btn = Gtk.Button(label=_("Cancel"))
        self._cancel_btn.get_style_context().add_class('destructive-action')
        self._cancel_btn.connect('clicked', self._on_cancel_clicked)
        self._cancel_btn.set_sensitive(False)
        button_box.pack_start(self._cancel_btn, False, False, 0)
        
        self._done_btn = Gtk.Button(label=_("Done"))
        self._done_btn.connect('clicked', self._on_done_clicked)
        self._done_btn.set_no_show_all(True)
        button_box.pack_start(self._done_btn, False, False, 8)
        
        build_box.pack_start(button_box, False, False, 0)
        
        self._stack.add_named(build_box, "build")
        
        main_box.pack_start(self._stack, True, True, 0)
        self.add(main_box)
        self.show_all()
    
    def _load_initial_data(self) -> None:
        """Load initial data when window opens."""
        # Detect distro
        distro_info = self._distro.detect()
        self._distro_value.set_text(distro_info.pretty_name)
        
        # Check if supported
        if not self._distro.is_supported():
            self._show_unsupported_dialog(distro_info.pretty_name)
        
        # Get current kernel
        current = self._kernel_manager.get_current_kernel()
        self._kernel_value.set_text(current)
        
        # Detect bootloader and initramfs
        self._bootloader_value.set_text(self._distro.get_bootloader_name())
        self._initramfs_value.set_text(self._distro.get_initramfs_name())
        
        # Fetch available versions
        self._version_picker.refresh_versions()
        
        # Load history
        self._history_view.refresh()
    
    def _show_unsupported_dialog(self, distro_name: str) -> None:
        """Show dialog for unsupported distributions."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.WARNING,
            buttons=Gtk.ButtonsType.OK,
            text=_("Unsupported distribution")
        )
        dialog.format_secondary_text(
            _("%(distro)s is not officially supported. "
            "The program might not work correctly.") % {'distro': distro_name}
        )
        dialog.run()
        dialog.destroy()
    
    def _on_install_clicked(self, button: Gtk.Button) -> None:
        """Handle install button click."""
        version = self._version_picker.get_selected_version()
        profile = self._profile_selector.get_selected_profile()
        
        if not version:
            self._show_error(_("Please select a kernel version."))
            return
        
        # Confirm
        if not self._confirm_install(version, profile):
            return
        
        # Switch to build view
        self._stack.set_visible_child_name("build")
        self._build_progress.start_build()
        self._cancel_btn.set_sensitive(True)
        self._building = True
        
        # Set progress callback
        self._kernel_manager.set_progress_callback(self._on_build_progress)
        
        # Start build in thread
        custom_name = self.get_kernel_name()
        def build_thread():
            try:
                success = self._kernel_manager.full_install(version, profile, custom_name)
                GLib.idle_add(self._on_build_complete, success)
            except Exception as e:
                GLib.idle_add(self._on_build_error, str(e))
        
        thread = threading.Thread(target=build_thread, daemon=True)
        thread.start()
    
    def _confirm_install(self, version: str, profile: KernelProfile) -> bool:
        """Show confirmation dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Install kernel?")
        )
        dialog.format_secondary_text(
            _("You are about to download, compile and install:\n\n"
            "• Version: Linux %(version)s\n"
            "• Profile: %(profile)s\n\n"
            "This process may take several hours.") % {'version': version, 'profile': profile.name}
        )
        
        response = dialog.run()
        dialog.destroy()
        return response == Gtk.ResponseType.YES
    
    def _on_build_progress(self, message: str, percent: int) -> None:
        """Handle build progress updates."""
        self._build_progress.update_progress(message, percent)
        if message:
            self._build_progress.append_log(message)
    
    def _on_build_complete(self, success: bool) -> None:
        """Handle build completion."""
        self._building = False
        self._cancel_btn.set_sensitive(False)
        self._done_btn.show()
        self._build_progress.set_complete(success)
        
        # Refresh history
        self._history_view.refresh()
        
        # Send notification
        version = self._version_picker.get_selected_version()
        notifier = get_notification_manager()
        notifier.notify_build_complete(version, success)
        
        if success:
            self._ask_reboot()
    
    def _on_build_error(self, error: str) -> None:
        """Handle build error."""
        self._building = False
        self._cancel_btn.set_sensitive(False)
        self._done_btn.show()
        self._build_progress.set_complete(False)
        self._build_progress.append_log(f"ERROR: {error}")
    
    def _on_cancel_clicked(self, button: Gtk.Button) -> None:
        """Handle cancel button click."""
        # TODO: Implement build cancellation
        pass
    
    def _on_done_clicked(self, button: Gtk.Button) -> None:
        """Handle done button click - return to config view."""
        self._stack.set_visible_child_name("config")
        self._done_btn.hide()
    
    def _ask_reboot(self) -> None:
        """Ask user if they want to reboot."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.QUESTION,
            buttons=Gtk.ButtonsType.YES_NO,
            text=_("Installation complete!")
        )
        dialog.format_secondary_text(
            _("The kernel has been installed successfully.\n\n"
            "Do you want to reboot now to use the new kernel?")
        )
        
        response = dialog.run()
        dialog.destroy()
        
        if response == Gtk.ResponseType.YES:
            from ..utils.system import run_privileged
            run_privileged("reboot")
    
    def _show_error(self, message: str) -> None:
        """Show error dialog."""
        dialog = Gtk.MessageDialog(
            transient_for=self,
            modal=True,
            message_type=Gtk.MessageType.ERROR,
            buttons=Gtk.ButtonsType.OK,
            text=_("Error")
        )
        dialog.format_secondary_text(message)
        dialog.run()
        dialog.destroy()
    
    def refresh_versions(self) -> None:
        """Public method to refresh kernel versions from kernel.org."""
        self._version_picker.refresh_versions()
    
    def _on_kernel_name_changed(self, entry: Gtk.Entry) -> None:
        """Handle kernel name entry change."""
        self._update_name_hint()
    
    def _update_name_hint(self) -> None:
        """Update the kernel name preview hint."""
        name = self.get_kernel_name()
        version = self._version_picker.get_selected_version() or "6.x.x"
        profile = self._profile_selector.get_selected_profile()
        profile_suffix = profile.suffix if profile else "gaming"
        
        if name:
            preview = f"{version}-{name}-{profile_suffix}"
        else:
            preview = f"{version}-{profile_suffix}"
        
        self._name_hint_label.set_text(_("Result: %s") % preview)
    
    def get_kernel_name(self) -> str:
        """Get the custom kernel name from entry field."""
        name = self._kernel_name_entry.get_text().strip()
        # Sanitize: only allow alphanumeric, dash, underscore
        import re
        name = re.sub(r'[^a-zA-Z0-9_-]', '', name)
        return name
    
    def _on_profile_changed(self, widget, profile) -> None:
        """Handle profile selection change."""
        self._update_name_hint()
