"""Test cases for the __main__ module."""
from pathlib import Path
from typing import Optional
from typing import Tuple

import osmnx
import pytest
from click.testing import CliRunner
from click.testing import Result

from nomad import __main__
from tests.types import RunnerArgs


def sanitize_runner_params(args: Tuple[RunnerArgs, ...], sep: str = " ") -> str:
    """Utility function to clean args and prepare for CliRunner."""
    # sanitized list
    sanitized = []

    # clean
    for arg in args:
        if arg is not None and type(arg) is not tuple:
            # update list
            sanitized.append(str(arg))

        elif type(arg) is tuple:
            # extend the list with the contents of arg list
            for element in arg:
                sanitized.append(str(element))

        else:
            # do nothing with empty arg (i.e a tuple)
            pass

    # finally
    return sep.join(sanitized)


def run_command(runner: CliRunner, *args: RunnerArgs) -> Result:
    """Utility function to run arbitray numbers of commands/options/values."""
    # remove empty tuples (i.e. args meant to be empty)
    sanitized = sanitize_runner_params(args)

    # get result
    return runner.invoke(__main__.main, sanitized)


@pytest.mark.parametrize("cmd,code", [(None, 0), ("geocode", 0)])
def test_help_by_default_succeeds(
    runner: CliRunner, cmd: Optional[str], code: int
) -> None:
    """Without arguments/options should print help message and exit."""
    # test if command exits normally
    result = run_command(runner, cmd)

    # check code
    assert result.exit_code == code

    # check usage message printed
    assert "Usage" in result.output


def test_default_cache_dir() -> None:
    """Sanity check for default caching directory."""
    assert osmnx.settings.cache_folder == __main__.NOMAD_CACHE_DIR


@pytest.mark.slow
def test_geocode_location_error(runner: CliRunner) -> None:
    """Confirm geocode handles location errors correctly."""
    # execute command
    result = run_command(runner, "geocode", "laksdfljasdkfj")

    # check output
    assert "Nominatim could not geocode query" in result.output


@pytest.mark.slow
def test_download_location_error(runner: CliRunner, tmp_path: Path) -> None:
    """Confirm download cmd handles location errors correctly."""
    # get custom path
    cache_dir = tmp_path / "cache"

    # execute command
    result = run_command(runner, "download", "-d", str(cache_dir), "laksdfljasdkfj")

    # check output
    assert "could not be found" in result.output


@pytest.mark.slow
def test_download_cache_dir(runner: CliRunner, tmp_path: Path) -> None:
    """Confirm download cmd handles location errors correctly."""
    # get custom path
    cache_dir = tmp_path / "cache"

    # execute command
    _ = run_command(runner, "download", "-d", str(cache_dir), "laksdfljasdkfj")

    # check correct cache folder used
    assert osmnx.settings.cache_folder == str(cache_dir)

    # check cache only mode set
    assert osmnx.settings.cache_only_mode
