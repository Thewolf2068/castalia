import pytest
import sqlite3
from pathlib import Path
from castalia.db import add_alt_name, add_rom_file, connect, init_schema, link_game_platform, seed_platforms, upsert_game

@pytest.fixture
def conn():
    c = connect(Path(":memory:"))
    init_schema(c)
    yield(c)
    c.close()

def test_seed_inserts_platform(conn: sqlite3.Connection):
    conn = seed_platforms(conn, {"platforms": {"psx": {"name": "Sony Playstation"}}})

    row = conn.execute("SELECT name FROM platform WHERE id = 'psx'").fetchone()
    print (row[0])
    assert row[0] == "Sony Playstation"

def test_upsert_game(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076800)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800

def test_upsert_game_updates_existing(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076800)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076801)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076801

def test_upsert_game_stores_fetched_at(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)
    row = conn.execute("SELECT fetched_at FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076801)
    row = conn.execute("SELECT fetched_at FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076801


def test_link_game_platform(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)
    seed_platforms(conn, {"platforms": {"psx": {"name": "Sony Playstation"}}})

    link_game_platform(conn, 393025, "psx")
    link_game_platform(conn, 393025, "psx")

    count = conn.execute("SELECT COUNT(*) FROM game_platform").fetchone()[0]
    assert count == 1
def test_link_requires_existing_platform(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)

    with pytest.raises(sqlite3.IntegrityError):
        link_game_platform(conn, 393025, "ps1")



def test_add_alt_titles(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII")
    add_alt_name(conn, 393025, "Final Fantasy VII")
    row = conn.execute("SELECT name FROM alt_name WHERE game_id = ?", (393025,)).fetchone()
    assert row[0] == "Final Fantasy VII"


def test_add_same_title_twice(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII")
    add_alt_name(conn, 393025, "Final Fantasy VII")
    add_alt_name(conn, 393025, "Final Fantasy VII")
    count = conn.execute("SELECT COUNT(*) FROM alt_name").fetchone()[0]
    assert count == 1


def test_update_alt_title_region(conn: sqlite3.Connection):
    upsert_game(conn, 393025, "Final Fantasy VII")
    add_alt_name(conn, 393025, "Final Fantasy VII")
    add_alt_name(conn, 393025, "Final Fantasy VII", region="Europe")
    row = conn.execute("SELECT region FROM alt_name WHERE game_id = ?" , (393025,)).fetchone()
    assert row[0] == "Europe"


def test_add_rom(conn: sqlite3.Connection):
    rom = Path(__file__).parent / "Shin Megami Tensei - Persona 3 Portable (Europe).iso"
    upsert_game(conn, 12345, "Persona 3 Portable")
    seed_platforms(conn, {"platforms": {"psp": {"name": "Sony Playstation Portable"}}})
    add_rom_file(conn, rom, "psp", game_id=12345)
    row = conn.execute("SELECT size FROM rom_file WHERE game_id = ?", (12345,)).fetchone()
    assert row[0] == 1321893888 # Manually extracted using du -b beforehand
