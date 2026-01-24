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
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/48x48/apps"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/128x128/apps"
mkdir -p "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$DEB_ROOT/usr/share/man/man1"
mkdir -p "$DEB_ROOT/usr/share/doc/$APP_NAME"

cp packaging/debian/control "$DEB_ROOT/DEBIAN/"
cp bin/kernel-installer "$DEB_ROOT/usr/bin/kernel-installer"
chmod +x "$DEB_ROOT/usr/bin/kernel-installer"
cp -r kernel_installer_gui "$DEB_ROOT/usr/share/kernel-installer/"
cp kernel_installer_gui/data/kernel-installer.desktop "$DEB_ROOT/usr/share/applications/"
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml "$DEB_ROOT/usr/share/metainfo/"
cp kernel_installer_gui/assets/icons/kernel-installer-48.png "$DEB_ROOT/usr/share/icons/hicolor/48x48/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-128.png "$DEB_ROOT/usr/share/icons/hicolor/128x128/apps/kernel-installer.png"
cp kernel_installer_gui/assets/icons/kernel-installer-256.png "$DEB_ROOT/usr/share/icons/hicolor/256x256/apps/kernel-installer.png"

# Documentation
cp kernel_installer_gui/data/kernel-installer.1 "$DEB_ROOT/usr/share/man/man1/"
gzip -9f "$DEB_ROOT/usr/share/man/man1/kernel-installer.1"
cp kernel_installer_gui/data/copyright "$DEB_ROOT/usr/share/doc/$APP_NAME/"

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
    --exclude="releases" \
    --exclude=".git" \
    --exclude="__pycache__" \
    .

echo "✅ Source tarball created."

# --- 3. Organized Releases ---
echo "🔹 Organizing releases..."
mkdir -p releases

# Move new DEB to releases (overwrite if exists)
if [ -f "${APP_NAME}_${VERSION}_all.deb" ]; then
    mv -f "${APP_NAME}_${VERSION}_all.deb" releases/
fi

# Copy source tarball to releases
if [ -f "$BUILD_DIR/${APP_NAME}-${VERSION}.tar.gz" ]; then
    cp -f "$BUILD_DIR/${APP_NAME}-${VERSION}.tar.gz" releases/
fi

echo ""
echo "✅ Current contents of 'releases/' directory:"
ls -lh releases/

echo ""
echo "--- Build Status ---"
echo "DEB: Updated"
echo "Tarball: Updated"
echo "RPM/Arch: Instructions available in packaging/ folder"
echo ""
echo "Note: This script now preserves other files in 'releases/' (additive)."
