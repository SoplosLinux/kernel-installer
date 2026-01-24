"""
Profile selector widget - cards for selecting kernel profiles.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GObject

from ..core.profiles import KernelProfile, ProfileType, get_all_profiles
from ..locale.i18n import _


class ProfileCard(Gtk.RadioButton):
    """
    A card widget representing a kernel profile.
    Uses RadioButton for mutual exclusion.
    """
    
    def __init__(self, profile: KernelProfile, group: Gtk.RadioButton = None):
        super().__init__(group=group)
        
        self.profile = profile
        self.set_mode(False)  # Don't show radio indicator
        self.get_style_context().add_class('profile-card')
        
        # Main container
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        box.set_margin_top(16)
        box.set_margin_bottom(16)
        box.set_margin_start(12)
        box.set_margin_end(12)
        
        # Icon
        icon = Gtk.Image.new_from_icon_name(profile.icon, Gtk.IconSize.DIALOG)
        icon.set_pixel_size(48)
        box.pack_start(icon, False, False, 0)
        
        # Name
        name_label = Gtk.Label(label=profile.name)
        name_label.get_style_context().add_class('profile-name')
        name_label.set_halign(Gtk.Align.CENTER)
        box.pack_start(name_label, False, False, 0)
        
        # Description
        desc_label = Gtk.Label(label=profile.description)
        desc_label.set_line_wrap(True)
        desc_label.set_max_width_chars(25)
        desc_label.set_justify(Gtk.Justification.CENTER)
        desc_label.get_style_context().add_class('profile-description')
        desc_label.set_halign(Gtk.Align.CENTER)
        box.pack_start(desc_label, True, True, 0)
        
        self.add(box)
        self.show_all()


class ProfileSelector(Gtk.Box):
    """
    Widget for selecting a kernel profile from available options.
    Displays profile cards in a horizontal layout.
    """
    
    __gsignals__ = {
        'profile-changed': (GObject.SignalFlags.RUN_FIRST, None, (object,))
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        self._selected_profile: KernelProfile = None
        self._cards: dict[ProfileType, ProfileCard] = {}
        
        # Header
        header = Gtk.Label(label=_("Select kernel profile"))
        header.get_style_context().add_class('section-header')
        header.set_halign(Gtk.Align.START)
        self.pack_start(header, False, False, 0)
        
        # Cards container
        cards_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=16)
        cards_box.set_halign(Gtk.Align.CENTER)
        cards_box.set_homogeneous(True)
        
        # Create profile cards
        first_card = None
        for profile in get_all_profiles():
            card = ProfileCard(profile, group=first_card)
            if first_card is None:
                first_card = card
                card.set_active(True)
                self._selected_profile = profile
            
            card.connect('toggled', self._on_card_toggled)
            self._cards[profile.id] = card
            cards_box.pack_start(card, True, True, 0)
        
        self.pack_start(cards_box, False, False, 0)
        self.show_all()
    
    def _on_card_toggled(self, card: ProfileCard) -> None:
        """Handle card selection."""
        if card.get_active():
            self._selected_profile = card.profile
            self.emit('profile-changed', card.profile)
    
    def get_selected_profile(self) -> KernelProfile:
        """Get the currently selected profile."""
        return self._selected_profile
    
    def set_selected_profile(self, profile_type: ProfileType) -> None:
        """Set the selected profile by type."""
        if profile_type in self._cards:
            self._cards[profile_type].set_active(True)
