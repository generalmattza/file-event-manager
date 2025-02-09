import asyncio

# from path_observer.asynchronous.event_handler import AsyncTestDataEventHandler
# from path_observer.asynchronous.processor import process_incoming_events
# from path_observer.path_observer import PathObserver
# import pytest


# @pytest.mark.asyncio
# async def test_event_handler(buffer, test_directory):
#     event_queue = asyncio.Queue()

#     # Build an async event handler for Watchdog
#     loop = asyncio.get_running_loop()

#     event_handler = AsyncTestDataEventHandler(
#         loop=loop,
#         event_queue=event_queue,
#         regexes=[".*"],
#         ignore_directories=False,
#         case_sensitive=False,
#     )

#     # Set up the PathObserver with the async event handler, then start it in a thread
#     observer = PathObserver(
#         path_to_monitor=test_directory,
#         recursive=False,
#         event_handler=event_handler,
#     )
#     observer.start_in_thread()

#     # Launch async tasks to process events -> input_buffer, and input_buffer -> output_buffer
#     validation_timeout = 10
#     process_delay = None
#     events_consumer_task = asyncio.create_task(
#         process_incoming_events(event_queue, buffer, validation_enabled=True, validation_timeout=validation_timeout, process_delay=process_delay)
#     )

#     await asyncio.gather(events_consumer_task)

