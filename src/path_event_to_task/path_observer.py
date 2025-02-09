from dataclasses import dataclass
from pathlib import Path
import threading
import logging

# from watchdog.observers import Observer
from watchdog.observers.polling import PollingObserver
from watchdog.events import LoggingEventHandler
from typing import Optional, Union

logger = logging.getLogger(__name__)

@dataclass
class PathObserverConfig:
    path_to_monitor: Union[str, Path]
    recursive: bool = False
    event_handler = None

class PathObserver:
    """
    Encapsulates folder monitoring with dynamic handlers.

    This class monitors a given directory path for file system events such as
    creation, modification, and deletion of files and folders. Event handlers
    for these events can be dynamically assigned to handle actions as needed.

    Users will need to create a custom event handler class by inheriting from
    `FileSystemEventHandler` and overriding methods such as `on_created`,
    `on_modified`, or `on_deleted` to implement custom actions when these
    events occur.

    :param path_to_monitor: The path to monitor for file system events.
    :param recursive: Whether to monitor subdirectories. Defaults to False.
    :param event_handler: An optional event handler class derived from
                          `FileSystemEventHandler`. If not provided, a default
                          logging event handler is used.
    """

    def __init__(
        self,
        path_to_monitor: Union[str, Path],
        recursive: bool = False,
        event_handler=None,
    ):
        """
        Initialize the observer for a specific path.

        :param path_to_monitor: The path to monitor for file system events.
        :param recursive: Whether to monitor subdirectories.
        """
        if not isinstance(path_to_monitor, Path):
            path_to_monitor = Path(path_to_monitor)
        self.path_to_monitor = path_to_monitor
        self.recursive = recursive
        self.event_handler = (
            LoggingEventHandler(logger=logger)
            if event_handler is None
            else event_handler
        )
        self.observer = PollingObserver()
        self._thread: Optional[threading.Thread] = None

    def start(self):
        """Start monitoring the path."""
        self.observer.schedule(
            self.event_handler, path=self.path_to_monitor, recursive=self.recursive
        )
        self.observer.start()
        logger.info(f"Started monitoring {self.path_to_monitor}")

    def stop(self):
        """Stop monitoring the path."""
        self.observer.stop()
        self.observer.join()
        logger.info(f"Stopped monitoring {self.path_to_monitor}")

    def start_in_thread(self):
        """
        Start monitoring the path in a separate thread.
        This allows monitoring to run in the background.
        """
        if self._thread and self._thread.is_alive():
            logger.warning("Observer is already running in a thread.")
            return

        def run_observer():
            try:
                self.start()
            except Exception as e:
                logger.error(f"Error in observer thread: {e}")

        self._thread = threading.Thread(target=run_observer, daemon=True)
        self._thread.start()
        logger.info(f"Observer thread started for {self.path_to_monitor}")
