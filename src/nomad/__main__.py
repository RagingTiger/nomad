"""Command-line interface."""
import json
import logging
import pathlib
import re
import sys
from typing import Any
from typing import Callable
from typing import Dict
from typing import Generator
from typing import Tuple

import click
import osmnx


# globals
NOMAD_CACHE_DIR = "./.nomad/osmnx/cache"

# configure settings for nomad
osmnx.settings.cache_folder = NOMAD_CACHE_DIR


@click.group(invoke_without_command=True, no_args_is_help=True)
@click.version_option()
@click.option("-n", "--dry-run", is_flag=True, help="Simulates running commands.")
@click.option("-e", "--debug", is_flag=True, help="Turn on debugging features.")
@click.pass_context
def main(ctx: click.Context, dry_run: bool, debug: bool) -> None:
    """Nomad CLI entry point."""
    # check context is from __name__ == __main__
    ctx.ensure_object(dict)

    # update dry run key
    ctx.obj["DRY_RUN"] = dry_run
    ctx.obj["DEBUG"] = debug

    # check for debugging
    if debug:
        # turn on console logging
        osmnx.settings.log_level = logging.DEBUG
        osmnx.settings.log_console = True


def sync_main_flags(ctx: click.Context) -> Tuple[bool, bool]:
    """Simply sync flags from main with subcommands flags."""
    # sync flags
    return ctx.obj["DRY_RUN"], ctx.obj["DEBUG"]


@main.command(
    "geocode",
    no_args_is_help=True,
    short_help="Convert location string into latitude/longitude pair.",
)
@click.option("-c", "--cache", is_flag=True, help="Cache geocode JSON response.")
@click.option("-p", "--pretty-print", is_flag=True, help="Toggle pretty printing.")
@click.argument("location", type=str)
@click.pass_context
def geocode(ctx: click.Context, cache: bool, pretty_print: bool, location: str) -> None:
    """Convert location string into latitude/longitude pair."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # toggle cache
    osmnx.settings.use_cache = cache

    # control flow
    if dry_run:
        # just get location
        result = f"{location}"

    else:
        # attempt to geocode location
        try:
            geocoded = osmnx.geocoder.geocode(location)
            if pretty_print:
                result = (
                    f"{'latitude:':<10}{geocoded[0]:>14.8f}"
                    "\n"
                    f"{'longitude:':<10}{geocoded[1]:>14.8f}"
                )

            else:
                result = f"{geocoded[0]} {geocoded[1]}"

        except osmnx._errors.InsufficientResponseError as e:
            sys.exit(e)

    # show
    print(result)


@main.command(
    "download",
    no_args_is_help=True,
    short_help="Download GIS data from various sources.",
)
@click.option(
    "-d",
    "--download-dir",
    type=click.Path(),
    default=NOMAD_CACHE_DIR,
    show_default=True,
    help="Path to GIS download directory.",
)
@click.argument("location", type=str)
@click.pass_context
def download(
    ctx: click.Context,
    download_dir: str,
    location: str,
) -> None:
    """Download GIS data from various sources for a given location."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # setting directory path/name
    osmnx.settings.cache_folder = download_dir
    osmnx.settings.cache_only_mode = True

    # download
    try:
        osmnx.graph_from_place(location)

    # succesfully cached
    except osmnx._errors.CacheOnlyInterruptError:
        # results
        print(f"Location {location} successfully downloaded to: {download_dir}.")

    # cannot be found
    except osmnx._errors.InsufficientResponseError:
        sys.exit(f"Location {location!r} could not be found.")


@main.group(
    "cache",
    no_args_is_help=True,
    short_help="Manage GIS data cache.",
)
@click.pass_context
def cache(ctx: click.Context) -> None:
    """Manage GIS data cache."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # do nothing
    pass


def get_cache_data(
    cache_dir: str = NOMAD_CACHE_DIR,
    filter_func: Callable[[Any], bool] = lambda x: len(x) != 0,
) -> Generator[Tuple[pathlib.Path, Dict[str, Any]], None, None]:
    """Get all GIS JSON data from files in cache directory."""
    # get pathlib obj of cache data dir
    cache_path_obj = pathlib.Path(cache_dir)

    # iterate through files
    for data_path in cache_path_obj.glob("**/*.json"):
        # open file
        with open(data_path, encoding="utf8") as data_file:
            # get JSON data
            json_data = json.load(data_file)

            # filter out
            if filter_func(json_data):
                # if list get inner dictionary
                json_dict = json_data[0] if isinstance(json_data, list) else json_data

                # generate dict of JSON data
                yield (data_path, json_dict)


@cache.command(
    "inspect",
    no_args_is_help=False,
    short_help="Inspect the contents of the GIS data cache directory.",
)
@click.pass_context
def inspect_cache(ctx: click.Context) -> None:
    """Inspect contents of GIS data cache directory."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # loop over data a filter it
    for data_path, data in get_cache_data():
        # create title/contents for inspection dump case
        title = f"{'file_path':<12} {data_path}\n"
        contents = ""

        # loop over key/value pairs
        for key, value in data.items():
            # check type is not a list
            if type(value) not in {dict, list}:
                # append key/value to contents
                contents += f"{key:<12} {value}\n"

        # one final newline
        print(title + contents)


@cache.command(
    "search",
    no_args_is_help=True,
    short_help="Search through JSON data in GIS data cache directory.",
)
@click.argument("query", type=str)
@click.pass_context
def search_cache(ctx: click.Context, query: str) -> None:
    """Search through JSON data in GIS data cache directory."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # iterate through files
    for data_path, data in get_cache_data():
        # create title/contents for inspection dump case
        title = f"{'file_path':<12} {data_path}\n"
        contents = ""

        # loop over key/value pairs
        for key, value in data.items():
            # check type is not a list
            if type(value) not in {dict, list}:
                # append key/value to contents
                contents += f"{key:<12} {value}\n"

        # check if search matches
        if re.search(query, contents, re.IGNORECASE):
            # found match
            print(title + contents)


@cache.command(
    "rm",
    no_args_is_help=False,
    short_help="Remove select cached data from cache directory.",
)
@click.option("-e", "--empty", is_flag=True, help="Toggle remove empty cache.")
@click.option("-f", "--force", is_flag=True, help="Toggle no prompt before deleting.")
@click.pass_context
def remove_cache(ctx: click.Context, empty: bool, force: bool) -> None:
    """Remove select cached data from cache directory."""
    # get dry_run and debug info if any
    dry_run, debug = sync_main_flags(ctx)

    # check if empty is toggled
    if not empty:
        scope = "all cached data"
        cache_gen = get_cache_data(filter_func=lambda x: True)

    else:
        scope = "only empty JSON cached data"
        cache_gen = get_cache_data()

    # control flow
    if not force:
        # safety check
        if click.confirm(f"Do you want to delete {scope}?", abort=True):
            # notify user
            print("Confirmed. Now deleting ...")

            # print out selected cache data
            for data_path, _ in cache_gen:
                # unlink/delete the file
                data_path.unlink()

                # notify
                print(f"Deleted: {data_path}")

    else:
        # no safety check
        print("Now deleting ...")

        # print out selected cache data
        for data_path, _ in cache_gen:
            # unlink/delete the file
            data_path.unlink()

            # notify
            print(f"Deleted: {data_path}")


if __name__ == "__main__":
    main(prog_name="nomad")  # pragma: no cover
