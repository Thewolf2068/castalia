import pytest
from castalia.db import connect, init_schema, seed_platforms

@pytest.fixture
def conn():
    c = connect(":memory:")
    init_schema(c)
    yield(c)
    c.close

def test_seed_inserts_platform():
    conn = connect(":memory:")
    conn = init_schema(conn)
    conn = seed_platforms(conn, {"platforms": {"psx": {"name": "Sony Playstation"}}})

    row = conn.execute("SELECT name FROM platform WHERE id = 'psx'").fetchone()
    print (row[0])
    assert row[0] == "Sony Playstation"

