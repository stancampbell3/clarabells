"""Tests for configuration management."""
import os
import json
import tempfile
from pathlib import Path
from app.config import Config


def test_config_defaults():
    """Test that default configuration values are set correctly."""
    config = Config()
    assert config.host == "0.0.0.0"
    assert config.port == 8000
    assert config.audio_cache_ttl_seconds == 3600
    assert config.audio_cache_cleanup_interval_seconds == 300
    assert config.bearer_token == "mysecrettoken"


def test_config_from_file(tmp_path):
    """Test loading configuration from a JSON file."""
    # Create a temporary config file
    config_data = {
        "host": "127.0.0.1",
        "port": 9000,
        "audio_cache_ttl_seconds": 7200,
        "bearer_token": "test-token-123"
    }
    
    config_file = tmp_path / "clara_config.json"
    with open(config_file, 'w') as f:
        json.dump(config_data, f)
    
    # Change to the temp directory so Config finds the file
    original_dir = os.getcwd()
    try:
        os.chdir(tmp_path)
        config = Config()
        
        assert config.host == "127.0.0.1"
        assert config.port == 9000
        assert config.audio_cache_ttl_seconds == 7200
        assert config.bearer_token == "test-token-123"
    finally:
        os.chdir(original_dir)


def test_config_env_override():
    """Test that environment variables override config file."""
    # Set environment variables
    os.environ["CLARA_HOST"] = "192.168.1.1"
    os.environ["CLARA_PORT"] = "5000"
    os.environ["CLARA_AUDIO_TTL"] = "1800"
    os.environ["CLARA_BEARER_TOKEN"] = "env-token"
    
    try:
        config = Config()
        
        assert config.host == "192.168.1.1"
        assert config.port == 5000
        assert config.audio_cache_ttl_seconds == 1800
        assert config.bearer_token == "env-token"
    finally:
        # Clean up environment variables
        del os.environ["CLARA_HOST"]
        del os.environ["CLARA_PORT"]
        del os.environ["CLARA_AUDIO_TTL"]
        del os.environ["CLARA_BEARER_TOKEN"]


def test_config_save_template(tmp_path):
    """Test saving a configuration template."""
    config = Config()
    template_path = tmp_path / "test_config.json"
    
    config.save_template(str(template_path))
    
    assert template_path.exists()
    
    with open(template_path) as f:
        data = json.load(f)
    
    assert "host" in data
    assert "port" in data
    assert "audio_cache_ttl_seconds" in data
    assert "bearer_token" in data
    assert "_comment" in data

