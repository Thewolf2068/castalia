import sqlite3
import tomllib
from pathlib import Path
from typing import Any
import os


PLATFORMS_TOML = Path(__file__).parent / "data" / "platforms.toml"

def connect(path:str) -> sqlite3.Connection:
    conn = sqlite3.connect(path)
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return conn

def init_schema(conn: sqlite3.Connection) -> sqlite3.Connection:
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS game(
            igdb_id INTEGER PRIMARY KEY, 
            name TEXT NOT NULL, 
            summary TEXT, 
            first_release_date INTEGER,
            fetched_at INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS platform(
            id TEXT PRIMARY KEY NOT NULL, 
            name TEXT NOT NULL, 
            igdb_platform_id INTEGER
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS game_platform(
            game_id INTEGER NOT NULL REFERENCES game(igdb_id) ON DELETE CASCADE,
            platform_id TEXT NOT NULL REFERENCES platform(id) ON DELETE CASCADE,
            PRIMARY KEY(game_id, platform_id)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS alt_name(
            id INTEGER PRIMARY KEY,
            game_id INTEGER NOT NULL REFERENCES game(igdb_id) ON DELETE CASCADE, 
            name TEXT NOT NULL, 
            normalized_name TEXT, 
            comment TEXT,
            region TEXT,
            UNIQUE(game_id, name)
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS rom_file(
            id INTEGER PRIMARY KEY,
            file_name TEXT NOT NULL,
            game_id INTEGER REFERENCES game(igdb_id) ON DELETE CASCADE,
            platform_id TEXT NOT NULL REFERENCES platform(id) ON DELETE CASCADE,
            size INTEGER,
            UNIQUE(file_name, platform_id)
        )
    """)
    conn.commit()
    return conn

def seed_platforms(conn: sqlite3.Connection, data: dict[str, Any]) -> sqlite3.Connection:
    cur = conn.cursor()
    for platform_id, info in data["platforms"].items():
        cur.execute( 
                    """
                    INSERT INTO platform(id, name, igdb_platform_id) VALUES (?, ?, ?)
                    ON CONFLICT (id) DO UPDATE SET
                        name = excluded.name,
                        igdb_platform_id = excluded.igdb_platform_id;
                    """,
                    (platform_id, info["name"], info.get("igdb"))
                    )
    conn.commit()
    return conn

def load_platforms(path: Path = PLATFORMS_TOML) -> dict[str, Any]:
    with open(path, "rb") as f:
        return tomllib.load(f)

def upsert_game(conn: sqlite3.Connection, igdb_id: int, name: str, fetched_at: int | None = None,
                first_release_date: int | None = None, summary: str | None = None) -> None:
    cur = conn.cursor()
    cur.execute(
            """
            INSERT INTO game(igdb_id, name, summary, first_release_date, fetched_at) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (igdb_id) DO UPDATE SET
                name = excluded.name,
                summary = excluded.summary,
                first_release_date = excluded.first_release_date,
                fetched_at = excluded.fetched_at;
            """,
            (igdb_id, name, summary, first_release_date, fetched_at)
            )

def link_game_platform(conn: sqlite3.Connection, game_id: int, platform_id: str) -> None:
    cur = conn.cursor()
    cur.execute(
            """
            INSERT INTO game_platform(game_id, platform_id) VALUES (?, ?)
            ON CONFLICT (game_id, platform_id) DO NOTHING
            """,
            (game_id, platform_id)
            )

def add_alt_name(conn: sqlite3.Connection, game_id: int, name: str, 
                 comment: str | None = None, region: str | None = None) -> None:
    cur = conn.cursor()
    cur.execute(
            """
            INSERT INTO alt_name(game_id, name, normalized_name, comment, region) VALUES (?, ?, ?, ?, ?)
            ON CONFLICT (game_id, name) DO UPDATE SET
                comment = excluded.comment,
                region = excluded.region;

            """,
            (game_id, name, name.casefold(), comment, region)
            )

def add_rom_file(conn: sqlite3.Connection, path: Path, platform_id: str, game_id: int | None = None) -> None:
    size = os.path.getsize(path) # This will be so fucking complicated for multi disc roms omgbruh
    filename = path.name
    cur = conn.cursor()
    cur.execute(

            """
            INSERT INTO rom_file(file_name, game_id, platform_id, size) VALUES (?, ?, ?, ?)
            ON CONFLICT (file_name, platform_id) DO UPDATE SET
                game_id = excluded.game_id,
                size = excluded.size;

            """,
            (filename, game_id, platform_id, size)
            )


def main():
    conn = connect(r"sql.db")
    conn = init_schema(conn)
    conn = seed_platforms(conn, load_platforms())
    cur = conn.cursor()
    for row in cur.execute("SELECT * FROM platform "):
        print(row)
    conn.close()



if __name__ == "__main__":
    main()
