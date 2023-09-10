"""Global fixtures."""
import pytest
from click.testing import CliRunner
from pytest import Config


def pytest_configure(config: Config) -> None:
    """For configuring pytest dynamically."""
    # add marker for slow tests
    config.addinivalue_line("markers", "slow: tests that are slower than average.")


@pytest.fixture
def runner() -> CliRunner:
    """Fixture for invoking command-line interfaces."""
    return CliRunner()
