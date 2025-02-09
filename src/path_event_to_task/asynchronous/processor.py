# event_processor.py
import asyncio
from dataclasses import dataclass
import logging
from typing import Optional

from path_event_to_task.asynchronous.validator import BaseValidator
logger = logging.getLogger(__name__)


@dataclass
class EventProcessorConfig:
    event_queue: asyncio.Queue
    buffer: Optional[asyncio.Queue] = None
    validator: Optional[BaseValidator] = None
    process_delay: Optional[float] = 0

class EventProcessor:

    def __init__(
        self,
        event_queue: asyncio.Queue,
        buffer: asyncio.Queue = None,
        validator=None,
        process_delay: float = 0,
    ):
        """
        Args:
            event_queue (asyncio.Queue): Queue from which filesystem events are read.
            buffer: Target buffer where validated paths are added.
            validator: A single validator instance. This object must have a synchronous
                       validate(path_input) method that returns (bool, dict).
            process_delay (float): Optional delay (in seconds) before processing an event.
        """
        self.event_queue = event_queue
        self.buffer = buffer
        self.validator = validator
        self.process_delay = process_delay

    async def process_events(self):
        """
        Continuously processes events by:
          1. Dequeuing an event.
          2. Validating its source path using the provided validator.
          3. If validation passes, optionally waiting a delay and adding the path
             (or an alternate value provided via extra info) to the buffer.
        """
        while True:
            event = await self.event_queue.get()
            logger.debug(f"EventProcessor: Processing event for {event.src_path}")

            if self.validator:
                valid, info = self.validator.validate(event.src_path)
                if not valid:
                    logger.debug(
                        f"EventProcessor: Validation failed for {event.src_path} with error: {info.get('error', 'unknown error')}"
                    )
                    self.event_queue.task_done()
                    continue
            else:
                info = {}

            if self.process_delay:
                await asyncio.sleep(self.process_delay)

            if self.buffer is None:
                logger.debug(
                    f"EventProcessor: Skipping buffer addition for {event.src_path}."
                )
                self.event_queue.task_done()
                continue
            # Use an alternate path if provided by the validator; otherwise, use event.src_path.
            folder_name = info.get("new_folder", event.src_path)
            logger.info(
                f"EventProcessor: Adding folder '{folder_name}' for further processing."
            )
            await self.buffer.put(str(folder_name))
            self.event_queue.task_done()
