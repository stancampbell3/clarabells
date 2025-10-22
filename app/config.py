"""Configuration management for Clara server."""
import os
import json
from pathlib import Path
from typing import Optional


class Config:
    """Clara server configuration."""
    
    def __init__(self):
        # Server settings
        self.host: str = "0.0.0.0"
        self.port: int = 8000
        
        # Audio cache settings
        self.audio_cache_ttl_seconds: int = 3600  # 1 hour default
        self.audio_cache_cleanup_interval_seconds: int = 300  # Check every 5 minutes
        
        # Authentication
        self.bearer_token: str = "mysecrettoken"
        
        # Load from config file if exists
        self._load_from_file()
    
    def _load_from_file(self):
        """Load configuration from clara_config.json if it exists."""
        config_path = Path("clara_config.json")
        if config_path.exists():
            try:
                with open(config_path) as f:
                    data = json.load(f)
                
                # Override defaults with values from file
                self.host = data.get("host", self.host)
                self.port = data.get("port", self.port)
                self.audio_cache_ttl_seconds = data.get("audio_cache_ttl_seconds", self.audio_cache_ttl_seconds)
                self.audio_cache_cleanup_interval_seconds = data.get(
                    "audio_cache_cleanup_interval_seconds", 
                    self.audio_cache_cleanup_interval_seconds
                )
                self.bearer_token = data.get("bearer_token", self.bearer_token)
                
            except Exception as e:
                print(f"Warning: Failed to load config from {config_path}: {e}")
        
        # Environment variables override file config
        self.host = os.getenv("CLARA_HOST", self.host)
        self.port = int(os.getenv("CLARA_PORT", str(self.port)))
        self.audio_cache_ttl_seconds = int(os.getenv("CLARA_AUDIO_TTL", str(self.audio_cache_ttl_seconds)))
        self.bearer_token = os.getenv("CLARA_BEARER_TOKEN", self.bearer_token)
    
    def save_template(self, path: str = "clara_config.json"):
        """Save a template configuration file."""
        template = {
            "host": self.host,
            "port": self.port,
            "audio_cache_ttl_seconds": self.audio_cache_ttl_seconds,
            "audio_cache_cleanup_interval_seconds": self.audio_cache_cleanup_interval_seconds,
            "bearer_token": self.bearer_token,
            "_comment": "TTL is time-to-live in seconds. Generated audio files older than this will be deleted. Set to 0 to disable cleanup."
        }
        with open(path, 'w') as f:
            json.dump(template, f, indent=2)


# Global config instance
config = Config()

