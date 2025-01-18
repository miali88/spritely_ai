#!/bin/bash
set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Installing Spritely AI Assistant...${NC}"

# Check Python version
python_version=$(python3 -c 'import sys; print(".".join(map(str, sys.version_info[:2])))')
required_version="3.9"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${YELLOW}Error: Python $required_version or higher is required (found $python_version)${NC}"
    exit 1
fi

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${GREEN}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install or upgrade pip
echo -e "${GREEN}Upgrading pip...${NC}"
pip install --upgrade pip

# Install the package in development mode
echo -e "${GREEN}Installing package dependencies...${NC}"
pip install -e ".[dev]"

# Check for required system dependencies
echo -e "${GREEN}Checking system dependencies...${NC}"

# Check for PortAudio (required for PyAudio)
if ! brew list portaudio &>/dev/null; then
    echo -e "${YELLOW}Installing PortAudio...${NC}"
    brew install portaudio
fi

# Create application shortcuts
echo -e "${GREEN}Creating application shortcuts...${NC}"
SHORTCUT_DIR="$HOME/Applications"
mkdir -p "$SHORTCUT_DIR"

# Create a shell script to launch the application
cat > "$SHORTCUT_DIR/spritely" <<EOL
#!/bin/bash
source "$(pwd)/venv/bin/activate"
python -m spritely "\$@"
EOL

chmod +x "$SHORTCUT_DIR/spritely"

echo -e "${GREEN}Installation complete!${NC}"
echo -e "You can now run Spritely by typing 'spritely' in the terminal"
echo -e "Make sure to set up your API keys in the .env file" 