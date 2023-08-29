"""Command-line interface."""
import click


@click.command()
@click.version_option()
def main() -> None:
    """Nomad."""


if __name__ == "__main__":
    main(prog_name="nomad")  # pragma: no cover
