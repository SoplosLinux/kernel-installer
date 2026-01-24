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

%description
Kernel Installer GUI allows users to easily manage Linux kernel versions,
apply optimization profiles (Gaming, Audio/Video, Office) and install them
safely in Debian, Ubuntu, Fedora and Arch Linux.

%install
mkdir -p %{buildroot}%{_bindir}
mkdir -p %{buildroot}%{_datadir}/kernel-installer
mkdir -p %{buildroot}%{_datadir}/applications
mkdir -p %{buildroot}%{_datadir}/metainfo
mkdir -p %{buildroot}%{_datadir}/icons/hicolor/scalable/apps

cp main.py %{buildroot}%{_bindir}/kernel-installer-gui
cp -r kernel_installer_gui/* %{buildroot}%{_datadir}/kernel-installer/
cp kernel_installer_gui/data/kernel-installer.desktop %{buildroot}%{_datadir}/applications/
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml %{buildroot}%{_datadir}/metainfo/
cp kernel_installer_gui/assets/icons/kernel-installer.png %{buildroot}%{_datadir}/icons/hicolor/scalable/apps/

%files
%{_bindir}/kernel-installer-gui
%{_datadir}/kernel-installer/
%{_datadir}/applications/kernel-installer.desktop
%{_datadir}/metainfo/io.github.alexiarstein.kernelinstall.metainfo.xml
%{_datadir}/icons/hicolor/scalable/apps/kernel-installer.png

%changelog
* Sat Jan 24 2026 Sergi Perich <info@soploslinux.com> - 1.0.0-1
- Initial release with Python and GTK3
