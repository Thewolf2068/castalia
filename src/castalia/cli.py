from typing import Annotated

import typer
from castalia import *
from pathlib import Path

app = typer.Typer()

@app.callback()
def main():
    """CLI for Castalia."""

@app.command(name="import",)
def import_command(
        input: Annotated[Path, typer.Argument(help="Can be either a single rom or a directory of roms")],
        platform: Annotated[str, typer.Option(help="The abbreviation of the platform (can be found in platforms.toml)")]
        ):
    path = Path(input)
    path = path.expanduser().resolve() #The total path of the file to import
    print (path)

if __name__ == "__main__":
    app()
