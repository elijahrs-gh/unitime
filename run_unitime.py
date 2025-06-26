import os
import sys
import time
import signal
import subprocess
from pathlib import Path


def start_api_server():
    api_script = Path(__file__).parent.parent / "track_api.py"
    
    if not api_script.exists():
        print(f"Error: API script not found at {api_script}")
        return None
    
    print("Starting UniTime API server...")
    try:
        api_process = subprocess.Popen([
            sys.executable, str(api_script)
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        time.sleep(2)
        
        if api_process.poll() is None:
            print("API server started successfully")
            return api_process
        else:
            stdout, stderr = api_process.communicate()
            print(f"API server failed to start:")
            print(f"stdout: {stdout.decode()}")
            print(f"stderr: {stderr.decode()}")
            return None
            
    except Exception as e:
        print(f"Error starting API server: {e}")
        return None


def start_ui():
    ui_script = Path(__file__).parent / "launcher.py"
    
    if not ui_script.exists():
        print(f"Error: UI launcher not found at {ui_script}")
        return None
    
    print("Starting UniTime UI...")
    try:
        ui_process = subprocess.Popen([
            sys.executable, str(ui_script)
        ])
        
        return ui_process
        
    except Exception as e:
        print(f"Error starting UI: {e}")
        return None


def main():
    print("=" * 50)
    print("UniTime - Complete Time Tracking Solution")
    print("=" * 50)
    
    try:
        import PyQt6
        import requests
        import flask
        import watchdog
    except ImportError as e:
        print(f"Missing dependency: {e}")
        print("\nPlease install required packages:")
        print("pip install -r requirements.txt")
        sys.exit(1)
    
    api_process = start_api_server()
    if not api_process:
        print("Failed to start API server. Exiting.")
        sys.exit(1)
    
    time.sleep(1)
    
    ui_process = start_ui()
    if not ui_process:
        print("Failed to start UI. Stopping API server.")
        api_process.terminate()
        sys.exit(1)
    
    print("\n" + "=" * 50)
    print("UniTime is now running!")
    print("API Server: http://localhost:5000")
    print("UI: Running in separate window")
    print("\nPress Ctrl+C to stop both services")
    print("=" * 50)
    
    def signal_handler(signum, frame):
        print("\n\nShutting down UniTime...")
        
        if ui_process and ui_process.poll() is None:
            print("Stopping UI...")
            ui_process.terminate()
            try:
                ui_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                ui_process.kill()
        
        if api_process and api_process.poll() is None:
            print("Stopping API server...")
            api_process.terminate()
            try:
                api_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                api_process.kill()
        
        print("UniTime stopped. Goodbye!")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        ui_process.wait()
    except KeyboardInterrupt:
        pass
    finally:
        signal_handler(None, None)


if __name__ == "__main__":
    main()
