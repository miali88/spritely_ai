#!/usr/bin/env python3
"""
Build script for creating a macOS application bundle.
"""

import os
import sys
import shutil
from pathlib import Path
import subprocess
import PyInstaller.__main__

def ensure_resources():
    """Ensure all required resources are available."""
    resources_dir = Path("src/spritely/resources")
    resources_dir.mkdir(parents=True, exist_ok=True)
    
    # Check for icon file
    icon_file = resources_dir / "icon.icns"
    if not icon_file.exists():
        print("Warning: No application icon found at", icon_file)
        print("Using default icon")

def build_app():
    """Build the macOS application bundle."""
    print("Building Spritely macOS application...")
    
    # Ensure resources are available
    ensure_resources()
    
    # PyInstaller arguments
    args = [
        'src/spritely/main.py',
        '--name=Spritely',
        '--windowed',
        '--noconfirm',
        '--clean',
        '--add-data=src/spritely/resources:resources',
        '--hidden-import=tkinter',
        '--hidden-import=pyaudio',
        '--hidden-import=sounddevice',
        '--collect-all=anthropic',
        '--collect-all=elevenlabs',
        '--collect-all=groq',
        '--collect-all=deepgram',
        '--osx-bundle-identifier=com.spritely.app',
    ]
    
    # Add icon if available
    icon_path = Path("src/spritely/resources/icon.icns")
    if icon_path.exists():
        args.append(f'--icon={icon_path}')
    
    try:
        PyInstaller.__main__.run(args)
        print("\nBuild completed successfully!")
        print(f"Application bundle created at: {os.path.abspath('dist/Spritely.app')}")
    except Exception as e:
        print(f"Error building application: {e}", file=sys.stderr)
        sys.exit(1)

def create_dmg():
    """Create a DMG installer for the application."""
    try:
        subprocess.run([
            'create-dmg',
            '--volname', 'Spritely Installer',
            '--volicon', 'src/spritely/resources/icon.icns',
            '--window-pos', '200', '120',
            '--window-size', '800', '400',
            '--icon-size', '100',
            '--icon', 'Spritely.app', '200', '200',
            '--hide-extension', 'Spritely.app',
            '--app-drop-link', '600', '200',
            'dist/Spritely.dmg',
            'dist/Spritely.app'
        ], check=True)
        print("\nDMG installer created successfully!")
    except subprocess.CalledProcessError as e:
        print(f"Error creating DMG: {e}", file=sys.stderr)
        print("Note: To create DMG installers, install create-dmg:")
        print("brew install create-dmg")
    except FileNotFoundError:
        print("create-dmg not found. Install with: brew install create-dmg")

if __name__ == '__main__':
    build_app()
    create_dmg() 