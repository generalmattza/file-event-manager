import pytest
import asyncio
import logging
import os
from path_event_to_task.path_task_manager import ManagerConfig, PathTaskManager

from path_event_to_task.asynchronous.validator import FileValidator

logger = logging.getLogger(__name__)


@pytest.mark.asyncio(loop_scope="module")
async def test_task_manager(tmp_path):
    # Create a directory inside tmp_path for the manager to monitor
    monitor_dir = tmp_path / "test"
    monitor_dir.mkdir(parents=True)

    # Create a manager config that watches the newly-created directory
    manager_config = ManagerConfig(
        path_to_monitor=str(monitor_dir),  # convert to string if needed
        whitelisted_patterns=None,  # Example patterns
        process_delay=0,  # how quickly to process events
    )

    # Create a FileValidator that accepts files named "LastShot.txt"
    file_validator = FileValidator(name_pattern=r"LastShot.txt")

    # We'll store any "consumed" items in a list so we can assert on them
    consumed_items = []

    def my_consume_callback(item):
        logger.info(f"Callback got item: {item}")
        consumed_items.append(item)

    # Initialize the manager
    manager = PathTaskManager(
        manager_config=manager_config,
        validator=file_validator,
        consume_callback=my_consume_callback,
    )

    # Run the manager in a background task
    run_task = asyncio.create_task(manager.run())

    try:
        # Create a file that should match our validator pattern
        target_file = monitor_dir / "LastShot.txt"
        target_file.write_text("Some content")

        # Wait a short time for the observer + processor to notice the file
        while True:
            await asyncio.sleep(0.1)

        # Check that our callback was triggered
        # We expect at least one item in 'consumed_items'
        assert len(consumed_items) > 0, "No items were consumed."
        # Optionally, check the exact content, e.g.:
        # assert consumed_items[0].endswith("LastShot.txt")

    finally:
        # Stop the manager to clean up the observer thread
        manager.stop()
        # Also cancel our background task so it doesn't hang the test
        run_task.cancel()
        # If you want to await cancellation, do so here:
        try:
            await run_task
        except asyncio.CancelledError:
            pass
