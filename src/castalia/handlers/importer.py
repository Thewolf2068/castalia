from pathlib import Path
import hashlib
import shutil
import tempfile
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
        try:
            stuff = directory.rglob("*")
        except OSError as err:
            raise OSError(f"Provided directory {directory} doesn't exist") from err
    else:
        try:
            stuff = directory.iterdir()
        except OSError as err:
            raise OSError(f"Provided directory {directory} doesn't exist") from err
    for file in stuff:
        if file.suffix in extensions:
            output.append(file.expanduser().resolve())
    return output





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
    config_directory = config.get_castalia_dir()
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
            verified_move(rom, moved_location)
        except IOError as err:
            raise IOError(f"[bold red]Failed to move rom to destination '{moved_location.parent.name}': {err}[/bold red]")
        
        try:
            add_game_to_db(db_location, selected_title, platform, moved_location)
        except sqlite3.Error as err:
            print(f"[bold red]something broke fuck you: {err}[/bold red]")
            try:
                verified_move (moved_location, rom)
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


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()

    with path.open("rb") as f:
        while chunk := f.read(1024 * 1024):
            digest.update(chunk)

    return digest.hexdigest()

def verified_move(src: Path, dst: Path):
    fd, temp_name = tempfile.mkstemp(dir=dst.parent, prefix=f".{dst.name}.", suffix=".tmp")
    os.close(fd)

    temp = Path(temp_name)

    try:
        shutil.copy2(src, temp)
        with temp.open("rb") as f:
            os.fsync(f.fileno())
        source_hash = sha256_file(src)
        destination_hash = sha256_file(temp)

        if source_hash != destination_hash:
            raise IOError("File verification failed: SHA-256 mismatch")
        
        os.replace(temp, dst)
        src.unlink()
    finally:
        if temp.exists():
            temp.unlink()


def main():
    rom_directory = Path("~/roms/psp/").expanduser().resolve()
    import_path(rom_directory, "psp", True)





if __name__ == "__main__":
    main()
