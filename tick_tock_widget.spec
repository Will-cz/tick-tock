# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

# Define the analysis for the main application
a = Analysis(
    ['src/tick_tock.py'],  # Main entry point
    pathex=[],
    binaries=[],
    datas=[
        # Embed a prototype marker file to identify prototype builds
        ('src/tick_tock_widget/prototype_marker.txt', '.'),
        ('assets/tick_tock_icon.ico', 'assets/'),
    ],
    hiddenimports=[
        'tick_tock_widget.main',
        'tick_tock_widget.tick_tock_widget',
        'tick_tock_widget.config',
        'tick_tock_widget.project_data',
        'tick_tock_widget.project_management',
        'tick_tock_widget.minimized_widget',
        'tick_tock_widget.monthly_report',
        'tick_tock_widget.theme_colors',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='TickTockWidget',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # Set to False for windowed app (no console)
    disable_windowing_system=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='assets/tick_tock_icon.ico',  # Icon for the executable
)
