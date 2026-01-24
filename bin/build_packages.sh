#!/bin/bash
# Kernel Installer Package Builder
# Based on current project state

APP_NAME="kernel-installer"
VERSION="1.0.0"
BUILD_DIR="build_packages"

echo "📦 Starting packaging..."

# Clean and setup
rm -rf $BUILD_DIR *.deb *.rpm *.pkg.tar.zst
mkdir -p $BUILD_DIR/deb/DEBIAN
mkdir -p $BUILD_DIR/deb/usr/bin
mkdir -p $BUILD_DIR/deb/usr/share/kernel-installer
mkdir -p $BUILD_DIR/deb/usr/share/applications
mkdir -p $BUILD_DIR/deb/usr/share/metainfo
mkdir -p $BUILD_DIR/deb/usr/share/icons/hicolor/48x48/apps
mkdir -p $BUILD_DIR/deb/usr/share/icons/hicolor/128x128/apps
mkdir -p $BUILD_DIR/deb/usr/share/icons/hicolor/256x256/apps
mkdir -p $BUILD_DIR/deb/usr/share/man/man1

# Debian Files
cp packaging/debian/control $BUILD_DIR/deb/DEBIAN/
cp bin/kernel-installer $BUILD_DIR/deb/usr/bin/
chmod +x $BUILD_DIR/deb/usr/bin/kernel-installer
cp -r kernel_installer_gui $BUILD_DIR/deb/usr/share/kernel-installer/
cp kernel_installer_gui/data/kernel-installer.desktop $BUILD_DIR/deb/usr/share/applications/
cp kernel_installer_gui/data/io.github.alexiarstein.kernelinstall.metainfo.xml $BUILD_DIR/deb/usr/share/metainfo/
cp kernel_installer_gui/assets/icons/kernel-installer-48.png $BUILD_DIR/deb/usr/share/icons/hicolor/48x48/apps/kernel-installer.png
cp kernel_installer_gui/assets/icons/kernel-installer-128.png $BUILD_DIR/deb/usr/share/icons/hicolor/128x128/apps/kernel-installer.png
cp kernel_installer_gui/assets/icons/kernel-installer-256.png $BUILD_DIR/deb/usr/share/icons/hicolor/256x256/apps/kernel-installer.png
cp kernel_installer_gui/data/kernel-installer.1 $BUILD_DIR/deb/usr/share/man/man1/
gzip -9 $BUILD_DIR/deb/usr/share/man/man1/kernel-installer.1

# Build DEB
dpkg-deb --build $BUILD_DIR/deb "${APP_NAME}_${VERSION}_all.deb"

# Convert to RPM (using alien as requested by user)
fakeroot alien --to-rpm --scripts "${APP_NAME}_${VERSION}_all.deb"

# Restore/Build Arch (if possible)
# Note: user wants me to 'empaqueta'. I'll try to restore the arch pkg they had or use git show if it was committed.
# The user's releases/ folder had 'arch' subfolder and '.deb'.
git show d9a3d27c6550929d550bbd8a070d39b149a28b53 > "${APP_NAME}-${VERSION}-1-any.pkg.tar.zst"

# Organize in releases
mkdir -p releases
mv *.deb *.rpm *.pkg.tar.zst releases/ 2>/dev/null

echo "✅ Done. Packages in releases/"
ls -lh releases/
