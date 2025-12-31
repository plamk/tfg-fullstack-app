import logging

from watchdog.events import FileSystemEventHandler


class FileMonitor:
    def __init__(self, path: str, on_change=None):
        self.path = path
        self.event_handler = FileChangeHandler()
        self.observer = None
        if on_change:
            self.event_handler.on_created = on_change
            self.event_handler.on_modified = on_change
            self.event_handler.on_deleted = on_change
            self.event_handler.on_moved = on_change

    def start(self):
        from watchdog.observers import Observer

        self.observer = Observer()
        self.observer.schedule(self.event_handler, self.path, recursive=True)
        self.observer.start()
        logging.info("Started monitoring %s", self.path)

    def stop(self):
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logging.info("Stopped monitoring %s", self.path)


class FileChangeHandler(FileSystemEventHandler):
    def on_created(self, event):
        logging.info("Created: %s", event.src_path)

    def on_modified(self, event):
        logging.info("Modified: %s", event.src_path)

    def on_deleted(self, event):
        logging.info("Deleted: %s", event.src_path)

    def on_moved(self, event):
        logging.info("Moved: %s -> %s", event.src_path, event.dest_path)
