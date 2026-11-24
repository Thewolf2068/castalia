import json
import toml
import os
import time
import tomllib
from pathlib import Path
from typing import Any
from importlib import resources

from castalia.igdb_authenticator import get_bearer_token, verify_bearer_token

DEFAULT_FILES = ("config.toml", "platforms.toml")
ENV_VAR = "CASTALIADIR"
CONFIG_FILE = "config.toml"
KEYS_FILE = "keys.json"
EXPIRY_MARGIN = 60  # refresh the token this many seconds before it expires

def ensure_castalia_dir(directory: Path) -> list[Path]:
    directory.mkdir(parents=True, exist_ok=True)
    defaults = resources.files("castalia") / "data"
    created: list[Path] = []
    for name in DEFAULT_FILES:
        target = directory / name
        try:
            with open(target, "xb") as f:  # "x" fails if the file already exists
                f.write((defaults / name).read_bytes())
        except FileExistsError:
            continue
        created.append(target)
    return created

def get_castalia_dir() -> Path:
    env = os.environ.get(ENV_VAR)
    if env:
        directory = Path(env).expanduser()
        if not directory.is_dir():
            raise FileNotFoundError(
                f"{ENV_VAR} points to a directory that does not exist: {directory}"
            )
        return directory

    return Path.home() / ".config" / "castalia"


def load_config(directory: Path) -> dict[str, Any]:
    config_path = directory / CONFIG_FILE
    if not config_path.is_file():
        raise FileNotFoundError(f"Could not find configuration file: {config_path}")

    with open(config_path, "rb") as f:
        return tomllib.load(f)


def load_keys(directory: Path) -> dict[str, Any]:
    try:
        with open(directory / KEYS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def save_keys(directory: Path, keys: dict[str, Any]) -> None:
    """Write keys.json readable only by the owner, via a temp file so a crash
    cannot leave a half-written file behind."""
    keys_path = directory / KEYS_FILE
    tmp_path = directory / (KEYS_FILE + ".tmp")

    fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, 0o600)
    with os.fdopen(fd, "w", encoding="utf-8") as f:
        json.dump(keys, f)
    try:
        os.replace(tmp_path, keys_path)
    except OSError as err:
        raise OSError(f"Issue updating oauth keys: {err}")


def get_token(directory: Path, config: dict[str, Any]) -> str:
    """Return a valid bearer token, fetching a new one if needed."""
    keys = load_keys(directory)
    expiration = keys.get("expiration")

    if (
        keys.get("bearer_token") is None
        or expiration is None
        or expiration <= time.time() + EXPIRY_MARGIN
    ):
        igdb = config["igdb"]
        token, expiration = get_bearer_token(igdb["client_id"], igdb["client_secret"])
        keys = {"bearer_token": token, "expiration": expiration}
        save_keys(directory, keys)

    return keys["bearer_token"]

def get_db_location(config_directory: Path) -> Path:
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)
    try:
        return Path(config_file['database']['path']).expanduser().resolve()
    except KeyError:
        print(f"[yellow]no database location set in {config_directory / "config.toml"}, used/created {config_directory / "sql.db"} as fallback[/yellow]")
        return config_directory / "sql.db"

def get_library_location(config_directory: Path) -> Path:
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)

    try:
        return Path(config_file['library']['path']).expanduser().resolve()
    except KeyError:
        return Path("~/Roms").expanduser().resolve()


def get_authentication_clean(config_directory: Path) -> tuple[str, str]:
    output: tuple[str, str] = "", ""
    with open(config_directory / "config.toml", 'r') as f:
        config_file = toml.load(f)
    try:
        client_id = config_file['igdb']['client_id']
    except KeyError as e:
        raise ValueError(f"Missing required Client-ID: {e}. Did you read the Docs?") from e


    config_file = load_config(config_directory)
    bearer_token = get_token(config_directory, config_file)

    output = client_id, bearer_token
    return output

def main() -> None:
    config = load_config(get_castalia_dir())
    token = get_token(get_castalia_dir(), config)
    verify_bearer_token(config["igdb"]["client_id"], token)


if __name__ == "__main__":
    main()
