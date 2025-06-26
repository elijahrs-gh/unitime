import json
import os
from pathlib import Path
from typing import Dict, Optional


class SettingsManager:
    def __init__(self, config_dir=None):
        if config_dir is None:
            config_dir = Path.home() / ".unitime"
        
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        
        self.settings_file = self.config_dir / "ui_settings.json"
        self.default_settings = {
            "api_key": "",
            "api_url": "https://hackatime.hackclub.com/api/v1",
            "default_project": "",
            "ide": "Zed",
            "heartbeat_interval": 30,
            "auto_start": True,
            "debug_mode": False,
            "window_geometry": None,
            "theme": "default"
        }
    
    def load_settings(self) -> Dict:
        try:
            if self.settings_file.exists():
                with open(self.settings_file, 'r') as f:
                    settings = json.load(f)
                
                merged_settings = self.default_settings.copy()
                merged_settings.update(settings)
                return merged_settings
            else:
                return self.default_settings.copy()
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error loading settings: {e}")
            return self.default_settings.copy()
    
    def save_settings(self, settings: Dict) -> bool:
        try:
            self.config_dir.mkdir(exist_ok=True)
            
            with open(self.settings_file, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return True
        
        except (IOError, TypeError) as e:
            print(f"Error saving settings: {e}")
            return False
    
    def get_setting(self, key: str, default=None):
        settings = self.load_settings()
        return settings.get(key, default)
    
    def set_setting(self, key: str, value) -> bool:
        settings = self.load_settings()
        settings[key] = value
        return self.save_settings(settings)
    
    def reset_to_defaults(self) -> bool:
        return self.save_settings(self.default_settings.copy())
    
    def backup_settings(self, backup_path: Optional[str] = None) -> bool:
        try:
            if backup_path is None:
                backup_path = self.config_dir / "ui_settings_backup.json"
            
            settings = self.load_settings()
            
            with open(backup_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return True
        
        except (IOError, TypeError) as e:
            print(f"Error creating backup: {e}")
            return False
    
    def restore_from_backup(self, backup_path: str) -> bool:
        try:
            with open(backup_path, 'r') as f:
                settings = json.load(f)
            
            return self.save_settings(settings)
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error restoring from backup: {e}")
            return False
    
    def get_config_dir(self) -> Path:
        return self.config_dir
    
    def export_settings(self, export_path: str) -> bool:
        try:
            settings = self.load_settings()
            
            with open(export_path, 'w') as f:
                json.dump(settings, f, indent=2)
            
            return True
        
        except (IOError, TypeError) as e:
            print(f"Error exporting settings: {e}")
            return False
    
    def import_settings(self, import_path: str) -> bool:
        try:
            with open(import_path, 'r') as f:
                settings = json.load(f)
            
            valid_settings = {}
            for key, value in settings.items():
                if key in self.default_settings:
                    valid_settings[key] = value
            
            current_settings = self.load_settings()
            current_settings.update(valid_settings)
            
            return self.save_settings(current_settings)
        
        except (json.JSONDecodeError, IOError) as e:
            print(f"Error importing settings: {e}")
            return False
