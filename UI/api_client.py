import requests
import json
from typing import Dict, Optional, List


class APIClient:
    def __init__(self, base_url="http://localhost:5000"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.timeout = 10
    
    def get_status(self) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting status: {e}")
            return None
    
    def add_project(self, project_path: str) -> bool:
        try:
            data = {"path": project_path}
            response = self.session.post(f"{self.base_url}/api/track", json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"Error adding project: {e}")
            return False
    
    def remove_project(self, project_path: str) -> bool:
        try:
            data = {"path": project_path}
            response = self.session.post(f"{self.base_url}/api/untrack", json=data)
            response.raise_for_status()
            result = response.json()
            return result.get("success", False)
        except requests.RequestException as e:
            print(f"Error removing project: {e}")
            return False
    
    def send_heartbeat(self, file_path: str) -> bool:
        try:
            data = {"file": file_path}
            response = self.session.post(f"{self.base_url}/api/heartbeat", json=data)
            response.raise_for_status()
            return True
        except requests.RequestException as e:
            print(f"Error sending heartbeat: {e}")
            return False
    
    def get_config(self) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.base_url}/api/config")
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error getting config: {e}")
            return None
    
    def update_config(self, config: Dict) -> bool:
        try:
            response = self.session.post(f"{self.base_url}/api/config", json=config)
            response.raise_for_status()
            result = response.json()
            print(f"Config update response: {result}")
            return True
        except requests.RequestException as e:
            print(f"Error updating config: {e}")
            return False
    
    def test_connection(self) -> bool:
        try:
            response = self.session.get(f"{self.base_url}/api/status")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_tracked_projects(self) -> List[str]:
        try:
            status = self.get_status()
            if status and 'stats' in status:
                return status['stats'].get('tracked_directories', [])
            return []
        except Exception as e:
            print(f"Error getting tracked projects: {e}")
            return []
    
    def get_editor_config(self) -> Optional[str]:
        """Get the current editor configuration from the API"""
        try:
            config = self.get_config()
            if config:
                return config.get('editor_name', 'unitime')
            return 'unitime'
        except Exception as e:
            print(f"Error getting editor config: {e}")
            return 'unitime'
    
    def set_editor_config(self, editor_name: str) -> bool:
        """Set the editor name in the API configuration"""
        try:
            return self.update_config({'ide': editor_name})
        except Exception as e:
            print(f"Error setting editor config: {e}")
            return False
