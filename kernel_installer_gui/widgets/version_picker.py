"""
Version picker widget - dropdown and refresh for kernel versions.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, GObject

from ..core.kernel import KernelManager, KernelVersion
from ..locale.i18n import _
from typing import List, Optional


class VersionPicker(Gtk.Box):
    """
    Widget for selecting a kernel version to install.
    Features a dropdown of available versions and a refresh button.
    """
    
    __gsignals__ = {
        'version-changed': (GObject.SignalFlags.RUN_FIRST, None, (str,)),
        'versions-loaded': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self, kernel_manager: KernelManager = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        self._kernel_manager = kernel_manager or KernelManager()
        self._versions: List[KernelVersion] = []
        self._selected_version: Optional[str] = None
        
        # Header
        header = Gtk.Label(label=_("Kernel version"))
        header.get_style_context().add_class('section-header')
        header.set_halign(Gtk.Align.START)
        self.pack_start(header, False, False, 0)
        
        # Row with combo and button
        row = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=8)
        
        # Version combo box
        self._combo = Gtk.ComboBoxText()
        self._combo.set_hexpand(True)
        self._combo.connect('changed', self._on_combo_changed)
        row.pack_start(self._combo, True, True, 0)
        
        # Refresh button
        refresh_btn = Gtk.Button()
        refresh_icon = Gtk.Image.new_from_icon_name('view-refresh-symbolic', Gtk.IconSize.BUTTON)
        refresh_btn.set_image(refresh_icon)
        refresh_btn.set_tooltip_text(_("Check for updates"))
        refresh_btn.connect('clicked', self._on_refresh_clicked)
        row.pack_start(refresh_btn, False, False, 0)
        
        self.pack_start(row, False, False, 0)
        
        # Info label
        self._info_label = Gtk.Label()
        self._info_label.get_style_context().add_class('dim-label')
        self._info_label.set_halign(Gtk.Align.START)
        self.pack_start(self._info_label, False, False, 0)
        
        # Loading spinner (hidden by default)
        self._spinner = Gtk.Spinner()
        self._spinner.set_no_show_all(True)
        self.pack_start(self._spinner, False, False, 0)
        
        self.show_all()
    
    def _on_combo_changed(self, combo: Gtk.ComboBoxText) -> None:
        """Handle version selection change."""
        active_text = combo.get_active_text()
        if active_text:
            # Extract version from display text
            version = active_text.split()[0]
            self._selected_version = version
            self.emit('version-changed', version)
            self._update_info_label()
    
    def _on_refresh_clicked(self, button: Gtk.Button) -> None:
        """Handle refresh button click."""
        self.refresh_versions()
    
    def _update_info_label(self) -> None:
        """Update the info label with version details."""
        if not self._selected_version:
            self._info_label.set_text("")
            return
        
        for v in self._versions:
            if v.version == self._selected_version:
                if v.is_mainline:
                    if '-rc' in v.version:
                        self._info_label.set_markup(_("<span foreground='orange'>⚠ Experimental version (RC)</span>"))
                    else:
                        self._info_label.set_markup(_("<span foreground='lightblue'>✦ Mainline version (Development)</span>"))
                elif v.is_latest:
                    self._info_label.set_markup(_("<b>✓ Latest stable version</b>"))
                elif v.is_longterm:
                    self._info_label.set_text(_("Long-term support version (LTS)"))
                else:
                    self._info_label.set_text(_("Stable version"))
                return
        
        self._info_label.set_text("")
    
    def refresh_versions(self) -> None:
        """Fetch available versions in background."""
        self._spinner.show()
        self._spinner.start()
        self._combo.set_sensitive(False)
        
        def fetch_in_thread():
            versions = self._kernel_manager.fetch_available_versions()
            GLib.idle_add(self._on_versions_fetched, versions)
        
        import threading
        thread = threading.Thread(target=fetch_in_thread, daemon=True)
        thread.start()
    
    def _on_versions_fetched(self, versions: List[KernelVersion]) -> None:
        """Handle fetched versions on main thread."""
        self._spinner.stop()
        self._spinner.hide()
        self._combo.set_sensitive(True)
        
        self._versions = versions
        self._combo.remove_all()
        
        for v in versions:
            label = v.version
            if v.is_mainline:
                if '-rc' in v.version:
                    label += _(" (RC - Experimental)")
                else:
                    label += _(" (Mainline)")
            elif v.is_latest:
                label += _(" (Latest)")
            elif v.is_longterm:
                label += _(" (LTS)")
            self._combo.append_text(label)
        
        if versions:
            self._combo.set_active(0)
        
        self.emit('versions-loaded')
    
    def get_selected_version(self) -> Optional[str]:
        """Get the currently selected version."""
        return self._selected_version
    
    def set_versions(self, versions: List[KernelVersion]) -> None:
        """Manually set available versions."""
        self._on_versions_fetched(versions)
