from pathlib import Path
import json
from typing import Dict, Any, Optional
import logging
from pydantic import BaseModel, Field

class UserSettings(BaseModel):
    voice_id: str = Field(default="")
    model: str = Field(default="claude-3-opus-20240229")
    transcription_provider: str = Field(default="deepgram")
    voice_provider: str = Field(default="elevenlabs")
    auto_save: bool = Field(default=True)

class Config:
    def __init__(self):
        self.config_dir = Path.home() / ".spritely"
        self.config_file = self.config_dir / "config.json"
        self.settings_file = self.config_dir / "settings.json"
        self.ensure_config_dir()
        self.settings = self.load_settings()
        
    def ensure_config_dir(self) -> None:
        """Ensure the configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)
        
    def load_settings(self) -> UserSettings:
        """Load user settings from file or create defaults."""
        if self.settings_file.exists():
            try:
                data = json.loads(self.settings_file.read_text())
                return UserSettings(**data)
            except Exception as e:
                logging.error(f"Error loading settings: {e}")
                return UserSettings()
        return UserSettings()
    
    def save_settings(self) -> None:
        """Save current settings to file."""
        try:
            self.settings_file.write_text(self.settings.model_dump_json(indent=2))
        except Exception as e:
            logging.error(f"Error saving settings: {e}")
    
    def update_settings(self, **kwargs) -> None:
        """Update settings with new values."""
        for key, value in kwargs.items():
            if hasattr(self.settings, key):
                setattr(self.settings, key, value)
        if self.settings.auto_save:
            self.save_settings()

    def get_api_keys(self) -> Dict[str, Optional[str]]:
        """Get API keys from environment or config."""
        from dotenv import load_dotenv
        import os
        
        load_dotenv()
        
        return {
            "anthropic": os.getenv("ANTHROPIC_API_KEY"),
            "elevenlabs": os.getenv("ELEVENLABS_API_KEY"),
            "groq": os.getenv("GROQ_API_KEY"),
            "deepgram": os.getenv("DEEPGRAM_API_KEY"),
        }

# Global config instance
config = Config() 