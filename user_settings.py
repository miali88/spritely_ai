# Default settings
DEFAULT_SETTINGS = {
    "microphone_index": None  # None means use system default
}

# Current settings
settings = DEFAULT_SETTINGS.copy()

def save_settings():
    """Save current settings to file"""
    import json
    with open('settings.json', 'w') as f:
        json.dump(settings, f)

def load_settings():
    """Load settings from file"""
    import json
    import os
    global settings
    
    try:
        if os.path.exists('settings.json'):
            with open('settings.json', 'r') as f:
                loaded_settings = json.load(f)
                settings.update(loaded_settings)
    except Exception as e:
        print(f"Error loading settings: {e}")
        settings = DEFAULT_SETTINGS.copy()

# Load settings on import
load_settings()
