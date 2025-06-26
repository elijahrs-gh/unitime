import os
import time
import json
import threading
import hashlib
import platform
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Set, Optional, List
from dataclasses import dataclass, asdict
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import requests
from flask import Flask, request, jsonify
import configparser

API_BASE_URL = "https://hackatime.hackclub.com/api/v1"
PLUGIN_NAME = "unitime-wakatime"
PLUGIN_VERSION = "0.1.0"
EDITOR_NAME = ""
WAKATIME_CONFIG_FILE = os.path.expanduser("~/.wakatime.cfg")
TRACKER_CONFIG_FILE = os.path.expanduser("~/.hackatime_tracker.cfg")
DEFAULT_HEARTBEAT_INTERVAL = 30
ACTIVITY_TIMEOUT = 120
MAX_FILE_SIZE = 2 * 1024 * 1024

def detect_runtime_info():
    info = {}
    
    info['os_name'] = platform.system().lower()
    info['kernel_version'] = platform.release()
    info['arch'] = platform.machine()
    
    try:
        info['python_version'] = platform.python_version()
        info['runtime'] = f"python{info['python_version']}"
    except (AttributeError, ImportError):
        pass
    
    try:
        import subprocess
        node_version = subprocess.check_output(['node', '--version'], stderr=subprocess.DEVNULL)
        if node_version:
            info['node_version'] = node_version.decode('utf-8').strip().lstrip('v')
            info['runtime'] = f"node{info['node_version']}"
    except (subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        ruby_version = subprocess.check_output(['ruby', '--version'], stderr=subprocess.DEVNULL)
        if ruby_version:
            version_str = ruby_version.decode('utf-8')
            import re
            match = re.search(r'ruby (\d+\.\d+\.\d+)', version_str)
            if match:
                info['ruby_version'] = match.group(1)
                info['runtime'] = f"ruby{info['ruby_version']}"
    except (NameError, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    try:
        java_version = subprocess.check_output(['java', '-version'], stderr=subprocess.STDOUT)
        if java_version:
            version_str = java_version.decode('utf-8')
            match = re.search(r'version "([^"]+)"', version_str)
            if match:
                info['java_version'] = match.group(1)
                info['runtime'] = f"java{info['java_version']}"
    except (NameError, subprocess.SubprocessError, FileNotFoundError):
        pass
    
    if 'runtime' not in info and 'python_version' in info:
        info['runtime'] = f"python{info['python_version']}"
    elif 'runtime' not in info:
        info['runtime'] = "unknown-runtime"
    
    return info

def build_user_agent(editor_name="unitime"):
    runtime_info = detect_runtime_info()
    os_name = runtime_info.get('os_name', platform.system().lower())
    kernel_version = runtime_info.get('kernel_version', platform.release())
    runtime = runtime_info.get('runtime', f"python{platform.python_version()}")
    
    return f"wakatime/v{PLUGIN_VERSION} ({os_name}-{kernel_version}) {runtime} {editor_name}/{PLUGIN_VERSION}"

def build_plugin_name(editor_name="unitime"):
    runtime_info = detect_runtime_info()
    os_name = runtime_info.get('os_name', platform.system().lower())
    kernel_version = runtime_info.get('kernel_version', platform.release())
    runtime = runtime_info.get('runtime', f"python{platform.python_version()}")
    
    return f"wakatime/v{PLUGIN_VERSION} ({os_name}-{kernel_version}) {runtime} {editor_name}/{PLUGIN_VERSION}"

@dataclass
class Heartbeat:
    entity: str
    type: str = "file"
    time: int = None
    category: str = "coding"
    project: str = None
    branch: str = "main"
    language: str = None
    lineno: int = None
    cursorpos: int = None
    lines: int = None
    is_write: bool = False
    plugin: str = None

    def __post_init__(self):
        if self.time is None:
            self.time = int(time.time())
        if self.plugin is None:
            self.plugin = build_plugin_name("unitime")

class WakaTimeConfig:
    def __init__(self, wakatime_config_file: str = WAKATIME_CONFIG_FILE, tracker_config_file: str = TRACKER_CONFIG_FILE):
        self.wakatime_config_file = wakatime_config_file
        self.tracker_config_file = tracker_config_file
        self.api_key = None
        self.api_url = API_BASE_URL
        self.project = None
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
        self.tracked_folders = []
        self.editor_name = "unitime"
        self.load_config()
    
    def load_config(self):
        self._load_wakatime_config()
        self._load_tracker_config()
    
    def update_from_ui_config(self, ui_config: Dict):
        """Update configuration from UI settings"""
        if 'api_key' in ui_config and ui_config['api_key']:
            self.api_key = ui_config['api_key']
        if 'api_url' in ui_config and ui_config['api_url']:
            self.api_url = ui_config['api_url']
        if 'project' in ui_config and ui_config['project']:
            self.project = ui_config['project']
        if 'ide' in ui_config and ui_config['ide']:
            self.editor_name = ui_config['ide'].lower()
        if 'heartbeat_interval' in ui_config:
            self.heartbeat_interval = ui_config['heartbeat_interval']
    
    def save_wakatime_config(self):
        """Save current settings to wakatime config file"""
        try:
            config = configparser.ConfigParser()
            
            if os.path.exists(self.wakatime_config_file):
                config.read(self.wakatime_config_file)
            
            if not config.has_section('settings'):
                config.add_section('settings')
            
            if self.api_key:
                config.set('settings', 'api_key', self.api_key)
            if self.api_url:
                config.set('settings', 'api_url', self.api_url)
            if self.project:
                config.set('settings', 'project', self.project)
            if self.heartbeat_interval:
                config.set('settings', 'heartbeat_rate_limit_seconds', str(self.heartbeat_interval))
            
            with open(self.wakatime_config_file, 'w') as f:
                config.write(f)
            print(f"Updated WakaTime config file: {self.wakatime_config_file}")
            return True
        except Exception as e:
            print(f"Failed to save WakaTime config: {e}")
            return False
    
    def _load_wakatime_config(self):
        if not os.path.exists(self.wakatime_config_file):
            print(f"Warning: WakaTime config file not found at {self.wakatime_config_file}")
            return
        
        config = configparser.ConfigParser()
        config.read(self.wakatime_config_file)
        
        if 'settings' in config:
            self.api_key = config['settings'].get('api_key')
            self.api_url = config['settings'].get('api_url', API_BASE_URL)
            self.project = config['settings'].get('project')
            
            rate_limit = config['settings'].get('heartbeat_rate_limit_seconds')
            if rate_limit:
                try:
                    self.heartbeat_interval = int(rate_limit)
                    print(f"Using heartbeat interval from WakaTime config: {self.heartbeat_interval} seconds")
                except ValueError:
                    print(f"Invalid heartbeat_rate_limit_seconds in config: {rate_limit}, using default: {DEFAULT_HEARTBEAT_INTERVAL}")
                    self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
            else:
                self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
    
    def _load_tracker_config(self):
        if not os.path.exists(self.tracker_config_file):
            print(f"Warning: Tracker config file not found at {self.tracker_config_file}")
            print("Creating default tracker config...")
            self._create_default_tracker_config()
            return
        
        config = configparser.ConfigParser()
        config.read(self.tracker_config_file)
        
        if 'tracker' in config:
            tracked_folders_str = config['tracker'].get('tracked_folders', '')
            if tracked_folders_str:
                self.tracked_folders = [
                    os.path.expanduser(folder.strip()) 
                    for folder in tracked_folders_str.split(',') 
                    if folder.strip()
                ]
                print(f"Tracked folders from tracker config: {self.tracked_folders}")
            else:
                print("No tracked folders configured in tracker config")
                self.tracked_folders = []
    
    def _create_default_tracker_config(self):
        config = configparser.ConfigParser()
        config.add_section('tracker')
        
        config.set('tracker', 'tracked_folders', '# Add your project folders here, comma-separated')
        config.set('tracker', '# Example', '~/Documents/MyProject, ~/Code/AnotherProject')
        self.tracked_folders = []
        
        try:
            with open(self.tracker_config_file, 'w') as f:
                config.write(f)
            print(f"Created tracker config file: {self.tracker_config_file}")
        except Exception as e:
            print(f"Failed to create tracker config file: {e}")

class FileTracker:
    def __init__(self, config: WakaTimeConfig):
        self.config = config
        self.file_hashes: Dict[str, str] = {}
        self.last_heartbeat: Dict[str, float] = {}
        self.tracked_directories: Set[str] = set()
        self.observers: List[Observer] = []
        self.heartbeat_queue: List[Heartbeat] = []
        self.lock = threading.Lock()
        self.last_activity_time: float = 0
        self.is_tracking_active: bool = True
        self.sender_thread = threading.Thread(target=self._heartbeat_sender, daemon=True)
        self.sender_thread.start()
    
    def add_directory(self, directory: str) -> bool:
        directory = os.path.abspath(directory)
        print(f"DEBUG: Adding directory to track: {directory}")
        
        if not os.path.exists(directory):
            print(f"DEBUG: Directory does not exist: {directory}")
            return False
        
        if directory in self.tracked_directories:
            print(f"DEBUG: Directory already being tracked: {directory}")
            return True
        
        try:
            event_handler = FileChangeHandler(self)
            observer = Observer()
            observer.schedule(event_handler, directory, recursive=True)
            observer.start()
            
            self.observers.append(observer)
            self.tracked_directories.add(directory)
            print(f"DEBUG: Successfully added directory to tracking: {directory}")
            print(f"DEBUG: All tracked directories: {list(self.tracked_directories)}")
            
            self._initial_scan(directory)
            return True
        except Exception as e:
            print(f"Error adding directory {directory}: {e}")
            return False
    
    def remove_directory(self, directory: str) -> bool:
        directory = os.path.abspath(directory)
        if directory not in self.tracked_directories:
            return False
        
        for observer in self.observers[:]:
            observer.stop()
            observer.join()
        
        self.observers.clear()
        self.tracked_directories.discard(directory)
        
        for tracked_dir in self.tracked_directories.copy():
            self.tracked_directories.remove(tracked_dir)
            self.add_directory(tracked_dir)
        
        return True
    
    def _initial_scan(self, directory: str):
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if self._should_track_file(file_path):
                    initial_hash = self._update_file_hash(file_path)
                    if initial_hash:
                        self.file_hashes[file_path] = initial_hash
    
    def _should_track_file(self, file_path: str) -> bool:
        if any(part.startswith('.') for part in Path(file_path).parts):
            return False
        
        skip_extensions = {
            '.exe', '.dll', '.so', '.dylib', '.bin', '.obj', '.o',
            '.jpg', '.jpeg', '.png', '.gif', '.bmp', '.ico', '.svg',
            '.mp3', '.mp4', '.avi', '.mov', '.wav', '.flac',
            '.zip', '.tar', '.gz', '.7z', '.rar',
            '.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx'
        }
        
        file_ext = Path(file_path).suffix.lower()
        if file_ext in skip_extensions:
            return False
        
        try:
            if os.path.getsize(file_path) > MAX_FILE_SIZE:
                return False
        except OSError:
            return False
        
        return True
    
    def _update_file_hash(self, file_path: str) -> str:
        try:
            time.sleep(0.1)
            
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()
                return file_hash
        except (OSError, IOError) as e:
            print(f"DEBUG: Error reading file {file_path}: {e}")
            return None
    
    def _get_file_language(self, file_path: str) -> Optional[str]:
        extension_map = {
            '.py': 'Python',
            '.pyi': 'Python',
            '.pyx': 'Cython',
            '.pxd': 'Cython',
            '.pyd': 'Python',
            '.ipynb': 'Jupyter Notebook',
            '.js': 'JavaScript',
            '.jsx': 'React JSX',
            '.ts': 'TypeScript',
            '.tsx': 'React TSX',
            '.vue': 'Vue',
            '.svelte': 'Svelte',
            '.html': 'HTML',
            '.htm': 'HTML',
            '.xhtml': 'XHTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.php': 'PHP',
            '.wasm': 'WebAssembly',
            '.java': 'Java',
            '.kt': 'Kotlin',
            '.kts': 'Kotlin Script',
            '.scala': 'Scala',
            '.sc': 'Scala Script',
            '.groovy': 'Groovy',
            '.gvy': 'Groovy',
            '.gradle': 'Gradle',
            '.clj': 'Clojure',
            '.cljs': 'ClojureScript',
            '.cs': 'C#',
            '.vb': 'Visual Basic',
            '.fs': 'F#',
            '.fsx': 'F# Script',
            '.xaml': 'XAML',
            '.c': 'C',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.cxx': 'C++',
            '.cp': 'C++',
            '.c++': 'C++',
            '.h': 'C Header',
            '.hpp': 'C++ Header',
            '.hh': 'C++ Header',
            '.hxx': 'C++ Header',
            '.inl': 'C++ Inline',
            '.cu': 'CUDA',
            '.cuh': 'CUDA Header',
            '.rs': 'Rust',
            '.go': 'Go',
            '.swift': 'Swift',
            '.d': 'D',
            '.zig': 'Zig',
            '.nim': 'Nim',
            '.cr': 'Crystal',
            '.odin': 'Odin',
            '.rb': 'Ruby',
            '.erb': 'ERB',
            '.rake': 'Ruby Rake',
            '.pl': 'Perl',
            '.pm': 'Perl Module',
            '.t': 'Perl Test',
            '.lua': 'Lua',
            '.tcl': 'Tcl',
            '.rb': 'Ruby',
            '.php': 'PHP',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.fish': 'Fish',
            '.ps1': 'PowerShell',
            '.psm1': 'PowerShell Module',
            '.psd1': 'PowerShell Data',
            '.bat': 'Batch',
            '.cmd': 'Batch',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.toml': 'TOML',
            '.ini': 'INI',
            '.xml': 'XML',
            '.csv': 'CSV',
            '.tsv': 'TSV',
            '.sql': 'SQL',
            '.graphql': 'GraphQL',
            '.gql': 'GraphQL',
            '.proto': 'Protocol Buffers',
            '.avdl': 'Avro IDL',
            '.thrift': 'Thrift',
            '.hs': 'Haskell',
            '.lhs': 'Literate Haskell',
            '.ml': 'OCaml',
            '.mli': 'OCaml Interface',
            '.elm': 'Elm',
            '.erl': 'Erlang',
            '.ex': 'Elixir',
            '.exs': 'Elixir Script',
            '.gleam': 'Gleam',
            '.lisp': 'Lisp',
            '.cl': 'Common Lisp',
            '.rkt': 'Racket',
            '.r': 'R',
            '.jl': 'Julia',
            '.m': 'MATLAB/Objective-C',
            '.mm': 'Objective-C++',
            '.f': 'Fortran',
            '.f90': 'Fortran 90',
            '.f95': 'Fortran 95',
            '.f03': 'Fortran 2003',
            '.stan': 'Stan',
            '.dart': 'Dart',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.java': 'Java',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.gd': 'GDScript',
            '.cs': 'C# (Unity)',
            '.hlsl': 'HLSL',
            '.glsl': 'GLSL',
            '.shader': 'Unity Shader',
            '.as': 'ActionScript',
            '.md': 'Markdown',
            '.mdx': 'MDX',
            '.rst': 'reStructuredText',
            '.tex': 'LaTeX',
            '.wiki': 'Wiki',
            '.org': 'Org Mode',
            '.adoc': 'AsciiDoc',
            '.vim': 'Vim Script',
            '.asm': 'Assembly',
            '.s': 'Assembly',
            '.nasm': 'NASM',
            '.v': 'Verilog/V',
            '.vhd': 'VHDL',
            '.cmake': 'CMake',
            '.make': 'Makefile',
            '.nix': 'Nix',
            '.awk': 'AWK',
            '.ahk': 'AutoHotkey',
            '.applescript': 'AppleScript',
            '.bf': 'Brainfuck',
            '.io': 'Io',
            '.j': 'J',
            '.hy': 'Hy',
        }
        
        ext = Path(file_path).suffix.lower()
        language = extension_map.get(ext)
        
        if ext == '.m':
            try:
                with open(file_path, 'r', errors='ignore') as f:
                    content = f.read(4096)
                    if '@interface' in content or '@implementation' in content or '#import' in content:
                        return 'Objective-C'
                    elif 'function ' in content or '];\n' in content:
                        return 'MATLAB'
            except:
                pass
        
        return language
    
    def _get_git_branch(self, file_path: str) -> str:
        try:
            path = Path(file_path)
            for parent in [path.parent] + list(path.parents):
                git_dir = parent / '.git'
                if git_dir.exists():
                    head_file = git_dir / 'HEAD'
                    if head_file.exists():
                        with open(head_file, 'r') as f:
                            head_content = f.read().strip()
                            if head_content.startswith('ref: refs/heads/'):
                                return head_content.replace('ref: refs/heads/', '')
                    break
        except Exception:
            pass
        return "main"
    
    def _get_project_name(self, file_path: str) -> Optional[str]:
        file_path = os.path.abspath(file_path)
        
        for tracked_dir in self.tracked_directories:
            normalized_tracked_dir = os.path.abspath(tracked_dir)
            if file_path.startswith(normalized_tracked_dir):
                project_name = Path(normalized_tracked_dir).name
                print(f"DEBUG: File {file_path} -> Project {project_name} (from tracked dir {normalized_tracked_dir})")
                return project_name
        
        fallback_name = Path(file_path).parent.name
        print(f"DEBUG: File {file_path} -> Project {fallback_name} (fallback - no matching tracked dir)")
        print(f"DEBUG: Tracked directories: {list(self.tracked_directories)}")
        return fallback_name
    
    def _count_lines(self, file_path: str) -> Optional[int]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (OSError, IOError):
            return None
    
    def handle_file_change(self, file_path: str, is_write: bool = False):
        print(f"DEBUG: Processing file change: {file_path}")
        
        if not self._should_track_file(file_path):
            print(f"DEBUG: File not tracked (filtered out): {file_path}")
            return
        
        now = time.time()
        
        if not self.is_tracking_active:
            print(f"Activity detected after timeout - reactivating tracking for {file_path}")
            self.is_tracking_active = True
        
        self.last_activity_time = now
        old_hash = self.file_hashes.get(file_path)
        
        current_hash = self._update_file_hash(file_path)
        if current_hash is None:
            print(f"DEBUG: Could not read file {file_path}, skipping heartbeat")
            return
        
        if old_hash == current_hash and not is_write:
            print(f"DEBUG: File {file_path} unchanged (hash: {current_hash[:8]}...), skipping heartbeat")
            return
        
        if old_hash != current_hash:
            print(f"DEBUG: File {file_path} changed (old: {old_hash[:8] if old_hash else 'None'}... -> new: {current_hash[:8]}...)")
            self.file_hashes[file_path] = current_hash
        elif is_write:
            print(f"DEBUG: File {file_path} write event detected")
            self.file_hashes[file_path] = current_hash
        
        total_lines = self._count_lines(file_path)
        heartbeat = Heartbeat(
            entity=file_path,
            time=int(now),
            category="coding",
            project=self._get_project_name(file_path),
            branch=self._get_git_branch(file_path),
            language=self._get_file_language(file_path),
            lineno=total_lines if total_lines else 1,
            cursorpos=0,
            lines=total_lines,
            is_write=is_write,
            plugin=build_plugin_name(self.config.editor_name)
        )
        
        print(f"DEBUG: Queuing heartbeat for {file_path} (will be sent within 30 seconds)")
        
        with self.lock:
            self.heartbeat_queue = [hb for hb in self.heartbeat_queue if hb.entity != file_path]
            self.heartbeat_queue.append(heartbeat)
            self.last_heartbeat[file_path] = now
    
    def _heartbeat_sender(self):
        last_heartbeat_sent = 0
        
        while True:
            try:
                now = time.time()
                if self.last_activity_time > 0:
                    time_since_last_activity = now - self.last_activity_time

                    if time_since_last_activity <= 30 and (now - last_heartbeat_sent) >= 30:
                        heartbeats_to_send = []
                        with self.lock:
                            if self.heartbeat_queue:
                                heartbeats_to_send = self.heartbeat_queue[:]
                                self.heartbeat_queue.clear()
                        
                        if heartbeats_to_send:
                            print(f"DEBUG: Sending {len(heartbeats_to_send)} heartbeat(s) - activity detected within last 30 seconds")
                            self._send_heartbeats(heartbeats_to_send)
                            last_heartbeat_sent = now
                        else:
                            print(f"DEBUG: No queued heartbeats to send (activity detected but no file changes)")
                    
                    if time_since_last_activity > ACTIVITY_TIMEOUT:
                        if self.is_tracking_active:
                            print(f"DEBUG: No activity for {ACTIVITY_TIMEOUT} seconds - pausing heartbeat tracking")
                            self.is_tracking_active = False
                        with self.lock:
                            if self.heartbeat_queue:
                                print(f"DEBUG: Clearing {len(self.heartbeat_queue)} queued heartbeats due to inactivity")
                                self.heartbeat_queue.clear()
                    else:
                        if not self.is_tracking_active:
                            print(f"DEBUG: Activity detected - reactivating tracking")
                            self.is_tracking_active = True
                
                time.sleep(30)
                
            except Exception as e:
                print(f"Error in heartbeat sender: {e}")
                time.sleep(30)
    
    def _send_heartbeats(self, heartbeats: List[Heartbeat]):
        if not self.config.api_key:
            print("Warning: No API key configured")
            return
        
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json',
            'User-Agent': build_user_agent(self.config.editor_name)
        }
        
        for heartbeat in heartbeats:
            try:
                data = {k: v for k, v in asdict(heartbeat).items() if v is not None}
                
                print(f"DEBUG: Sending heartbeat data:")
                print(f"  URL: {self.config.api_url}/users/current/heartbeats")
                print(f"  Data: {json.dumps(data, indent=2)}")
                
                response = requests.post(
                    f"{self.config.api_url}/users/current/heartbeats",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code in [201, 202]:
                    print(f"DEBUG: Heartbeat sent successfully for {heartbeat.entity} (status: {response.status_code})")
                else:
                    print(f"DEBUG: Failed to send heartbeat: {response.status_code} - {response.text}")
                    
            except requests.RequestException as e:
                print(f"DEBUG: Error sending heartbeat: {e}")
    
    def get_stats(self) -> Dict:
        now = time.time()
        time_since_last_activity = now - self.last_activity_time if self.last_activity_time > 0 else 0
        
        return {
            'tracked_directories': list(self.tracked_directories),
            'tracked_files': len(self.file_hashes),
            'pending_heartbeats': len(self.heartbeat_queue),
            'last_heartbeats': dict(self.last_heartbeat),
            'is_tracking_active': self.is_tracking_active,
            'time_since_last_activity': round(time_since_last_activity, 1),
            'heartbeat_interval': self.config.heartbeat_interval,
            'activity_timeout': ACTIVITY_TIMEOUT
        }
    
    def stop(self):
        for observer in self.observers:
            observer.stop()
            observer.join()

class FileChangeHandler(FileSystemEventHandler):
    def __init__(self, tracker: FileTracker):
        self.tracker = tracker
    
    def on_modified(self, event):
        if not event.is_directory:
            self.tracker.handle_file_change(event.src_path, is_write=False)
    
    def on_created(self, event):
        if not event.is_directory:
            self.tracker.handle_file_change(event.src_path, is_write=True)

app = Flask(__name__)
config = WakaTimeConfig()
tracker = FileTracker(config)

for folder_path in config.tracked_folders:
    if os.path.exists(folder_path):
        success = tracker.add_directory(folder_path)
        if success:
            print(f"Auto-tracking: {folder_path}")
        else:
            print(f"Failed to auto-track: {folder_path}")
    else:
        print(f"Configured folder does not exist: {folder_path}")

if not config.tracked_folders:
    print("No folders configured for tracking.")
    print(f"Edit {config.tracker_config_file} and add folders to the 'tracked_folders' setting.")
    print("Example: tracked_folders = ~/Documents/DNR, ~/Projects/MyProject")

@app.route('/api/track', methods=['POST'])
def track_directory():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Path is required'}), 400
    
    path = data['path']
    success = tracker.add_directory(path)
    
    if success:
        return jsonify({'success': True, 'message': f'Successfully tracking {path}'}), 200
    else:
        return jsonify({'success': False, 'error': f'Failed to track {path}'}), 400

@app.route('/api/untrack', methods=['POST'])
def untrack_directory():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Path is required'}), 400
    
    path = data['path']
    success = tracker.remove_directory(path)
    
    if success:
        return jsonify({'success': True, 'message': f'Successfully stopped tracking {path}'}), 200
    else:
        return jsonify({'success': False, 'error': f'Directory {path} was not being tracked'}), 400

@app.route('/api/status', methods=['GET'])
def get_status():
    stats = tracker.get_stats()
    return jsonify({
        'status': 'running',
        'api_key_configured': bool(config.api_key),
        'api_url': config.api_url,
        'heartbeat_interval': config.heartbeat_interval,
        'activity_timeout': ACTIVITY_TIMEOUT,
        'stats': stats
    })

@app.route('/api/heartbeat', methods=['POST'])
def manual_heartbeat():
    data = request.get_json()
    if not data or 'file' not in data:
        return jsonify({'error': 'File path is required'}), 400
    
    file_path = data['file']
    if not os.path.exists(file_path):
        return jsonify({'error': 'File does not exist'}), 400
    
    tracker.handle_file_change(file_path, is_write=True)
    return jsonify({'message': f'Heartbeat queued for {file_path}'}), 200

@app.route('/api/config', methods=['GET'])
def get_config():
    return jsonify({
        'api_url': config.api_url,
        'api_key_configured': bool(config.api_key),
        'project': config.project,
        'editor_name': config.editor_name,
        'wakatime_config_file': config.wakatime_config_file,
        'tracker_config_file': config.tracker_config_file,
        'heartbeat_interval': config.heartbeat_interval,
        'tracked_folders': config.tracked_folders
    })

@app.route('/api/config', methods=['POST'])
def update_config():
    data = request.get_json()
    
    if 'api_key' in data:
        config.api_key = data['api_key']
    if 'api_url' in data:
        config.api_url = data['api_url']
    if 'project' in data:
        config.project = data['project']
    if 'ide' in data:
        config.editor_name = data['ide'].lower()
    if 'heartbeat_interval' in data:
        config.heartbeat_interval = data['heartbeat_interval']
    
    config.save_wakatime_config()
    
    return jsonify({'message': 'Configuration updated and saved'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        tracker.stop()
