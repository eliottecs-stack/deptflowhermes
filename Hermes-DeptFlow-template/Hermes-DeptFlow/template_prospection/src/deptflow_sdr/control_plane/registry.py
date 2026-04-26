from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

from deptflow_sdr.domain.models import utc_now_iso


def _new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:16]}"


class Registry:
    """SQLite source of truth for local multi-client control plane state."""

    def __init__(self, path: Path):
        self.path = path
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()

    @contextmanager
    def _connect(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.path)
        connection.row_factory = sqlite3.Row
        try:
            yield connection
            connection.commit()
        finally:
            connection.close()

    def _init_schema(self) -> None:
        with self._connect() as db:
            db.executescript(
                """
                create table if not exists clients (
                  id text primary key,
                  name text not null,
                  market text not null default 'France B2B',
                  created_at text not null
                );

                create table if not exists profiles (
                  id text primary key,
                  client_id text not null references clients(id),
                  slug text not null unique,
                  status text not null default 'draft',
                  daily_connection_limit integer not null default 0,
                  created_at text not null,
                  updated_at text not null
                );

                create table if not exists profile_releases (
                  id text primary key,
                  profile_id text not null references profiles(id),
                  template_version text not null,
                  config_snapshot text not null,
                  prompt_snapshot text not null,
                  created_at text not null
                );

                create table if not exists runs (
                  id text primary key,
                  profile_id text not null references profiles(id),
                  dry_run integer not null,
                  status text not null,
                  summary text not null,
                  created_at text not null
                );

                create table if not exists leads (
                  id text primary key,
                  profile_id text not null references profiles(id),
                  lead_key text not null,
                  full_name text not null default '',
                  linkedin_url text not null default '',
                  score_total integer not null default 0,
                  tier text not null default '',
                  status text not null default 'new',
                  message_body text,
                  created_at text not null,
                  updated_at text not null,
                  unique(profile_id, lead_key)
                );

                create table if not exists messages (
                  id text primary key,
                  profile_id text not null references profiles(id),
                  lead_key text not null,
                  message_type text not null,
                  body text not null,
                  status text not null default 'draft',
                  created_at text not null
                );

                create table if not exists quota_events (
                  id text primary key,
                  client_id text not null references clients(id),
                  event_type text not null,
                  used integer not null,
                  limit_value integer not null,
                  created_at text not null
                );

                create table if not exists audit_events (
                  id text primary key,
                  profile_id text,
                  event_type text not null,
                  payload text not null,
                  created_at text not null
                );

                create table if not exists crm_syncs (
                  id text primary key,
                  profile_id text not null references profiles(id),
                  target text not null,
                  status text not null,
                  rows_synced integer not null default 0,
                  error text not null default '',
                  created_at text not null
                );
                """
            )

    def create_client(self, name: str, market: str = "France B2B") -> str:
        client_id = _new_id("client")
        with self._connect() as db:
            db.execute(
                "insert into clients (id, name, market, created_at) values (?, ?, ?, ?)",
                (client_id, name.strip(), market.strip() or "France B2B", utc_now_iso()),
            )
        return client_id

    def get_client(self, client_id: str) -> dict[str, Any]:
        return self._get_by_id("clients", client_id)

    def create_profile(self, client_id: str, slug: str) -> str:
        profile_id = _new_id("profile")
        now = utc_now_iso()
        with self._connect() as db:
            db.execute(
                """
                insert into profiles (id, client_id, slug, created_at, updated_at)
                values (?, ?, ?, ?, ?)
                """,
                (profile_id, client_id, slug.strip(), now, now),
            )
        return profile_id

    def get_profile(self, profile_id: str) -> dict[str, Any]:
        return self._get_by_id("profiles", profile_id)

    def list_profiles(self) -> list[dict[str, Any]]:
        with self._connect() as db:
            rows = db.execute(
                """
                select profiles.*, clients.name as client_name, clients.market as market
                from profiles
                join clients on clients.id = profiles.client_id
                order by profiles.updated_at desc
                """
            ).fetchall()
        return [dict(row) for row in rows]

    def set_profile_limits(self, profile_id: str, daily_connection_limit: int) -> None:
        with self._connect() as db:
            db.execute(
                """
                update profiles
                set daily_connection_limit = ?, updated_at = ?
                where id = ?
                """,
                (int(daily_connection_limit), utc_now_iso(), profile_id),
            )

    def create_release(
        self,
        profile_id: str,
        template_version: str,
        config_snapshot: dict[str, Any],
        prompt_snapshot: dict[str, str],
    ) -> str:
        release_id = _new_id("release")
        with self._connect() as db:
            db.execute(
                """
                insert into profile_releases
                (id, profile_id, template_version, config_snapshot, prompt_snapshot, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (
                    release_id,
                    profile_id,
                    template_version,
                    json.dumps(config_snapshot, ensure_ascii=False),
                    json.dumps(prompt_snapshot, ensure_ascii=False),
                    utc_now_iso(),
                ),
            )
        return release_id

    def get_release(self, release_id: str) -> dict[str, Any]:
        row = self._get_by_id("profile_releases", release_id)
        row["config_snapshot"] = json.loads(row["config_snapshot"])
        row["prompt_snapshot"] = json.loads(row["prompt_snapshot"])
        return row

    def record_run(self, profile_id: str, dry_run: bool, status: str, summary: dict[str, Any]) -> str:
        run_id = _new_id("run")
        with self._connect() as db:
            db.execute(
                """
                insert into runs (id, profile_id, dry_run, status, summary, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (run_id, profile_id, int(dry_run), status, json.dumps(summary, ensure_ascii=False), utc_now_iso()),
            )
        return run_id

    def latest_successful_dry_run(self, profile_id: str) -> dict[str, Any] | None:
        with self._connect() as db:
            row = db.execute(
                """
                select * from runs
                where profile_id = ? and dry_run = 1 and status = 'completed'
                order by created_at desc
                limit 1
                """,
                (profile_id,),
            ).fetchone()
        if not row:
            return None
        data = dict(row)
        data["summary"] = json.loads(data["summary"])
        return data

    def upsert_lead(
        self,
        profile_id: str,
        lead_key: str,
        full_name: str,
        linkedin_url: str,
        score_total: int,
        tier: str,
        status: str,
        message_body: str | None = None,
    ) -> str:
        lead_id = _new_id("lead")
        now = utc_now_iso()
        with self._connect() as db:
            db.execute(
                """
                insert into leads
                (id, profile_id, lead_key, full_name, linkedin_url, score_total, tier, status, message_body, created_at, updated_at)
                values (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                on conflict(profile_id, lead_key) do update set
                  full_name = excluded.full_name,
                  linkedin_url = excluded.linkedin_url,
                  score_total = excluded.score_total,
                  tier = excluded.tier,
                  status = excluded.status,
                  message_body = excluded.message_body,
                  updated_at = excluded.updated_at
                """,
                (
                    lead_id,
                    profile_id,
                    lead_key,
                    full_name,
                    linkedin_url,
                    int(score_total),
                    tier,
                    status,
                    message_body,
                    now,
                    now,
                ),
            )
        return lead_id

    def approved_lead_count(self, profile_id: str) -> int:
        with self._connect() as db:
            row = db.execute(
                "select count(*) as value from leads where profile_id = ? and status in ('approved', 'connection_ready')",
                (profile_id,),
            ).fetchone()
        return int(row["value"])

    def list_leads(self, profile_id: str, status: str | None = None) -> list[dict[str, Any]]:
        query = "select * from leads where profile_id = ?"
        params: list[Any] = [profile_id]
        if status:
            query += " and status = ?"
            params.append(status)
        query += " order by score_total desc, updated_at desc"
        with self._connect() as db:
            rows = db.execute(query, params).fetchall()
        return [dict(row) for row in rows]

    def record_quota_event(self, client_id: str, event_type: str, used: int, limit: int) -> str:
        event_id = _new_id("quota")
        with self._connect() as db:
            db.execute(
                """
                insert into quota_events (id, client_id, event_type, used, limit_value, created_at)
                values (?, ?, ?, ?, ?, ?)
                """,
                (event_id, client_id, event_type, int(used), int(limit), utc_now_iso()),
            )
        return event_id

    def quota_usage(self, client_id: str, event_type: str) -> dict[str, int]:
        with self._connect() as db:
            row = db.execute(
                """
                select coalesce(sum(used), 0) as used, coalesce(max(limit_value), 0) as limit_value
                from quota_events
                where client_id = ? and event_type = ?
                """,
                (client_id, event_type),
            ).fetchone()
        return {"used": int(row["used"]), "limit": int(row["limit_value"])}

    def record_crm_sync(
        self,
        profile_id: str,
        target: str,
        status: str,
        rows_synced: int,
        error: str = "",
    ) -> str:
        sync_id = _new_id("crm")
        with self._connect() as db:
            db.execute(
                """
                insert into crm_syncs (id, profile_id, target, status, rows_synced, error, created_at)
                values (?, ?, ?, ?, ?, ?, ?)
                """,
                (sync_id, profile_id, target, status, rows_synced, error, utc_now_iso()),
            )
        return sync_id

    def _get_by_id(self, table: str, row_id: str) -> dict[str, Any]:
        with self._connect() as db:
            row = db.execute(f"select * from {table} where id = ?", (row_id,)).fetchone()
        if not row:
            raise KeyError(f"{table} row not found: {row_id}")
        return dict(row)
