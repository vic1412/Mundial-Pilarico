import hashlib
import sqlite3
import uuid
import streamlit as st
from datetime import datetime, timedelta
from pathlib import Path

# ---------------------------------------------------------------------------
# Backend selection: Supabase if credentials present, else SQLite fallback
# ---------------------------------------------------------------------------

def _use_supabase() -> bool:
    try:
        url = st.secrets.get("SUPABASE_URL", "")
        key = st.secrets.get("SUPABASE_KEY", "")
        return bool(url and key)
    except Exception:
        return False


@st.cache_resource
def _db():
    from supabase import create_client
    from urllib.parse import urlparse
    raw = st.secrets["SUPABASE_URL"].strip()
    parsed = urlparse(raw)
    # Keep only scheme + host — drop any path/query that breaks the SDK
    url = f"{parsed.scheme}://{parsed.netloc}"
    return create_client(url, st.secrets["SUPABASE_KEY"])


def _sb(fn):
    """Run a Supabase lambda and surface actionable errors instead of crashing."""
    try:
        return fn()
    except Exception as e:
        msg = str(e)
        if "does not exist" in msg:
            hint = "Las tablas no existen. Ejecuta **setup_supabase.sql** en el SQL Editor de Supabase."
        elif "row-level security" in msg or "permission denied" in msg or "violates" in msg:
            hint = "RLS activo. Ejecuta en Supabase SQL Editor: `ALTER TABLE users DISABLE ROW LEVEL SECURITY; ALTER TABLE predictions DISABLE ROW LEVEL SECURITY; ALTER TABLE match_results DISABLE ROW LEVEL SECURITY;`"
        elif "Invalid API key" in msg or "401" in msg:
            hint = "API key inválida. Verifica `SUPABASE_KEY` en los secrets de Streamlit Cloud."
        elif "connect" in msg.lower() or "timeout" in msg.lower():
            hint = "No se puede conectar a Supabase. Verifica `SUPABASE_URL`."
        else:
            hint = f"`{msg}`"
        st.error(f"⚠️ **Error Supabase:** {hint}")
        st.stop()


# ── SQLite helpers ──────────────────────────────────────────────────────────

_DB_PATH = Path(__file__).parent / "mundial2026.db"


def _conn():
    conn = sqlite3.connect(str(_DB_PATH), check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


def init_db():
    if _use_supabase():
        _sb(lambda: _db().table("users").select("id").limit(1).execute())
        return
    with _conn() as c:
        c.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS predictions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                match_id TEXT NOT NULL,
                home_goals INTEGER NOT NULL DEFAULT 0,
                away_goals INTEGER NOT NULL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(user_id, match_id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
            CREATE TABLE IF NOT EXISTS match_results (
                match_id TEXT PRIMARY KEY,
                home_score INTEGER NOT NULL,
                away_score INTEGER NOT NULL,
                status TEXT NOT NULL DEFAULT 'FT',
                source TEXT NOT NULL DEFAULT 'manual',
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );
            CREATE TABLE IF NOT EXISTS sessions (
                token TEXT PRIMARY KEY,
                user_id INTEGER NOT NULL,
                expires_at TIMESTAMP NOT NULL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            );
        """)
        # Migration: add source column if upgrading from older schema
        try:
            c.execute("ALTER TABLE match_results ADD COLUMN source TEXT NOT NULL DEFAULT 'manual'")
        except Exception:
            pass


# ── Users ──────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> tuple[bool, str | None]:
    username = username.strip()
    if _use_supabase():
        db = _db()
        existing = _sb(lambda: db.table("users").select("id").eq("username", username).execute())
        if existing.data:
            return False, "Ese usuario ya existe."
        _sb(lambda: db.table("users").insert(
            {"username": username, "password_hash": _hash(password)}).execute())
        return True, None
    try:
        with _conn() as c:
            c.execute("INSERT INTO users (username, password_hash) VALUES (?, ?)",
                      (username, _hash(password)))
        return True, None
    except sqlite3.IntegrityError:
        return False, "Ese usuario ya existe."


def authenticate(username: str, password: str) -> dict | None:
    username = username.strip()
    if _use_supabase():
        db = _db()
        res = _sb(lambda: db.table("users").select("id,username")
                  .eq("username", username).eq("password_hash", _hash(password)).execute())
        return res.data[0] if res.data else None
    with _conn() as c:
        row = c.execute(
            "SELECT id, username FROM users WHERE username=? AND password_hash=?",
            (username, _hash(password))).fetchone()
    return dict(row) if row else None


def get_user_by_username(username: str) -> dict | None:
    if _use_supabase():
        db = _db()
        res = _sb(lambda: db.table("users").select("id,username").eq("username", username).execute())
        return res.data[0] if res.data else None
    with _conn() as c:
        row = c.execute("SELECT id, username FROM users WHERE username=?", (username,)).fetchone()
    return dict(row) if row else None


def get_users() -> list:
    if _use_supabase():
        db = _db()
        return _sb(lambda: db.table("users").select("id,username,created_at").order("created_at").execute()).data
    with _conn() as c:
        rows = c.execute("SELECT id, username, created_at FROM users ORDER BY created_at").fetchall()
    return [dict(r) for r in rows]


def delete_user(user_id: int):
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("predictions").delete().eq("user_id", user_id).execute())
        _sb(lambda: db.table("users").delete().eq("id", user_id).execute())
        return
    with _conn() as c:
        c.execute("DELETE FROM predictions WHERE user_id=?", (user_id,))
        c.execute("DELETE FROM users WHERE id=?", (user_id,))


# ── Predictions ────────────────────────────────────────────────────────────

def save_prediction(user_id: int, match_id: str, home: int, away: int):
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("predictions").upsert(
            {"user_id": user_id, "match_id": match_id, "home_goals": home, "away_goals": away},
            on_conflict="user_id,match_id").execute())
        return
    with _conn() as c:
        c.execute("""
            INSERT INTO predictions (user_id, match_id, home_goals, away_goals, updated_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(user_id, match_id) DO UPDATE SET
                home_goals=excluded.home_goals,
                away_goals=excluded.away_goals,
                updated_at=excluded.updated_at
        """, (user_id, match_id, home, away, datetime.now().isoformat()))


def get_predictions(user_id: int) -> dict:
    if _use_supabase():
        db = _db()
        res = _sb(lambda: db.table("predictions").select("match_id,home_goals,away_goals")
                  .eq("user_id", user_id).execute())
        return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in res.data}
    with _conn() as c:
        rows = c.execute(
            "SELECT match_id, home_goals, away_goals FROM predictions WHERE user_id=?",
            (user_id,)).fetchall()
    return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in rows}


def get_all_predictions() -> list:
    if _use_supabase():
        db = _db()
        preds = _sb(lambda: db.table("predictions")
                    .select("user_id,match_id,home_goals,away_goals").execute()).data
        users_map = {u["id"]: u["username"] for u in get_users()}
        for p in preds:
            p["username"] = users_map.get(p["user_id"], "?")
        return preds
    with _conn() as c:
        rows = c.execute("""
            SELECT p.user_id, p.match_id, p.home_goals, p.away_goals, u.username
            FROM predictions p JOIN users u ON p.user_id=u.id
        """).fetchall()
    return [dict(r) for r in rows]


# ── Match results ──────────────────────────────────────────────────────────

def set_match_result(match_id: str, home_score: int, away_score: int, status: str = "FT", source: str = "manual"):
    if _use_supabase():
        db = _db()
        try:
            db.table("match_results").upsert(
                {"match_id": match_id, "home_score": home_score,
                 "away_score": away_score, "status": status, "source": source},
                on_conflict="match_id").execute()
        except Exception:
            # Fallback for Supabase instances without the source column yet
            _sb(lambda: db.table("match_results").upsert(
                {"match_id": match_id, "home_score": home_score,
                 "away_score": away_score, "status": status},
                on_conflict="match_id").execute())
        return
    with _conn() as c:
        c.execute("""
            INSERT INTO match_results (match_id, home_score, away_score, status, source, updated_at)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(match_id) DO UPDATE SET
                home_score=excluded.home_score,
                away_score=excluded.away_score,
                status=excluded.status,
                source=excluded.source,
                updated_at=excluded.updated_at
        """, (match_id, home_score, away_score, status, source, datetime.now().isoformat()))


def get_match_results() -> dict:
    if _use_supabase():
        db = _db()
        res = _sb(lambda: db.table("match_results").select("*").execute())
        results = {}
        for r in res.data:
            r.setdefault("source", "manual")
            results[r["match_id"]] = r
        return results
    with _conn() as c:
        rows = c.execute(
            "SELECT match_id, home_score, away_score, status, source FROM match_results"
        ).fetchall()
    return {r["match_id"]: dict(r) for r in rows}


def clear_match_result(match_id: str):
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("match_results").delete().eq("match_id", match_id).execute())
        return
    with _conn() as c:
        c.execute("DELETE FROM match_results WHERE match_id=?", (match_id,))


def clear_all_results():
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("match_results").delete().neq("match_id", "").execute())
        return
    with _conn() as c:
        c.execute("DELETE FROM match_results")


def sync_api_results(matches: list):
    """Persist finished/live match results from the real API to the DB.

    Only runs for matches with actual scores. Skips any match that already has
    a manual override so admin entries are never overwritten automatically.
    Call this after a successful fetch_api_matches() — never with mock data.
    """
    _DONE = {"FT", "AET", "PEN"}
    _LIVE = {"1H", "2H", "HT", "ET", "BT", "P", "INT"}

    current = get_match_results()

    for m in matches:
        mid    = m.get("match_id", "")
        status = m.get("status", "")
        hs     = m.get("home_score")
        as_    = m.get("away_score")

        if not mid or status not in (_DONE | _LIVE):
            continue
        if hs is None or as_ is None:
            continue

        existing = current.get(mid)

        # Never overwrite a manual entry
        if existing and existing.get("source", "manual") == "manual":
            continue

        # Skip if already stored with identical data (avoid unnecessary writes)
        if existing and (
            existing.get("home_score") == hs
            and existing.get("away_score") == as_
            and existing.get("status") == status
        ):
            continue

        set_match_result(mid, int(hs), int(as_), status, source="api")


# ── Sessions ───────────────────────────────────────────────────────────────

def create_session(user_id: int) -> str:
    token = str(uuid.uuid4())
    expires = (datetime.utcnow() + timedelta(days=30)).isoformat()
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("sessions").delete().eq("user_id", user_id).execute())
        _sb(lambda: db.table("sessions").insert(
            {"token": token, "user_id": user_id, "expires_at": expires}).execute())
    else:
        with _conn() as c:
            c.execute("DELETE FROM sessions WHERE user_id=?", (user_id,))
            c.execute("INSERT INTO sessions (token, user_id, expires_at) VALUES (?,?,?)",
                      (token, user_id, expires))
    return token


def validate_session(token: str) -> dict | None:
    if not token:
        return None
    if _use_supabase():
        db = _db()
        res = _sb(lambda: db.table("sessions").select("user_id").eq("token", token).execute())
        if not res.data:
            return None
        uid = res.data[0]["user_id"]
        res2 = _sb(lambda: db.table("users").select("id,username").eq("id", uid).execute())
        return res2.data[0] if res2.data else None
    with _conn() as c:
        row = c.execute("""
            SELECT u.id, u.username FROM sessions s
            JOIN users u ON s.user_id=u.id
            WHERE s.token=? AND s.expires_at > ?
        """, (token, datetime.utcnow().isoformat())).fetchone()
    return dict(row) if row else None


def delete_session(token: str):
    if _use_supabase():
        db = _db()
        _sb(lambda: db.table("sessions").delete().eq("token", token).execute())
    else:
        with _conn() as c:
            c.execute("DELETE FROM sessions WHERE token=?", (token,))
