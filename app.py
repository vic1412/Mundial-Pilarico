import streamlit as st
import base64
from pathlib import Path
from collections import defaultdict
from datetime import datetime, timedelta

from database import (
    init_db, create_user, authenticate, get_user_by_username,
    save_prediction, get_predictions, get_all_predictions, get_users,
    delete_user, set_match_result, get_match_results, clear_match_result, clear_all_results,
    create_session, validate_session, delete_session, sync_api_results,
)
from football_api import (
    get_matches, get_live_ids, fetch_api_matches, calculate_points, get_flag,
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
.block-container { padding: 1.2rem 1rem 2rem !important; max-width: 860px !important; }

/* ── Title ── */
.app-header { display:flex; align-items:center; justify-content:center; gap:12px; margin-bottom:1rem; }
.app-logo   { width:60px; height:60px; object-fit:cover; border-radius:50%;
              border:2px solid #FFD700; box-shadow:0 0 12px rgba(255,215,0,.35); flex-shrink:0; }
.app-title  { font-family:'Oswald',sans-serif; font-size:clamp(1.3rem,5vw,2.4rem);
              font-weight:700; letter-spacing:1.5px;
              background:linear-gradient(90deg,#FFD700 0%,#FFA500 50%,#FFD700 100%);
              -webkit-background-clip:text; -webkit-text-fill-color:transparent;
              background-clip:text; margin:0; }
.app-subtitle { color:rgba(255,255,255,.4); font-size:.75rem;
                letter-spacing:3px; text-transform:uppercase; margin:2px 0 0; }

/* ── Match card ── */
.match-card { background:rgba(255,255,255,.04); border:1px solid rgba(255,255,255,.08);
              border-radius:12px; padding:10px 12px 6px; margin-bottom:6px; }
.match-card:hover   { border-color:rgba(255,215,0,.22); }
.match-card-live    { border-color:rgba(0,255,100,.3)!important; box-shadow:0 0 10px rgba(0,255,100,.08); }
.match-card-done    { opacity:.9; }
.mc-meta  { display:flex; justify-content:space-between; font-size:.66rem;
            color:rgba(255,255,255,.3); margin-bottom:6px; }
.mc-teams { display:flex; align-items:center; justify-content:space-between; gap:4px; }
.mc-home  { display:flex; align-items:center; gap:5px; flex:1; min-width:0;
            font-family:'Oswald',sans-serif; font-size:.88rem; font-weight:600;
            text-transform:uppercase; letter-spacing:.3px; }
.mc-away  { display:flex; align-items:center; justify-content:flex-end; gap:5px;
            flex:1; min-width:0; font-family:'Oswald',sans-serif; font-size:.88rem;
            font-weight:600; text-transform:uppercase; letter-spacing:.3px; text-align:right; }
.mc-tname { white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }
.mc-score { font-family:'Oswald',sans-serif; font-size:.82rem; font-weight:600;
            color:rgba(255,255,255,.65); white-space:nowrap; flex-shrink:0; padding:0 3px; }
.mc-vs    { font-size:.75rem; color:rgba(255,255,255,.25); white-space:nowrap;
            flex-shrink:0; padding:0 4px; }
.pred-center { text-align:center; font-family:'Oswald',sans-serif;
               font-size:1.25rem; font-weight:700; padding:4px 0; }
.pred-dash   { text-align:center; color:rgba(255,255,255,.3); font-size:.95rem; padding-top:9px; }
.pred-none   { color:rgba(255,255,255,.18); text-align:center; font-size:.7rem; padding-top:10px; }

/* ── Group header ── */
.group-label { font-family:'Oswald',sans-serif; color:#FFD700; font-size:.85rem;
               letter-spacing:1.5px; text-transform:uppercase;
               border-left:3px solid #FFD700; padding-left:8px; margin:14px 0 5px; }

/* ── Points badge ── */
.pts { display:inline-block; padding:3px 10px; border-radius:20px;
       font-family:'Oswald',sans-serif; font-size:.92rem; font-weight:700;
       min-width:48px; text-align:center; }
.pts-live { background:rgba(0,230,80,.18); color:#00e664; border:1px solid rgba(0,230,80,.5);
            animation:glow 1.4s ease-in-out infinite alternate; }
.pts-4 { background:rgba(255,215,0,.18); color:#FFD700;  border:1px solid rgba(255,215,0,.4); }
.pts-3 { background:rgba(100,200,255,.15); color:#64c8ff; border:1px solid rgba(100,200,255,.3); }
.pts-2 { background:rgba(200,200,200,.12); color:#d0d0d0; border:1px solid rgba(200,200,200,.25); }
.pts-0 { background:rgba(255,80,80,.12);  color:#ff7070; border:1px solid rgba(255,80,80,.2); }
@keyframes glow { from{box-shadow:0 0 4px rgba(0,230,80,.3)} to{box-shadow:0 0 12px rgba(0,230,80,.7)} }

/* ── Live badge ── */
.live-tag { display:inline-block; background:#e02020; color:#fff; font-size:.6rem;
            font-weight:700; letter-spacing:1px; padding:1px 6px; border-radius:4px;
            animation:glow 1s infinite alternate; }

/* ── Leaderboard ── */
.lb-row    { display:flex; align-items:center; background:rgba(255,255,255,.04);
             border-radius:10px; padding:11px 14px; margin:5px 0; }
.lb-rank   { font-family:'Oswald',sans-serif; font-size:1.3rem; font-weight:700; width:32px; flex-shrink:0; }
.lb-name   { font-family:'Oswald',sans-serif; font-size:1rem; font-weight:600;
             flex:1; padding-left:8px; min-width:0; overflow:hidden; text-overflow:ellipsis; }
.lb-pts    { font-family:'Oswald',sans-serif; font-size:1.3rem; font-weight:700; color:#FFD700; flex-shrink:0; }
.lb-meta   { font-size:.7rem; color:rgba(255,255,255,.4); text-align:right; white-space:nowrap; }
.lb-gold   { border-left:4px solid #FFD700; }
.lb-silver { border-left:4px solid #C0C0C0; }
.lb-bronze { border-left:4px solid #CD7F32; }
.lb-other  { border-left:4px solid rgba(255,255,255,.08); }

/* ── Group standings table ── */
.gs-wrap  { overflow-x:auto; -webkit-overflow-scrolling:touch; }
.gs-table { width:100%; border-collapse:collapse; font-size:.82rem; }
.gs-table th { color:rgba(255,215,0,.8); font-family:'Oswald',sans-serif; font-weight:600;
               letter-spacing:.4px; padding:5px 6px; border-bottom:1px solid rgba(255,215,0,.2);
               text-align:center; white-space:nowrap; }
.gs-table th:nth-child(2) { text-align:left; }
.gs-table td { padding:6px 6px; text-align:center; border-bottom:1px solid rgba(255,255,255,.05); }
.gs-table td:nth-child(2) { text-align:left; font-weight:500; white-space:nowrap; }
.gs-row-1 { border-left:3px solid #FFD700; }
.gs-row-2 { border-left:3px solid rgba(255,215,0,.4); }
.gs-row-3 { border-left:3px solid rgba(100,180,100,.5); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] { background:transparent; gap:6px; padding:4px 0;
                                     overflow-x:auto; flex-wrap:nowrap; }
.stTabs [data-baseweb="tab"] { color:rgba(255,255,255,.55); font-family:'Oswald',sans-serif;
    font-size:.9rem; letter-spacing:.6px; border-radius:9px; white-space:nowrap;
    border:1px solid rgba(255,255,255,.13)!important; background:rgba(255,255,255,.04)!important;
    padding:8px 16px!important; min-height:38px!important; transition:all .18s ease; }
.stTabs [data-baseweb="tab"]:hover { background:rgba(255,255,255,.09)!important;
    border-color:rgba(255,255,255,.25)!important; color:rgba(255,255,255,.85)!important; }
.stTabs [aria-selected="true"] { background:rgba(255,215,0,.18)!important; color:#FFD700!important;
    border:1px solid rgba(255,215,0,.55)!important; font-weight:600; }

/* ── Inputs / buttons ── */
input[type="number"] { background:rgba(255,255,255,.08)!important;
    border:1px solid rgba(255,215,0,.3)!important; color:#fff!important;
    text-align:center; font-size:1rem!important; font-weight:700!important; border-radius:8px!important; }
.stButton>button { background:rgba(255,215,0,.14); color:#FFD700; border:1px solid rgba(255,215,0,.35);
    border-radius:8px; font-family:'Oswald',sans-serif; letter-spacing:.6px;
    padding:4px 12px; transition:all .2s; }
.stButton>button:hover { background:rgba(255,215,0,.26); border-color:#FFD700; transform:translateY(-1px); }

/* ── Radio selector ── */
.stRadio>div { gap:6px; }
.stRadio>div>label { background:rgba(255,255,255,.05); border:1px solid rgba(255,255,255,.1);
    border-radius:8px; padding:5px 14px; cursor:pointer; transition:all .2s;
    font-family:'Oswald',sans-serif; font-size:.88rem; letter-spacing:.4px; }
.stRadio>div>label:has(input:checked) { background:rgba(255,215,0,.18); border-color:#FFD700; color:#FFD700; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] { background:rgba(7,15,30,.97)!important;
                                    border-right:1px solid rgba(255,215,0,.1); }

/* ── Mobile ── */
@media (max-width: 640px) {
    .block-container { padding: 0.75rem 0.6rem 2rem !important; }
    .app-logo   { width:46px; height:46px; }
    .app-title  { font-size:1.2rem !important; letter-spacing:1px; }
    .app-subtitle { font-size:.65rem; letter-spacing:2px; }
    .mc-tname   { max-width:80px; font-size:.8rem; }
    .mc-score, .mc-vs { font-size:.72rem; }
    .stTabs [data-baseweb="tab"] { padding:6px 9px!important; font-size:.75rem!important; letter-spacing:0!important; }
    .lb-row  { padding:9px 10px; }
    .lb-rank { font-size:1.1rem; width:26px; }
    .lb-name { font-size:.9rem; }
    .lb-pts  { font-size:1.1rem; }
    .lb-meta { display:none; }
    .gs-table { font-size:.75rem; }
    .gs-table td, .gs-table th { padding:4px 4px; }
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

# ── Confederation config ─────────────────────────────────────────────────

_CONF_MAP: dict[str, str] = {
    "Nueva Zelanda": "OFC",
    "Colombia": "CONMEBOL", "Argentina": "CONMEBOL", "Brasil": "CONMEBOL",
    "Ecuador": "CONMEBOL", "Paraguay": "CONMEBOL", "Uruguay": "CONMEBOL",
    "Curaçao": "CONCACAF", "USA": "CONCACAF", "Canadá": "CONCACAF",
    "Panamá": "CONCACAF", "Haití": "CONCACAF", "México": "CONCACAF",
    "Irak": "AFC", "Arabia Saudí": "AFC", "Japón": "AFC",
    "Corea del Sur": "AFC", "Uzbekistán": "AFC", "Jordania": "AFC",
    "Catar": "AFC", "Australia": "AFC", "Irán": "AFC",
    "Egipto": "CAF", "Túnez": "CAF", "Argelia": "CAF",
    "Marruecos": "CAF", "Senegal": "CAF", "Cabo Verde": "CAF",
    "Costa de Marfil": "CAF", "Ghana": "CAF", "Rep. Dem. Congo": "CAF",
    "Sudáfrica": "CAF",
}
CONFS = ["UEFA", "CONCACAF", "CONMEBOL", "AFC", "CAF", "OFC"]
_CONF_N = {"UEFA": 16, "CONCACAF": 6, "CONMEBOL": 6, "AFC": 9, "CAF": 10, "OFC": 1}

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


# ── Confederation stats helpers ───────────────────────────────────────────

def _get_conf(team: str) -> str:
    return _CONF_MAP.get(team, "UEFA")


def _compute_conf_stats(matches: list, round_filter=None) -> dict:
    raw = {c: {"gf": 0, "ga": 0, "pts": 0, "mp": 0} for c in CONFS}
    played = STATUS_DONE | STATUS_LIVE
    for m in matches:
        if round_filter and m["round"] != round_filter:
            continue
        if m["status"] not in played or m["home_score"] is None:
            continue
        hc = _get_conf(m["home_team"])
        ac = _get_conf(m["away_team"])
        hs, as_ = m["home_score"], m["away_score"]
        raw[hc]["gf"] += hs; raw[hc]["ga"] += as_; raw[hc]["mp"] += 1
        raw[ac]["gf"] += as_; raw[ac]["ga"] += hs; raw[ac]["mp"] += 1
        if hs > as_:
            raw[hc]["pts"] += 3
        elif hs == as_:
            raw[hc]["pts"] += 1; raw[ac]["pts"] += 1
        else:
            raw[ac]["pts"] += 3
    result = {}
    for c in CONFS:
        r = raw[c]; n = _CONF_N[c]
        result[c] = {
            "avg_gf":  r["gf"] / n,
            "avg_ga":  r["ga"] / n,
            "avg_pts": r["pts"] / n,
            "rend":    r["pts"] / (r["mp"] * 3) * 100 if r["mp"] > 0 else 0.0,
        }
    return result


def _compute_vs_stats(matches: list, round_filter=None) -> dict:
    vs = {c1: {c2: {"gf": 0, "ga": 0, "pts": 0, "mp": 0} for c2 in CONFS} for c1 in CONFS}
    played = STATUS_DONE | STATUS_LIVE
    for m in matches:
        if round_filter and m["round"] != round_filter:
            continue
        if m["status"] not in played or m["home_score"] is None:
            continue
        hc = _get_conf(m["home_team"])
        ac = _get_conf(m["away_team"])
        hs, as_ = m["home_score"], m["away_score"]

        if hc == ac:
            # Intra-confederation: both teams contribute to the same diagonal cell.
            # Each team slot counts separately → mp += 2, gf/ga = sum of both sides.
            c = hc
            vs[c][c]["gf"] += hs + as_
            vs[c][c]["ga"] += hs + as_
            vs[c][c]["mp"] += 2
            if hs > as_:
                vs[c][c]["pts"] += 3   # only winner earns points
            elif hs == as_:
                vs[c][c]["pts"] += 2   # 1 pt each → 2 total
            else:
                vs[c][c]["pts"] += 3
        else:
            vs[hc][ac]["gf"] += hs; vs[hc][ac]["ga"] += as_; vs[hc][ac]["mp"] += 1
            vs[ac][hc]["gf"] += as_; vs[ac][hc]["ga"] += hs; vs[ac][hc]["mp"] += 1
            if hs > as_:
                vs[hc][ac]["pts"] += 3
            elif hs == as_:
                vs[hc][ac]["pts"] += 1; vs[ac][hc]["pts"] += 1
            else:
                vs[ac][hc]["pts"] += 3
    return vs


def _html_conf_table(stats: dict) -> str:
    hdr = (
        "<th style='text-align:left'>Confederación</th>"
        "<th>⚽ Goles marcados (prom)</th>"
        "<th>📈 Rendimiento</th>"
        "<th>🥅 Goles recibidos (prom)</th>"
        "<th>🏅 Puntos (prom)</th>"
    )
    rows = ""
    for c in CONFS:
        s = stats[c]
        rows += (
            f"<tr>"
            f"<td style='text-align:left;font-family:\"Oswald\",sans-serif;"
            f"font-weight:700;color:#FFD700'>{c}</td>"
            f"<td>{s['avg_gf']:.2f}</td>"
            f"<td>{s['rend']:.1f}%</td>"
            f"<td>{s['avg_ga']:.2f}</td>"
            f"<td>{s['avg_pts']:.2f}</td>"
            f"</tr>"
        )
    return (
        f"<div class='gs-wrap'><table class='gs-table'>"
        f"<thead><tr>{hdr}</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


def _html_vs_table(conf: str, vs: dict) -> str:
    hdr = f"<th style='text-align:left;color:#FFD700;font-family:\"Oswald\",sans-serif'>{conf}</th>"
    for c2 in CONFS:
        hdr += f"<th style='font-size:.75rem'>vs {c2}</th>"

    metrics = [
        ("Goles a favor",  lambda d: str(d["gf"]) if d["mp"] > 0 else "—"),
        ("Goles en contra", lambda d: str(d["ga"]) if d["mp"] > 0 else "—"),
        ("Puntos",         lambda d: str(d["pts"]) if d["mp"] > 0 else "—"),
        ("Rendimiento",    lambda d: (
            f"{d['pts'] / (d['mp'] * 3) * 100:.1f}%" if d["mp"] > 0 else "—"
        )),
    ]
    rows = ""
    for label, val_fn in metrics:
        row = (
            f"<tr><td style='text-align:left;color:rgba(255,255,255,.7);"
            f"font-size:.78rem;white-space:nowrap'>{label}</td>"
        )
        for c2 in CONFS:
            row += f"<td>{val_fn(vs[conf][c2])}</td>"
        row += "</tr>"
        rows += row
    return (
        f"<div class='gs-wrap'><table class='gs-table'>"
        f"<thead><tr>{hdr}</tr></thead>"
        f"<tbody>{rows}</tbody></table></div>"
    )


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

    score_html = (f'<div class="mc-score">{hs}&nbsp;–&nbsp;{as_}</div>'
                  if hs is not None and as_ is not None
                  else '<div class="mc-vs">VS</div>')

    st.markdown(f"""
<div class="match-card {card_cls}">
  <div class="mc-meta">
    <span>{m.get('group','')}</span>
    <span>{fmt_date(m.get('match_date',''))} {live_html}</span>
  </div>
  <div class="mc-teams">
    <div class="mc-home">{get_flag(home)}<span class="mc-tname">{home}</span></div>
    {score_html}
    <div class="mc-away"><span class="mc-tname">{away}</span>{get_flag(away)}</div>
  </div>
</div>""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns([2.5, .6, 2.5, 2.5])

    with c1:
        if can_edit:
            new_h = st.number_input(" ", 0, 30, pred_h, key=f"h_{mid}", label_visibility="collapsed")
        else:
            st.markdown(f'<div class="pred-center">{pred_h}</div>', unsafe_allow_html=True)
            new_h = pred_h
    with c2:
        st.markdown('<div class="pred-dash">–</div>', unsafe_allow_html=True)
    with c3:
        if can_edit:
            new_a = st.number_input("  ", 0, 30, pred_a, key=f"a_{mid}", label_visibility="collapsed")
        else:
            st.markdown(f'<div class="pred-center">{pred_a}</div>', unsafe_allow_html=True)
            new_a = pred_a
    with c4:
        if pts is not None:
            cls = "pts-live" if is_live else PTS_CSS.get(pts, "pts-0")
            st.markdown(f'<div class="pts {cls}" style="margin-top:4px">{pts} pts</div>', unsafe_allow_html=True)
        elif can_edit:
            if st.button("💾", key=f"sv_{mid}", help="Guardar pronóstico"):
                save_prediction(user_id, mid, int(new_h), int(new_a))
                st.session_state.pop("user_preds", None)
                st.toast(f"✅ {home} {new_h}–{new_a} {away}", icon="⚽")
        else:
            st.markdown('<div class="pred-none">sin pred</div>', unsafe_allow_html=True)

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
    cols_per_row = 2
    group_rows = [group_letters[i:i+cols_per_row] for i in range(0, len(group_letters), cols_per_row)]

    for group_row in group_rows:
        cols = st.columns(cols_per_row)
        for col, letter in zip(cols, group_row):
            grp = f"Grupo {letter}"
            data = standings.get(grp, [])
            with col:
                st.markdown(f'<div class="group-label" style="margin-top:12px">{grp}</div>',
                            unsafe_allow_html=True)
                header = "<div class='gs-wrap'><table class='gs-table'><thead><tr><th>#</th><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>GF</th><th>GC</th><th>DG</th><th>Pts</th></tr></thead><tbody>"
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
                st.markdown(header + rows_html + "</tbody></table></div>", unsafe_allow_html=True)

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


# ── Estadísticas tab ─────────────────────────────────────────────────────

def show_estadisticas(matches: list):
    _SUBTAB_ROUND = {
        "Total":         None,
        "Jornada 1":     "Jornada 1",
        "Jornada 2":     "Jornada 2",
        "Jornada 3":     "Jornada 3",
        "Dieciseisavos": "Dieciseisavos",
        "Octavos":       "Octavos",
        "Cuartos":       "Cuartos de Final",
        "Semifinal":     "Semifinal",
        "Final":         "Final",
    }
    tab_names = list(_SUBTAB_ROUND.keys()) + ["VS"]
    subtabs = st.tabs(tab_names)
    played = STATUS_DONE | STATUS_LIVE

    # Round sub-tabs
    for i, (tab_name, rf) in enumerate(_SUBTAB_ROUND.items()):
        with subtabs[i]:
            any_data = any(
                m["status"] in played
                and m["home_score"] is not None
                and (rf is None or m["round"] == rf)
                for m in matches
            )
            if not any_data:
                st.markdown(
                    "<div style='color:rgba(255,255,255,.35);font-size:.85rem;margin-top:1rem'>"
                    "⏳ Aún no hay resultados para esta fase.</div>",
                    unsafe_allow_html=True,
                )
            else:
                stats = _compute_conf_stats(matches, rf)
                st.markdown(_html_conf_table(stats), unsafe_allow_html=True)
                st.markdown(
                    "<div style='margin-top:.6rem;font-size:.72rem;color:rgba(255,255,255,.3)'>"
                    "Prom = total / equipos de la confederación · Rendimiento = pts totales / pts posibles</div>",
                    unsafe_allow_html=True,
                )

    # VS sub-tab
    with subtabs[len(_SUBTAB_ROUND)]:
        vs = _compute_vs_stats(matches, None)
        any_vs = any(
            m["status"] in played and m["home_score"] is not None
            and _get_conf(m["home_team"]) != _get_conf(m["away_team"])
            for m in matches
        )
        st.markdown(
            "<div style='font-size:.78rem;color:rgba(255,255,255,.4);margin-bottom:.6rem'>"
            "Métricas entre confederaciones distintas · total del torneo</div>",
            unsafe_allow_html=True,
        )
        if not any_vs:
            st.markdown(
                "<div style='color:rgba(255,255,255,.35);font-size:.85rem'>"
                "⏳ Aún no hay resultados entre confederaciones distintas.</div>",
                unsafe_allow_html=True,
            )
        else:
            for conf in CONFS:
                st.markdown(
                    f"<div class='group-label' style='margin-top:14px'>{conf}</div>",
                    unsafe_allow_html=True,
                )
                st.markdown(_html_vs_table(conf, vs), unsafe_allow_html=True)


# ── Admin tab ─────────────────────────────────────────────────────────────

_ALL_ROUNDS = [
    "Jornada 1", "Jornada 2", "Jornada 3",
    "Dieciseisavos", "Octavos", "Cuartos de Final", "Semifinal", "Final",
]
_STATUS_OPTS = ["FT", "AET", "PEN", "1H", "2H", "HT", "ET"]


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
    st.markdown("### ⚽ Ingresar resultado real")
    st.markdown(
        "<div style='font-size:.8rem;color:rgba(255,255,255,.45);margin-bottom:1rem'>"
        "Ingresa los resultados reales de los partidos para calcular los puntos. "
        "Los resultados manuales tienen prioridad sobre la API automática.</div>",
        unsafe_allow_html=True,
    )

    overrides = get_match_results()

    # ── Round selector ──
    sel_round = st.selectbox("Fase / Jornada", _ALL_ROUNDS, key="admin_round_sel")
    round_matches = [m for m in matches if m["round"] == sel_round]

    if not round_matches:
        st.info("No hay partidos definidos para esta fase todavía (equipos TBD).")
    else:
        # ── Match selector ──
        match_labels: dict[str, str] = {}
        for m in round_matches:
            home = m["home_team"] if m["home_team"] != "TBD" else "Por definir"
            away = m["away_team"] if m["away_team"] != "TBD" else "Por definir"
            grp  = m.get("group", "")
            date_str = fmt_date(m.get("match_date", ""))

            grp_label = f"  ({grp})" if grp and grp != sel_round and grp.startswith("Grupo") else f"  ({date_str})"
            score_label = ""
            if m["home_score"] is not None:
                src  = overrides.get(m["match_id"], {}).get("source", "api")
                icon = "📝" if src == "manual" else "🌐"
                score_label = f"  → {icon} {m['home_score']}-{m['away_score']} [{m['status']}]"

            match_labels[m["match_id"]] = f"{home} vs {away}{grp_label}{score_label}"

        sel_mid = st.selectbox(
            "Partido",
            list(match_labels.keys()),
            format_func=lambda k: match_labels[k],
            key="admin_match_sel",
        )
        sel_m = next(m for m in round_matches if m["match_id"] == sel_mid)

        # Show current result if known
        if sel_m["home_score"] is not None:
            src = overrides.get(sel_mid, {}).get("source", "api")
            src_label = "📝 Manual" if src == "manual" else "🌐 API automática"
            st.info(
                f"Resultado actual ({src_label}): "
                f"**{sel_m['home_team']}** {sel_m['home_score']} – {sel_m['away_score']} "
                f"**{sel_m['away_team']}** [{sel_m['status']}]"
            )

        home_name = sel_m["home_team"] if sel_m["home_team"] != "TBD" else "Local"
        away_name = sel_m["away_team"] if sel_m["away_team"] != "TBD" else "Visitante"
        default_h  = int(sel_m["home_score"]) if sel_m["home_score"] is not None else 0
        default_a  = int(sel_m["away_score"]) if sel_m["away_score"] is not None else 0
        cur_status = sel_m["status"] if sel_m["status"] in _STATUS_OPTS else "FT"

        c1, c2, c3 = st.columns([2, 2, 3])
        with c1:
            new_h = st.number_input(home_name, 0, 20, default_h, key="admin_sim_h")
        with c2:
            new_a = st.number_input(away_name, 0, 20, default_a, key="admin_sim_a")
        with c3:
            new_status = st.selectbox(
                "Estado", _STATUS_OPTS,
                index=_STATUS_OPTS.index(cur_status),
                key="admin_sim_status",
            )

        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("✅ Guardar resultado", key="admin_sim_apply", use_container_width=True):
                set_match_result(sel_mid, int(new_h), int(new_a), new_status, source="manual")
                st.success(f"✅ {home_name} {new_h}–{new_a} {away_name} ({new_status})")
                st.rerun()
        with bc2:
            if sel_mid in overrides and overrides[sel_mid].get("source", "manual") == "manual":
                if st.button("🗑️ Borrar resultado manual", key="admin_sim_clear", use_container_width=True):
                    clear_match_result(sel_mid)
                    st.info("Resultado manual eliminado. La API tomará el control.")
                    st.rerun()

    # ── Active results summary ──
    st.markdown("---")
    overrides = get_match_results()
    manual    = {mid: ov for mid, ov in overrides.items() if ov.get("source", "manual") == "manual"}
    api_count = sum(1 for ov in overrides.values() if ov.get("source") == "api")

    col1, col2 = st.columns(2)
    col1.metric("📝 Resultados manuales", len(manual))
    col2.metric("🌐 Sincronizados de API", api_count)

    if manual:
        st.markdown("**Resultados ingresados manualmente:**")
        match_map = {m["match_id"]: m for m in matches}
        for mid, ov in manual.items():
            m    = match_map.get(mid, {})
            home = m.get("home_team", mid)
            away = m.get("away_team", "")
            rnd  = m.get("round", "")
            st.markdown(
                f"- **{home}** {ov['home_score']}–{ov['away_score']} **{away}** "
                f"[{ov['status']}]  ·  *{rnd}*"
            )
        if st.button("🗑️ Borrar todos los resultados manuales", key="clear_manual_all"):
            for mid in list(manual.keys()):
                clear_match_result(mid)
            st.rerun()

    if overrides:
        st.markdown("<br>", unsafe_allow_html=True)
        if st.button("🗑️ Borrar TODOS los resultados (manuales + API cache)", key="clear_all_results"):
            clear_all_results()
            st.rerun()


# ── Main app ──────────────────────────────────────────────────────────────

def show_app():
    user = st.session_state["user"]

    raw_matches = get_matches()

    # Auto-persist real API results so they survive restarts / API outages
    api_data = fetch_api_matches()
    if api_data:
        sync_api_results(api_data)

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

    is_admin = user["username"].lower() == "vic73"

    tab_labels = ["🏆  Pronósticos", "📊  Grupos", "🥇  Clasificación", "📈  Estadísticas"]
    if is_admin:
        tab_labels.append("⚙️  Admin")
    tabs = st.tabs(tab_labels)
    t_pred, t_groups, t_lb, t_stats = tabs[0], tabs[1], tabs[2], tabs[3]
    t_admin = tabs[4] if is_admin else None

    with t_pred:
        show_predictions(user, matches, live_ids)
    with t_groups:
        show_group_standings(matches)
    with t_lb:
        show_leaderboard(matches, live_ids)
    with t_stats:
        show_estadisticas(matches)
    if is_admin:
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
