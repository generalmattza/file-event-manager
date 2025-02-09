import pytest

import pytest

import time
from unittest.mock import MagicMock, patch
from path_event_to_task import PathObserver, FileSystemEventHandler


# Create a temporary directory for testing
@pytest.fixture(scope="module")
def test_directory(tmp_path_factory):
    # Create a temporary directory
    temp_dir = tmp_path_factory.mktemp("test_directory")
    return temp_dir


@pytest.fixture
def observer(test_directory):
    """Fixture to create a PathObserver instance."""
    observer = PathObserver(path_to_monitor=str(test_directory), recursive=False)
    return observer


@pytest.fixture(scope="function")
def handler():
    """Fixture to create a dictionary of mock event handlers.
    Used to test the event handling methods and ensure they are called correctly."""

    class TestHandler(FileSystemEventHandler):
        def __init__(self):
            self.handlers = {
                "on_created": MagicMock(),
                "on_modified": MagicMock(),
                "on_deleted": MagicMock(),
            }

        def on_created(self, event):
            super().on_created(event)  # Call the parent class method
            self.handlers["on_created"](event.src_path)
            self.handlers["on_created"](event.src_path)

        def on_modified(self, event):
            self.handlers["on_modified"](event.src_path)

        def on_deleted(self, event):
            self.handlers["on_deleted"](event.src_path)

        def assert_called_with(self, event_type: str, path: str):
            try:
                self.handlers[event_type].assert_called_with(path)
            except KeyError:
                raise ValueError(f"Invalid event type: {event_type}")

    return TestHandler()


# Test starting and stopping the observer
def test_start_and_stop_observer(observer):
    """Test starting and stopping the observer."""

    with (
        patch.object(observer.observer, "start") as mock_start,
        patch.object(observer.observer, "stop") as mock_stop,
        patch.object(observer.observer, "join"),  # Prevent blocking
    ):

        # Start the observer
        observer.start_in_thread()
        time.sleep(0.1)  # Give it a moment to start

        mock_start.assert_called_once()  # Ensure start was called

        # Stop the observer
        observer.stop()
        time.sleep(0.1)  # Give it a moment to stop

        mock_stop.assert_called_once()  # Ensure stop was called


# Test handling folder creation events
def test_handle_created_event(observer, test_directory, handler):
    """Test the event handler for folder creation."""

    observer.event_handler = handler
    observer.start_in_thread()
    while not observer.observer.is_alive():
        time.sleep(0.1)  # Give it a moment to start

    new_folder = test_directory / "new_folder"
    new_folder.mkdir()  # Simulate folder creation

    time.sleep(0.1)  # Allow time for the observer to pick up the event

    observer.event_handler.assert_called_with("on_created", str(new_folder))


# Test handling file modification events
def test_handle_modified_event(observer, test_directory, handler):
    """Test the event handler for file modification."""

    observer.event_handler = handler
    observer.start_in_thread()
    while not observer.observer.is_alive():
        time.sleep(0.1)  # Give it a moment to start

    new_file = test_directory / "new_file.txt"
    new_file.write_text("initial content")  # Create file and add content

    time.sleep(0.1)  # Allow time for the observer to pick up the event

    new_file.write_text("updated content")  # Modify the file

    time.sleep(0.1)  # Allow time for the observer to pick up the event

    # Check if the handler was called
    observer.event_handler.assert_called_with("on_modified", str(new_file))


# Test handling file deletion events
def test_handle_deleted_event(observer, test_directory, handler):
    """Test the event handler for file deletion."""

    observer.event_handler = handler
    observer.start_in_thread()
    while not observer.observer.is_alive():
        time.sleep(0.1)  # Give it a moment to start

    file_to_delete = test_directory / "file_to_delete.txt"
    file_to_delete.write_text("some content")  # Create file

    time.sleep(0.1)  # Allow time for the observer to pick up the event

    file_to_delete.unlink()  # Delete the file

    time.sleep(0.1)  # Allow time for the observer to pick up the event

    # Check if the handler was called
    observer.event_handler.assert_called_with("on_deleted", str(file_to_delete))


# Test if the observer is already running
def test_observer_already_running(observer):
    """Test if observer thread is already running."""

    observer.start_in_thread()
    with patch("path_observer.path_observer.logger.warning") as mock_logger:
        observer.start_in_thread()  # Attempt to start again
        time.sleep(1)  # Allow time for the observer thread

        mock_logger.assert_called_with("Observer is already running in a thread.")

