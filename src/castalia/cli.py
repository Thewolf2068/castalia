from typing import Annotated
import typer
from pathlib import Path
from typing import Literal
from rich.table import Table
from rich.console import Console

from castalia import config
from castalia.handlers import query
from castalia.handlers import importer

app = typer.Typer()

@app.callback()
def main():
    config_dir = config.get_castalia_dir()
    output = config.ensure_castalia_dir(config_dir)
    if output:
        print(f"First Run Detected. Don't forget to add your keys to {Path(config_dir / "config.toml")}")

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
    importer.import_path(rom_location, platform, recursive, dry)

@app.command()
def search(
    qualifier: Annotated[
        Literal["game", "platform"],
        typer.Argument(help="Where to search")
    ],
    search_content: Annotated[
        str,
        typer.Argument(help="What to search for")
    ],
    exact: Annotated[
        bool,
        typer.Option("-e", "--exact", help="Search only searches for exact search_content")
    ] = False,
):
    table = Table()
    match qualifier:
        case "game":
            titles: list[query.GameEntry] = query.get_matching_titles(search_content, exact)
            table.add_column("IGDB ID", no_wrap=True, justify="center")
            table.add_column("Name", no_wrap=True)
            table.add_column("Platform ID", no_wrap=True, justify="center")

            for game in titles:
                table.add_row (str(game["igdb_id"]), game["name"], game["platform_id"])
        case "platform":
            platforms: list[query.PlatformEntry] = query.get_matching_platforms(search_content, exact)

            table.add_column("Platform ID", no_wrap=True, justify="center")
            table.add_column("Name", no_wrap=True)
            table.add_column("IGDB Platform ID", no_wrap=True, justify="center")

            for entry in platforms:
                table.add_row(entry["platform_id"], entry["name"], entry["platform_igdb_id"])

    console = Console()
    console.print(table)





if __name__ == "__main__":
    app()
