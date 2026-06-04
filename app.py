import streamlit as st
import random
import base64
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

from database import (
    init_db, create_user, authenticate, get_user_by_username,
    save_prediction, get_predictions, get_all_predictions, get_users,
    delete_user, set_match_result, get_match_results, clear_match_result, clear_all_results,
    create_session, validate_session, delete_session,
)
from football_api import (
    get_matches, get_live_ids, calculate_points, get_flag,
    get_group_standings, GROUPS, STATUS_DONE, STATUS_LIVE,
)

# ── Page config ─────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="⚽ Mundial Pilarico 2026",
    page_icon="⚽",
    layout="centered",
    initial_sidebar_state="collapsed",
)

init_db()

@st.cache_data
def _logo_b64() -> str:
    p = Path("omar chiquitico.png")
    return base64.b64encode(p.read_bytes()).decode() if p.exists() else ""

def _render_header():
    b64 = _logo_b64()
    img_html = f'<img src="data:image/png;base64,{b64}" class="app-logo">' if b64 else "👤"
    st.markdown(f"""
<div class="app-header">
  {img_html}
  <div>
    <div class="app-title">⚽ MUNDIAL PILARICO 2026</div>
    <div class="app-subtitle">La quiniela de los panas</div>
  </div>
</div>""", unsafe_allow_html=True)

# ── CSS ──────────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Oswald:wght@400;600;700&family=Inter:wght@300;400;500&display=swap');

html, body, [class*="css"] { font-family: 'Inter', sans-serif; }
.stApp { background: linear-gradient(160deg,#070f1e 0%,#0d1b33 55%,#091525 100%); }
#MainMenu, footer, header { visibility: hidden; }

/* ── Title ── */
.app-header {
    display:flex; align-items:center; justify-content:center;
    gap:14px; margin-bottom:1.2rem;
}
.app-logo {
    width:68px; height:68px; object-fit:cover;
    border-radius:50%; border:2px solid #FFD700;
    box-shadow:0 0 12px rgba(255,215,0,.35);
}
.app-title {
    text-align:center; font-family:'Oswald',sans-serif;
    font-size:clamp(1.6rem,5vw,2.8rem); font-weight:700; letter-spacing:2px;
    background:linear-gradient(90deg,#FFD700 0%,#FFA500 50%,#FFD700 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    background-clip:text; margin:0;
}
.app-subtitle {
    text-align:center; color:rgba(255,255,255,.4);
    font-size:.82rem; letter-spacing:4px; text-transform:uppercase; margin:2px 0 0;
}

/* ── Match card ── */
.match-card {
    background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
    border-radius:14px; padding:12px 14px 8px; margin-bottom:8px;
}
.match-card:hover { border-color:rgba(255,215,0,.22); }
.match-card-live  { border-color:rgba(0,255,100,.3)!important; box-shadow:0 0 10px rgba(0,255,100,.08); }
.match-card-done  { opacity:.9; }

/* ── Group header ── */
.group-label {
    font-family:'Oswald',sans-serif; color:#FFD700; font-size:.88rem;
    letter-spacing:1.5px; text-transform:uppercase;
    border-left:3px solid #FFD700; padding-left:8px; margin:16px 0 6px;
}

/* ── Team names ── */
.team-r { display:flex; align-items:center; justify-content:flex-end;
           gap:6px; font-family:'Oswald',sans-serif; font-size:.95rem;
           font-weight:600; letter-spacing:.5px; text-transform:uppercase; }
.team-l { display:flex; align-items:center; gap:6px;
           font-family:'Oswald',sans-serif; font-size:.95rem;
           font-weight:600; letter-spacing:.5px; text-transform:uppercase; }

/* ── Points badge ── */
.pts { display:inline-block; padding:3px 12px; border-radius:20px;
       font-family:'Oswald',sans-serif; font-size:.98rem; font-weight:700;
       min-width:52px; text-align:center; }
.pts-live { background:rgba(0,230,80,.18); color:#00e664; border:1px solid rgba(0,230,80,.5);
             animation:glow 1.4s ease-in-out infinite alternate; }
.pts-4 { background:rgba(255,215,0,.18); color:#FFD700;  border:1px solid rgba(255,215,0,.4); }
.pts-3 { background:rgba(100,200,255,.15); color:#64c8ff; border:1px solid rgba(100,200,255,.3); }
.pts-2 { background:rgba(200,200,200,.12); color:#d0d0d0; border:1px solid rgba(200,200,200,.25); }
.pts-0 { background:rgba(255,80,80,.12);  color:#ff7070; border:1px solid rgba(255,80,80,.2); }
@keyframes glow { from{box-shadow:0 0 4px rgba(0,230,80,.3)} to{box-shadow:0 0 12px rgba(0,230,80,.7)} }

/* ── Live badge ── */
.live-tag { display:inline-block; background:#e02020; color:#fff;
             font-size:.63rem; font-weight:700; letter-spacing:1px;
             padding:1px 7px; border-radius:4px; animation:glow 1s infinite alternate; }

/* ── Leaderboard ── */
.lb-row { display:flex; align-items:center; justify-content:space-between;
           background:rgba(255,255,255,.04); border-radius:10px; padding:12px 18px; margin:5px 0; }
.lb-rank { font-family:'Oswald',sans-serif; font-size:1.4rem; font-weight:700; width:34px; }
.lb-name { font-family:'Oswald',sans-serif; font-size:1.1rem; font-weight:600; flex:1; padding-left:10px; }
.lb-pts  { font-family:'Oswald',sans-serif; font-size:1.4rem; font-weight:700; color:#FFD700; }
.lb-meta { font-size:.73rem; color:rgba(255,255,255,.4); text-align:right; }
.lb-gold   { border-left:4px solid #FFD700; }
.lb-silver { border-left:4px solid #C0C0C0; }
.lb-bronze { border-left:4px solid #CD7F32; }
.lb-other  { border-left:4px solid rgba(255,255,255,.08); }

/* ── Group standings table ── */
.gs-table { width:100%; border-collapse:collapse; font-size:.85rem; }
.gs-table th { color:rgba(255,215,0,.8); font-family:'Oswald',sans-serif;
                font-weight:600; letter-spacing:.5px; padding:6px 8px;
                border-bottom:1px solid rgba(255,215,0,.2); text-align:center; }
.gs-table th:nth-child(2) { text-align:left; }
.gs-table td { padding:7px 8px; text-align:center; border-bottom:1px solid rgba(255,255,255,.05); }
.gs-table td:nth-child(2) { text-align:left; font-weight:500; }
.gs-row-adv { background:rgba(255,215,0,.05); }
.gs-row-1   { border-left:3px solid #FFD700; }
.gs-row-2   { border-left:3px solid rgba(255,215,0,.4); }
.gs-row-3   { border-left:3px solid rgba(100,180,100,.5); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
    background: transparent;
    gap: 8px;
    padding: 4px 0;
    overflow-x: auto;
    flex-wrap: nowrap;
}
.stTabs [data-baseweb="tab"] {
    color: rgba(255,255,255,.55);
    font-family: 'Oswald', sans-serif;
    font-size: .95rem;
    letter-spacing: .8px;
    border-radius: 9px;
    white-space: nowrap;
    border: 1px solid rgba(255,255,255,.13) !important;
    background: rgba(255,255,255,.04) !important;
    padding: 9px 20px !important;
    min-height: 40px !important;
    transition: all .18s ease;
}
.stTabs [data-baseweb="tab"]:hover {
    background: rgba(255,255,255,.09) !important;
    border-color: rgba(255,255,255,.25) !important;
    color: rgba(255,255,255,.85) !important;
}
.stTabs [aria-selected="true"] {
    background: rgba(255,215,0,.18) !important;
    color: #FFD700 !important;
    border: 1px solid rgba(255,215,0,.55) !important;
    font-weight: 600;
}

/* ── Inputs / buttons ── */
input[type="number"] {
    background:rgba(255,255,255,.08)!important; border:1px solid rgba(255,215,0,.3)!important;
    color:#fff!important; text-align:center; font-size:1.1rem!important;
    font-weight:700!important; border-radius:8px!important;
}
.stButton>button {
    background:rgba(255,215,0,.14); color:#FFD700; border:1px solid rgba(255,215,0,.35);
    border-radius:8px; font-family:'Oswald',sans-serif; letter-spacing:.8px;
    padding:4px 14px; transition:all .2s;
}
.stButton>button:hover { background:rgba(255,215,0,.26); border-color:#FFD700; transform:translateY(-1px); }

/* ── Radio selector (fase) ── */
.stRadio>div { gap:8px; }
.stRadio>div>label {
    background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
    border-radius:8px; padding:6px 16px; cursor:pointer; transition:all .2s;
    font-family:'Oswald',sans-serif; font-size:.9rem; letter-spacing:.5px;
}
.stRadio>div>label:has(input:checked) { background:rgba(255,215,0,.18); border-color:#FFD700; color:#FFD700; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background:rgba(7,15,30,.97)!important; border-right:1px solid rgba(255,215,0,.1);
}
</style>
""", unsafe_allow_html=True)


# ── Constants ─────────────────────────────────────────────────────────────

ROUND_ORDER = ["Jornada 1","Jornada 2","Jornada 3",
               "Dieciseisavos","Octavos","Cuartos de Final","Semifinal","Final"]

ROUND_LABELS = {
    "Jornada 1":      "J1 · Jun 11-14",
    "Jornada 2":      "J2 · Jun 15-18",
    "Jornada 3":      "J3 · Jun 22-25",
    "Dieciseisavos":  "Dieciseisavos",
    "Octavos":        "Octavos",
    "Cuartos de Final": "Cuartos",
    "Semifinal":      "Semifinal",
    "Final":          "Final",
}

RANK_CSS   = ["lb-gold","lb-silver","lb-bronze"]
RANK_MEDAL = ["🥇","🥈","🥉"]
PTS_CSS    = {4:"pts-4", 3:"pts-3", 2:"pts-2", 0:"pts-0"}


# ── Helpers ───────────────────────────────────────────────────────────────

def fmt_date(d: str) -> str:
    try:
        from datetime import datetime as dt
        return dt.strptime(d[:10], "%Y-%m-%d").strftime("%d %b")
    except Exception:
        return d[:10]


def apply_overrides(matches: list, overrides: dict) -> list:
    result = []
    for m in matches:
        mc = m.copy()
        if mc["match_id"] in overrides:
            ov = overrides[mc["match_id"]]
            mc["home_score"] = ov["home_score"]
            mc["away_score"] = ov["away_score"]
            mc["status"]     = ov["status"]
        result.append(mc)
    return result


def compute_user_stats(user_id: int, matches: list, live_ids: set):
    preds = get_predictions(user_id)
    match_map = {m["match_id"]: m for m in matches}
    pts = live_pts = 0
    for mid, (ph, pa) in preds.items():
        m = match_map.get(mid)
        if not m:
            continue
        p = calculate_points(ph, pa, m["home_score"], m["away_score"])
        if p is not None:
            pts += p
            if mid in live_ids or m["status"] in STATUS_LIVE:
                live_pts += p
    return pts, live_pts, preds


# ── Auth ──────────────────────────────────────────────────────────────────

def _login(user: dict):
    token = create_session(user["id"])
    st.session_state["user"] = user
    st.session_state["_token"] = token
    st.query_params["t"] = token


def show_auth():
    _render_header()

    t_in, t_reg = st.tabs(["🔑  Iniciar sesión", "📝  Registrarse"])

    with t_in:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("login"):
            u = st.text_input("Usuario", placeholder="tu nombre de usuario")
            p = st.text_input("Contraseña", type="password", placeholder="••••••••")
            ok = st.form_submit_button("Entrar  →", use_container_width=True)
        if ok:
            result = authenticate(u, p)
            if result:
                _login(result)
                st.rerun()
            else:
                st.error("Usuario o contraseña incorrectos.")

    with t_reg:
        st.markdown("<br>", unsafe_allow_html=True)
        with st.form("register"):
            nu = st.text_input("Elige un usuario", placeholder="ej: diegoG10")
            np = st.text_input("Elige una contraseña", type="password", placeholder="••••••••")
            np2 = st.text_input("Repite la contraseña", type="password", placeholder="••••••••")
            ok2 = st.form_submit_button("Crear cuenta  →", use_container_width=True)
        if ok2:
            if not nu.strip():
                st.error("El nombre no puede estar vacío.")
            elif len(np) < 4:
                st.error("Contraseña mínimo 4 caracteres.")
            elif np != np2:
                st.error("Las contraseñas no coinciden.")
            else:
                created, err = create_user(nu, np)
                if created:
                    _login(authenticate(nu, np))
                    st.success("¡Cuenta creada! 🎉")
                    st.rerun()
                else:
                    st.error(err)


# ── Sidebar ───────────────────────────────────────────────────────────────

def show_sidebar(user_name: str, pts: int, live_pts: int):
    with st.sidebar:
        st.markdown(f"""
        <div style="padding:1rem 0 .5rem;text-align:center">
            <div style="font-size:2.2rem">⚽</div>
            <div style="font-family:'Oswald',sans-serif;font-size:1.25rem;font-weight:700;color:#FFD700;letter-spacing:1px">
                {user_name.upper()}</div>
            <div style="color:rgba(255,255,255,.35);font-size:.75rem;margin-top:2px">jugador activo</div>
        </div>
        <hr style="border-color:rgba(255,215,0,.15);margin:.5rem 0">
        <div style="text-align:center;padding:.4rem 0">
            <div style="color:rgba(255,255,255,.4);font-size:.72rem;letter-spacing:2px;text-transform:uppercase">Mis puntos</div>
            <div style="font-family:'Oswald',sans-serif;font-size:2.8rem;font-weight:700;color:#FFD700;line-height:1.1">{pts}</div>
            {"<div style='color:#00e664;font-size:.75rem'>+"+str(live_pts)+" en juego 🔴</div>" if live_pts else ""}
        </div>
        <hr style="border-color:rgba(255,215,0,.15);margin:.5rem 0">
        """, unsafe_allow_html=True)

        st.markdown("**Sistema de puntos**")
        st.markdown("""
        <div style="font-size:.78rem;color:rgba(255,255,255,.55);line-height:2">
        🥇 Resultado exacto → <b style="color:#FFD700">4 pts</b><br>
        🥈 Ganador + diferencial → <b style="color:#64c8ff">3 pts</b><br>
        🥉 Ganador correcto → <b style="color:#d0d0d0">2 pts</b><br>
        🤝 Empate (marcador dist.) → <b style="color:#d0d0d0">2 pts</b><br>
        ❌ Incorrecto → <b style="color:#ff7070">0 pts</b>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🚪  Cerrar sesión", use_container_width=True):
            token = st.session_state.pop("_token", None)
            if token:
                delete_session(token)
            del st.session_state["user"]
            st.query_params.clear()
            st.rerun()


# ── Match card ────────────────────────────────────────────────────────────

def render_match(m: dict, user_id: int, user_preds: dict, live_ids: set):
    mid    = m["match_id"]
    home, away = m["home_team"], m["away_team"]
    hs, as_ = m["home_score"], m["away_score"]
    status = m["status"]
    is_live = mid in live_ids or status in STATUS_LIVE
    is_done = status in STATUS_DONE
    can_edit = not is_done and not is_live

    pred   = user_preds.get(mid)
    pred_h = pred[0] if pred else 0
    pred_a = pred[1] if pred else 0
    pts    = calculate_points(pred_h, pred_a, hs, as_) if pred else None

    card_cls = "match-card-live" if is_live else ("match-card-done" if is_done else "")
    min_str  = f" {m.get('minute', '')}'" if is_live and m.get("minute") else ""
    live_html = f'<span class="live-tag">🔴 EN VIVO{min_str}</span>' if is_live else ""

    # Card header row
    st.markdown(f"""
    <div class="match-card {card_cls}">
        <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:7px">
            <div style="font-size:.7rem;color:rgba(255,255,255,.3);letter-spacing:.5px">{m.get('group','')}</div>
            <div style="font-size:.7rem;color:rgba(255,255,255,.3)">{fmt_date(m.get('match_date',''))} {live_html}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3, c4, c5, c6, c7 = st.columns([2.8, 1, .4, 1, 2.8, 1.5, 1.2])

    with c1:
        st.markdown(f'<div class="team-r"><span style="font-size:.9rem;color:#f0f0f0">{home}</span>'
                    f'<span style="font-size:1.4rem;line-height:1">{get_flag(home)}</span></div>',
                    unsafe_allow_html=True)
    with c2:
        if can_edit:
            new_h = st.number_input(" ", 0, 30, pred_h, key=f"h_{mid}", label_visibility="collapsed")
        else:
            st.markdown(f'<div style="text-align:center;font-family:Oswald,sans-serif;font-size:1.2rem;font-weight:700;padding-top:5px">{pred_h}</div>', unsafe_allow_html=True)
            new_h = pred_h
    with c3:
        st.markdown('<div style="text-align:center;font-family:Oswald,sans-serif;font-size:1.1rem;font-weight:600;color:rgba(255,255,255,.35);padding-top:7px">–</div>', unsafe_allow_html=True)
    with c4:
        if can_edit:
            new_a = st.number_input("  ", 0, 30, pred_a, key=f"a_{mid}", label_visibility="collapsed")
        else:
            st.markdown(f'<div style="text-align:center;font-family:Oswald,sans-serif;font-size:1.2rem;font-weight:700;padding-top:5px">{pred_a}</div>', unsafe_allow_html=True)
            new_a = pred_a
    with c5:
        st.markdown(f'<div class="team-l"><span style="font-size:1.4rem;line-height:1">{get_flag(away)}</span>'
                    f'<span style="font-size:.9rem;color:#f0f0f0">{away}</span></div>',
                    unsafe_allow_html=True)
    with c6:
        if hs is not None and as_ is not None:
            st.markdown(f'<div style="text-align:center;font-family:Oswald,sans-serif;font-size:1.1rem;font-weight:600;color:rgba(255,255,255,.75);padding-top:5px">⚽ {hs} – {as_}</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div style="text-align:center;color:rgba(255,255,255,.18);font-size:.85rem;padding-top:8px">– vs –</div>', unsafe_allow_html=True)
    with c7:
        if pts is not None:
            cls = "pts-live" if is_live else PTS_CSS.get(pts, "pts-0")
            st.markdown(f'<div class="pts {cls}" style="margin-top:4px">{pts} pts</div>', unsafe_allow_html=True)
        elif can_edit:
            if st.button("💾", key=f"sv_{mid}", help="Guardar pronóstico"):
                save_prediction(user_id, mid, int(new_h), int(new_a))
                st.session_state.pop("user_preds", None)
                st.toast(f"✅ {home} {new_h}–{new_a} {away}", icon="⚽")
        else:
            st.markdown('<div style="color:rgba(255,255,255,.18);text-align:center;font-size:.75rem;padding-top:8px">sin pred</div>', unsafe_allow_html=True)

    if can_edit and pred is not None and (int(new_h) != pred_h or int(new_a) != pred_a):
        if st.button(f"💾 Actualizar", key=f"up_{mid}"):
            save_prediction(user_id, mid, int(new_h), int(new_a))
            st.session_state.pop("user_preds", None)
            st.toast("Pronóstico actualizado ✅")


def show_round(round_name: str, matches: list, user_id: int, user_preds: dict, live_ids: set):
    rnd_matches = [m for m in matches if m["round"] == round_name]
    rnd_matches.sort(key=lambda x: (x["match_date"], x["match_id"]))
    by_group: dict[str, list] = defaultdict(list)
    for m in rnd_matches:
        by_group[m.get("group", round_name)].append(m)
    for grp, ms in by_group.items():
        if grp != round_name:
            st.markdown(f'<div class="group-label">{grp}</div>', unsafe_allow_html=True)
        for m in ms:
            render_match(m, user_id, user_preds, live_ids)


# ── Predictions tab ───────────────────────────────────────────────────────

def show_predictions(user: dict, matches: list, live_ids: set):
    uid = user["id"]
    if "user_preds" not in st.session_state:
        st.session_state["user_preds"] = get_predictions(uid)
    preds = st.session_state["user_preds"]

    fase = st.radio(
        "Fase",
        ["🏟  Fase de Grupos", "⚔️  Fase Eliminatoria"],
        horizontal=True, label_visibility="collapsed", key="fase"
    )
    st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)

    if fase == "🏟  Fase de Grupos":
        tj1, tj2, tj3 = st.tabs(["J1 · Jun 11-17", "J2 · Jun 18-23", "J3 · Jun 24-27"])
        with tj1: show_round("Jornada 1", matches, uid, preds, live_ids)
        with tj2: show_round("Jornada 2", matches, uid, preds, live_ids)
        with tj3: show_round("Jornada 3", matches, uid, preds, live_ids)
    else:
        td, to, tq, ts, tf = st.tabs(["Dieciseisavos", "Octavos", "Cuartos", "Semifinal", "Final"])
        with td: show_round("Dieciseisavos", matches, uid, preds, live_ids)
        with to: show_round("Octavos",       matches, uid, preds, live_ids)
        with tq: show_round("Cuartos de Final", matches, uid, preds, live_ids)
        with ts: show_round("Semifinal",     matches, uid, preds, live_ids)
        with tf: show_round("Final",         matches, uid, preds, live_ids)

    st.markdown("""
    <div style="margin-top:1.2rem;padding:9px 14px;background:rgba(255,215,0,.05);
         border-radius:10px;border:1px solid rgba(255,215,0,.1);font-size:.78rem;
         color:rgba(255,255,255,.4)">
    💡 Pulsa 💾 para guardar. Puedes cambiar tus pronósticos hasta que comience cada partido.
    </div>""", unsafe_allow_html=True)


# ── Group standings tab ───────────────────────────────────────────────────

def show_group_standings(matches: list):
    standings = get_group_standings(matches)

    group_letters = list(GROUPS.keys())
    cols_per_row = 3
    rows = [group_letters[i:i+cols_per_row] for i in range(0, len(group_letters), cols_per_row)]

    for row in rows:
        cols = st.columns(cols_per_row)
        for col, letter in zip(cols, row):
            grp = f"Grupo {letter}"
            data = standings.get(grp, [])
            with col:
                st.markdown(f'<div class="group-label" style="margin-top:12px">{grp}</div>',
                            unsafe_allow_html=True)
                header = "<table class='gs-table'><thead><tr><th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th></tr></thead><tbody>"
                rows_html = ""
                for pos, (team, s) in enumerate(data, 1):
                    adv_cls = "gs-row-1" if pos == 1 else ("gs-row-2" if pos == 2 else ("gs-row-3" if pos == 3 else ""))
                    flag = get_flag(team)
                    rows_html += (
                        f"<tr class='{adv_cls}'>"
                        f"<td>{pos}</td>"
                        f"<td>{flag} {team}</td>"
                        f"<td>{s['P']}</td><td>{s['G']}</td><td>{s['E']}</td><td>{s['P_']}</td>"
                        f"<td>{s['GF']}</td><td>{s['GC']}</td>"
                        f"<td>{'+'if s['DG']>0 else ''}{s['DG']}</td>"
                        f"<td><b>{s['Pts']}</b></td>"
                        f"</tr>"
                    )
                st.markdown(header + rows_html + "</tbody></table>", unsafe_allow_html=True)

    st.markdown("""
    <div style="margin-top:1.5rem;font-size:.75rem;color:rgba(255,255,255,.35);text-align:center">
    🟡 Top 2 de cada grupo clasifican directo · 🟢 Los 8 mejores terceros también avanzan
    </div>""", unsafe_allow_html=True)


# ── Leaderboard tab ───────────────────────────────────────────────────────

def show_leaderboard(matches: list, live_ids: set):
    match_map = {m["match_id"]: m for m in matches}
    all_preds = get_all_predictions()
    users = get_users()

    stats: dict[str, dict] = {u["username"]: {
        "pts": 0, "n": 0, "exact": 0, "live_pts": 0, "has_live": False
    } for u in users}

    for p in all_preds:
        un = p["username"]; mid = p["match_id"]
        m = match_map.get(mid)
        if not m:
            continue
        pts = calculate_points(p["home_goals"], p["away_goals"], m["home_score"], m["away_score"])
        if pts is None:
            continue
        is_live = mid in live_ids or m["status"] in STATUS_LIVE
        if un not in stats:
            stats[un] = {"pts": 0, "n": 0, "exact": 0, "live_pts": 0, "has_live": False}
        stats[un]["pts"]  += pts
        stats[un]["n"]    += 1
        if pts == 4:
            stats[un]["exact"] += 1
        if is_live:
            stats[un]["live_pts"] += pts
            stats[un]["has_live"]  = True

    ranked = sorted(stats.items(), key=lambda x: x[1]["pts"], reverse=True)

    st.markdown("<br>", unsafe_allow_html=True)
    for i, (name, s) in enumerate(ranked):
        rc  = RANK_CSS[i]   if i < 3 else "lb-other"
        med = RANK_MEDAL[i] if i < 3 else f"#{i+1}"
        live_badge = ""
        if s["has_live"]:
            live_badge = f'<span style="font-size:.72rem;color:#00e664;margin-left:8px">(+{s["live_pts"]} en juego 🔴)</span>'
        st.markdown(f"""
        <div class="lb-row {rc}">
            <div class="lb-rank">{med}</div>
            <div class="lb-name">{name.upper()}{live_badge}</div>
            <div style="text-align:right">
                <div class="lb-pts">{s['pts']} pts</div>
                <div class="lb-meta">✅ {s['exact']} exactos &nbsp;·&nbsp; 🎯 {s['n']} pronósticos</div>
            </div>
        </div>""", unsafe_allow_html=True)

    if not ranked:
        st.info("Aún no hay pronósticos. ¡Sé el primero!")

    st.markdown("<br>", unsafe_allow_html=True)
    st.markdown("### 📊 Estadísticas")
    played = sum(1 for m in matches if m["status"] in STATUS_DONE | STATUS_LIVE)
    c1, c2, c3 = st.columns(3)
    c1.metric("Partidos jugados", f"{played} / {len(matches)}")
    c2.metric("Pronósticos totales", len(all_preds))
    c3.metric("Líder con", f"{ranked[0][1]['pts']} pts" if ranked else "—")


# ── Admin tab ─────────────────────────────────────────────────────────────

def show_admin(current_user: dict, matches: list):
    st.markdown("### ⚙️ Administración")

    # ── Delete user ──
    with st.expander("🗑️ Eliminar usuario", expanded=False):
        users = get_users()
        opts  = [u for u in users if u["id"] != current_user["id"]]
        if not opts:
            st.info("No hay otros usuarios para eliminar.")
        else:
            names = [u["username"] for u in opts]
            sel   = st.selectbox("Selecciona el usuario a eliminar", names, key="del_user_sel")
            uid   = next(u["id"] for u in opts if u["username"] == sel)
            st.warning(f"⚠️ Esto eliminará al usuario **{sel}** y todos sus pronósticos.")
            if st.button(f"🗑️ Eliminar {sel}", key="del_user_btn"):
                delete_user(uid)
                st.success(f"Usuario {sel} eliminado.")
                st.rerun()

    st.markdown("---")

    # ── Simulate / set match result ──
    with st.expander("⚽ Simular resultado de partido", expanded=True):
        gs_matches = [m for m in matches if m["round"].startswith("Jornada")]
        labels = {m["match_id"]: f"{m['home_team']} vs {m['away_team']}  ({m['group']})"
                  for m in gs_matches}
        sel_mid = st.selectbox("Partido", list(labels.keys()),
                               format_func=lambda k: labels[k], key="sim_match")
        sel_m   = next(m for m in gs_matches if m["match_id"] == sel_mid)

        c1, c2, c3 = st.columns([2, 2, 3])
        with c1:
            sim_h = st.number_input(f"{sel_m['home_team']}", 0, 20, 0, key="sim_h")
        with c2:
            sim_a = st.number_input(f"{sel_m['away_team']}", 0, 20, 0, key="sim_a")
        with c3:
            sim_status = st.selectbox("Estado", ["FT","1H","2H","HT","ET","PEN"], key="sim_status")

        bc1, bc2, bc3 = st.columns(3)
        with bc1:
            if st.button("✅ Aplicar resultado", key="sim_apply"):
                set_match_result(sel_mid, int(sim_h), int(sim_a), sim_status)
                st.success(f"Resultado guardado: {sel_m['home_team']} {sim_h}–{sim_a} {sel_m['away_team']} ({sim_status})")
                st.rerun()
        with bc2:
            if st.button("🎲 Aleatorio", key="sim_random"):
                rh = random.randint(0, 5)
                ra = random.randint(0, 5)
                set_match_result(sel_mid, rh, ra, "FT")
                st.success(f"Resultado aleatorio: {sel_m['home_team']} {rh}–{ra} {sel_m['away_team']} (FT)")
                st.rerun()
        with bc3:
            if st.button("🗑️ Borrar resultado", key="sim_clear"):
                clear_match_result(sel_mid)
                st.info("Resultado eliminado.")
                st.rerun()

    # Show active overrides
    overrides = get_match_results()
    if overrides:
        st.markdown("**Resultados simulados activos:**")
        match_map = {m["match_id"]: m for m in matches}
        for mid, ov in overrides.items():
            m = match_map.get(mid, {})
            home = m.get("home_team", mid); away = m.get("away_team", "")
            st.markdown(
                f"- **{home}** {ov['home_score']}–{ov['away_score']} **{away}** "
                f"[{ov['status']}]"
            )
        if st.button("🗑️ Borrar todos los resultados simulados", key="clear_all"):
            clear_all_results()
            st.rerun()


# ── Main app ──────────────────────────────────────────────────────────────

def show_app():
    user = st.session_state["user"]

    raw_matches = get_matches()
    overrides   = get_match_results()
    matches     = apply_overrides(raw_matches, overrides)
    live_ids    = get_live_ids()

    pts, live_pts, _ = compute_user_stats(user["id"], matches, live_ids)
    show_sidebar(user["username"], pts, live_pts)

    _render_header()

    if live_ids:
        st.markdown(
            f'<div style="text-align:center;margin-bottom:.5rem">'
            f'<span class="live-tag">🔴 EN VIVO</span> '
            f'<span style="color:rgba(255,255,255,.45);font-size:.8rem">'
            f'{len(live_ids)} partido(s) en curso</span></div>',
            unsafe_allow_html=True
        )

    t_pred, t_groups, t_lb, t_admin = st.tabs([
        "🏆  Pronósticos", "📊  Grupos", "🥇  Clasificación", "⚙️  Admin"
    ])

    with t_pred:
        show_predictions(user, matches, live_ids)
    with t_groups:
        show_group_standings(matches)
    with t_lb:
        show_leaderboard(matches, live_ids)
    with t_admin:
        show_admin(user, matches)

    if live_ids:
        import time
        time.sleep(30)
        st.rerun()


# ── Entry point ───────────────────────────────────────────────────────────

def main():
    if "user" not in st.session_state:
        token = st.query_params.get("t")
        if token:
            user = validate_session(token)
            if user:
                st.session_state["user"] = user
                st.session_state["_token"] = token
            else:
                st.query_params.clear()
        if "user" not in st.session_state:
            show_auth()
            return
    show_app()


main()
