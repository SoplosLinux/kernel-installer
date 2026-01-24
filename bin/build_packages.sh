#!/bin/bash
# Master Package Builder for Kernel Installer GUI

APP_NAME="kernel-installer"
VERSION="1.0.0"
BUILD_DIR="build_packages"

echo "📦 Starting package building process..."

# Setup clean build directory
rm -rf $BUILD_DIR
mkdir -p $BUILD_DIR

# --- 1. Debian (.deb) ---
echo "🔹 Building Debian package..."
DEB_ROOT="$BUILD_DIR/deb"
mkdir -p "$DEB_ROOT/DEBIAN"
mkdir -p "$DEB_ROOT/usr/bin"
mkdir -p "$DEB_ROOT/usr/share/kernel-installer"
mkdir -p "$DEB_ROOT/usr/share/applications"
mkdir -p "$DEB_ROOT/usr/share/metainfo"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps"

cp packaging/debian/control "$DEB_ROOT/DEBIAN/"
cp bin/kernel-installer "$DEB_ROOT/usr/bin/kernel-installer"
chmod +x "$DEB_ROOT/usr/bin/kernel-installer"
cp -r kernel_installer_gui "$DEB_ROOT/usr/share/kernel-installer/"
cp kernel_installer_gui/data/kernel-installer.desktop "$DEB_ROOT/usr/share/applications/"
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml "$DEB_ROOT/usr/share/metainfo/"
cp kernel_installer_gui/assets/icons/kernel-installer.png "$DEB_ROOT/usr/share/icons/hicolor/scalable/apps/"

if command -v dpkg-deb &> /dev/null; then
    dpkg-deb --build "$DEB_ROOT" "${APP_NAME}_${VERSION}_all.deb"
    echo "✅ DEB package created."
else
    echo "⚠️  dpkg-deb not found. Skipping .deb creation (folder structure kept in $DEB_ROOT)."
fi

# --- 2. Archive for others ---
echo "🔹 Creating source tarball for RPM and Arch..."
tar -czf "$BUILD_DIR/${APP_NAME}-${VERSION}.tar.gz" \
    --exclude="build_packages" \
    --exclude=".git" \
    --exclude="__pycache__" \
    .

echo "✅ Source tarball created."

# --- 3. RPM and Arch instructions ---
echo ""
echo "--- Build Info ---"
echo "RPM: Use 'rpmbuild -ba packaging/rpm/kernel-installer.spec' (needs rpm-build tools)"
echo "Arch: Use 'cd packaging/arch && makepkg -si' (needs base-devel)"
echo ""
echo "All packaging files are ready in 'packaging/' directory."
