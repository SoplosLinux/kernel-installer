# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.1] - 2026-01-26

### Added

- Optimized sudo authentication: ask for password only once during installation
- Robust reboot functionality using `systemctl reboot`
- New "Hardware Optimized" profile with auto-detection for CPU, GPU (NVIDIA/AMD/Intel) and NVMe
- Automatic virtualization detection (QEMU/KVM, VirtualBox, VMware) in optimized profile
- Added checkbox for optional build directory cleanup after installation
- Fixed build errors when the source or build directory already existed from a previous attempt
- Refined Arch Linux support (fixed kernel module paths)

### Fixed

- Fixed 404 error when downloading Release Candidate (RC) kernels by correctly using the `/testing/` subdirectory on kernel.org

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
- Support for 8 languages: EN, ES, FR, PT, DE, IT, RO, RU
- Verified support for Debian, Fedora and Arch Linux systems
- Transient notifications via libnotify (auto-hide after 5s)
- Professional packaging for .deb, .rpm and Arch Linux
- AppStream/Metainfo integration for software centers
- Automated system dependency verification and installation
- New feature: Kernel removal support for Debian, Fedora, and Arch Linux
- Enhanced localization: 100% translated for all 8 supported languages
- Improved "Minimal" profile with optimized kernel configuration and mandatory drivers

### Authors

- Sergi Perich <info@soploslinux.com>
- Alexia Michelle <alexia@goldendoglinux.org>
