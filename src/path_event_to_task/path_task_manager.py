import asyncio
import logging
from dataclasses import dataclass
from typing import Optional, Callable, Awaitable, Union

from path_event_to_task.path_observer import PathObserver
from path_event_to_task.asynchronous.event_handler import AsyncEventHandler
from path_event_to_task.asynchronous.processor import EventProcessor
from path_event_to_task.asynchronous.validator import (
    BaseValidator, 
)
logger = logging.getLogger(__name__)

#NOTE This implementation is not complete. It is a snippet that shows how to use the classes in the path_event_to_task package.
# However it fails to enagage the consumer task and the event processor task

@dataclass
class ManagerConfig:
    """Example config class for your manager."""

    path_to_monitor: str
    whitelisted_patterns: list
    recursive: bool = False
    process_delay: float = 2.0
    ignore_directories: bool = False
    case_sensitive: bool = False


class PathTaskManager:
    """
    Encapsulates:
      - AsyncEventHandler + PathObserver that watch a filesystem path
      - A user-supplied validator (e.g., FileValidator/FolderValidator)
      - An EventProcessor that takes events from event_queue -> input_buffer
      - A consumer task for the input_buffer, which may call a user-supplied callback
    """

    def __init__(
        self,
        manager_config: ManagerConfig,
        validator: BaseValidator,
        loop = None,
        consume_callback: Optional[Union[Callable, Awaitable]] = None,
    ):
        """
        :param manager_config: Configuration for the path observer and event processor.
        :param validator: A validator object (e.g., FileValidator or FolderValidator).
        :param consume_callback: Optional callback invoked when an item is read from input_buffer.
                                 May be synchronous or async.
        """
        # 1) Create an asyncio loop (if not already in one)
        self.loop = loop or asyncio.new_event_loop()

        # 2) Create the queues
        self.event_queue = asyncio.Queue()
        self.task_queue = asyncio.Queue()

        # 3) Create the async event handler
        self.event_handler = AsyncEventHandler(
            loop=self.loop,
            event_queue=self.event_queue,
            regexes=manager_config.whitelisted_patterns,
            ignore_directories=manager_config.ignore_directories,
            case_sensitive=manager_config.case_sensitive,
        )

        # 4) Create the observer (but don’t start it yet)
        self.observer = PathObserver(
            path_to_monitor=manager_config.path_to_monitor,
            recursive=manager_config.recursive,
            event_handler=self.event_handler,
        )

        # 5) Use the user-supplied validator
        self.validator = validator

        # 6) Create the event processor
        self.event_processor = EventProcessor(
            event_queue=self.event_queue,
            buffer=self.task_queue,
            validator=self.validator,
            process_delay=manager_config.process_delay,
        )

        # 7) Store the optional consume callback
        self.consume_callback = consume_callback

        # 8) Track any running tasks so we can cancel if needed
        self._tasks = []

    async def _consume_task_queue(self):
        """
        Continuously consume task from `self.task_queue`.
        If `consume_callback` is provided, each task is passed to that callback.
        """
        while True:
            task = await self.task_queue.get()  # blocks until an item is available
            try:
                logger.info(f"Consuming task: {task}")
                # If a callback is provided, call it (sync or async).
                if self.consume_callback:
                    if asyncio.iscoroutinefunction(self.consume_callback):
                        await self.consume_callback(task)
                    else:
                        self.consume_callback(task)
            except Exception as e:
                logger.exception("Error while consuming input buffer: %s", e)
            finally:
                self.task_queue.task_done()

    async def run(self):
        """
        Start the observer in a background thread, create the event-processing tasks,
        and run them indefinitely (or until canceled).
        """
        # 1) Start the observer in a background thread
        self.observer.start_in_thread()
        logger.info("Observer started in background thread.")

        # 2) Create and start tasks
        processor_task = asyncio.create_task(self.event_processor.process_events())
        consumer_task = asyncio.create_task(self._consume_task_queue())
        self._tasks.extend([processor_task, consumer_task])

        # 3) Run them forever (or until exception/cancel)
        await asyncio.gather(processor_task, consumer_task)

    def stop(self):
        """
        Stop the observer and cancel running tasks.
        """
        logger.info("Stopping observer...")
        self.observer.stop()
        logger.info("Observer stopped.")

        for t in self._tasks:
            t.cancel()
        logger.info("All tasks canceled.")


# ----------------------------------------------------------------------------
# Example usage
# ----------------------------------------------------------------------------
if __name__ == "__main__":

    logging.basicConfig(level=logging.DEBUG)

    loop = asyncio.new_event_loop()

    # Example config
    manager_config = ManagerConfig(
        path_to_monitor="./input/",
        whitelisted_patterns=[r".*"],
        process_delay=0,
    )

    # Example usage with a FileValidator or FolderValidator
    from path_event_to_task.asynchronous.validator import FileValidator

    file_validator = FileValidator(name_pattern=r"LastShot.txt")

    # Optional callback (can be synchronous)
    def my_consume_callback(item):
        print(f"Callback got item: {item}")

    # Or an async callback:
    async def my_consume_callback(item):
       await asyncio.sleep(0.01)
       print(f"Async callback got item: {item}")

    manager = PathTaskManager(
        loop=loop,
        manager_config=manager_config,
        validator=file_validator,
        consume_callback=my_consume_callback,
    )

    try:
        asyncio.run(manager.run())
    except KeyboardInterrupt:
        manager.stop()
