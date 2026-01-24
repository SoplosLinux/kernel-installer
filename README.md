# Kernel Installer

A graphical interface for downloading, compiling, and installing the Linux kernel with optimized profiles.

![Kernel Installer Icon](kernel_installer_gui/assets/icons/kernel-installer-128.png)

## Authors

- **Sergi Perich** <info@soploslinux.com>
- **Alexia Michelle** <alexia@goldendoglinux.org>

## Features

- Download kernels directly from kernel.org (stable, LTS, RC)
- Optimized profiles: Gaming, Audio/Video, Minimal
- Multi-distro support: Debian, Ubuntu, Fedora, Arch
- Auto-detection of bootloader (GRUB, systemd-boot, rEFInd)
- Auto-detection of initramfs tool (dracut, initramfs-tools, mkinitcpio)
- Custom kernel naming
- i18n support (English, Spanish, French, Portuguese, German, Italian, Romanian, Russian)
- Desktop notifications

## Requirements

- Python 3.10+
- GTK 3.0
- PyGObject

### Debian/Ubuntu

```bash
sudo apt install python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-notify-0.7
```

### Fedora

```bash
sudo dnf install python3-gobject gtk3
```

### Arch

```bash
sudo pacman -S python-gobject gtk3
```

## Usage

```bash
# From source directory
./bin/kernel-installer

# Or using Python
python3 main.py
```

## Keyboard Shortcuts

| Shortcut | Action           |
| -------- | ---------------- |
| Ctrl+Q   | Quit             |
| F5       | Refresh versions |

## License

GPL-3.0 - See [LICENSE](LICENSE)

## Links

- [GitHub Repository](https://github.com/alexiarstein/kernelinstall)
