import os
import glob
import time
import json
import threading
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
from PyQt5.QtCore import QThread, pyqtSignal

class LogFileHandler(FileSystemEventHandler):
    def __init__(self, callback, watch_dirs):
        self.callback = callback
        self.watch_dirs = watch_dirs
        self.last_pos = {}
        
        # Initialize sizes for all existing files in watched directories
        for d in self.watch_dirs:
            if not os.path.exists(d): continue
            for root, _, files in os.walk(d):
                for f in files:
                    if f.endswith('.jsonl') or f.endswith('.log'):
                        path = os.path.join(root, f)
                        try:
                            self.last_pos[path] = os.path.getsize(path)
                        except Exception:
                            self.last_pos[path] = 0

    def on_modified(self, event):
        if event.is_directory: return
        if event.src_path.endswith(".jsonl") or event.src_path.endswith(".log"):
            self.read_new_lines(event.src_path)
            
    def on_created(self, event):
        if event.is_directory: return
        if event.src_path.endswith(".jsonl") or event.src_path.endswith(".log"):
            self.last_pos[event.src_path] = 0
            self.read_new_lines(event.src_path)

    def read_new_lines(self, filepath):
        try:
            current_size = os.path.getsize(filepath)
            last_pos = self.last_pos.get(filepath, 0)
            
            if current_size < last_pos:
                last_pos = 0
                
            if current_size == last_pos:
                return

            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                f.seek(last_pos)
                new_data = f.read()
                self.last_pos[filepath] = f.tell()

            for line in new_data.splitlines():
                if line.strip():
                    self.process_line(line)
        except Exception:
            pass

    def process_line(self, line):
        try:
            # Try to parse as JSON (Antigravity format)
            data = json.loads(line)
            step_type = data.get("type", "")
            
            if step_type == "USER_INPUT":
                self.callback("working")
            elif step_type == "PLANNER_RESPONSE":
                tool_calls = data.get("tool_calls", [])
                if tool_calls and len(tool_calls) > 0:
                    self.callback("working")
                else:
                    self.callback("handing_file")
        except json.JSONDecodeError:
            # Fallback for plain text logs (other agents)
            lower_line = line.lower()
            if "working" in lower_line or "thinking" in lower_line or "running tool" in lower_line:
                self.callback("working")
            elif "finished" in lower_line or "handing_file" in lower_line or "response sent" in lower_line:
                self.callback("handing_file")
        except Exception:
            pass

class LogMonitorThread(QThread):
    state_changed = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.observer = Observer()

    def run(self):
        # 1. Base Antigravity log dir
        brain_dir = os.path.join(os.environ.get('USERPROFILE', ''), '.gemini', 'antigravity', 'brain')
        watch_dirs = [brain_dir] if os.path.exists(brain_dir) else []
        
        # 2. Configurable log dir
        import sys
        if getattr(sys, 'frozen', False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(os.path.abspath(__file__))
            
        config_path = os.path.join(base_dir, 'config.json')
        if os.path.exists(config_path):
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    custom_log = config.get("log_path", "")
                    if custom_log and os.path.exists(custom_log):
                        # If it's a file, watch its directory
                        if os.path.isfile(custom_log):
                            watch_dirs.append(os.path.dirname(custom_log))
                        else:
                            watch_dirs.append(custom_log)
            except Exception:
                pass
                
        # Remove duplicates
        watch_dirs = list(set(watch_dirs))
        
        event_handler = LogFileHandler(self.emit_state, watch_dirs)
        
        for d in watch_dirs:
            if os.path.exists(d):
                self.observer.schedule(event_handler, d, recursive=True)
                
        if watch_dirs:
            self.observer.start()
            
            try:
                while True:
                    time.sleep(1)
            except Exception:
                self.observer.stop()
            self.observer.join()

    def emit_state(self, state):
        self.state_changed.emit(state)
