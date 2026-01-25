"""Allow running as python -m kernel_installer_gui."""

from .app import KernelInstallerApp

def main():
    import sys
    from gi.repository import GLib
    
    # Force program name for WM_CLASS consistency (Icon mapping fix)
    GLib.set_prgname('kernel-installer')
    GLib.set_application_name('Kernel Installer')
    
    app = KernelInstallerApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
