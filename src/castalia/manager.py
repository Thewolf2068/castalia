from pathlib import Path
import shutil
import toml
from rich.console import Console
from castalia import config, db, library, parser, selector
from castalia.parser import SimilarityGames
from rich import print
from rich.markup import escape
import sqlite3
import os

console = Console()
def extract_valid_list_of_roms(directory: Path, extensions: list[str], recursive: bool = False) -> list[Path]:
    output: list[Path] = []
    if recursive:
        stuff = directory.rglob("*")
    else:
        stuff = directory.iterdir()
    for file in stuff:
        if file.suffix in extensions:
            output.append(file.expanduser().resolve())
    return output

def get_system_extensions(platforms_location: Path, platform: str) -> list[str]:
    output: list[str] = []
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)
    for extensions in platforms["platforms"][platform]["extensions"]:
        output.append(extensions)
    return output

def get_platform_id(platform: str, platforms_location: Path) -> int:
    with open(platforms_location, 'r') as f:
        platforms = toml.load(f)

    if platforms["platforms"][platform]["igdb"] is not None:
        return platforms["platforms"][platform]["igdb"]
    return 0

def get_authentication_stuff(config_directory: Path) -> tuple[str, str]:
    output: tuple[str, str] = "", ""
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)

    client_id = config_file['igdb']['client_id']

    config_file= config.load_config(config_directory)
    bearer_token = config.get_token(config_directory, config_file)

    output = client_id, bearer_token
    return output

def get_library_location(config_directory: Path) -> Path:
    library = Path("~/Roms").expanduser().resolve()
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)

    library = Path(config_file['library']['path']).expanduser().resolve()
    return library

def db_entry(db_location: Path) -> sqlite3.Connection:
    db_exists = os.path.isfile(db_location)

    conn = db.connect(db_location)
    conn = db.init_schema(conn)
    if db_exists == False:
        conn = db.seed_platforms(conn, db.load_platforms())
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def add_game_to_db(db_location: Path, game: SimilarityGames, extension: str,
                   platform: str, rom: Path):
    conn = db_entry(db_location)
    game_igdb_id = game["id"]
    game_name = game["name"] + extension

    db.upsert_game(conn, igdb_id=game_igdb_id, name=game_name)
    db.link_game_platform(conn, game_id=game_igdb_id, platform_id=platform)
    db.add_rom_file(conn, rom, platform_id=platform, extension=extension, game_id=game_igdb_id,)
    conn.commit()
    conn.close()


def import_path(path: Path, platform: str, recursive: bool = False, dry : bool = False):
    config_directory = config.find_castalia_dir()
    platforms_location = config_directory / "platforms.toml"
    platform_id = get_platform_id(platform, platforms_location)
    client_id, bearer_token = get_authentication_stuff(config_directory)
    library_root = get_library_location(config_directory)
    db_location = config_directory / "sql.db"

    valid_extensions = get_system_extensions(platforms_location, platform)
    valid_roms = extract_valid_list_of_roms(path, valid_extensions, recursive)
    valid_roms.sort()
    platform_directory = library_root / platform
    final_name = ""

    for rom in valid_roms:
        selected_title, filename = process_file(rom, platform_id, valid_extensions, client_id, bearer_token)
        extension = Path(filename).suffix
        if selected_title:
            final_name = selected_title["name"] + extension
        moved_location = platform_directory / final_name
        if dry == False:
            if selected_title:
                import_file(moved_location, rom, db_location, selected_title)
            else:
                print(f"[bold red]No Matches found for '{escape(str(rom))}'. Skipped[/bold red]")
        elif selected_title:
            print(f"{escape(str(rom))} would have been moved to {escape(str(moved_location))}")
        else:
            print(f"[bold red]No Matches found for '{escape(str(rom))}'. Would have been Skipped[/bold red]")
            # Explain that no resultst were found or something idk you figure it out asswipe


def import_file(moved_location: Path, rom: Path, db_location: Path, selected_title: SimilarityGames):
    library.create_directory_if_missing(moved_location.parent)
    if moved_location.exists():
        print(f"[bold red]File '{escape(str(moved_location))}' already exists. Skipping[/bold red]")
    else:
        #extrapolate the stuff because i am too prideful to pass them as arguments
        platform = moved_location.parent.name

        add_game_to_db(db_location, selected_title, moved_location.suffix, platform, rom)
        shutil.move(rom, moved_location)



def process_file(directory: Path, platform_id: int,
                 valid_extensions: list[str], client_id: str, bearer_token: str):
    file = directory.name

    with console.status(f"[bold cyan]Searching IGDB for [white]{escape(file)}[/white]...", spinner="dots"):
        search_results = parser.search_game(file, valid_extensions, platform_id, client_id, bearer_token)
    diffed_titles = parser.compare_titles(file, valid_extensions, search_results)
    if diffed_titles:
        selected_title = selector.list_options(diffed_titles, str(file))
    else:
        selected_title = None


    return selected_title, file



def main():
    rom_directory = Path("~/roms/psp/").expanduser().resolve()
    import_path(rom_directory, "psp", True)





if __name__ == "__main__":
    main()
