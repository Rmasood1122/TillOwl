"""Root conftest.py (installs to conftest.py at the repo root; G1-protected).

Fixtures every step's tests may use:

  pg_server      session  a throwaway PostgreSQL started by the test command itself:
                          initdb + pg_ctl in a temporary folder, listening on 127.0.0.1 only,
                          no Unix socket (design choice; works inside Claude Code's sandbox:
                          on Linux/WSL2 a sandboxed command's localhost is private to that
                          command tree, and on macOS it needs sandbox.network.allowLocalBinding).
  pg_template    session  database "tillowl_template" with migrations/*.sql applied in lexical
                          order, each file in its own transaction.
  fresh_db       function a new database copied from the template for one test; .dsn(role) gives a
                          libpq connection string for any role the migrations created.
  staging_schema function CI staging gates only: a schema ci_<run>_<attempt>_<step> in the staging
                          database from STAGING_DATABASE_URL, migrations applied, dropped afterwards.

Nothing here runs unless a test asks for the fixture, so the suite passes on a repo with no app
code. A missing PostgreSQL install fails the requesting test loudly; it never skips.
"""
from __future__ import annotations

import glob
import os
import re
import shutil
import socket
import subprocess
import tempfile
import uuid
from dataclasses import dataclass
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent
MIGRATIONS = ROOT / "migrations"
TEMPLATE_DB = "tillowl_template"
SUPERUSER = "postgres"


def _pg_bindir() -> Path:
    candidates: list[str] = []
    if os.environ.get("PG_BIN"):
        candidates.append(os.environ["PG_BIN"])
    if shutil.which("pg_config"):
        out = subprocess.run(["pg_config", "--bindir"], capture_output=True, text=True)
        if out.returncode == 0:
            candidates.append(out.stdout.strip())
    candidates += sorted(glob.glob("/usr/lib/postgresql/*/bin"), reverse=True)
    candidates += sorted(glob.glob("/opt/homebrew/opt/postgresql@*/bin"), reverse=True)
    candidates += sorted(glob.glob("/usr/local/opt/postgresql@*/bin"), reverse=True)
    if shutil.which("initdb"):
        candidates.append(str(Path(shutil.which("initdb")).parent))
    for cand in candidates:
        if (Path(cand) / "initdb").exists() and (Path(cand) / "pg_ctl").exists():
            return Path(cand)
    pytest.fail("PostgreSQL server binaries (initdb, pg_ctl) not found. Install PostgreSQL 16 "
                "(macOS: brew install postgresql@16; Ubuntu/WSL2: apt install postgresql) "
                "or set PG_BIN to the folder holding initdb.", pytrace=False)


def _free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def _connect(dsn: str):
    try:
        import psycopg  # imported lazily: the empty repo has no dependencies yet
    except ImportError:
        pytest.fail("psycopg is not installed; run the setup command in CLAUDE.md", pytrace=False)
    return psycopg.connect(dsn, autocommit=True)


def _migration_files() -> list[Path]:
    return sorted(MIGRATIONS.glob("*.sql")) if MIGRATIONS.is_dir() else []


def _apply_migrations(conn, search_path: str | None = None) -> None:
    for path in _migration_files():
        sql = path.read_text(encoding="utf-8")
        with conn.transaction():
            if search_path:
                conn.execute(f'SET LOCAL search_path TO "{search_path}"')
            conn.execute(sql)


@dataclass
class PgServer:
    host: str
    port: int

    def dsn(self, dbname: str = "postgres", role: str = SUPERUSER) -> str:
        return f"host={self.host} port={self.port} dbname={dbname} user={role}"


@dataclass
class FreshDb:
    server: PgServer
    name: str

    def dsn(self, role: str = SUPERUSER) -> str:
        return self.server.dsn(self.name, role)


@pytest.fixture(scope="session")
def pg_server():
    if hasattr(os, "geteuid") and os.geteuid() == 0:
        pytest.fail("initdb refuses to run as root; run the tests as a normal user", pytrace=False)
    bindir = _pg_bindir()
    workdir = Path(tempfile.mkdtemp(prefix="tillowl-pg-"))
    data = workdir / "data"
    port = _free_port()
    subprocess.run(
        [str(bindir / "initdb"), "-D", str(data), "-U", SUPERUSER, "-A", "trust", "-E", "UTF8",
         "--no-sync", "--no-instructions"],
        check=True, capture_output=True,
    )
    options = f"-h 127.0.0.1 -p {port} -k '' -F -c fsync=off -c full_page_writes=off"
    start = subprocess.run(
        [str(bindir / "pg_ctl"), "-D", str(data), "-o", options, "-l", str(workdir / "pg.log"),
         "-w", "-t", "60", "start"],
        capture_output=True, text=True,
    )
    if start.returncode != 0:
        log = (workdir / "pg.log").read_text(errors="replace")[-1500:] if (workdir / "pg.log").exists() else ""
        shutil.rmtree(workdir, ignore_errors=True)
        pytest.fail(f"PostgreSQL did not start on 127.0.0.1:{port}. On macOS inside Claude Code's "
                    f"sandbox, set sandbox.network.allowLocalBinding: true.\n{log}", pytrace=False)
    try:
        yield PgServer("127.0.0.1", port)
    finally:
        subprocess.run([str(bindir / "pg_ctl"), "-D", str(data), "-m", "immediate", "stop"],
                       capture_output=True)
        shutil.rmtree(workdir, ignore_errors=True)


@pytest.fixture(scope="session")
def pg_template(pg_server: PgServer) -> str:
    with _connect(pg_server.dsn()) as conn:
        conn.execute(f'CREATE DATABASE "{TEMPLATE_DB}"')
    with _connect(pg_server.dsn(TEMPLATE_DB)) as conn:
        _apply_migrations(conn)
    return TEMPLATE_DB


@pytest.fixture
def fresh_db(pg_server: PgServer, pg_template: str):
    name = f"t_{uuid.uuid4().hex[:12]}"
    with _connect(pg_server.dsn()) as conn:
        conn.execute(f'CREATE DATABASE "{name}" TEMPLATE "{pg_template}"')
    try:
        yield FreshDb(pg_server, name)
    finally:
        with _connect(pg_server.dsn()) as conn:
            conn.execute(f'DROP DATABASE IF EXISTS "{name}" WITH (FORCE)')


@dataclass
class StagingSchema:
    url: str
    schema: str

    def dsn(self) -> str:
        sep = "&" if "?" in self.url else "?"
        return f"{self.url}{sep}options=-csearch_path%3D{self.schema}"


@pytest.fixture
def staging_schema():
    url = os.environ.get("STAGING_DATABASE_URL")
    run = os.environ.get("TILLOWL_CI_RUN", "")
    if not url or not run:
        pytest.fail("staging_schema runs only in the CI 'staging' workflow (STAGING_DATABASE_URL and "
                    "TILLOWL_CI_RUN are set there). Local sessions never hold the staging URL (G4).",
                    pytrace=False)
    schema = "ci_" + re.sub(r"[^a-z0-9_]", "_", run.lower())[:50]
    with _connect(url) as conn:
        conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
        conn.execute(f'CREATE SCHEMA "{schema}"')
        _apply_migrations(conn, search_path=schema)
    try:
        yield StagingSchema(url, schema)
    finally:
        with _connect(url) as conn:
            conn.execute(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE')
