"""
Script de prueba - crea 3 usuarios, agrega pronosticos y simula un resultado.
Ejecutar: python setup_test.py
"""
import sys
sys.stdout.reconfigure(encoding="utf-8")
import random
from database import init_db, create_user, authenticate, save_prediction, get_users, set_match_result
from football_api import calculate_points, get_mock_matches

init_db()

# ── Partido de prueba ────────────────────────────────────────────────────
# Argentina vs Austria  (Grupo J, Jornada 2 — 22 Jun 2026)
TEST_MATCH_ID = "GS-J-MD2-1"   # Argentina (home) vs Austria (away)
HOME_TEAM = "Argentina"
AWAY_TEAM = "Austria"

# ── Resultado "real" simulado (aleatorio) ────────────────────────────────
random.seed(42)
REAL_HOME = random.randint(0, 4)
REAL_AWAY = random.randint(0, 3)

# ── Pronósticos de cada usuario ──────────────────────────────────────────
TEST_USERS = [
    ("Pilara",  "pass1234", (REAL_HOME,     REAL_AWAY    )),   # resultado exacto → 4 pts
    ("Juancho", "pass1234", (REAL_HOME + 1, REAL_AWAY + 1)),   # mismo ganador, mismo DG → 3 pts (si no empate)
    ("Beto",    "pass1234", (0,             0            )),   # puede ser correcto si real es 0-0 o empate
]

print(f"\n{'='*55}")
print(f"  SIMULACIÓN — {HOME_TEAM} vs {AWAY_TEAM}")
print(f"{'='*55}")
print(f"  Resultado REAL simulado: {REAL_HOME} – {REAL_AWAY}")
print()

for username, password, (ph, pa) in TEST_USERS:
    # Crear usuario si no existe
    users = {u["username"] for u in get_users()}
    if username not in users:
        ok, err = create_user(username, password)
        if ok:
            print(f"  ✅ Usuario '{username}' creado.")
        else:
            print(f"  ⚠️  {err} — usando existente.")

    user = authenticate(username, password)
    if user:
        save_prediction(user["id"], TEST_MATCH_ID, ph, pa)
        pts = calculate_points(ph, pa, REAL_HOME, REAL_AWAY)
        result = f"+{pts} pts" if pts else "0 pts"
        sign   = "✅" if pts and pts >= 2 else "❌"
        print(f"  {sign} {username:12s}  pronosticó {ph}–{pa}  →  {result}")
    else:
        print(f"  ❌ No se pudo autenticar '{username}'")

# ── Guardar resultado en la base de datos ────────────────────────────────
set_match_result(TEST_MATCH_ID, REAL_HOME, REAL_AWAY, "FT")
print(f"\n  💾 Resultado guardado en DB para el partido {TEST_MATCH_ID}")

# ── Clasificación esperada ───────────────────────────────────────────────
print(f"\n{'─'*55}")
print("  CLASIFICACIÓN ESPERADA")
print(f"{'─'*55}")
scores = []
for username, password, (ph, pa) in TEST_USERS:
    pts = calculate_points(ph, pa, REAL_HOME, REAL_AWAY) or 0
    scores.append((username, pts, ph, pa))

for rank, (name, pts, ph, pa) in enumerate(sorted(scores, key=lambda x: -x[1]), 1):
    medal = ["🥇","🥈","🥉"][rank-1] if rank <= 3 else f"#{rank}"
    print(f"  {medal}  {name:12s}  {pts} pts  (pronosticó {ph}–{pa})")

print(f"\n{'='*55}")
print("  Abre http://localhost:8501 y ve a la pestaña 🥇 Clasificación")
print(f"{'='*55}\n")
