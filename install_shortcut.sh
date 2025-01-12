#!/bin/bash

# Configuration
SCRIPT_NAME="TranscriptionShortcut"
SHORTCUT="cmd+alt+k"

# Create the workflow directory
WORKFLOW_DIR="/Users/$USER/Library/Services/${SCRIPT_NAME}.workflow"
mkdir -p "$WORKFLOW_DIR/Contents"

# Create Info.plist
cat << EOF > "$WORKFLOW_DIR/Contents/Info.plist"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>NSServices</key>
    <array>
        <dict>
            <key>NSMenuItem</key>
            <dict>
                <key>default</key>
                <string>Start Transcription</string>
            </dict>
            <key>NSMessage</key>
            <string>runWorkflowAsService</string>
        </dict>
    </array>
</dict>
</plist>
EOF

# Create document.wflow
cat << EOF > "$WORKFLOW_DIR/Contents/document.wflow"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>AMApplicationBuild</key>
    <string>521.1</string>
    <key>AMApplicationVersion</key>
    <string>2.10</string>
    <key>AMDocumentVersion</key>
    <string>2</string>
    <key>actions</key>
    <array>
        <dict>
            <key>action</key>
            <dict>
                <key>AMActionVersion</key>
                <string>2.0.3</string>
                <key>AMApplication</key>
                <array>
                    <string>Automator</string>
                </array>
                <key>AMParameterProperties</key>
                <dict>
                    <key>source</key>
                    <dict/>
                </dict>
                <key>AMProvides</key>
                <dict>
                    <key>Container</key>
                    <string>List</string>
                    <key>Types</key>
                    <array>
                        <string>com.apple.applescript.object</string>
                    </array>
                </dict>
                <key>ActionBundlePath</key>
                <string>/System/Library/Automator/Run Shell Script.action</string>
                <key>ActionName</key>
                <string>Run Shell Script</string>
                <key>ActionParameters</key>
                <dict>
                    <key>source</key>
                    <string>#!/bin/bash
DIR="\$( cd "\$( dirname "\${BASH_SOURCE[0]}" )" && pwd )"
"\$DIR/venv/bin/python3" "\$DIR/mac_mic.py" --from-shortcut</string>
                </dict>
                <key>BundleIdentifier</key>
                <string>com.apple.Automator.RunShellScript</string>
                <key>CFBundleVersion</key>
                <string>2.0.3</string>
            </dict>
        </dict>
    </array>
</dict>
</plist>
EOF

echo "✅ Service workflow created!"
echo "Now, please:"
echo "1. Open System Preferences"
echo "2. Go to Keyboard > Shortcuts > Services"
echo "3. Find 'Start Transcription' under General"
echo "4. Click on 'none' next to it and press Cmd+Option+K to set the shortcut" 