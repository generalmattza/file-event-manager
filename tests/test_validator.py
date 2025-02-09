# test_composite_validator.py
import os
from datetime import datetime, timedelta

from path_event_to_task.asynchronous.validator import FileValidator, FolderValidator, CompositeValidator


def test_valid_file(tmp_path):
    # Create a file named "report.txt" that should pass the name regex.
    file_path = tmp_path / "report.txt"
    # Write 1500 'a' characters (approx. 1500 bytes for ascii).
    file_path.write_text("a" * 1500)

    # Create a FileValidator that requires:
    # - name containing "report"
    # - file size between 1000 and 2000 bytes
    # - no date constraints for this test.
    validator = FileValidator(
        name_pattern=r"report", filesize_min=1000, filesize_max=2000
    )
    valid, info = validator.validate(file_path)
    assert valid is True
    # We expect info to contain filesize, creation_time, modified_time, etc.
    assert "filesize" in info
    assert info["filesize"] == 1500


def test_invalid_file_name(tmp_path):
    # Create a file that does NOT match the name pattern.
    file_path = tmp_path / "other.txt"
    file_path.write_text("a" * 1500)

    validator = FileValidator(
        name_pattern=r"report", filesize_min=1000, filesize_max=2000
    )
    valid, info = validator.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "does not match" in info["error"]


def test_invalid_file_size_min(tmp_path):
    # Create a file with size below the minimum.
    file_path = tmp_path / "report.txt"
    file_path.write_text("a" * 500)  # 500 bytes, below minimum of 1000
    validator = FileValidator(
        name_pattern=r"report", filesize_min=1000, filesize_max=2000
    )
    valid, info = validator.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "less than minimum" in info["error"]


def test_invalid_file_size_max(tmp_path):
    # Create a file with size above the maximum.
    file_path = tmp_path / "report.txt"
    file_path.write_text("a" * 2500)  # 2500 bytes, above maximum of 2000
    validator = FileValidator(
        name_pattern=r"report", filesize_min=1000, filesize_max=2000
    )
    valid, info = validator.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "greater than maximum" in info["error"]


def test_invalid_file_modified_date(tmp_path):
    # Create a file and then set its modification time to 2 days ago.
    file_path = tmp_path / "report.txt"
    file_path.write_text("a" * 1500)
    two_days_ago = datetime.now() - timedelta(days=2)
    mod_time = two_days_ago.timestamp()
    os.utime(file_path, (mod_time, mod_time))

    # Validator requires a modified date at least as recent as yesterday.
    validator = FileValidator(
        name_pattern=r"report", modified_date_min=datetime.now() - timedelta(days=1)
    )
    valid, info = validator.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "Modified time" in info["error"]


def test_file_validator_with_directory(tmp_path):
    # Create a directory but pass it to FileValidator.
    dir_path = tmp_path / "report.txt"
    dir_path.mkdir()

    validator = FileValidator(name_pattern=r"report")
    valid, info = validator.validate(dir_path)
    assert valid is False
    assert "error" in info
    assert "is not a file" in info["error"]


def test_valid_folder(tmp_path):
    # Create a folder that matches the required name pattern.
    folder_path = tmp_path / "data_folder"
    folder_path.mkdir()

    validator = FolderValidator(name_pattern=r"data")
    valid, info = validator.validate(folder_path)
    assert valid is True
    # The info dict should include creation_time and modified_time.
    assert "creation_time" in info
    assert "modified_time" in info


def test_invalid_folder_name(tmp_path):
    # Create a folder that does not match the name pattern.
    folder_path = tmp_path / "other_folder"
    folder_path.mkdir()

    validator = FolderValidator(name_pattern=r"data")
    valid, info = validator.validate(folder_path)
    assert valid is False
    assert "error" in info
    assert "does not match" in info["error"]


def test_folder_validator_with_file(tmp_path):
    # Create a file and pass it to FolderValidator.
    file_path = tmp_path / "data_folder"
    file_path.write_text("some content")

    validator = FolderValidator(name_pattern=r"data")
    valid, info = validator.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "is not a folder" in info["error"]


def test_composite_valid_file(tmp_path):
    # Create a temporary file that meets our criteria.
    file_path = tmp_path / "report_valid.txt"
    file_path.write_text("a" * 1500)  # 1500 bytes

    # Create two file validators with slightly different conditions.
    validator1 = FileValidator(
        name_pattern=r"report",
        filesize_min=1000,
        filesize_max=2000,
        modified_date_min=datetime.now() - timedelta(days=1),
    )
    validator2 = FileValidator(
        name_pattern=r".*valid.*",  # file name must contain 'valid'
    )

    composite = CompositeValidator(validators=[validator1, validator2])
    valid, info = composite.validate(file_path)
    assert valid is True, f"Validation should pass, got info: {info}"


def test_composite_invalid_file(tmp_path):
    # Create a temporary file that fails one of the validators.
    file_path = tmp_path / "invalid_report.txt"
    file_path.write_text("a" * 500)  # 500 bytes, which is below the minimum of 1000

    validator1 = FileValidator(
        name_pattern=r"report",
        filesize_min=1000,
        filesize_max=2000,
    )
    # This second validator might be irrelevant here because the first will fail.
    validator2 = FileValidator(
        name_pattern=r".*report.*",
    )
    composite = CompositeValidator(validators=[validator1, validator2])
    valid, info = composite.validate(file_path)
    assert valid is False
    assert "error" in info
    assert "less than minimum" in info["error"]
