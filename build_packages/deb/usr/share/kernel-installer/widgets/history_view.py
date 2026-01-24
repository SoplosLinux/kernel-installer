"""
History view widget - shows previously installed kernels.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk

from ..core.kernel import KernelManager, InstalledKernel
from ..locale.i18n import _
from typing import List


class HistoryView(Gtk.Box):
    """
    Widget showing previously installed kernels with profile info.
    """
    
    def __init__(self, kernel_manager: KernelManager = None):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        
        self._kernel_manager = kernel_manager or KernelManager()
        
        # Header with expander
        expander = Gtk.Expander(label=_("📜 Installed kernels history"))
        expander.set_expanded(False)
        
        # List container
        self._list_box = Gtk.ListBox()
        self._list_box.set_selection_mode(Gtk.SelectionMode.NONE)
        self._list_box.get_style_context().add_class('history-list')
        
        # Scroll window for list
        scroll = Gtk.ScrolledWindow()
        scroll.set_policy(Gtk.PolicyType.NEVER, Gtk.PolicyType.AUTOMATIC)
        scroll.set_max_content_height(150)
        scroll.set_propagate_natural_height(True)
        scroll.add(self._list_box)
        
        expander.add(scroll)
        self.pack_start(expander, False, False, 0)
        
        self.show_all()
    
    def refresh(self) -> None:
        """Refresh the history list."""
        # Clear existing items
        for child in self._list_box.get_children():
            self._list_box.remove(child)
        
        history = self._kernel_manager.get_installation_history()
        
        if not history:
            empty_label = Gtk.Label(label=_("No kernels installed yet"))
            empty_label.get_style_context().add_class('dim-label')
            empty_label.set_margin_top(8)
            empty_label.set_margin_bottom(8)
            self._list_box.add(empty_label)
        else:
            for kernel in history:
                row = self._create_history_row(kernel)
                self._list_box.add(row)
        
        self._list_box.show_all()
    
    def _create_history_row(self, kernel: InstalledKernel) -> Gtk.ListBoxRow:
        """Create a row for a kernel entry."""
        row = Gtk.ListBoxRow()
        
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        box.set_margin_top(4)
        box.set_margin_bottom(4)
        box.set_margin_start(8)
        box.set_margin_end(8)
        
        # Current indicator
        if kernel.is_current:
            current_icon = Gtk.Image.new_from_icon_name('emblem-ok-symbolic', Gtk.IconSize.SMALL_TOOLBAR)
            current_icon.set_tooltip_text(_("Current kernel"))
            box.pack_start(current_icon, False, False, 0)
        
        # Version
        version_label = Gtk.Label(label=kernel.version)
        version_label.set_halign(Gtk.Align.START)
        if kernel.is_current:
            version_label.get_style_context().add_class('current-kernel')
        box.pack_start(version_label, True, True, 0)
        
        # Profile badge
        profile_label = Gtk.Label(label=kernel.profile)
        profile_label.get_style_context().add_class('profile-badge')
        box.pack_start(profile_label, False, False, 0)
        
        # Date
        try:
            from datetime import datetime
            dt = datetime.fromisoformat(kernel.installed_date)
            date_str = dt.strftime("%Y-%m-%d")
        except Exception:
            date_str = kernel.installed_date[:10]
        
        date_label = Gtk.Label(label=date_str)
        date_label.get_style_context().add_class('dim-label')
        box.pack_start(date_label, False, False, 0)
        
        row.add(box)
        return row
    
    def set_history(self, history: List[InstalledKernel]) -> None:
        """Manually set history items."""
        # Clear existing
        for child in self._list_box.get_children():
            self._list_box.remove(child)
        
        for kernel in history:
            row = self._create_history_row(kernel)
            self._list_box.add(row)
        
        self._list_box.show_all()
