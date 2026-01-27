# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.2] - 2026-01-27

### Changed

- **Major Build Optimization**: Disabled `CONFIG_DEBUG_INFO` globally during kernel configuration. This drastically reduces compilation time (up to 50% faster) and storage usage for all distributions.
- Optimized RPM packaging: disabled debuginfo package generation and removed unsupported zstd compression levels to improve compatibility with Mageia and Fedora.
- Standardized versioning (1.0.1 -> 1.0.2) and release numbers across all supported distributions.

### Fixed

- Fixed build failures on Fedora and Mageia by isolating the `rpmbuild` directory (`_topdir`) and preventing permission/path conflicts.
- Corrected Fedora-specific dependencies in both `fedora.spec` and runtime detection (`elfutils-devel`, `rpm-build`, `perl`, `newt-devel`).
- Fixed "PackageKit daemon disappeared" and transaction errors during RPM installation in isolated Fedora environments.

## [1.0.1] - 2026-01-26

### Added

- Optimized sudo authentication: ask for password only once during installation
- Robust reboot functionality using `systemctl reboot`
- New "Hardware Optimized" profile with auto-detection for CPU, GPU (NVIDIA/AMD/Intel) and NVMe
- Automatic virtualization detection (QEMU/KVM, VirtualBox, VMware) in optimized profile
- Added checkbox for optional build directory cleanup after installation
- Fixed build errors when the source or build directory already existed from a previous attempt
- Refined Arch Linux support (fixed kernel module paths) and added CachyOS
- Added official support for LMDE (Linux Mint Debian Edition)
- Extended Mandriva family support: Mageia, OpenMandriva, Rosa Linux, PCLinuxOS
- Fixed Mageia/Mandriva package dependencies and architecture naming (lib64)
- Redesigned Profile cards: compact layout, reduced padding, and smart text wrap for names
- Improved cancellation support: distinct "Build cancelled" notifications and logic
- Transient notifications: all build status alerts now auto-hide after 5 seconds
- Multi-language expansion: 100% translation coverage for 8 languages (EN, ES, FR, PT, DE, IT, RO, RU)

### Fixed

- Fixed 404 error when downloading Release Candidate (RC) kernels by using reliable snapshots from `git.kernel.org`.
- Improved visibility and labeling of "Mainline" kernel versions in the selection menu.
- Added support for both `.tar.xz` and `.tar.gz` kernel source formats.
- Fixed secondary password prompt during reboot by attempting unprivileged reboot first (vía systemd/logind).

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
