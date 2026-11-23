from pathlib import Path
import shutil
from rich.console import Console
from castalia import config, db, library, parser, selector, platforms
from castalia.parser import SimilarityGames
from rich import print
from rich.markup import escape
import sqlite3
import os
from contextlib import closing

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





def db_entry(db_location: Path) -> sqlite3.Connection:
    db_exists = os.path.isfile(db_location)

    conn = db.connect(db_location)
    conn = db.init_schema(conn)
    if db_exists == False:
        conn = db.seed_platforms(conn, db.load_platforms())
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def add_game_to_db(db_location: Path, game: SimilarityGames,
                   platform: str, rom: Path):
    game_igdb_id = game["id"]
    game_name = game["name"]

    with closing(sqlite3.connect(db_location)) as conn:
        with conn:
            cur = conn.cursor()
            cur.execute("PRAGMA foreign_keys = ON;")
            db.upsert_game(conn, igdb_id=game_igdb_id, name=game_name)
            db.link_game_platform(conn, game_id=game_igdb_id, platform_id=platform)
            db.add_rom_file(conn, rom, platform_id=platform, game_id=game_igdb_id)

        




def import_path(path: Path, platform: str, recursive: bool = False, dry : bool = False):
    config_directory = config.find_castalia_dir()
    platforms_location = config_directory / "platforms.toml"
    platform_id = platforms.get_platform_id(platform, platforms_location)
    client_id, bearer_token = config.get_authentication_clean(config_directory)
    library_root = config.get_library_location(config_directory)
    db_location = config.get_db_location(config_directory)

    valid_extensions = platforms.get_system_extensions(platforms_location, platform)
    valid_roms = extract_valid_list_of_roms(path, valid_extensions, recursive)
    valid_roms.sort()
    platform_directory = library_root / platform
    final_name = ""
    filename = ""

    for rom in valid_roms:
        try:
            selected_title, filename = process_file(rom, platform_id, valid_extensions, client_id, bearer_token)
        except parser.IGDBFatalError as err:
            print(f"[bold red]{escape(str(err))}[/bold red]")
            break
        except parser.IGDBRequestError as err:
            print(f"[bold red]{escape(str(err))}. Skipping '{escape(rom.name)}'[/bold red]")
            continue
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


def import_file(moved_location: Path, rom: Path, db_location: Path, selected_title: SimilarityGames):
    library.create_directory_if_missing(moved_location.parent)
    if moved_location.exists():
        print(f"[bold red]File '{escape(str(moved_location))}' already exists. Skipping[/bold red]")
    else:
        #extrapolate the stuff because i am too prideful to pass them as arguments
        platform = moved_location.parent.name
        try:
            shutil.move(rom, moved_location)
        except OSError as err:
            print(f"[bold red]Failed to move rom to destination '{moved_location.parent.name}': {err}[/bold red]")
            return
        
        try:
            add_game_to_db(db_location, selected_title, platform, moved_location)
        except sqlite3.Error as err:
            print(f"[bold red]something broke fuck you: {err}[/bold red]")
            try:
                shutil.move (moved_location, rom)
            except OSError as err:
                print(f"[bold red]Could not move it back. The file is now at {escape(str(moved_location))}[/bold red]")
            return
        


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
