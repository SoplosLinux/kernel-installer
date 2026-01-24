"""Allow running as python -m kernel_installer_gui."""

from .app import KernelInstallerApp

def main():
    import sys
    app = KernelInstallerApp()
    return app.run(sys.argv)

if __name__ == "__main__":
    main()
