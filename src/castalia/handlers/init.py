from pathlib import Path
from importlib import resources
import sqlite3
from urllib3.exceptions import HTTPError
from castalia import config, igdb_authenticator, db
import toml
from rich.prompt import Prompt
from rich import print

DEFAULTS_DIR = resources.files("castalia") / "data" / "defaults"

def get_missing_files(config_dir: Path) -> list[str]:

    files_in_config = {
        f.name for f in config_dir.iterdir() if f.is_file()
    }

    files_in_defaults = {
        f.name for f in DEFAULTS_DIR.iterdir() if f.is_file()
    }

    return list(files_in_defaults - files_in_config)

def ensure_castalia_dir_exists(config_dir: Path):
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
    except OSError as err:
        raise OSError(f"Unable to create missing config directory at {config_dir}") from err

def fill_missing_files(missing_files: list[str], config_dir: Path):
    for file in missing_files:
        missing_file_in_config = Path(config_dir / file)
        try:
            with missing_file_in_config.open("xb") as f:
                f.write((DEFAULTS_DIR / file).read_bytes())
        except OSError as err:
            raise OSError(
                f"Unable to write {file} to {config_dir}"
            ) from err


def ensure_database_exists(config_dir: Path):
    config_file = config_dir / "config.toml"
    with open(config_file, "r") as f:
        config_file = toml.load(f)
    databaseLocation = Path(config_file['database']['path']).expanduser().resolve()
    try:
        conn = db.connect(databaseLocation)
        conn = db.init_schema(conn)
        conn = db.seed_platforms(conn, db.load_platforms())
        conn.close()
    except sqlite3.Error as err:
        raise sqlite3.Error(f"Failed to initialize database at {databaseLocation}: {err}") from err


# Interactive method tat copies missing config file from  defaults, then adds the required keys using typer
def init_config(config_dir: Path):
    target_config = config_dir / "config.toml"
    with open(target_config, "r") as f:
        config_file =  toml.load(f)
    
    # Link will be changed to docs when i have those
    print("Visit [link=https://google.com]the docs[/link] for help")

    client_id = Prompt.ask("[yellow]Enter your Twitch Applications Client ID[/yellow]")
    client_secret= Prompt.ask("[yellow]Enter your Twitch Applications Client Secret[/yellow]")

    config_file['igdb']['client_id'] = client_id
    config_file['igdb']['client_secret'] = client_secret


    igdb = config_file["igdb"]
    try:
        token, expiration = igdb_authenticator.get_bearer_token(igdb["client_id"], igdb["client_secret"])
    except HTTPError as err:
        raise HTTPError(f"Bearer Token initialization failed. Verify Credentials and re-run castalia init\n{err}") from err
    keys = {"bearer_token": token, "expiration": expiration}
    config.save_keys(config_dir, keys)

    with open(target_config, "w") as f:
        toml.dump(config_file, f)






def ensure_full_config():
    config_dir = config.get_castalia_dir().expanduser().resolve()
    ensure_castalia_dir_exists(config_dir)
    missing_files = get_missing_files(config_dir)
    fill_missing_files(missing_files, config_dir)
    init_config(config_dir)
    ensure_database_exists(config_dir)

