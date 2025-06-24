import os
import time
import json
import threading
import hashlib
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
WAKATIME_CONFIG_FILE = os.path.expanduser("~/.wakatime.cfg")
DEFAULT_HEARTBEAT_INTERVAL = 30
ACTIVITY_TIMEOUT = 120
MAX_FILE_SIZE = 2 * 1024 * 1024

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
    
    def __post_init__(self):
        if self.time is None:
            self.time = int(time.time())

class WakaTimeConfig:
    def __init__(self, config_file: str = WAKATIME_CONFIG_FILE):
        self.config_file = config_file
        self.api_key = None
        self.api_url = API_BASE_URL
        self.project = None
        self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
        self.load_config()
    
    def load_config(self):
        if not os.path.exists(self.config_file):
            return
        
        config = configparser.ConfigParser()
        config.read(self.config_file)
        
        if 'settings' in config:
            self.api_key = config['settings'].get('api_key')
            self.api_url = config['settings'].get('api_url', API_BASE_URL)
            self.project = config['settings'].get('project')
            
            rate_limit = config['settings'].get('heartbeat_rate_limit_seconds')
            if rate_limit:
                try:
                    self.heartbeat_interval = int(rate_limit)
                except ValueError:
                    self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL
            else:
                self.heartbeat_interval = DEFAULT_HEARTBEAT_INTERVAL

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
        if not os.path.exists(directory):
            return False
        
        if directory in self.tracked_directories:
            return True
        
        try:
            event_handler = FileChangeHandler(self)
            observer = Observer()
            observer.schedule(event_handler, directory, recursive=True)
            observer.start()
            self.observers.append(observer)
            self.tracked_directories.add(directory)
            self._initial_scan(directory)
            return True
        except Exception as e:
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
                    self._update_file_hash(file_path)
    
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
            with open(file_path, 'rb') as f:
                content = f.read()
                file_hash = hashlib.md5(content).hexdigest()
                self.file_hashes[file_path] = file_hash
                return file_hash
        except (OSError, IOError):
            return None
    
    def _get_file_language(self, file_path: str) -> Optional[str]:
        extension_map = {
            '.py': 'Python',
            '.js': 'JavaScript',
            '.ts': 'TypeScript',
            '.java': 'Java',
            '.c': 'C',
            '.cpp': 'C++',
            '.cc': 'C++',
            '.cxx': 'C++',
            '.h': 'C Header',
            '.hpp': 'C++ Header',
            '.cs': 'C#',
            '.php': 'PHP',
            '.rb': 'Ruby',
            '.go': 'Go',
            '.rs': 'Rust',
            '.swift': 'Swift',
            '.kt': 'Kotlin',
            '.scala': 'Scala',
            '.html': 'HTML',
            '.css': 'CSS',
            '.scss': 'SCSS',
            '.sass': 'Sass',
            '.less': 'Less',
            '.xml': 'XML',
            '.json': 'JSON',
            '.yaml': 'YAML',
            '.yml': 'YAML',
            '.md': 'Markdown',
            '.sh': 'Shell',
            '.bash': 'Bash',
            '.zsh': 'Zsh',
            '.fish': 'Fish',
            '.sql': 'SQL',
            '.r': 'R',
            '.m': 'Objective-C',
            '.mm': 'Objective-C++',
            '.pl': 'Perl',
            '.lua': 'Lua',
            '.vim': 'Vim Script',
            '.dart': 'Dart',
            '.elm': 'Elm',
            '.ex': 'Elixir',
            '.exs': 'Elixir',
            '.clj': 'Clojure',
            '.hs': 'Haskell',
            '.ml': 'OCaml',
            '.fs': 'F#',
            '.jl': 'Julia',
            '.nim': 'Nim',
            '.zig': 'Zig'
        }
        
        ext = Path(file_path).suffix.lower()
        return extension_map.get(ext)
    
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
        for tracked_dir in self.tracked_directories:
            if file_path.startswith(tracked_dir):
                return Path(tracked_dir).name
        
        return Path(file_path).parent.name
    
    def _count_lines(self, file_path: str) -> Optional[int]:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except (OSError, IOError):
            return None
    
    def handle_file_change(self, file_path: str, is_write: bool = False):
        if not self._should_track_file(file_path):
            return
        
        now = time.time()
        
        if not self.is_tracking_active:
            self.is_tracking_active = True
        
        self.last_activity_time = now
        
        if file_path in self.last_heartbeat:
            if now - self.last_heartbeat[file_path] < self.config.heartbeat_interval:
                return
        
        current_hash = self._update_file_hash(file_path)
        if current_hash is None:
            return
        
        old_hash = self.file_hashes.get(file_path)
        if old_hash == current_hash and not is_write:
            return
        
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
            is_write=is_write
        )
        
        with self.lock:
            self.heartbeat_queue.append(heartbeat)
            self.last_heartbeat[file_path] = now
    
    def _heartbeat_sender(self):
        while True:
            try:
                now = time.time()
                
                if self.is_tracking_active and self.last_activity_time > 0:
                    time_since_last_activity = now - self.last_activity_time
                    if time_since_last_activity > ACTIVITY_TIMEOUT:
                        self.is_tracking_active = False
                
                heartbeats_to_send = []
                if self.is_tracking_active:
                    with self.lock:
                        if self.heartbeat_queue:
                            heartbeats_to_send = self.heartbeat_queue[:]
                            self.heartbeat_queue.clear()
                    
                    if heartbeats_to_send:
                        self._send_heartbeats(heartbeats_to_send)
                else:
                    with self.lock:
                        if self.heartbeat_queue:
                            self.heartbeat_queue.clear()
                
                time.sleep(5)
            except Exception as e:
                time.sleep(10)
    
    def _send_heartbeats(self, heartbeats: List[Heartbeat]):
        if not self.config.api_key:
            return
        
        headers = {
            'Authorization': f'Bearer {self.config.api_key}',
            'Content-Type': 'application/json'
        }
        
        for heartbeat in heartbeats:
            try:
                data = {k: v for k, v in asdict(heartbeat).items() if v is not None}
                
                response = requests.post(
                    f"{self.config.api_url}/users/current/heartbeats",
                    headers=headers,
                    json=data,
                    timeout=10
                )
                
                if response.status_code != 201:
                    pass
                    
            except requests.RequestException as e:
                pass
    
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

dnr_path = os.path.expanduser("~/Documents/DNR")
if os.path.exists(dnr_path):
    tracker.add_directory(dnr_path)

@app.route('/api/track', methods=['POST'])
def track_directory():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Path is required'}), 400
    
    path = data['path']
    success = tracker.add_directory(path)
    
    if success:
        return jsonify({'message': f'Successfully tracking {path}'}), 200
    else:
        return jsonify({'error': f'Failed to track {path}'}), 400

@app.route('/api/untrack', methods=['POST'])
def untrack_directory():
    data = request.get_json()
    if not data or 'path' not in data:
        return jsonify({'error': 'Path is required'}), 400
    
    path = data['path']
    success = tracker.remove_directory(path)
    
    if success:
        return jsonify({'message': f'Successfully stopped tracking {path}'}), 200
    else:
        return jsonify({'error': f'Directory {path} was not being tracked'}), 400

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
        'config_file': config.config_file
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
    
    return jsonify({'message': 'Configuration updated'})

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    except KeyboardInterrupt:
        tracker.stop()
