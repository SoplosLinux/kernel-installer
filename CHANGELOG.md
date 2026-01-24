# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-24

### Added

- Initial release of Kernel Installer GUI
- GTK3 graphical interface
- Kernel profiles: Gaming, Audio/Video, Minimal
- Full i18n support: English, Spanish, French, Portuguese, German, Italian, Romanian, Russian
- Support for Debian, Ubuntu, Fedora, and Arch Linux
- Bootloader detection (GRUB2, systemd-boot, rEFInd, LILO, Syslinux)
- Initramfs detection (initramfs-tools, dracut, mkinitcpio)
- All kernel versions from kernel.org (stable, LTS, mainline RC)
- Custom kernel naming
- i18n support with gettext (English, Spanish)
- Desktop notifications for build completion
- Installation history tracking
- Keyboard shortcuts (Ctrl+Q, F5)

### Authors

- Sergi Perich <info@soploslinux.com>
- Alexia Michelle <alexia@goldendoglinux.org>
