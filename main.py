#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Example async path  that uses an AsyncTestDataEventHandler,
a CompositeValidator, and an EventProcessor.
"""
import asyncio
from dataclasses import asdict
import logging
from pathlib import Path

from path_event_to_task.path_observer import PathObserver
from path_event_to_task.asynchronous.event_handler import AsyncEventHandler
from path_event_to_task.asynchronous.processor import EventProcessor
from path_event_to_task.asynchronous.validator import (
    FileValidator,
)


WHITELIST = "LastShot.txt"
PATH_TO_MONITOR = Path("./input")

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

input_buffer = asyncio.Queue()
async def consume_input_buffer(input_buffer):
    """
    Continuously check the input_buffer, and whenever a path is available,
    load it into the output_buffer using load_dir_to_buffer.
    """
    while True:
        if input_buffer.qsize() > 0:
            work_to_do = await input_buffer.get()
            logger.debug(f"Doing some work with {work_to_do}")
            input_buffer.task_done()

        else:
            await asyncio.sleep(0.1)


async def main():
    # Create an asyncio Queue for new filesystem events.
    event_queue = asyncio.Queue()
    loop = asyncio.get_running_loop()
    event_handler = AsyncEventHandler(
        loop=loop,
        event_queue=event_queue,
        regexes=None,
        ignore_directories=False,
        case_sensitive=False,
    )

    observer = PathObserver(
        path_to_monitor=PATH_TO_MONITOR,
        recursive=False,
        event_handler=event_handler,
    )
    observer.start_in_thread()

    # Set up our validators:
    # FileValidator checks that the filename exactly matches "LastShot.txt".
    file_validator = FileValidator(name_pattern=WHITELIST)

    # Create the event processor that uses our composite validator.
    event_processor = EventProcessor(
        event_queue,
        buffer=input_buffer,
        validator=file_validator,
        process_delay=0,
    )
    events_consumer_task = asyncio.create_task(event_processor.process_events())
    input_buffer_task = asyncio.create_task(
        consume_input_buffer(input_buffer)
    )

    # Wait for the tasks to run indefinitely.
    await asyncio.gather(events_consumer_task, input_buffer_task)


if __name__ == "__main__":
    asyncio.run(main())
