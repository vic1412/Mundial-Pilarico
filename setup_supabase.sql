-- Ejecuta esto en el SQL Editor de tu proyecto Supabase
-- (Dashboard → SQL Editor → New query → pega todo → Run)

CREATE TABLE IF NOT EXISTS users (
    id            SERIAL PRIMARY KEY,
    username      TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at    TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS predictions (
    id          SERIAL PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    match_id    TEXT NOT NULL,
    home_goals  INTEGER NOT NULL DEFAULT 0,
    away_goals  INTEGER NOT NULL DEFAULT 0,
    updated_at  TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(user_id, match_id)
);

CREATE TABLE IF NOT EXISTS match_results (
    match_id    TEXT PRIMARY KEY,
    home_score  INTEGER NOT NULL,
    away_score  INTEGER NOT NULL,
    status      TEXT NOT NULL DEFAULT 'FT',
    updated_at  TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS sessions (
    token       TEXT PRIMARY KEY,
    user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    expires_at  TIMESTAMPTZ NOT NULL
);

-- Desactiva RLS en todas las tablas (la app usa la service_role key, no la anon key)
ALTER TABLE users         DISABLE ROW LEVEL SECURITY;
ALTER TABLE predictions   DISABLE ROW LEVEL SECURITY;
ALTER TABLE match_results DISABLE ROW LEVEL SECURITY;
ALTER TABLE sessions      DISABLE ROW LEVEL SECURITY;
