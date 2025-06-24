import requests
import json
import argparse
import sys
from typing import Optional

class HackatimeClient:
    def __init__(self, base_url: str = "http://localhost:5000"):
        self.base_url = base_url.rstrip('/')
    
    def track_directory(self, path: str) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/track",
                json={"path": path}
            )
            if response.status_code == 200:
                print(f"Successfully started tracking: {path}")
                return True
            else:
                print(f"Failed to track directory: {response.json().get('error', 'Unknown error')}")
                return False
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False
    
    def untrack_directory(self, path: str) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/untrack",
                json={"path": path}
            )
            if response.status_code == 200:
                print(f"Successfully stopped tracking: {path}")
                return True
            else:
                print(f"Failed to untrack directory: {response.json().get('error', 'Unknown error')}")
                return False
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False
    
    def get_status(self) -> Optional[dict]:
        try:
            response = requests.get(f"{self.base_url}/api/status")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get status: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def send_heartbeat(self, file_path: str) -> bool:
        try:
            response = requests.post(
                f"{self.base_url}/api/heartbeat",
                json={"file": file_path}
            )
            if response.status_code == 200:
                print(f"Heartbeat sent for: {file_path}")
                return True
            else:
                print(f"Failed to send heartbeat: {response.json().get('error', 'Unknown error')}")
                return False
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False
    
    def get_config(self) -> Optional[dict]:
        try:
            response = requests.get(f"{self.base_url}/api/config")
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Failed to get config: {response.status_code}")
                return None
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def update_config(self, api_key: str = None, api_url: str = None, project: str = None) -> bool:
        data = {}
        if api_key:
            data['api_key'] = api_key
        if api_url:
            data['api_url'] = api_url
        if project:
            data['project'] = project
        
        if not data:
            print("No configuration values provided")
            return False
        
        try:
            response = requests.post(
                f"{self.base_url}/api/config",
                json=data
            )
            if response.status_code == 200:
                print("Configuration updated successfully")
                return True
            else:
                print(f"Failed to update config: {response.status_code}")
                return False
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return False

def print_status(status: dict):
    print("\nTracker Status:")
    print(f"   Status: {status['status']}")
    print(f"   API Key Configured: {'Yes' if status['api_key_configured'] else 'No'}")
    print(f"   API URL: {status['api_url']}")
    print(f"   Heartbeat Interval: {status.get('heartbeat_interval', 'Unknown')} seconds")
    print(f"   Activity Timeout: {status.get('activity_timeout', 'Unknown')} seconds")
    
    stats = status['stats']
    print(f"\nTracking Statistics:")
    print(f"   Tracked Directories: {len(stats['tracked_directories'])}")
    for directory in stats['tracked_directories']:
        print(f"     - {directory}")
    print(f"   Tracked Files: {stats['tracked_files']}")
    print(f"   Pending Heartbeats: {stats['pending_heartbeats']}")
    
    if 'is_tracking_active' in stats:
        status_emoji = "Active" if stats['is_tracking_active'] else "Inactive"
        print(f"   Activity Status: {status_emoji}")
        
        if 'time_since_last_activity' in stats and stats['time_since_last_activity'] > 0:
            print(f"   Time Since Last Activity: {stats['time_since_last_activity']} seconds")

def print_config(config: dict):
    print("\nConfiguration:")
    print(f"   API URL: {config['api_url']}")
    print(f"   API Key Configured: {'Yes' if config['api_key_configured'] else 'No'}")
    print(f"   Project: {config.get('project', 'Not set')}")
    print(f"   Config File: {config['config_file']}")

def main():
    parser = argparse.ArgumentParser(description="Hackatime Tracker Client")
    parser.add_argument("--url", default="http://localhost:5000", help="Base URL of the tracker API")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    track_parser = subparsers.add_parser("track", help="Start tracking a directory")
    track_parser.add_argument("path", help="Directory path to track")
    
    untrack_parser = subparsers.add_parser("untrack", help="Stop tracking a directory")
    untrack_parser.add_argument("path", help="Directory path to stop tracking")
    
    subparsers.add_parser("status", help="Get tracker status")
    
    heartbeat_parser = subparsers.add_parser("heartbeat", help="Send manual heartbeat")
    heartbeat_parser.add_argument("file", help="File path to send heartbeat for")
    
    config_parser = subparsers.add_parser("config", help="View or update configuration")
    config_parser.add_argument("--api-key", help="Set API key")
    config_parser.add_argument("--api-url", help="Set API URL")
    config_parser.add_argument("--project", help="Set project name")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    client = HackatimeClient(args.url)
    
    if args.command == "track":
        client.track_directory(args.path)
    
    elif args.command == "untrack":
        client.untrack_directory(args.path)
    
    elif args.command == "status":
        status = client.get_status()
        if status:
            print_status(status)
    
    elif args.command == "heartbeat":
        client.send_heartbeat(args.file)
    
    elif args.command == "config":
        if args.api_key or args.api_url or args.project:
            client.update_config(args.api_key, args.api_url, args.project)
        
        config = client.get_config()
        if config:
            print_config(config)

if __name__ == "__main__":
    main()
