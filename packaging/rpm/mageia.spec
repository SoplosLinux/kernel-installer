Name:           kernel-installer
Version:        1.0.3
Release:        1
Summary:        Graphical interface for downloading, compiling and installing Linux kernels (Mageia Family)
Group:          System/Configuration/Hardware
License:        GPLv3+
URL:            https://github.com/SoplosLinux/kernel-installer
BuildArch:      noarch

# Core runtime (Mageia provides - architecture independent)
Requires:       python3
Requires:       python3-gi
Requires:       gtk+3.0
Requires:       newt
Requires:       wget
Requires:       curl
Requires:       git
Requires:       tar
Requires:       xz
Requires:       openssl
Requires:       coreutils

# Build dependencies (Mageia specific names)
Requires:       binutils
Requires:       flex
Requires:       bison
Requires:       openssl-devel
Requires:       elfutils-devel
Requires:       bc
Requires:       rsync
Requires:       kmod
Requires:       dwarves
Requires:       cpio
Requires:       ncurses-devel
Requires:       make
Requires:       gcc
Requires:       gcc-c++
Requires:       gettext
Requires:       fakeroot
Requires:       newt-devel
Requires:       rpm-build

# Kernel headers
Requires:       kernel-desktop-devel

Source0:        %{name}-%{version}.tar.gz

%description
Kernel Installer GUI allows users to easily manage Linux kernel versions,
apply optimization profiles (Gaming, Audio/Video, Office) and install them
safely.

This package is optimized for Mageia, OpenMandriva and PCLinuxOS.

%prep
%setup -q

%build

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
cp main.py README.md LICENSE CHANGELOG.md setup.py %{buildroot}%{_datadir}/kernel-installer/
cp -r kernel_installer_gui/ %{buildroot}%{_datadir}/kernel-installer/
cp kernel_installer_gui/data/org.soplos.kernel-installer.desktop %{buildroot}%{_datadir}/applications/
cp kernel_installer_gui/data/org.soplos.kernel-installer.metainfo.xml %{buildroot}%{_datadir}/metainfo/

cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-48.png %{buildroot}%{_datadir}/icons/hicolor/48x48/apps/org.soplos.kernel-installer.png
cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-128.png %{buildroot}%{_datadir}/icons/hicolor/128x128/apps/org.soplos.kernel-installer.png
cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-256.png %{buildroot}%{_datadir}/icons/hicolor/256x256/apps/org.soplos.kernel-installer.png

%files
%{_bindir}/kernel-installer
%{_datadir}/kernel-installer/
%{_datadir}/applications/org.soplos.kernel-installer.desktop
%{_datadir}/metainfo/org.soplos.kernel-installer.metainfo.xml
%{_datadir}/icons/hicolor/*/apps/org.soplos.kernel-installer.png

%changelog
* Wed Jan 28 2026 Sergi Perich <info@soploslinux.com> - 1.0.3-1
- New visual identity and active packaging feedback
- Improved history management and duplicate prevention
- Consolidated kernel removal to reduce password prompts
- Updated translations for all 8 supported languages

* Mon Jan 26 2026 Sergi Perich <info@soploslinux.com> - 1.0.1-2
- Corrected dependencies for Mageia 10 with DNF
- Changed gtk+3.0 (virtual provide, architecture independent)
- Changed libopenssl-devel to openssl-devel (virtual provide)
- Changed libelf-devel to elfutils-devel (virtual provide)
- Changed lib64ncurses-devel to ncurses-devel (virtual provide)
- Changed lib64newt-devel to newt-devel (virtual provide)
- Using virtual provides when possible for better compatibility

* Mon Jan 26 2026 Sergi Perich <info@soploslinux.com> - 1.0.1-1
- Sudo optimization and RC fix
- Initial Mageia/OpenMandriva package