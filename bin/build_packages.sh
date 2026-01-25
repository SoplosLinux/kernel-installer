#!/bin/bash
# Kernel Installer Package Builder (Reconstructed & Robust)
set -e

APP_NAME="kernel-installer"
VERSION="1.0.0"
BUILD_DIR="build_packages"
RPM_BUILD_DIR="$HOME/rpmbuild"

echo "📦 Starting proper packaging..."

# 1. Clean previous builds
rm -rf "$BUILD_DIR" releases
mkdir -p releases

# --- DEBIAN PACKAGE ---
echo "🔹 Building Debian (.deb)..."
DEB_DIR="$BUILD_DIR/deb"
mkdir -p "$DEB_DIR/DEBIAN"
mkdir -p "$DEB_DIR/usr/bin"
mkdir -p "$DEB_DIR/usr/share/kernel-installer"
mkdir -p "$DEB_DIR/usr/share/applications"
mkdir -p "$DEB_DIR/usr/share/metainfo"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/48x48/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$DEB_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_DIR/usr/share/man/man1"

# Copy files
cp packaging/debian/control "$DEB_DIR/DEBIAN/"
cp bin/kernel-installer "$DEB_DIR/usr/bin/"
chmod +x "$DEB_DIR/usr/bin/kernel-installer"
# Include everything from root in share dir
cp main.py README.md LICENSE CHANGELOG.md setup.py "$DEB_DIR/usr/share/kernel-installer/"
cp -r kernel_installer_gui "$DEB_DIR/usr/share/kernel-installer/"
cp kernel_installer_gui/data/kernel-installer.desktop "$DEB_DIR/usr/share/applications/"
# Professional Metadata (AppStream)
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml "$DEB_DIR/usr/share/metainfo/"
cp kernel_installer_gui/assets/icons/kernel-installer-48.png "$DEB_DIR/usr/share/icons/hicolor/48x48/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-128.png "$DEB_DIR/usr/share/icons/hicolor/128x128/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-256.png "$DEB_DIR/usr/share/icons/hicolor/256x256/apps/kernel-installer.png"

cp kernel_installer_gui/data/kernel-installer.1 "$DEB_DIR/usr/share/man/man1/"
gzip -9 "$DEB_DIR/usr/share/man/man1/kernel-installer.1"

# Build .deb
dpkg-deb --build --root-owner-group "$DEB_DIR" "releases/${APP_NAME}_${VERSION}_all.deb"


# --- FEDORA PACKAGE (RPM) ---
echo "🔹 Building Fedora (.rpm)..."
mkdir -p "$RPM_BUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}

# Create source tarball
TAR_NAME="${APP_NAME}-${VERSION}"
mkdir -p "$BUILD_DIR/$TAR_NAME"
# Professional completeness: include everything in the source tarball
cp -r bin kernel_installer_gui main.py README.md LICENSE CHANGELOG.md setup.py "$BUILD_DIR/$TAR_NAME/"
tar -czf "$RPM_BUILD_DIR/SOURCES/${TAR_NAME}.tar.gz" -C "$BUILD_DIR" "${TAR_NAME}"

# Copy spec file
cp packaging/rpm/kernel-installer.spec "$RPM_BUILD_DIR/SPECS/"

# Build RPM
if command -v rpmbuild >/dev/null; then
    rpmbuild -bb "$RPM_BUILD_DIR/SPECS/kernel-installer.spec" --define "_topdir $RPM_BUILD_DIR"
    # Move and rename to avoid the release suffix in the artifact name if user requested
    cp "$RPM_BUILD_DIR"/RPMS/noarch/kernel-installer-1.0.0-1.noarch.rpm releases/kernel-installer-1.0.0.noarch.rpm
else
    echo "⚠️ rpmbuild not found. Skipping RPM build."
fi


# --- ARCH LINUX ---
echo "🔹 Building Arch Linux (.pkg.tar.zst) [Manual]..."

# Create package structure
ARCH_DIR="$BUILD_DIR/arch/pkg"
mkdir -p "$ARCH_DIR/usr/bin"
mkdir -p "$ARCH_DIR/usr/share/kernel-installer"
mkdir -p "$ARCH_DIR/usr/share/applications"
mkdir -p "$ARCH_DIR/usr/share/metainfo"
mkdir -p "$ARCH_DIR/usr/share/icons/hicolor/48x48/apps"
mkdir -p "$ARCH_DIR/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$ARCH_DIR/usr/share/icons/hicolor/256x256/apps"

# Copy files
cp bin/kernel-installer "$ARCH_DIR/usr/bin/"
chmod +x "$ARCH_DIR/usr/bin/kernel-installer"
# Mirror Debian completeness
cp main.py README.md LICENSE CHANGELOG.md setup.py "$ARCH_DIR/usr/share/kernel-installer/"
cp -r kernel_installer_gui "$ARCH_DIR/usr/share/kernel-installer/"
cp kernel_installer_gui/data/kernel-installer.desktop "$ARCH_DIR/usr/share/applications/"
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml "$ARCH_DIR/usr/share/metainfo/"

cp kernel_installer_gui/assets/icons/kernel-installer-48.png "$ARCH_DIR/usr/share/icons/hicolor/48x48/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-128.png "$ARCH_DIR/usr/share/icons/hicolor/128x128/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-256.png "$ARCH_DIR/usr/share/icons/hicolor/256x256/apps/kernel-installer.png"

# Generate .PKGINFO
cat > "$ARCH_DIR/.PKGINFO" <<EOF
pkgname = kernel-installer
pkgver = ${VERSION}
pkgdesc = Graphical interface for downloading, compiling and installing Linux kernels
url = https://github.com/SoplosLinux/kernell-installer
builddate = $(date +%s)
packager = Kernel Installer Builder
size = $(du -sb "$ARCH_DIR" | cut -f1)
arch = any
license = GPL3
depend = python-gobject
depend = gtk3
depend = base-devel
depend = bc
depend = rsync
depend = wget
depend = tar
depend = xz
depend = libelf
depend = kmod
depend = cpio
depend = openssl
depend = ncurses
depend = gettext
depend = git
EOF

# Compress
# Use tar to create zst package. --zstd is supported by GNU tar (usually).
# If not, pipe to zstd.
if tar --help | grep -q zstd; then
    tar -C "$ARCH_DIR" -c --zstd -f "releases/${APP_NAME}-${VERSION}-any.pkg.tar.zst" .
elif command -v zstd >/dev/null; then
    tar -C "$ARCH_DIR" -c . | zstd - > "releases/${APP_NAME}-${VERSION}-any.pkg.tar.zst"
else
    echo "⚠️ zstd not found. Skipping Arch package."
fi

# Cleanup
echo "✅ Packaging complete. Files in 'releases/':"
ls -lh releases/
