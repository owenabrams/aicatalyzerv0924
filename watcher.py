from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import os
import signal
import subprocess
import time

class Watcher:
    def __init__(self, directory_to_watch):
        self.DIRECTORY_TO_WATCH = directory_to_watch
        self.observer = Observer()
        self.process = None

    def run(self):
        event_handler = Handler(self)
        self.observer.schedule(event_handler, self.DIRECTORY_TO_WATCH, recursive=True)
        self.observer.start()
        self.start_services()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            self.stop_services()
            self.observer.stop()

        self.observer.join()

    def start_services(self):
        print("Starting Flask and ngrok...")
        self.process = subprocess.Popen(["./run_services.sh"], shell=True)

    def stop_services(self):
        if self.process:
            print("Stopping Flask and ngrok...")
            self.process.terminate()
            try:
                self.process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                self.process.kill()
            self.process = None

class Handler(FileSystemEventHandler):
    def __init__(self, watcher):
        self.watcher = watcher

    def on_any_event(self, event):
        if event.event_type in ('modified', 'created', 'deleted'):
            print(f"Detected change in: {event.src_path}")
            self.watcher.stop_services()
            time.sleep(1)  # Optional: delay to allow for file save completion
            self.watcher.start_services()

if __name__ == '__main__':
    w = Watcher(directory_to_watch=".")
    w.run()
