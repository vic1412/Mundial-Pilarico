import hashlib
import streamlit as st
from supabase import create_client, Client


@st.cache_resource
def _db() -> Client:
    return create_client(
        st.secrets["SUPABASE_URL"],
        st.secrets["SUPABASE_KEY"],
    )


def init_db():
    pass  # Tables pre-created in Supabase dashboard (see SQL below)


def _hash(pw: str) -> str:
    return hashlib.sha256(pw.encode("utf-8")).hexdigest()


# ── Users ──────────────────────────────────────────────────────────────────

def create_user(username: str, password: str) -> tuple[bool, str | None]:
    db = _db()
    existing = db.table("users").select("id").eq("username", username.strip()).execute()
    if existing.data:
        return False, "Ese usuario ya existe."
    db.table("users").insert({
        "username": username.strip(),
        "password_hash": _hash(password),
    }).execute()
    return True, None


def authenticate(username: str, password: str) -> dict | None:
    db = _db()
    res = (
        db.table("users")
        .select("id,username")
        .eq("username", username.strip())
        .eq("password_hash", _hash(password))
        .execute()
    )
    return res.data[0] if res.data else None


def get_user_by_username(username: str) -> dict | None:
    db = _db()
    res = db.table("users").select("id,username").eq("username", username).execute()
    return res.data[0] if res.data else None


def get_users() -> list:
    db = _db()
    res = db.table("users").select("id,username,created_at").order("created_at").execute()
    return res.data


def delete_user(user_id: int):
    db = _db()
    db.table("predictions").delete().eq("user_id", user_id).execute()
    db.table("users").delete().eq("id", user_id).execute()


# ── Predictions ────────────────────────────────────────────────────────────

def save_prediction(user_id: int, match_id: str, home: int, away: int):
    db = _db()
    db.table("predictions").upsert(
        {"user_id": user_id, "match_id": match_id, "home_goals": home, "away_goals": away},
        on_conflict="user_id,match_id",
    ).execute()


def get_predictions(user_id: int) -> dict:
    db = _db()
    res = (
        db.table("predictions")
        .select("match_id,home_goals,away_goals")
        .eq("user_id", user_id)
        .execute()
    )
    return {r["match_id"]: (r["home_goals"], r["away_goals"]) for r in res.data}


def get_all_predictions() -> list:
    db = _db()
    preds = db.table("predictions").select("user_id,match_id,home_goals,away_goals").execute().data
    users_map = {u["id"]: u["username"] for u in get_users()}
    for p in preds:
        p["username"] = users_map.get(p["user_id"], "?")
    return preds


# ── Match results ──────────────────────────────────────────────────────────

def set_match_result(match_id: str, home_score: int, away_score: int, status: str = "FT"):
    db = _db()
    db.table("match_results").upsert(
        {"match_id": match_id, "home_score": home_score, "away_score": away_score, "status": status},
        on_conflict="match_id",
    ).execute()


def get_match_results() -> dict:
    db = _db()
    res = db.table("match_results").select("match_id,home_score,away_score,status").execute()
    return {r["match_id"]: r for r in res.data}


def clear_match_result(match_id: str):
    db = _db()
    db.table("match_results").delete().eq("match_id", match_id).execute()


def clear_all_results():
    db = _db()
    db.table("match_results").delete().neq("match_id", "").execute()
