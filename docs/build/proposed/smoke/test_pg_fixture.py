"""G7-c smoke test: the root conftest.py starts PostgreSQL inside a sandboxed Claude session.

Not installed anywhere; run in place after the governance install:
  .venv/bin/pip install -q 'psycopg[binary]==3.*'
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 .venv/bin/python -m pytest -c pytest.ini --rootdir=. \
      docs/build/proposed/smoke/test_pg_fixture.py
Expect: 1 passed.
"""


def test_fresh_db_answers_on_localhost(fresh_db):
    import psycopg

    with psycopg.connect(fresh_db.dsn(), autocommit=True) as conn:
        assert conn.execute("SELECT 1").fetchone()[0] == 1
        assert conn.execute("SHOW listen_addresses").fetchone()[0] == "127.0.0.1"
