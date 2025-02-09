from collections import deque
import os
from pathlib import Path
import time
import logging

from prometheus_client import Counter
from watchdog.events import (
    RegexMatchingEventHandler,
    LoggingEventHandler,
)

logger = logging.getLogger(__name__)

class BaseEventHandler(RegexMatchingEventHandler, LoggingEventHandler):

    folders_detected = Counter(
        "path_observer_folders_detected",
        "Number of folders detected by the path observer",
        ["path"],
    )

    def __init__(
        self,
        buffer: deque,
        regexes: list[str] | None = None,
        ignore_regexes: list[str] | None = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
        validation_enabled: bool = True,
        validation_timeout: int = 2,
    ):
        LoggingEventHandler.__init__(self, logger=logger)
        RegexMatchingEventHandler.__init__(
            self,
            regexes=regexes,
            ignore_regexes=ignore_regexes,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.buffer = buffer
        self.validation_enabled = validation_enabled
        self.validation_timeout = validation_timeout

    def process_event(self, event):
        """Validate a detected event for addition to the buffer."""
        pass

    def on_created(self, event):
        """Event handler for when a file or directory is created."""
        pass

    def on_modified(self, event):
        """Event handler for when a file or directory is modified."""
        pass

    def validate(self, event, timeout=None):
        # Ensure that event is a directory
        # Ensure that ShotLog.json file is in directory
        # Ensure that ShotLog.json file is not empty

        return True


class TestDataEventHandler(BaseEventHandler):

    def __init__(
        self,
        buffer: deque,
        regexes: list[str] | None = None,
        ignore_regexes: list[str] | None = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
        validation_enabled: bool = True,
        validation_timeout: int = 2,
    ):
        super().__init__(
            buffer=buffer,
            regexes=regexes,
            ignore_regexes=ignore_regexes,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
            validation_enabled=validation_enabled,
            validation_timeout=validation_timeout,
        )

    def process_event(self, event):
        """Validate a detected event for addition to the buffer."""
        folder_name = os.path.basename(event.src_path)
        logger.debug(
            f"Folder '{folder_name}' detected for ingest.",
            extra={"path": event.src_path},
        )
        # If validation is enabled, validate the event
        if self.validation_enabled:
            if not self.validate(event):
                # If validation fails, return None
                return

        # Put the path in the buffer
        logger.debug(
            f"Folder '{folder_name}' added to processing queue",
            extra={"path": event.src_path},
        )
        self.buffer.put(event.src_path)
        self.folders_detected.labels(event.src_path).inc()

    def on_created(self, event):
        """Event handler for when a file or directory is created."""
        self.process_event(event)

    def validate(self, event, timeout=None):
        # Ensure that event is a directory
        # Ensure that ShotLog.json file is in directory
        # Ensure that ShotLog.json file is not empty

        timeout = timeout or self.validation_timeout
        start_time = time.time()

        # Ensure that event is a directory
        if not event.is_directory:
            logger.error(f"Detected event is not a directory, and is not suitable for ingest. Only directories are supported at this time")
            return False

        # Ensure that directory exists
        if not Path(event.src_path).exists():
            logger.error(f"Detected event does not exist")
            return False

        # Ensure that ShotLog.json file is in directory
        while time.time() - start_time < timeout:
            for file in os.listdir(event.src_path):
                if file == "ShotLog.json":
                    try:
                        with open(os.path.join(event.src_path, file), "r") as f:
                            if f.read():
                                return True
                    except OSError as e:
                        logger.error(f"A non-critical error occurred {e}, continuing ...")
                        continue

                else:
                    continue
        else:
            logger.error(
                f"Directory {event.src_path} detected, however a non-empty ShotLog.json not found within timeout of {timeout}s. Ensure that ShotLog.json is present and not empty.",
                extra={"event": event},
            )
            return False


class LastShotEventHandler(BaseEventHandler):

    def __init__(
        self,
        buffer: deque,
        regexes: list[str] | None = None,
        ignore_regexes: list[str] | None = None,
        ignore_directories: bool = False,
        case_sensitive: bool = False,
        validation_enabled: bool = True,
        validation_timeout: int = 2,
        trigger_filename: str = "LastShot.txt",
    ):
        super().__init__(
            buffer=buffer,
            regexes=regexes,
            ignore_regexes=ignore_regexes,
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
            validation_enabled=validation_enabled,
            validation_timeout=validation_timeout,
        )
        self.trigger_filename = trigger_filename    

    def process_event(self, event):
        """Validate a detected event for addition to the buffer."""
        folder_name = os.path.basename(event.src_path)
        logger.debug(
            f"Folder '{folder_name}' detected for ingest.",
            extra={"path": event.src_path},
        )
        # If validation is enabled, validate the event
        if self.validation_enabled:
            if not self.validate(event):
                # If validation fails, return None
                return

        # Put the path in the buffer
        logger.debug(
            f"Folder '{folder_name}' added to processing queue",
            extra={"path": event.src_path},
        )
        self.buffer.put(event.src_path)
        self.folders_detected.labels(event.src_path).inc()

    def on_created(self, event):
        """Event handler for when a file or directory is created."""
        self.process_event(event)

    def on_modified(self, event):
        """Event handler for when a file or directory is modified."""
        # self.process_event(event)
        self.process_event(event)

    def validate(self, event, timeout=None):
        # Ensure that event is a directory
        # Ensure that ShotLog.json file is in directory
        # Ensure that ShotLog.json file is not empty

        timeout = timeout or self.validation_timeout
        start_time = time.time()

        # Ensure that event is a directory
        if not event.is_directory:
            logger.error(
                f"Detected event is not a directory, and is not suitable for ingest. Only directories are supported at this time"
            )
            return False

        # Ensure that directory exists
        if not Path(event.src_path).exists():
            logger.error(f"Detected event does not exist")
            return False

        # Ensure that ShotLog.json file is in directory
        while time.time() - start_time < timeout:
            for file in os.listdir(event.src_path):
                if file == "ShotLog.json":
                    try:
                        with open(os.path.join(event.src_path, file), "r") as f:
                            if f.read():
                                return True
                    except OSError as e:
                        logger.error(
                            f"A non-critical error occurred {e}, continuing ..."
                        )
                        continue

                else:
                    continue
        else:
            logger.error(
                f"Directory {event.src_path} detected, however a non-empty ShotLog.json not found within timeout of {timeout}s. Ensure that ShotLog.json is present and not empty.",
                extra={"event": event},
            )
            return False
