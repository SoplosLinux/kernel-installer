Name:           kernel-installer
Version:        1.0.0
Release:        1%{?dist}
Summary:        Graphical interface for downloading, compiling and installing Linux kernels

License:        GPLv3+
URL:            https://github.com/SoplosLinux/kernell-installer
BuildArch:      noarch

Requires:       python3
Requires:       python3-gobject
Requires:       gtk3
Requires:       wget
Requires:       binutils
Requires:       flex
Requires:       bison
Requires:       openssl-devel
Requires:       elfutils-libelf-devel
Requires:       bc
Requires:       rsync
Requires:       kmod
Requires:       dwarves
Requires:       cpio
Requires:       kernel-headers
Requires:       pkgconfig
Requires:       ncurses-devel
Requires:       make
Requires:       gcc
Requires:       gcc-c++
Requires:       gettext
Requires:       fakeroot
Requires:       newt
Requires:       git
Requires:       tar
Requires:       xz
Requires:       curl
Requires:       openssl
Requires:       coreutils

%description
Kernel Installer GUI allows users to easily manage Linux kernel versions,
apply optimization profiles (Gaming, Audio/Video, Office) and install them
safely in Debian, Ubuntu, Fedora and Arch Linux.

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/kernel-installer
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/metainfo
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/48x48/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/128x128/apps
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/256x256/apps

cp bin/kernel-installer %{buildroot}%{_bindir}/kernel-installer
chmod +x %{buildroot}%{_bindir}/kernel-installer
cp -r kernel_installer_gui/ %{buildroot}%{_datadir}/kernel-installer/
cp kernel_installer_gui/data/kernel-installer.desktop %{buildroot}%{_datadir}/applications/
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml %{buildroot}%{_datadir}/metainfo/
cp kernel_installer_gui/assets/icons/kernel-installer-48.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/kernel-installer.png
cp kernel_installer_gui/assets/icons/kernel-installer-128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/kernel-installer.png
cp kernel_installer_gui/assets/icons/kernel-installer-256.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/kernel-installer.png

%files
%{_bindir}/kernel-installer
%{_datadir}/kernel-installer/
%{_datadir}/applications/kernel-installer.desktop
%{_datadir}/metainfo/io.github.alexiarstein.kernelinstall.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/kernel-installer.png

%changelog
* Sat Jan 24 2026 Sergi Perich <info@soploslinux.com> - 1.0.0-1
- Initial release with Python and GTK3
