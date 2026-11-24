from castalia import config
import sqlite3
from typing import TypedDict
from contextlib import closing

class GameEntry(TypedDict):
    igdb_id: int
    name: str
    platform_id: str

class PlatformEntry(TypedDict):
    platform_id: str
    name: str
    platform_igdb_id: str

def establish_connection() -> sqlite3.Connection:
    db_location =  config.get_db_location(config.get_castalia_dir())
    try:
        conn = sqlite3.connect(db_location)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as error:
        raise sqlite3.Error(f"Unable to connect to database: {error}")
        
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_matching_titles(title: str, exact: bool = False) -> list[GameEntry]:
    if exact:
        condition = "name = ?"
        param = title
    else:
        condition = "name LIKE ?"
        param = f"%{title.casefold()}%"

    output: list[GameEntry] = []
    with closing(establish_connection()) as conn:
        cur = conn.execute(
            f"""
            SELECT igdb_id, name, platform_id
            FROM game_platform
            INNER JOIN game ON game_platform.game_id = game.igdb_id
            WHERE {condition}
            """,
            (param,),
        )
        for row in cur.fetchall():
            entry: GameEntry = {
                "igdb_id": row["igdb_id"],
                "name": row["name"],
                "platform_id": row["platform_id"],
            }
            output.append(entry)
    return output


def get_matching_platforms(search: str, exact: bool = False) -> list[PlatformEntry]:
    if exact:
        condition = "id = ? or name = ?"
        param = search
    else:
        condition = "id LIKE ? or name LIKE ?"
        param = f"%{search.casefold()}%"

    output: list[PlatformEntry] = []
    with closing(establish_connection()) as conn:
        cur = conn.execute(f"""
                    SELECT id, name, igdb_platform_id
                    FROM platform
                    WHERE {condition}
                    """,
                    (param, param)
                    )

        for row in cur.fetchall():
            entry: PlatformEntry = {
                    "platform_id": row['id'],
                    "name": row['name'],
                    "platform_igdb_id": str(row['igdb_platform_id'])
                    }
            output.append(entry)


    return output
    
    

