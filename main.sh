#!/bin/bash

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Configuration for the shortcut installer
SCRIPT_NAME="TranscriptionApp"
SHORTCUT="cmd+shift+t"  # You can change this to your preferred shortcut

# Function to check if shortcut is installed
check_shortcut_installed() {
    if [ -d "/Applications/${SCRIPT_NAME}.app" ]; then
        return 0  # true
    else
        return 1  # false
    fi
}

# Function to install shortcut
install_shortcut() {
    echo -e "${BLUE}Installing keyboard shortcut...${NC}"
    
    # Create the script content that will be triggered by the shortcut
    SCRIPT_CONTENT="#!/bin/bash
    cd \"${DIR}\"
    ./start_transcription.sh"
    
    # Source and run the install_shortcut script with our configuration
    source "${DIR}/install_shortcut.sh"
    
    echo -e "${GREEN}Shortcut installation complete!${NC}"
}

# Main execution
echo "🎤 Transcription App Setup"

# Check if shortcut needs to be installed
if ! check_shortcut_installed; then
    echo "First-time setup detected!"
    install_shortcut
    
    echo -e "\n${BLUE}Please grant accessibility permissions:${NC}"
    echo "System Preferences → Security & Privacy → Privacy → Accessibility"
    open "x-apple.systempreferences:com.apple.preference.security?Privacy_Accessibility"
    
    echo -e "\n${GREEN}Setup complete! You can now use ${SHORTCUT} to start transcription${NC}"
else
    echo "Shortcut already installed. Starting transcription..."
    # Run the transcription script
    "${DIR}/start_transcription.sh"
fi