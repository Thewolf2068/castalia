import pytest
import time
import sqlite3
from castalia.db import connect, init_schema, link_game_platform, seed_platforms, upsert_game

@pytest.fixture
def conn():
    c = connect(":memory:")
    init_schema(c)
    yield(c)
    c.close()

def test_seed_inserts_platform(conn):
    conn = seed_platforms(conn, {"platforms": {"psx": {"name": "Sony Playstation"}}})

    row = conn.execute("SELECT name FROM platform WHERE id = 'psx'").fetchone()
    print (row[0])
    assert row[0] == "Sony Playstation"

def test_upsert_game(conn):
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076800)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800

def test_upsert_game_updates_existing(conn):
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076800)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800
    upsert_game(conn, 393025, "Final Fantasy VII", first_release_date=852076801)
    row = conn.execute("SELECT first_release_date FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076801

def test_upsert_game_stores_fetched_at(conn):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)
    row = conn.execute("SELECT fetched_at FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076800
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076801)
    row = conn.execute("SELECT fetched_at FROM game WHERE igdb_id = ?", (393025,)).fetchone()
    assert row[0] == 852076801


def test_link_game_platform(conn):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)
    seed_platforms(conn, {"platforms": {"psx": {"name": "Sony Playstation"}}})

    link_game_platform(conn, 393025, "psx")
    link_game_platform(conn, 393025, "psx")

    count = conn.execute("SELECT COUNT(*) FROM game_platform").fetchone()[0]
    assert count == 1
def test_link_requires_existing_platform(conn):
    upsert_game(conn, 393025, "Final Fantasy VII", fetched_at=852076800)

    with pytest.raises(sqlite3.IntegrityError):
        link_game_platform(conn, 393025, "ps1")
