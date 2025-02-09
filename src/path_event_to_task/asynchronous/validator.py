from __future__ import annotations
from dataclasses import dataclass
import re
from pathlib import Path
from datetime import datetime
from typing import Optional


@dataclass
class BaseValidatorConfig:
    name_pattern: Optional[str] = None
    creation_date_min: Optional[datetime] = None
    creation_date_max: Optional[datetime] = None
    modified_date_min: Optional[datetime] = None
    modified_date_max: Optional[datetime] = None

class BaseValidator:
    def __init__(
        self,
        name_pattern: str = None,
        creation_date_min: datetime = None,
        creation_date_max: datetime = None,
        modified_date_min: datetime = None,
        modified_date_max: datetime = None,
    ):
        self.name_pattern = re.compile(name_pattern) if name_pattern else None
        self.creation_date_min = creation_date_min
        self.creation_date_max = creation_date_max
        self.modified_date_min = modified_date_min
        self.modified_date_max = modified_date_max

    def get_creation_time(self, path: Path) -> datetime:
        stat_result = path.stat()
        # Use st_birthtime if available; otherwise, fallback to st_ctime.
        creation_timestamp = getattr(stat_result, "st_birthtime", stat_result.st_ctime)
        return datetime.fromtimestamp(creation_timestamp)

    def validate_common(self, path: Path) -> (bool, dict):
        info = {}

        # Validate name pattern
        if self.name_pattern:
            if not self.name_pattern.search(path.name):
                return False, {
                    "error": f"Name '{path.name}' does not match pattern '{self.name_pattern.pattern}'."
                }
            info["name_valid"] = True

        # Validate creation date.
        creation_time = self.get_creation_time(path)
        info["creation_time"] = creation_time
        if self.creation_date_min and creation_time < self.creation_date_min:
            return False, {
                "error": f"Creation time {creation_time} is before minimum allowed {self.creation_date_min}."
            }
        if self.creation_date_max and creation_time > self.creation_date_max:
            return False, {
                "error": f"Creation time {creation_time} is after maximum allowed {self.creation_date_max}."
            }

        # Validate modified date.
        modified_time = datetime.fromtimestamp(path.stat().st_mtime)
        info["modified_time"] = modified_time
        if self.modified_date_min and modified_time < self.modified_date_min:
            return False, {
                "error": f"Modified time {modified_time} is before minimum allowed {self.modified_date_min}."
            }
        if self.modified_date_max and modified_time > self.modified_date_max:
            return False, {
                "error": f"Modified time {modified_time} is after maximum allowed {self.modified_date_max}."
            }

        return True, info


@dataclass
class FileValidatorConfig(BaseValidatorConfig):
    filesize_min: Optional[int] = None
    filesize_max: Optional[int] = None


class FileValidator(BaseValidator):
    def __init__(
        self,
        name_pattern: str = None,
        filesize_min: int = None,
        filesize_max: int = None,
        creation_date_min: datetime = None,
        creation_date_max: datetime = None,
        modified_date_min: datetime = None,
        modified_date_max: datetime = None,
    ):
        """
        Args:
            filesize_min (int): Minimum file size in bytes.
            filesize_max (int): Maximum file size in bytes.
            All other parameters are passed to BaseValidator.
        """
        super().__init__(
            name_pattern,
            creation_date_min,
            creation_date_max,
            modified_date_min,
            modified_date_max,
        )
        self.filesize_min = filesize_min
        self.filesize_max = filesize_max

    def validate(self, path_input) -> (bool, dict):
        """
        Validates a file by checking:
          - The path exists and is a file.
          - The common attributes (name, creation date, modified date).
          - The file size is within the specified range (if provided).

        Args:
            path_input (str or Path): The file path to validate.

        Returns:
            tuple: (is_valid: bool, info: dict)
        """
        path = Path(path_input)
        info = {}

        if not path.exists():
            return False, {"error": f"Path '{path}' does not exist."}
        if not path.is_file():
            return False, {"error": f"Path '{path}' is not a file."}

        # Common validations: name, creation date, and modified date.
        is_valid, common_info = self.validate_common(path)
        if not is_valid:
            return False, common_info
        info.update(common_info)

        # Validate file size.
        filesize = path.stat().st_size
        info["filesize"] = filesize
        if self.filesize_min is not None and filesize < self.filesize_min:
            return False, {
                "error": f"Filesize {filesize} is less than minimum allowed {self.filesize_min}."
            }
        if self.filesize_max is not None and filesize > self.filesize_max:
            return False, {
                "error": f"Filesize {filesize} is greater than maximum allowed {self.filesize_max}."
            }

        return True, info

@dataclass
class FolderValidatorConfig(BaseValidatorConfig):
    pass

class FolderValidator(BaseValidator):
    def validate(self, path_input) -> (bool, dict):
        """
        Validates a folder by checking:
          - The path exists and is a directory.
          - The common attributes (name, creation date, modified date).

        Args:
            path_input (str or Path): The folder path to validate.

        Returns:
            tuple: (is_valid: bool, info: dict)
        """
        path = Path(path_input)
        info = {}

        if not path.exists():
            return False, {"error": f"Path '{path}' does not exist."}
        if not path.is_dir():
            return False, {"error": f"Path '{path}' is not a folder."}

        # Common validations: name, creation date, and modified date.
        is_valid, common_info = self.validate_common(path)
        if not is_valid:
            return False, common_info
        info.update(common_info)

        return True, info


class CompositeValidator:
    def __init__(self, validators: list):
        """
        Args:
            validators (list): A list of validator instances. Each must have a
                validate(path_input) method returning (bool, dict).
        """
        self.validators = validators

    def validate(self, path_input) -> (bool, dict):
        """
        Applies all validators in order on the given path_input.

        Returns:
            (bool, dict): True and merged extra info if all validators pass,
                          False and error info of the first failure otherwise.
        """
        combined_info = {}
        for validator in self.validators:
            valid, info = validator.validate(path_input)
            if not valid:
                return False, info
            combined_info.update(info)
        return True, combined_info
