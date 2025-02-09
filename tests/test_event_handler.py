
import time
from watchdog.observers import Observer
from path_event_to_task.synchronous.event_handler import TestDataEventHandler, LastShotEventHandler


# @pytest.fixture
# def test_directory():
#     """Fixture to create a temporary directory for testing."""
#     temp_dir = tempfile.mkdtemp()
#     yield Path(temp_dir)
#     shutil.rmtree(temp_dir)


# @pytest.fixture
# def buffer():
#     """Fixture to provide a mock Buffer object."""
#     return MagicMock(spec=Buffer)


def test_on_created_with_observer(buffer, test_directory):
    """Test the on_created method with a live observer."""
    # Create a handler with a regex to match .txt files
    handler = TestDataEventHandler(
        buffer=buffer,
        regexes=[r".*\.txt$"],
        ignore_directories=True,
        validation_enabled=False,
    )

    # Initialize and start the observer
    observer = Observer()
    observer.schedule(handler, str(test_directory), recursive=False)
    observer.start()

    try:
        # Create a matching file
        file_path = test_directory / "test_file.txt"
        file_path.touch()  # Create the file

        # Wait for the observer to process the event
        time.sleep(1)

        # Verify that the buffer's put method was called with the correct path
        buffer.put.assert_called_once_with(str(file_path))
    finally:
        observer.stop()
        observer.join()


def test_on_created_non_matching_with_observer(buffer, test_directory):
    """Test the on_created method with a non-matching file using a live observer."""
    # Create a handler with a regex to match .txt files
    handler = TestDataEventHandler(
        buffer=buffer,
        regexes=[r".*\.txt$"],
        ignore_directories=True,
    )

    # Initialize and start the observer
    observer = Observer()
    observer.schedule(handler, str(test_directory), recursive=False)
    observer.start()

    try:
        # Create a non-matching file
        file_path = test_directory / "test_file.json"
        file_path.touch()  # Create the file

        # Wait for the observer to process the event
        time.sleep(1)

        # Verify that the buffer's put method was not called
        buffer.put.assert_not_called()
    finally:
        observer.stop()
        observer.join()


# def test_modified_with_lastshot_event(buffer, test_directory):

#     handler = LastShotEventHandler(
#         buffer=buffer,
#         regexes=[r"LastShot.txt$"],
#         ignore_directories=True,
#         validation_enabled=True,
#         trigger_filename="LastShot.txt",
#     )

#     observer = Observer()
#     observer.schedule(handler, str(test_directory), recursive=False)
#     observer.start()

#     try:
#         file_path = test_directory / "LastShot.txt"
#         file_path.touch()

#         #Write "920" to the file
#         with open(file_path, "w") as file:
#             file.write("920")


#         time.sleep(1)

#         buffer.put.assert_called_once_with(str(file_path))

#     finally:
#         observer.stop()
#         observer.join()

