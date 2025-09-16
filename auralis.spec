# -*- mode: python ; coding: utf-8 -*-

"""
PyInstaller spec file for Auralis Audio Mastering System
"""

import os
import sys
from pathlib import Path

# Get the directory containing this spec file
spec_dir = Path(SPECPATH)
project_root = spec_dir

# Add project root to Python path
sys.path.insert(0, str(project_root))

# Define application metadata
APP_NAME = 'Auralis'
APP_VERSION = '1.0.0'
APP_DESCRIPTION = 'Professional Audio Mastering System'
APP_AUTHOR = 'Auralis Team'

# Main script
main_script = str(project_root / 'auralis_gui.py')

# Additional data files and folders to include
datas = [
    # Include the entire auralis package
    (str(project_root / 'auralis'), 'auralis'),
    # Include matchering core
    (str(project_root / 'matchering'), 'matchering'),
    # Include examples
    (str(project_root / 'examples'), 'examples'),
    # Include test files for demo
    (str(project_root / 'test_files'), 'test_files'),
    # Include docs for help
    (str(project_root / 'docs' / 'README.md'), 'docs'),
    # Include license
    (str(project_root / 'LICENSE'), '.'),
]

# Hidden imports needed by the application
hiddenimports = [
    # Core dependencies
    'numpy',
    'scipy',
    'soundfile',
    'resampy',
    'statsmodels',
    'sqlalchemy',
    'customtkinter',
    'tkinterdnd2',
    'mutagen',
    'psutil',

    # Auralis modules
    'auralis',
    'auralis.core',
    'auralis.dsp',
    'auralis.io',
    'auralis.library',
    'auralis.player',
    'auralis.utils',
    'auralis.library.models',
    'auralis.library.manager',
    'auralis.library.scanner',
    'auralis.player.enhanced_audio_player',
    'auralis.player.realtime_processor',

    # Matchering modules
    'matchering',
    'matchering.core',
    'matchering.dsp',
    'matchering.limiter',
    'matchering.log',
    'matchering.stage_helpers',

    # GUI related
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'threading',
    'pathlib',

    # Audio formats
    'mutagen.mp3',
    'mutagen.flac',
    'mutagen.wav',
    'mutagen.ogg',
    'mutagen.m4a',
    'mutagen.id3',

    # SQLAlchemy
    'sqlalchemy.sql.default_comparator',
    'sqlalchemy.dialects.sqlite',
    'sqlalchemy.pool',
]

# Files to exclude from the build
excludes = [
    # Web-related modules we don't need
    'fastapi',
    'uvicorn',
    'pydantic',
    'alembic',
    'asyncpg',
    'redis',
    'passlib',
    'jose',

    # Development tools
    'pytest',
    'coverage',
    'pylint',
    'black',

    # Large unused modules
    'matplotlib',
    'pandas',
    'jupyter',
    'notebook',
]

# Analysis configuration
a = Analysis(
    [main_script],
    pathex=[str(project_root)],
    binaries=[],
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=excludes,
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

# Remove duplicate files
pyz = PYZ(a.pure, a.zipped_data, cipher=None)

# Create executable
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name=APP_NAME,
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,  # Compress executable
    console=False,  # No console window (GUI app)
    disable_windowed_traceback=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=str(project_root / 'images' / 'logo.png') if (project_root / 'images' / 'logo.png').exists() else None,
)

# Create distribution folder
coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name=APP_NAME,
)