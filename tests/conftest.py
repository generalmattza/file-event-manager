from pathlib import Path
import shutil
import tempfile
from typing_extensions import Buffer
from unittest.mock import MagicMock
import pytest


@pytest.fixture(scope="function")
def test_directory():
    """Fixture to create a temporary directory for testing."""
    temp_dir = tempfile.mkdtemp()
    yield Path(temp_dir)
    shutil.rmtree(temp_dir)


@pytest.fixture(scope="function")
def buffer():
    """Fixture to provide a mock Buffer object."""
    return MagicMock(spec=Buffer)
