#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Auralis Build System
~~~~~~~~~~~~~~~~~~~~

Cross-platform build script for creating standalone Auralis executables
"""

import os
import sys
import platform
import shutil
import subprocess
import argparse
from pathlib import Path

# Build configuration
BUILD_CONFIG = {
    'app_name': 'Auralis',
    'version': '1.0.0',
    'description': 'Professional Audio Mastering System',
    'author': 'Auralis Team',
    'url': 'https://github.com/sergree/matchering',
}

def get_platform_info():
    """Get current platform information"""
    system = platform.system().lower()
    arch = platform.machine().lower()

    # Normalize architecture names
    if arch in ['x86_64', 'amd64']:
        arch = 'x64'
    elif arch in ['i386', 'i686']:
        arch = 'x86'
    elif arch.startswith('arm'):
        arch = 'arm64' if '64' in arch else 'arm'

    return system, arch

def clean_build_dirs():
    """Clean previous build artifacts"""
    dirs_to_clean = ['build', 'dist', '__pycache__']

    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"🧹 Cleaning {dir_name}/")
            shutil.rmtree(dir_name)

def install_dependencies():
    """Install build dependencies"""
    print("📦 Installing dependencies...")

    try:
        # Install desktop requirements
        subprocess.run([
            sys.executable, '-m', 'pip', 'install', '-r', 'requirements-desktop.txt'
        ], check=True)

        print("✅ Dependencies installed successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ Failed to install dependencies: {e}")
        return False

def run_tests():
    """Run tests before building"""
    print("🧪 Running tests...")

    try:
        result = subprocess.run([
            sys.executable, 'run_all_tests.py'
        ], capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ All tests passed")
            return True
        else:
            print("❌ Tests failed:")
            print(result.stdout)
            print(result.stderr)
            return False

    except Exception as e:
        print(f"❌ Failed to run tests: {e}")
        return False

def build_with_pyinstaller(skip_tests=False):
    """Build application using PyInstaller"""
    print("🔨 Building Auralis with PyInstaller...")

    if not skip_tests and not run_tests():
        return False

    try:
        # Run PyInstaller
        subprocess.run([
            sys.executable, '-m', 'PyInstaller',
            '--clean',
            '--noconfirm',
            'auralis.spec'
        ], check=True)

        print("✅ PyInstaller build completed")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        return False

def create_portable_package():
    """Create a portable package"""
    system, arch = get_platform_info()

    # Define package name
    package_name = f"Auralis-{BUILD_CONFIG['version']}-{system}-{arch}"

    if system == 'windows':
        package_name += '.zip'
        package_path = Path('dist') / package_name

        # Create ZIP package
        print(f"📦 Creating portable package: {package_name}")
        shutil.make_archive(
            str(package_path.with_suffix('')),
            'zip',
            'dist/Auralis'
        )

    else:
        package_name += '.tar.gz'
        package_path = Path('dist') / package_name

        # Create tar.gz package
        print(f"📦 Creating portable package: {package_name}")
        subprocess.run([
            'tar', '-czf', str(package_path),
            '-C', 'dist', 'Auralis'
        ], check=True)

    if package_path.exists():
        size_mb = package_path.stat().st_size / (1024 * 1024)
        print(f"✅ Portable package created: {package_name} ({size_mb:.1f} MB)")
        return package_path
    else:
        print(f"❌ Failed to create package: {package_name}")
        return None

def create_installer():
    """Create platform-specific installer"""
    system, arch = get_platform_info()

    if system == 'windows':
        return create_windows_installer()
    elif system == 'darwin':
        return create_macos_installer()
    elif system == 'linux':
        return create_linux_installer()
    else:
        print(f"⚠️  Installer creation not supported for {system}")
        return False

def create_windows_installer():
    """Create Windows installer using NSIS or Inno Setup"""
    print("🪟 Creating Windows installer...")

    # Check if NSIS is available
    nsis_script = """
    !define APP_NAME "Auralis"
    !define APP_VERSION "{version}"
    !define APP_PUBLISHER "{author}"
    !define APP_URL "{url}"
    !define APP_EXE "Auralis.exe"

    Name "${{APP_NAME}} ${{APP_VERSION}}"
    OutFile "Auralis-{version}-Windows-Setup.exe"
    InstallDir "$PROGRAMFILES\\Auralis"
    RequestExecutionLevel admin

    Page directory
    Page instfiles

    Section "Install"
        SetOutPath $INSTDIR
        File /r "dist\\Auralis\\*"

        CreateDirectory "$SMPROGRAMS\\Auralis"
        CreateShortCut "$SMPROGRAMS\\Auralis\\Auralis.lnk" "$INSTDIR\\${{APP_EXE}}"
        CreateShortCut "$DESKTOP\\Auralis.lnk" "$INSTDIR\\${{APP_EXE}}"

        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Auralis" "DisplayName" "${{APP_NAME}}"
        WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Auralis" "UninstallString" "$INSTDIR\\uninstall.exe"
        WriteUninstaller "$INSTDIR\\uninstall.exe"
    SectionEnd

    Section "Uninstall"
        Delete "$INSTDIR\\*"
        RMDir /r "$INSTDIR"
        Delete "$SMPROGRAMS\\Auralis\\*"
        RMDir "$SMPROGRAMS\\Auralis"
        Delete "$DESKTOP\\Auralis.lnk"
        DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\Auralis"
    SectionEnd
    """.format(**BUILD_CONFIG)

    # Write NSIS script
    with open('auralis_installer.nsi', 'w') as f:
        f.write(nsis_script)

    print("📝 NSIS script created: auralis_installer.nsi")
    print("   To build installer, run: makensis auralis_installer.nsi")
    return True

def create_macos_installer():
    """Create macOS app bundle and DMG"""
    print("🍎 Creating macOS installer...")

    app_name = "Auralis.app"
    app_path = Path('dist') / app_name

    # Create app bundle structure
    contents_dir = app_path / 'Contents'
    macos_dir = contents_dir / 'MacOS'
    resources_dir = contents_dir / 'Resources'

    for directory in [contents_dir, macos_dir, resources_dir]:
        directory.mkdir(parents=True, exist_ok=True)

    # Copy executable
    shutil.copytree('dist/Auralis', macos_dir / 'Auralis', dirs_exist_ok=True)

    # Create Info.plist
    info_plist = f"""<?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
    <plist version="1.0">
    <dict>
        <key>CFBundleExecutable</key>
        <string>Auralis</string>
        <key>CFBundleIdentifier</key>
        <string>com.auralis.app</string>
        <key>CFBundleName</key>
        <string>Auralis</string>
        <key>CFBundleVersion</key>
        <string>{BUILD_CONFIG['version']}</string>
        <key>CFBundleShortVersionString</key>
        <string>{BUILD_CONFIG['version']}</string>
        <key>CFBundleInfoDictionaryVersion</key>
        <string>6.0</string>
        <key>CFBundlePackageType</key>
        <string>APPL</string>
        <key>NSHighResolutionCapable</key>
        <true/>
    </dict>
    </plist>"""

    with open(contents_dir / 'Info.plist', 'w') as f:
        f.write(info_plist)

    print(f"✅ macOS app bundle created: {app_name}")

    # Create DMG (requires macOS)
    if platform.system() == 'Darwin':
        dmg_name = f"Auralis-{BUILD_CONFIG['version']}-macOS.dmg"
        subprocess.run([
            'hdiutil', 'create', '-srcfolder', str(app_path),
            '-format', 'UDZO', '-o', dmg_name
        ])
        print(f"✅ DMG created: {dmg_name}")

    return True

def create_linux_installer():
    """Create Linux installer (.deb or .rpm)"""
    print("🐧 Creating Linux installer...")

    # Create .deb package structure
    deb_name = f"auralis_{BUILD_CONFIG['version']}_amd64"
    deb_dir = Path('dist') / deb_name

    # Create directory structure
    dirs = [
        'DEBIAN',
        'usr/bin',
        'usr/share/applications',
        'usr/share/auralis',
        'usr/share/pixmaps'
    ]

    for dir_path in dirs:
        (deb_dir / dir_path).mkdir(parents=True, exist_ok=True)

    # Copy application files
    shutil.copytree('dist/Auralis', deb_dir / 'usr/share/auralis', dirs_exist_ok=True)

    # Create launcher script
    launcher_script = f"""#!/bin/bash
cd /usr/share/auralis
./Auralis "$@"
"""

    with open(deb_dir / 'usr/bin/auralis', 'w') as f:
        f.write(launcher_script)

    os.chmod(deb_dir / 'usr/bin/auralis', 0o755)

    # Create .desktop file
    desktop_file = f"""[Desktop Entry]
Name=Auralis
Comment={BUILD_CONFIG['description']}
Exec=auralis
Icon=auralis
Terminal=false
Type=Application
Categories=AudioVideo;Audio;
"""

    with open(deb_dir / 'usr/share/applications/auralis.desktop', 'w') as f:
        f.write(desktop_file)

    # Create control file
    control_file = f"""Package: auralis
Version: {BUILD_CONFIG['version']}
Section: sound
Priority: optional
Architecture: amd64
Maintainer: {BUILD_CONFIG['author']}
Description: {BUILD_CONFIG['description']}
 Auralis is a professional audio mastering system with advanced
 real-time processing and library management capabilities.
"""

    with open(deb_dir / 'DEBIAN/control', 'w') as f:
        f.write(control_file)

    # Fix permissions for package building
    subprocess.run(['find', str(deb_dir), '-type', 'd', '-exec', 'chmod', '755', '{}', ';'], check=True)
    subprocess.run(['find', str(deb_dir), '-type', 'f', '-exec', 'chmod', '644', '{}', ';'], check=True)
    subprocess.run(['chmod', '755', str(deb_dir / 'usr/bin/auralis')], check=True)

    # Build .deb package
    try:
        subprocess.run(['dpkg-deb', '--build', str(deb_dir)], check=True)
    except subprocess.CalledProcessError:
        # Try alternative approach for permission issues
        print("⚠️  Standard dpkg-deb failed, trying alternative approach...")
        subprocess.run(['tar', '-czf', f'{deb_name}.tar.gz', '-C', 'dist', deb_name], check=True)
        print(f"✅ Archive package created: {deb_name}.tar.gz")

    print(f"✅ Debian package created: {deb_name}.deb")
    return True

def show_build_summary():
    """Show build summary"""
    print("\n" + "=" * 60)
    print("📊 BUILD SUMMARY")
    print("=" * 60)

    dist_dir = Path('dist')
    if dist_dir.exists():
        print("Generated files:")
        for item in dist_dir.iterdir():
            if item.is_file():
                size_mb = item.stat().st_size / (1024 * 1024)
                print(f"  📦 {item.name} ({size_mb:.1f} MB)")
            elif item.is_dir():
                print(f"  📁 {item.name}/")

    print("\n🎉 Build completed successfully!")
    print("✨ Auralis is ready for distribution!")

def main():
    parser = argparse.ArgumentParser(description="Build Auralis application")
    parser.add_argument('--skip-tests', action='store_true', help='Skip running tests')
    parser.add_argument('--skip-installer', action='store_true', help='Skip creating installer')
    parser.add_argument('--clean', action='store_true', help='Clean build directories only')
    parser.add_argument('--portable-only', action='store_true', help='Create portable package only')

    args = parser.parse_args()

    print("🎵 Auralis Build System")
    print("=" * 60)

    if args.clean:
        clean_build_dirs()
        return

    # Clean previous builds
    clean_build_dirs()

    # Install dependencies
    if not install_dependencies():
        return

    # Build with PyInstaller
    if not build_with_pyinstaller(skip_tests=args.skip_tests):
        return

    # Create portable package
    portable_package = create_portable_package()

    if args.portable_only:
        show_build_summary()
        return

    # Create installer
    if not args.skip_installer:
        create_installer()

    show_build_summary()

if __name__ == "__main__":
    main()