from castalia import config
import sqlite3
from typing import TypedDict

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
    except sqlite3.Error as error:
        raise sqlite3.Error(f"Unable to connect to database: {error}")
        
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys = ON;")
    return conn


def get_matching_titles(title: str, exact: bool = False) -> list[GameEntry]:
    conn = establish_connection()
    output: list[GameEntry] = []
    cur = conn.cursor()
    if exact:
        query = "where name = "
    else:
        query = "where name like "
        title = f"%{title.casefold()}%"
    cur.execute(f"""
                SELECT igdb_id, name, platform_id
                FROM game_platform 
                inner join game on game_platform.game_id = game.igdb_id
                {query} "?"
                """,
                (title)
                )
    for row in cur.fetchall():
        entry: GameEntry = {
                "igdb_id": row['igdb_id'],
                "name": row['name'],
                "platform_id": row['platform_id']
                }
        output.append(entry)
    return output


def get_matching_platforms(search: str, exact: bool = False) -> list[PlatformEntry]:
    conn = establish_connection()
    output: list[PlatformEntry] = []
    cur = conn.cursor()
    if exact:
        cur.execute("""
                    SELECT id, name, igdb_platform_id
                    FROM platform
                    where id = "?" or name = "?"
                    """,
                    (search, search)
                    )

    else:
        cur.execute("""
                    SELECT id, name, igdb_platform_id
                    FROM platform
                    where id like '%?%' or name like '%?%'
                    """,
                    (search, search)
                    )
    for row in cur.fetchall():
        entry: PlatformEntry = {
                "platform_id": row['id'],
                "name": row['name'],
                "platform_igdb_id": row['igdb_platform_id']
                }
        output.append(entry)


    return output
    
    

