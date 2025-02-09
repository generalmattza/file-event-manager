# async_event_handler.py
from dataclasses import dataclass
import asyncio
import logging
from typing import Optional
from prometheus_client import Counter
from watchdog.events import (
    RegexMatchingEventHandler,
    LoggingEventHandler,
    FileSystemEvent,
)

logger = logging.getLogger(__name__)


@dataclass
class AsyncEventHandlerConfig:
    loop: Optional[asyncio.AbstractEventLoop] = None
    event_queue: Optional[asyncio.Queue] = None
    regexes: Optional[list] = None
    ignore_regexes: Optional[list] = None
    ignore_directories: Optional[bool] = False
    case_sensitive: Optional[bool] = False


class AsyncEventHandler(LoggingEventHandler, RegexMatchingEventHandler):

    folders_detected = Counter(
        "path_observer_events_detected",
        "Number of events detected by the path observer event handler",
        ["path"],
    )

    def __init__(
        self,
        loop: asyncio.AbstractEventLoop,
        event_queue: Optional[asyncio.Queue] = None,
        regexes: Optional[list] = None,
        ignore_regexes: Optional[list] = None,
        ignore_directories: Optional[bool] = False,
        case_sensitive: Optional[bool] = False,
    ):
        # Initialize parent classes
        LoggingEventHandler.__init__(self, logger=logger)
        RegexMatchingEventHandler.__init__(
            self,
            regexes=regexes or None,
            ignore_regexes=ignore_regexes or [],
            ignore_directories=ignore_directories,
            case_sensitive=case_sensitive,
        )
        self.loop = loop
        self.event_queue = event_queue or asyncio.Queue()

    def on_created(self, event: FileSystemEvent):
        """
        Enqueue the event for async processing.
        """
        logger.debug(
            f"on_created triggered for {event.src_path}. Queueing for async processing."
        )
        # Post to the event loop from the Watchdog thread
        self.loop.call_soon_threadsafe(self.event_queue.put_nowait, event)

    def on_modified(self, event: FileSystemEvent):
        """
        If you want to handle modifications asynchronously, you can do so similarly.
        """
        logger.debug(
            f"on_created triggered for {event.src_path}. Queueing for async processing."
        )
        # Post to the event loop from the Watchdog thread
        self.loop.call_soon_threadsafe(self.event_queue.put_nowait, event)
