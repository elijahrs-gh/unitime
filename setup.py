import os
import sys
import subprocess
import configparser
from pathlib import Path

def install_dependencies():
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        return True
    except subprocess.CalledProcessError as e:
        print(f"Failed to install dependencies: {e}")
        return False

def setup_wakatime_config():
    config_file = os.path.expanduser("~/.wakatime.cfg")
    config = configparser.ConfigParser()
    if os.path.exists(config_file):
        config.read(config_file)
    if 'settings' not in config:
        config.add_section('settings')
    current_api_key = config['settings'].get('api_key', '')
    if current_api_key:
        use_current = input("Use current API key? (y/n): ").lower().strip()
        if use_current != 'y':
            current_api_key = ''
    if not current_api_key:
        api_key = input("Enter your Hackatime API key: ").strip()
        if api_key:
            config['settings']['api_key'] = api_key
    config['settings']['api_url'] = 'https://hackatime.hackclub.com/api/v1'
    current_project = config['settings'].get('project', '')
    if current_project:
        use_current = input("Keep current project name? (y/n): ").lower().strip()
        if use_current != 'y':
            current_project = ''
    if not current_project:
        project = input("Enter default project name (optional): ").strip()
        if project:
            config['settings']['project'] = project
    try:
        with open(config_file, 'w') as f:
            config.write(f)
        return True
    except Exception as e:
        print(f"Failed to save configuration: {e}")
        return False

def create_systemd_service():
    if sys.platform != 'linux':
        return False
    service_content = f"""[Unit]
Description=Hackatime Tracker API
After=network.target

[Service]
Type=simple
User={os.getenv('USER')}
WorkingDirectory={os.getcwd()}
ExecStart={sys.executable} {os.path.join(os.getcwd(), 'track_api.py')}
Restart=always
RestartSec=3

[Install]
WantedBy=multi-user.target
"""
    service_file = "/etc/systemd/system/hackatime-tracker.service"
    try:
        process = subprocess.Popen(['sudo', 'tee', service_file], stdin=subprocess.PIPE, text=True)
        process.communicate(service_content)
        if process.returncode == 0:
            print("To enable and start the service:")
            print("  sudo systemctl enable hackatime-tracker")
            print("  sudo systemctl start hackatime-tracker")
            return True
        else:
            print("Failed to create systemd service")
            return False
    except Exception as e:
        print(f"Error creating systemd service: {e}")
        return False

def create_launchd_plist():
    if sys.platform != 'darwin':
        return False
    plist_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.hackatime.tracker</string>
    <key>ProgramArguments</key>
    <array>
        <string>{sys.executable}</string>
        <string>{os.path.join(os.getcwd(), 'track_api.py')}</string>
    </array>
    <key>WorkingDirectory</key>
    <string>{os.getcwd()}</string>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>{os.path.expanduser('~/Library/Logs/hackatime-tracker.log')}</string>
    <key>StandardErrorPath</key>
    <string>{os.path.expanduser('~/Library/Logs/hackatime-tracker.error.log')}</string>
</dict>
</plist>
"""
    plist_file = os.path.expanduser("~/Library/LaunchAgents/com.hackatime.tracker.plist")
    try:
        os.makedirs(os.path.dirname(plist_file), exist_ok=True)
        with open(plist_file, 'w') as f:
            f.write(plist_content)
        print("To load and start the service:")
        print(f"  launchctl load {plist_file}")
        print(f"  launchctl start com.hackatime.tracker")
        return True
    except Exception as e:
        print(f"Error creating launchd plist: {e}")
        return False

def main():
    print("Hackatime Tracker Setup")
    print("=" * 40)
    if not install_dependencies():
        print("Setup failed: Could not install dependencies")
        return 1
    if not setup_wakatime_config():
        print("Setup failed: Could not configure WakaTime")
        return 1
    setup_service = input("Would you like to set up the tracker as a system service? (y/n): ").lower().strip()
    if setup_service == 'y':
        if sys.platform == 'linux':
            create_systemd_service()
        elif sys.platform == 'darwin':
            create_launchd_plist()
        else:
            print("Automatic service setup not supported on this platform")
            print("You can run the tracker manually with: python track_api.py")
    print("Setup complete!")
    print("Next steps:")
    print("1. Start the tracker: python track_api.py")
    print("2. In another terminal, track a directory: python client.py track /path/to/your/project")
    print("3. Check status: python client.py status")
    print("Documentation: https://hackatime.hackclub.com/docs")
    return 0

if __name__ == "__main__":
    sys.exit(main())
