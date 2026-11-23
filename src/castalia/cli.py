from typing import Annotated
import typer
from castalia import *
from pathlib import Path

from castalia.manager import import_path

app = typer.Typer()

@app.callback()
def main():
    """CLI for Castalia."""

@app.command(name="import")
def import_command(
    input: Annotated[
        Path,
        typer.Argument(help="Can be either a single rom or a directory of roms")
    ],
    platform: Annotated[
        str,
        typer.Option("--platform", "-p", help="The Identifier of the platform (can be found in $CASTALIADIR/platforms.toml)")
    ],
    recursive: Annotated[
        bool,
        typer.Option("--recursive", "-r", help="Parses provided directory recursively")
    ] = False,
    dry: Annotated[
        bool,
        typer.Option("--dry-run", "-d", help="Simulates execution without changing anything permanently")
    ] = False,
):
    rom_location = input.expanduser().resolve()
    import_path(rom_location, platform, recursive, dry)


if __name__ == "__main__":
    app()
