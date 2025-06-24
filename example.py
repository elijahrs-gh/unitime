import time
import threading
import requests
import subprocess
import os
from pathlib import Path

class TrackerManager:
    def __init__(self, api_url: str = "http://localhost:5000"):
        self.api_url = api_url
        self.process = None
        self.running = False
    
    def start_tracker(self):
        print("🚀 Starting Hackatime Tracker...")
        self.process = subprocess.Popen([
            "python", "track_api.py"
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        for i in range(30):
            try:
                response = requests.get(f"{self.api_url}/api/status", timeout=1)
                if response.status_code == 200:
                    self.running = True
                    print("✅ Tracker started successfully")
                    return True
            except requests.RequestException:
                pass
            time.sleep(1)
        print("❌ Failed to start tracker")
        return False
    
    def stop_tracker(self):
        if self.process:
            print("🛑 Stopping tracker...")
            self.process.terminate()
            self.process.wait()
            self.running = False
            print("✅ Tracker stopped")
    
    def is_running(self):
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=2)
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def track_directory(self, path: str):
        try:
            response = requests.post(
                f"{self.api_url}/api/track",
                json={"path": path},
                timeout=5
            )
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_status(self):
        try:
            response = requests.get(f"{self.api_url}/api/status", timeout=5)
            if response.status_code == 200:
                return response.json()
        except requests.RequestException:
            pass
        return None

def demo_basic_usage():
    print("=" * 50)
    print("🎯 Hackatime Tracker Demo")
    print("=" * 50)
    manager = TrackerManager()
    try:
        if manager.is_running():
            print("📊 Tracker is already running")
        else:
            if not manager.start_tracker():
                print("❌ Failed to start tracker. Make sure dependencies are installed.")
                return
        current_dir = os.getcwd()
        print(f"\n📁 Tracking current directory: {current_dir}")
        if manager.track_directory(current_dir):
            print("✅ Successfully added directory to tracking")
        else:
            print("❌ Failed to add directory to tracking")
        print("\n⏳ Waiting for tracking to initialize...")
        time.sleep(3)
        status = manager.get_status()
        if status:
            print("\n📊 Current Status:")
            print(f"   API Key Configured: {'Yes' if status['api_key_configured'] else 'No'}")
            print(f"   Tracked Directories: {len(status['stats']['tracked_directories'])}")
            for directory in status['stats']['tracked_directories']:
                print(f"     - {directory}")
            print(f"   Tracked Files: {status['stats']['tracked_files']}")
            print(f"   Pending Heartbeats: {status['stats']['pending_heartbeats']}")
        test_file = Path("test_tracking.py")
        print(f"\n📝 Creating test file: {test_file}")
        with open(test_file, "w") as f:
            f.write('''#!/usr/bin/env python3

def hello_hackatime():
    print("Hello, Hackatime! 👋")
    return True

if __name__ == "__main__":
    hello_hackatime()
''')
        print("✅ Test file created")
        print("📡 File change should trigger a heartbeat...")
        time.sleep(5)
        status = manager.get_status()
        if status:
            print(f"\n📊 Updated Status:")
            print(f"   Tracked Files: {status['stats']['tracked_files']}")
            print(f"   Pending Heartbeats: {status['stats']['pending_heartbeats']}")
        print("\n✏️  Modifying test file...")
        with open(test_file, "a") as f:
            f.write(f"\n# Modified at {time.ctime()}\n")
        print("📡 Modification should trigger another heartbeat...")
        time.sleep(3)
        status = manager.get_status()
        if status:
            print(f"\n📊 Final Status:")
            print(f"   Pending Heartbeats: {status['stats']['pending_heartbeats']}")
        if test_file.exists():
            test_file.unlink()
            print(f"🗑️  Cleaned up test file: {test_file}")
        print("\n✅ Demo completed successfully!")
        if not status or not status['api_key_configured']:
            print("\n⚠️  Note: No API key configured, so heartbeats won't be sent to Hackatime.")
            print("   Run 'python setup.py' to configure your API key.")
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
    finally:
        if not manager.is_running():
            print("\n🛑 Tracker was already stopped")
        else:
            print("\n🛑 Leaving tracker running...")
            print("   Use 'python client.py status' to check status")
            print("   Use Ctrl+C in the tracker terminal to stop it")

def demo_client_usage():
    print("\n" + "=" * 50)
    print("🖥️  Client Script Demo")
    print("=" * 50)
    commands = [
        ("Get status", "python client.py status"),
        ("Track current directory", f"python client.py track {os.getcwd()}"),
        ("Get updated status", "python client.py status"),
        ("View configuration", "python client.py config"),
    ]
    for description, command in commands:
        print(f"\n📋 {description}:")
        print(f"   Command: {command}")
        print("   (Run this manually in your terminal)")

if __name__ == "__main__":
    print("🎯 Hackatime Tracker Examples")
    print("Choose a demo:")
    print("1. Basic API usage")
    print("2. Client script examples")
    print("3. Both")
    choice = input("\nEnter your choice (1-3): ").strip()
    if choice in ["1", "3"]:
        demo_basic_usage()
    if choice in ["2", "3"]:
        demo_client_usage()
    if choice not in ["1", "2", "3"]:
        print("❌ Invalid choice")
