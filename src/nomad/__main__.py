"""Command-line interface."""
import sys
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

    # download
    try:
        response = osmnx._nominatim._download_nominatim_element(location)
        full_name = response[0]["display_name"]
    except IndexError:
        sys.exit(f"Location {location!r} could not be found.")

    # results
    print(f"Location {full_name!r} successfully downloaded to: {download_dir}.")


if __name__ == "__main__":
    main(prog_name="nomad")  # pragma: no cover
