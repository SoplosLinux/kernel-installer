#!/bin/bash
# Kernel Installer Package Builder (Multi-Distro Edition)
set -e

APP_NAME="kernel-installer"
VERSION="1.0.1"
BUILD_DIR="build_packages"
RPM_BUILD_DIR="$HOME/rpmbuild"

echo "📦 Starting proper packaging for multiple distributions..."

# 1. Clean previous builds
rm -rf "$BUILD_DIR" releases
mkdir -p releases

# Helper function to create shared structure
prepare_base_structure() {
    local target_dir=$1
    mkdir -p "$target_dir/usr/bin"
    mkdir -p "$target_dir/usr/share/kernel-installer"
    mkdir -p "$target_dir/usr/share/applications"
    mkdir -p "$target_dir/usr/share/metainfo"
    mkdir -p "$target_dir/usr/share/icons/hicolor/48x48/apps"
    mkdir -p "$target_dir/usr/share/icons/hicolor/128x128/apps"
    mkdir -p "$target_dir/usr/share/icons/hicolor/256x256/apps"
    mkdir -p "$target_dir/usr/share/man/man1"

    # Copy files
    cp bin/kernel-installer "$target_dir/usr/bin/"
    chmod +x "$target_dir/usr/bin/kernel-installer"
    cp main.py README.md LICENSE CHANGELOG.md setup.py "$target_dir/usr/share/kernel-installer/"
    cp -r kernel_installer_gui "$target_dir/usr/share/kernel-installer/"
    cp kernel_installer_gui/data/org.soplos.kernel-installer.desktop "$target_dir/usr/share/applications/"
    cp kernel_installer_gui/data/org.soplos.kernel-installer.metainfo.xml "$target_dir/usr/share/metainfo/"
    cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-48.png "$target_dir/usr/share/icons/hicolor/48x48/apps/org.soplos.kernel-installer.png"
    cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-128.png "$target_dir/usr/share/icons/hicolor/128x128/apps/org.soplos.kernel-installer.png"
    cp kernel_installer_gui/assets/icons/org.soplos.kernel-installer-256.png "$target_dir/usr/share/icons/hicolor/256x256/apps/org.soplos.kernel-installer.png"
    
    if [ -f kernel_installer_gui/data/org.soplos.kernel-installer.1 ]; then
        cp kernel_installer_gui/data/org.soplos.kernel-installer.1 "$target_dir/usr/share/man/man1/"
        gzip -9 -f "$target_dir/usr/share/man/man1/org.soplos.kernel-installer.1"
    fi
}

# --- DEBIAN FAMILY (.deb) ---
for target in debian ubuntu; do
    echo "🔹 Building Debian-based ($target) .deb..."
    DEB_TARGET_DIR="$BUILD_DIR/deb-$target"
    mkdir -p "$DEB_TARGET_DIR/DEBIAN"
    prepare_base_structure "$DEB_TARGET_DIR"
    cp "packaging/debian/control.$target" "$DEB_TARGET_DIR/DEBIAN/control"
    dpkg-deb --build --root-owner-group "$DEB_TARGET_DIR" "releases/${APP_NAME}_${VERSION}_${target}.deb"
done

# --- RPM FAMILY (.rpm) ---
for target in fedora mageia; do
    echo "🔹 Building RPM-based ($target) .rpm..."
    # Create RPM structure and clean previous build for this package
    mkdir -p "$RPM_BUILD_DIR"/{BUILD,RPMS,SOURCES,SPECS,SRPMS}
    rm -f "$RPM_BUILD_DIR"/RPMS/noarch/${APP_NAME}-${VERSION}-*.noarch.rpm
    
    # Create source tarball
    TAR_NAME="${APP_NAME}-${VERSION}"
    mkdir -p "$BUILD_DIR/$TAR_NAME"
    cp -r bin kernel_installer_gui main.py README.md LICENSE CHANGELOG.md setup.py "$BUILD_DIR/$TAR_NAME/"
    tar -czf "$RPM_BUILD_DIR/SOURCES/${TAR_NAME}.tar.gz" -C "$BUILD_DIR" "${TAR_NAME}"
    
    # Copy specific spec
    cp "packaging/rpm/$target.spec" "$RPM_BUILD_DIR/SPECS/kernel-installer.spec"
    
    if command -v rpmbuild >/dev/null; then
        rpmbuild -bb "$RPM_BUILD_DIR/SPECS/kernel-installer.spec" --define "_topdir $RPM_BUILD_DIR"
        # Usar comodín para el release para evitar fallos si cambia en el .spec
        cp "$RPM_BUILD_DIR"/RPMS/noarch/kernel-installer-${VERSION}-*.noarch.rpm "releases/kernel-installer-${VERSION}-${target}.noarch.rpm"
    else
        echo "⚠️ rpmbuild not found. Skipping RPM build for $target."
    fi
done

# --- ARCH LINUX ---
echo "🔹 Building Arch Linux (.pkg.tar.zst) [Manual]..."
ARCH_DIR="$BUILD_DIR/arch/pkg"
prepare_base_structure "$ARCH_DIR"
# Generate .PKGINFO
cat > "$ARCH_DIR/.PKGINFO" <<EOF
pkgname = kernel-installer
pkgver = ${VERSION}
pkgdesc = Graphical interface for downloading, compiling and installing Linux kernels
url = https://github.com/SoplosLinux/kernel-installer
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

if tar --help | grep -q zstd; then
    tar -C "$ARCH_DIR" -c --zstd -f "releases/${APP_NAME}-${VERSION}-arch.pkg.tar.zst" .
elif command -v zstd >/dev/null; then
    tar -C "$ARCH_DIR" -c . | zstd - > "releases/${APP_NAME}-${VERSION}-arch.pkg.tar.zst"
fi

# Cleanup
echo "✅ Packaging complete. Files in 'releases/':"
ls -lh releases/
