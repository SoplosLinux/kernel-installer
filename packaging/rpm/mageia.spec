Name:           kernel-installer
Version:        1.0.1
Release:        1
Summary:        Graphical interface for downloading, compiling and installing Linux kernels (Mageia Family)

License:        GPLv3+
URL:            https://github.com/SoplosLinux/kernel-installer
BuildArch:      noarch

# Core runtime (Mageia names)
Requires:       python3
Requires:       python3-gobject
Requires:       gtk+3.0
Requires:       wget
Requires:       curl
Requires:       git
Requires:       tar
Requires:       xz
Requires:       openssl
Requires:       coreutils

# Build dependencies (Mageia/Mandriva specific names)
Requires:       binutils
Requires:       flex
Requires:       bison
Requires:       libopenssl-devel
Requires:       libelf-devel
Requires:       bc
Requires:       rsync
Requires:       kmod
Requires:       dwarves
Requires:       cpio
Requires:       kernel-devel
Requires:       pkgconfig
Requires:       ncurses-devel
Requires:       make
Requires:       gcc
Requires:       gcc-c++
Requires:       gettext
Requires:       fakeroot
Requires:       newt-devel

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
* Mon Jan 26 2026 Sergi Perich <info@soploslinux.com> - 1.0.1
- Sudo optimization and RC fix
- Adjusted dependencies for Mageia/OpenMandriva (gtk+3.0, kernel-devel, libopenssl-devel)
