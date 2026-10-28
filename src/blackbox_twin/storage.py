"""Append-only event evidence committed before the next interaction."""

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4


def utc_now():
    return datetime.now(timezone.utc).isoformat()


class Recorder:
    def __init__(self, path: Path, metadata: dict):
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        version = self.db.execute("PRAGMA user_version").fetchone()[0]
        if version not in (0, 1):
            raise ValueError(f"Unsupported evidence DB version: {version}")
        self.db.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                id TEXT PRIMARY KEY, started TEXT, metadata TEXT, status TEXT);
            CREATE TABLE IF NOT EXISTS experiments (
                id TEXT PRIMARY KEY, run_id TEXT, phase TEXT, started TEXT,
                status TEXT, actions TEXT);
            CREATE TABLE IF NOT EXISTS events (
                id INTEGER PRIMARY KEY, experiment_id TEXT, kind TEXT,
                request TEXT, response TEXT, elapsed REAL, status TEXT);
            CREATE INDEX IF NOT EXISTS event_experiment ON events(experiment_id);
            CREATE TABLE IF NOT EXISTS artifacts (
                run_id TEXT, kind TEXT, content TEXT);
            PRAGMA user_version=1;
        """)
        self.run_id = str(uuid4())
        self.db.execute(
            "INSERT INTO runs VALUES (?,?,?,?)",
            (self.run_id, utc_now(), json.dumps(metadata), "running"),
        )
        self.db.commit()

    def begin(self, phase):
        exp = str(uuid4())
        self.db.execute(
            "INSERT INTO experiments VALUES (?,?,?,?,?,?)",
            (exp, self.run_id, phase, utc_now(), "running", "[]"),
        )
        self.db.commit()
        return exp

    def event(self, exp, kind, request, response, elapsed, status):
        self.db.execute(
            "INSERT INTO events(experiment_id,kind,request,response,elapsed,status) "
            "VALUES (?,?,?,?,?,?)",
            (exp, kind, json.dumps(request), json.dumps(response), elapsed, status),
        )
        self.db.commit()

    def finish(self, exp, actions, status):
        self.db.execute(
            "UPDATE experiments SET status=?,actions=? WHERE id=?",
            (status, json.dumps(actions), exp),
        )
        self.db.commit()

    def artifact(self, kind, content):
        self.db.execute(
            "INSERT INTO artifacts VALUES (?,?,?)", (self.run_id, kind, json.dumps(content))
        )
        self.db.commit()

    def close(self, status):
        self.db.execute("UPDATE runs SET status=? WHERE id=?", (status, self.run_id))
        self.db.commit()
        self.db.close()


def export_database(path: Path, destination: Path):
    db = sqlite3.connect(f"file:{path.as_posix()}?mode=ro", uri=True)
    db.row_factory = sqlite3.Row
    with destination.open("w", encoding="utf-8") as out:
        for table in ("runs", "experiments", "events", "artifacts"):
            for row in db.execute(f"SELECT * FROM {table}"):
                out.write(json.dumps({"table": table, **dict(row)}) + "\n")
    db.close()
