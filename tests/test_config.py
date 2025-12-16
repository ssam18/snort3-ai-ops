"""Tests for the configuration module."""

import pytest
from pathlib import Path
from core.config import Config, load_config, expand_env_vars
import os


class TestConfig:
    """Test configuration loading and validation."""
    
    def test_default_config_creation(self):
        """Test creating config with defaults."""
        config = Config()
        
        assert config.event_stream.type == 'zeromq'
        assert config.event_stream.endpoint == 'tcp://127.0.0.1:5555'
        assert config.agents.threat_intelligence.enabled is True
        assert config.database.type == 'sqlite'
    
    def test_load_config_from_file(self, config_path):
        """Test loading configuration from YAML file."""
        config = load_config(str(config_path))
        
        assert isinstance(config, Config)
        assert config.event_stream.endpoint == 'tcp://127.0.0.1:5555'
        assert config.agents.threat_intelligence.enabled is True
    
    def test_config_file_not_found(self):
        """Test error handling for missing config file."""
        with pytest.raises(FileNotFoundError):
            load_config('nonexistent/config.yaml')
    
    def test_expand_env_vars(self):
        """Test environment variable expansion."""
        os.environ['TEST_VAR'] = 'test_value'
        
        data = {
            'key1': '${TEST_VAR}',
            'key2': {
                'nested': '${TEST_VAR}'
            },
            'key3': ['${TEST_VAR}', 'static']
        }
        
        expanded = expand_env_vars(data)
        
        assert expanded['key1'] == 'test_value'
        assert expanded['key2']['nested'] == 'test_value'
        assert expanded['key3'][0] == 'test_value'
        
        del os.environ['TEST_VAR']
