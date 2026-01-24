"""
Build progress widget - shows compilation progress and logs.
"""

import gi
gi.require_version('Gtk', '3.0')
from gi.repository import Gtk, GLib, Pango, GObject

from ..utils.system import get_load_average, get_cpu_count
from ..locale.i18n import _


class BuildProgress(Gtk.Box):
    """
    Widget showing kernel build progress with:
    - Progress bar with percentage
    - Status message
    - System load monitor
    - Scrollable log output
    """
    
    __gsignals__ = {
        'build-cancelled': (GObject.SignalFlags.RUN_FIRST, None, ())
    }
    
    def __init__(self):
        super().__init__(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        
        self._is_building = False
        self._load_timer_id = None
        self._cpu_count = get_cpu_count()
        
        # Main content paned (log left, stats right)
        paned = Gtk.Paned(orientation=Gtk.Orientation.HORIZONTAL)
        paned.set_wide_handle(True)
        
        # === Left side: Log view ===
        log_frame = Gtk.Frame()
        log_frame.set_shadow_type(Gtk.ShadowType.IN)
        
        log_scroll = Gtk.ScrolledWindow()
        log_scroll.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        log_scroll.set_min_content_height(300)
        
        self._log_view = Gtk.TextView()
        self._log_view.set_editable(False)
        self._log_view.set_cursor_visible(False)
        self._log_view.set_monospace(True)
        self._log_view.set_wrap_mode(Gtk.WrapMode.WORD_CHAR)
        self._log_buffer = self._log_view.get_buffer()
        
        log_scroll.add(self._log_view)
        log_frame.add(log_scroll)
        paned.pack1(log_frame, resize=True, shrink=False)
        
        # === Right side: System load ===
        stats_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        stats_box.set_margin_start(12)
        stats_box.set_size_request(180, -1)
        
        # Load header
        load_header = Gtk.Label(label=_("SYSTEM LOAD"))
        load_header.get_style_context().add_class('section-header')
        stats_box.pack_start(load_header, False, False, 0)
        
        # Load bar
        self._load_bar = Gtk.LevelBar()
        self._load_bar.set_min_value(0)
        self._load_bar.set_max_value(100)
        self._load_bar.add_offset_value("low", 35)
        self._load_bar.add_offset_value("high", 70)
        self._load_bar.add_offset_value("full", 100)
        stats_box.pack_start(self._load_bar, False, False, 0)
        
        # Load percentage
        self._load_label = Gtk.Label(label="0%")
        self._load_label.get_style_context().add_class('load-percentage')
        stats_box.pack_start(self._load_label, False, False, 0)
        
        # Separator
        stats_box.pack_start(Gtk.Separator(), False, False, 8)
        
        # Load averages
        avg_header = Gtk.Label(label=_("Load average:"))
        avg_header.set_halign(Gtk.Align.START)
        stats_box.pack_start(avg_header, False, False, 0)
        
        self._load_1m = Gtk.Label(label="1m:  0.00")
        self._load_1m.set_halign(Gtk.Align.START)
        stats_box.pack_start(self._load_1m, False, False, 0)
        
        self._load_5m = Gtk.Label(label="5m:  0.00")
        self._load_5m.set_halign(Gtk.Align.START)
        stats_box.pack_start(self._load_5m, False, False, 0)
        
        self._load_15m = Gtk.Label(label="15m: 0.00")
        self._load_15m.set_halign(Gtk.Align.START)
        stats_box.pack_start(self._load_15m, False, False, 0)
        
        # Cores
        cores_label = Gtk.Label(label=_("Cores: %d") % self._cpu_count)
        cores_label.set_halign(Gtk.Align.START)
        cores_label.set_margin_top(8)
        stats_box.pack_start(cores_label, False, False, 0)
        
        # Spacer
        stats_box.pack_start(Gtk.Box(), True, True, 0)
        
        paned.pack2(stats_box, resize=False, shrink=False)
        
        self.pack_start(paned, True, True, 0)
        
        # === Bottom: Progress bar and status ===
        bottom_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        
        # Status label
        self._status_label = Gtk.Label(label=_("Ready to build"))
        self._status_label.set_halign(Gtk.Align.START)
        self._status_label.set_ellipsize(Pango.EllipsizeMode.END)
        bottom_box.pack_start(self._status_label, False, False, 0)
        
        # Progress bar
        self._progress_bar = Gtk.ProgressBar()
        self._progress_bar.set_show_text(True)
        bottom_box.pack_start(self._progress_bar, False, False, 0)
        
        # Time elapsed
        self._time_label = Gtk.Label(label="")
        self._time_label.set_halign(Gtk.Align.END)
        self._time_label.get_style_context().add_class('dim-label')
        bottom_box.pack_start(self._time_label, False, False, 0)
        
        self.pack_start(bottom_box, False, False, 0)
        
        self.show_all()
    
    def start_build(self) -> None:
        """Start the build progress tracking."""
        self._is_building = True
        self._log_buffer.set_text("")
        self._progress_bar.set_fraction(0)
        self._start_time = GLib.get_monotonic_time()
        
        # Start load monitor
        self._load_timer_id = GLib.timeout_add(2000, self._update_load)
        self._update_load()
    
    def stop_build(self) -> None:
        """Stop the build progress tracking."""
        self._is_building = False
        if self._load_timer_id:
            GLib.source_remove(self._load_timer_id)
            self._load_timer_id = None
    
    def update_progress(self, message: str, percent: int) -> None:
        """
        Update progress display.
        
        Args:
            message: Status message to show
            percent: Progress percentage (0-100), or -1 for indeterminate
        """
        GLib.idle_add(self._do_update_progress, message, percent)
    
    def _do_update_progress(self, message: str, percent: int) -> None:
        """Update progress on main thread."""
        self._status_label.set_text(message)
        
        if percent >= 0:
            self._progress_bar.set_fraction(percent / 100.0)
            self._progress_bar.set_text(f"{percent}%")
        else:
            self._progress_bar.pulse()
        
        # Update elapsed time
        if self._is_building:
            elapsed = (GLib.get_monotonic_time() - self._start_time) / 1000000
            hours = int(elapsed) // 3600
            minutes = (int(elapsed) % 3600) // 60
            seconds = int(elapsed) % 60
            self._time_label.set_text(_("Time: %(h)02d:%(m)02d:%(s)02d") % {'h': hours, 'm': minutes, 's': seconds})
    
    def append_log(self, text: str) -> None:
        """Append text to the log view."""
        GLib.idle_add(self._do_append_log, text)
    
    def _do_append_log(self, text: str) -> None:
        """Append log on main thread."""
        end_iter = self._log_buffer.get_end_iter()
        self._log_buffer.insert(end_iter, text + "\n")
        
        # Auto-scroll to bottom
        mark = self._log_buffer.get_insert()
        self._log_view.scroll_to_mark(mark, 0, False, 0, 0)
    
    def _update_load(self) -> bool:
        """Update system load display."""
        if not self._is_building:
            return False
        
        load1, load5, load15 = get_load_average()
        usage = (load1 / self._cpu_count) * 100
        if usage > 100:
            usage = 100
        
        self._load_bar.set_value(usage)
        self._load_label.set_text(f"{usage:.1f}%")
        
        self._load_1m.set_text(f"1m:  {load1:.2f}")
        self._load_5m.set_text(f"5m:  {load5:.2f}")
        self._load_15m.set_text(f"15m: {load15:.2f}")
        
        return True  # Continue timer
    
    def set_complete(self, success: bool) -> None:
        """Mark build as complete."""
        self.stop_build()
        
        if success:
            self._status_label.set_text(_("Build completed successfully!"))
            self._progress_bar.set_fraction(1.0)
            self._progress_bar.set_text("100%")
        else:
            self._status_label.set_text(_("Build failed"))
            self._status_label.get_style_context().add_class('error')
