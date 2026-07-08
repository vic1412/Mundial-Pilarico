from __future__ import annotations

import requests
import streamlit as st

# ---------------------------------------------------------------------------
# Special flags (subdivision flags — England, Scotland, Wales)
# ---------------------------------------------------------------------------

# flagcdn.com codes for subdivision flags (not sovereign states)
_SUBDIV_CODES: dict[str, str] = {
    "England":    "gb-eng",
    "Inglaterra": "gb-eng",
    "Scotland":   "gb-sct",
    "Escocia":    "gb-sct",
    "Wales":      "gb-wls",
    "Gales":      "gb-wls",
}

COUNTRY_CODES: dict[str, str] = {
    # Group A
    "México": "MX", "Mexico": "MX",
    "Sudáfrica": "ZA", "South Africa": "ZA",
    "Corea del Sur": "KR", "South Korea": "KR", "Korea Republic": "KR",
    "Chequia": "CZ", "Czech Republic": "CZ", "Czechia": "CZ",
    # Group B
    "Canadá": "CA", "Canada": "CA",
    "Bosnia y Herzegovina": "BA", "Bosnia-Herzegovina": "BA", "Bosnia and Herzegovina": "BA",
    "Catar": "QA", "Qatar": "QA",
    "Suiza": "CH", "Switzerland": "CH",
    # Group C
    "Brasil": "BR", "Brazil": "BR",
    "Marruecos": "MA", "Morocco": "MA",
    "Haití": "HT", "Haiti": "HT",
    # Group D
    "USA": "US", "Estados Unidos": "US", "United States": "US",
    "Paraguay": "PY",
    "Australia": "AU",
    "Turquía": "TR", "Turkey": "TR", "Turkiye": "TR",
    # Group E
    "Alemania": "DE", "Germany": "DE",
    "Curaçao": "CW", "Curacao": "CW",
    "Costa de Marfil": "CI", "Ivory Coast": "CI", "Côte d'Ivoire": "CI",
    "Ecuador": "EC",
    # Group F
    "Países Bajos": "NL", "Netherlands": "NL",
    "Japón": "JP", "Japan": "JP",
    "Suecia": "SE", "Sweden": "SE",
    "Túnez": "TN", "Tunisia": "TN",
    # Group G
    "Bélgica": "BE", "Belgium": "BE",
    "Irán": "IR", "Iran": "IR", "IR Iran": "IR",
    "Egipto": "EG", "Egypt": "EG",
    "Nueva Zelanda": "NZ", "New Zealand": "NZ",
    # Group H
    "España": "ES", "Spain": "ES",
    "Uruguay": "UY",
    "Arabia Saudí": "SA", "Saudi Arabia": "SA",
    "Cabo Verde": "CV", "Cape Verde": "CV", "Cabo Verde": "CV",
    # Group I
    "Francia": "FR", "France": "FR",
    "Senegal": "SN",
    "Noruega": "NO", "Norway": "NO",
    "Irak": "IQ", "Iraq": "IQ",
    # Group J
    "Argentina": "AR",
    "Austria": "AT",
    "Argelia": "DZ", "Algeria": "DZ",
    "Jordania": "JO", "Jordan": "JO",
    # Group K
    "Portugal": "PT",
    "Colombia": "CO",
    "Uzbekistán": "UZ", "Uzbekistan": "UZ",
    "Rep. Dem. Congo": "CD", "DR Congo": "CD", "Congo DR": "CD",
    # Group L
    "Croacia": "HR", "Croatia": "HR",
    "Panamá": "PA", "Panama": "PA",
    "Ghana": "GH",
    # Legacy / extra
    "Venezuela": "VE", "Bolivia": "BO", "Chile": "CL", "Perú": "PE",
    "Honduras": "HN", "Costa Rica": "CR", "Jamaica": "JM",
    "El Salvador": "SV", "Serbia": "RS", "Polonia": "PL", "Poland": "PL",
    "Dinamarca": "DK", "Denmark": "DK", "Nigeria": "NG",
    "Camerún": "CM", "Cameroon": "CM", "Arabia Saudí": "SA",
}


def get_flag(country: str) -> str:
    """Returns an <img> flag from flagcdn.com — renders identically on all devices/browsers."""
    subdiv = _SUBDIV_CODES.get(country)
    if subdiv:
        code = subdiv
    else:
        iso = COUNTRY_CODES.get(country, "")
        if not iso:
            return "🏳"
        code = iso.lower()
    return (
        f'<img src="https://flagcdn.com/20x15/{code}.png" '
        f'style="height:15px;width:auto;vertical-align:middle;margin-bottom:1px" '
        f'loading="lazy">'
    )


# ---------------------------------------------------------------------------
# Real 2026 FIFA World Cup groups  (draw: December 5, 2024)
# ---------------------------------------------------------------------------

GROUPS: dict[str, list[str]] = {
    "A": ["México",         "Corea del Sur",       "Sudáfrica",          "Chequia"],
    "B": ["Canadá",         "Suiza",               "Catar",              "Bosnia y Herzegovina"],
    "C": ["Brasil",         "Marruecos",           "Escocia",            "Haití"],
    "D": ["USA",            "Paraguay",            "Australia",          "Turquía"],
    "E": ["Alemania",       "Ecuador",             "Costa de Marfil",    "Curaçao"],
    "F": ["Países Bajos",   "Japón",               "Túnez",              "Suecia"],
    "G": ["Bélgica",        "Irán",                "Egipto",             "Nueva Zelanda"],
    "H": ["España",         "Uruguay",             "Arabia Saudí",       "Cabo Verde"],
    "I": ["Francia",        "Senegal",             "Noruega",            "Irak"],
    "J": ["Argentina",      "Austria",             "Argelia",            "Jordania"],
    "K": ["Portugal",       "Colombia",            "Uzbekistán",         "Rep. Dem. Congo"],
    "L": ["Inglaterra",     "Croacia",             "Panamá",             "Ghana"],
}

# ---------------------------------------------------------------------------
# Complete official 2026 World Cup schedule
# Group stage: all 72 matches with exact dates
# ---------------------------------------------------------------------------

# (group_letter, match_id_suffix, home_team, away_team, date)
_GROUP_SCHEDULE = [
    # ── Group A ──────────────────────────────────────────────────────────
    ("A","MD1-1","México",              "Sudáfrica",           "2026-06-11"),
    ("A","MD1-2","Corea del Sur",       "Chequia",             "2026-06-11"),
    ("A","MD2-1","Chequia",             "Sudáfrica",           "2026-06-18"),
    ("A","MD2-2","México",              "Corea del Sur",       "2026-06-18"),
    ("A","MD3-1","Chequia",             "México",              "2026-06-24"),
    ("A","MD3-2","Sudáfrica",           "Corea del Sur",       "2026-06-24"),
    # ── Group B ──────────────────────────────────────────────────────────
    ("B","MD1-1","Canadá",              "Bosnia y Herzegovina","2026-06-12"),
    ("B","MD1-2","Catar",               "Suiza",               "2026-06-13"),
    ("B","MD2-1","Suiza",               "Bosnia y Herzegovina","2026-06-18"),
    ("B","MD2-2","Canadá",              "Catar",               "2026-06-18"),
    ("B","MD3-1","Suiza",               "Canadá",              "2026-06-24"),
    ("B","MD3-2","Bosnia y Herzegovina","Catar",               "2026-06-24"),
    # ── Group C ──────────────────────────────────────────────────────────
    ("C","MD1-1","Brasil",              "Marruecos",           "2026-06-13"),
    ("C","MD1-2","Haití",               "Escocia",             "2026-06-13"),
    ("C","MD2-1","Escocia",             "Marruecos",           "2026-06-19"),
    ("C","MD2-2","Brasil",              "Haití",               "2026-06-19"),
    ("C","MD3-1","Escocia",             "Brasil",              "2026-06-24"),
    ("C","MD3-2","Marruecos",           "Haití",               "2026-06-24"),
    # ── Group D ──────────────────────────────────────────────────────────
    ("D","MD1-1","USA",                 "Paraguay",            "2026-06-12"),
    ("D","MD1-2","Australia",           "Turquía",             "2026-06-13"),
    ("D","MD2-1","USA",                 "Australia",           "2026-06-19"),
    ("D","MD2-2","Turquía",             "Paraguay",            "2026-06-19"),
    ("D","MD3-1","Turquía",             "USA",                 "2026-06-25"),
    ("D","MD3-2","Paraguay",            "Australia",           "2026-06-25"),
    # ── Group E ──────────────────────────────────────────────────────────
    ("E","MD1-1","Alemania",            "Curaçao",             "2026-06-14"),
    ("E","MD1-2","Costa de Marfil",     "Ecuador",             "2026-06-14"),
    ("E","MD2-1","Alemania",            "Costa de Marfil",     "2026-06-20"),
    ("E","MD2-2","Ecuador",             "Curaçao",             "2026-06-20"),
    ("E","MD3-1","Ecuador",             "Alemania",            "2026-06-25"),
    ("E","MD3-2","Curaçao",             "Costa de Marfil",     "2026-06-25"),
    # ── Group F ──────────────────────────────────────────────────────────
    ("F","MD1-1","Países Bajos",        "Japón",               "2026-06-14"),
    ("F","MD1-2","Suecia",              "Túnez",               "2026-06-14"),
    ("F","MD2-1","Países Bajos",        "Suecia",              "2026-06-20"),
    ("F","MD2-2","Túnez",               "Japón",               "2026-06-20"),
    ("F","MD3-1","Japón",               "Suecia",              "2026-06-25"),
    ("F","MD3-2","Túnez",               "Países Bajos",        "2026-06-25"),
    # ── Group G ──────────────────────────────────────────────────────────
    ("G","MD1-1","Bélgica",             "Egipto",              "2026-06-15"),
    ("G","MD1-2","Irán",                "Nueva Zelanda",       "2026-06-15"),
    ("G","MD2-1","Bélgica",             "Irán",                "2026-06-21"),
    ("G","MD2-2","Nueva Zelanda",       "Egipto",              "2026-06-21"),
    ("G","MD3-1","Egipto",              "Irán",                "2026-06-26"),
    ("G","MD3-2","Nueva Zelanda",       "Bélgica",             "2026-06-26"),
    # ── Group H ──────────────────────────────────────────────────────────
    ("H","MD1-1","España",              "Cabo Verde",          "2026-06-15"),
    ("H","MD1-2","Arabia Saudí",        "Uruguay",             "2026-06-15"),
    ("H","MD2-1","España",              "Arabia Saudí",        "2026-06-21"),
    ("H","MD2-2","Uruguay",             "Cabo Verde",          "2026-06-21"),
    ("H","MD3-1","Cabo Verde",          "Arabia Saudí",        "2026-06-26"),
    ("H","MD3-2","Uruguay",             "España",              "2026-06-26"),
    # ── Group I ──────────────────────────────────────────────────────────
    ("I","MD1-1","Francia",             "Senegal",             "2026-06-16"),
    ("I","MD1-2","Irak",                "Noruega",             "2026-06-16"),
    ("I","MD2-1","Francia",             "Irak",                "2026-06-22"),
    ("I","MD2-2","Noruega",             "Senegal",             "2026-06-22"),
    ("I","MD3-1","Noruega",             "Francia",             "2026-06-26"),
    ("I","MD3-2","Senegal",             "Irak",                "2026-06-26"),
    # ── Group J ──────────────────────────────────────────────────────────
    ("J","MD1-1","Argentina",           "Argelia",             "2026-06-16"),
    ("J","MD1-2","Austria",             "Jordania",            "2026-06-16"),
    ("J","MD2-1","Argentina",           "Austria",             "2026-06-22"),
    ("J","MD2-2","Jordania",            "Argelia",             "2026-06-22"),
    ("J","MD3-1","Argelia",             "Austria",             "2026-06-27"),
    ("J","MD3-2","Jordania",            "Argentina",           "2026-06-27"),
    # ── Group K ──────────────────────────────────────────────────────────
    ("K","MD1-1","Portugal",            "Rep. Dem. Congo",     "2026-06-17"),
    ("K","MD1-2","Uzbekistán",          "Colombia",            "2026-06-17"),
    ("K","MD2-1","Portugal",            "Uzbekistán",          "2026-06-23"),
    ("K","MD2-2","Colombia",            "Rep. Dem. Congo",     "2026-06-23"),
    ("K","MD3-1","Colombia",            "Portugal",            "2026-06-27"),
    ("K","MD3-2","Rep. Dem. Congo",     "Uzbekistán",          "2026-06-27"),
    # ── Group L ──────────────────────────────────────────────────────────
    ("L","MD1-1","Inglaterra",          "Croacia",             "2026-06-17"),
    ("L","MD1-2","Ghana",               "Panamá",              "2026-06-17"),
    ("L","MD2-1","Inglaterra",          "Ghana",               "2026-06-23"),
    ("L","MD2-2","Panamá",              "Croacia",             "2026-06-23"),
    ("L","MD3-1","Panamá",              "Inglaterra",          "2026-06-27"),
    ("L","MD3-2","Croacia",             "Ghana",               "2026-06-27"),
]

# Round map: MD1-x → Jornada 1, MD2-x → Jornada 2, MD3-x → Jornada 3
_MD_ROUND = {"MD1": "Jornada 1", "MD2": "Jornada 2", "MD3": "Jornada 3"}

# ---------------------------------------------------------------------------
# API-Football name → app name (Spanish) mapping
# Covers every variant the API might return for the 48 WC teams
# ---------------------------------------------------------------------------
API_NAME_MAP: dict[str, str] = {
    # Group A
    "Mexico":                  "México",
    "South Africa":            "Sudáfrica",
    "Korea Republic":          "Corea del Sur",
    "South Korea":             "Corea del Sur",
    "Czech Republic":          "Chequia",
    "Czechia":                 "Chequia",
    # Group B
    "Canada":                  "Canadá",
    "Qatar":                   "Catar",
    "Switzerland":             "Suiza",
    "Bosnia-Herzegovina":      "Bosnia y Herzegovina",
    "Bosnia and Herzegovina":  "Bosnia y Herzegovina",
    "Bosnia":                  "Bosnia y Herzegovina",
    # Group C
    "Brazil":                  "Brasil",
    "Morocco":                 "Marruecos",
    "Scotland":                "Escocia",
    "Haiti":                   "Haití",
    # Group D
    "United States":           "USA",
    "Turkey":                  "Turquía",
    "Turkiye":                 "Turquía",
    # Group E
    "Germany":                 "Alemania",
    "Curacao":                 "Curaçao",
    "Ivory Coast":             "Costa de Marfil",
    "Côte d'Ivoire":           "Costa de Marfil",
    "Cote d'Ivoire":           "Costa de Marfil",
    # Group F
    "Netherlands":             "Países Bajos",
    "Japan":                   "Japón",
    "Sweden":                  "Suecia",
    "Tunisia":                 "Túnez",
    # Group G
    "Belgium":                 "Bélgica",
    "Iran":                    "Irán",
    "IR Iran":                 "Irán",
    "Egypt":                   "Egipto",
    "New Zealand":             "Nueva Zelanda",
    # Group H
    "Spain":                   "España",
    "Saudi Arabia":            "Arabia Saudí",
    "Cape Verde":              "Cabo Verde",
    # Group I
    "France":                  "Francia",
    "Norway":                  "Noruega",
    "Iraq":                    "Irak",
    # Group J
    "Algeria":                 "Argelia",
    "Jordan":                  "Jordania",
    # Group K
    "Uzbekistan":              "Uzbekistán",
    "DR Congo":                "Rep. Dem. Congo",
    "Congo DR":                "Rep. Dem. Congo",
    "Democratic Republic of Congo": "Rep. Dem. Congo",
    # Group L
    "England":                 "Inglaterra",
    "Croatia":                 "Croacia",
    "Panama":                  "Panamá",
}

# Round labels as API-Football sends them → app labels
_API_ROUND_MAP: dict[str, str] = {
    "Group Stage - 1": "Jornada 1",
    "Group Stage - 2": "Jornada 2",
    "Group Stage - 3": "Jornada 3",
    "Round of 32":     "Dieciseisavos",
    "Round of 16":     "Octavos",
    "Quarter-finals":  "Cuartos de Final",
    "Semi-finals":     "Semifinal",
    "3rd Place Final": "Final",
    "Final":           "Final",
}
_API_GROUP_MAP: dict[str, str] = {f"Group {l}": f"Grupo {l}" for l in "ABCDEFGHIJKL"}

# Reverse lookup: (home_es, away_es) → local match_id   e.g. ("Corea del Sur","Chequia") → "GS-A-MD1-2"
_SCHEDULE_LOOKUP: dict[tuple, str] = {
    (home, away): f"GS-{letter}-{suffix}"
    for letter, suffix, home, away, _date in _GROUP_SCHEDULE
}
# Also index by (away, home) so we can detect swapped fixtures (shouldn't happen, but defensive)
_SCHEDULE_LOOKUP_INV: dict[tuple, str] = {
    (away, home): f"GS-{letter}-{suffix}"
    for letter, suffix, home, away, _date in _GROUP_SCHEDULE
}

# Dieciseisavos de final — equipos confirmados (fuente: FIFA / Al Jazeera, 28-Jun-2026)
# (home, away, date)
_R32_MATCHES = [
    ("Sudáfrica",        "Canadá",              "2026-06-28"),  # R32-01
    ("Brasil",           "Japón",               "2026-06-29"),  # R32-02
    ("Alemania",         "Paraguay",            "2026-06-29"),  # R32-03
    ("Países Bajos",     "Marruecos",           "2026-06-29"),  # R32-04
    ("Costa de Marfil",  "Noruega",             "2026-06-30"),  # R32-05
    ("Francia",          "Suecia",              "2026-06-30"),  # R32-06
    ("México",           "Ecuador",             "2026-06-30"),  # R32-07
    ("Inglaterra",       "Rep. Dem. Congo",     "2026-07-01"),  # R32-08
    ("Bélgica",          "Senegal",             "2026-07-01"),  # R32-09
    ("USA",              "Bosnia y Herzegovina","2026-07-01"),  # R32-10
    ("España",           "Austria",             "2026-07-02"),  # R32-11
    ("Portugal",         "Croacia",             "2026-07-02"),  # R32-12
    ("Suiza",            "Argelia",             "2026-07-02"),  # R32-13
    ("Australia",        "Egipto",              "2026-07-03"),  # R32-14
    ("Argentina",        "Cabo Verde",          "2026-07-03"),  # R32-15
    ("Colombia",         "Ghana",               "2026-07-03"),  # R32-16
]
# Lookup (home, away) → local match ID for knockout stage (so API fixtures map correctly)
_KNOCKOUT_LOOKUP: dict[tuple, str] = {
    (home, away): f"R32-{i+1:02d}"
    for i, (home, away, _date) in enumerate(_R32_MATCHES)
}
_KNOCKOUT_LOOKUP_INV: dict[tuple, str] = {
    (away, home): f"R32-{i+1:02d}"
    for i, (home, away, _date) in enumerate(_R32_MATCHES)
}

# Octavos de final — equipos confirmados (fuente: FIFA/ESPN/Al Jazeera, 3-Jul-2026)
_R16_MATCHES = [
    ("Canadá",    "Marruecos",  "2026-07-04"),  # R16-01
    ("Paraguay",  "Francia",    "2026-07-04"),  # R16-02
    ("Brasil",    "Noruega",    "2026-07-05"),  # R16-03
    ("México",    "Inglaterra", "2026-07-05"),  # R16-04
    ("España",    "Portugal",   "2026-07-06"),  # R16-05
    ("Bélgica",   "USA",        "2026-07-06"),  # R16-06
    ("Egipto",    "Argentina",  "2026-07-07"),  # R16-07
    ("Suiza",     "Colombia",   "2026-07-07"),  # R16-08
]
_R16_LOOKUP: dict[tuple, str] = {
    (home, away): f"R16-{i+1:02d}"
    for i, (home, away, _date) in enumerate(_R16_MATCHES)
}
_R16_LOOKUP_INV: dict[tuple, str] = {
    (away, home): f"R16-{i+1:02d}"
    for i, (home, away, _date) in enumerate(_R16_MATCHES)
}

_QF_DATES  = ["2026-07-09","2026-07-10","2026-07-11","2026-07-11"]


def _m(mid, rnd, grp, home, away, date):
    return {
        "match_id": mid, "round": rnd, "group": grp,
        "home_team": home, "away_team": away,
        "match_date": date, "status": "NS",
        "home_score": None, "away_score": None, "minute": None,
    }


def _generate_group_matches() -> list:
    matches = []
    for letter, suffix, home, away, date in _GROUP_SCHEDULE:
        md_key = suffix[:3]                          # "MD1", "MD2", "MD3"
        rnd    = _MD_ROUND[md_key]
        grp    = f"Grupo {letter}"
        mid    = f"GS-{letter}-{suffix}"
        matches.append(_m(mid, rnd, grp, home, away, date))
    return matches


def _generate_knockout_matches() -> list:
    matches = []
    for i, (home, away, date) in enumerate(_R32_MATCHES):
        matches.append(_m(f"R32-{i+1:02d}", "Dieciseisavos", "Dieciseisavos",
                          home, away, date))
    for i, (home, away, date) in enumerate(_R16_MATCHES):
        matches.append(_m(f"R16-{i+1:02d}", "Octavos", "Octavos",
                          home, away, date))
    for i, date in enumerate(_QF_DATES):
        matches.append(_m(f"QF-{i+1:02d}", "Cuartos de Final", "Cuartos de Final",
                          "TBD", "TBD", date))
    matches.append(_m("SF-01", "Semifinal",    "Semifinal",    "TBD","TBD","2026-07-14"))
    matches.append(_m("SF-02", "Semifinal",    "Semifinal",    "TBD","TBD","2026-07-15"))
    matches.append(_m("TP-01", "Final",        "Tercer Puesto","TBD","TBD","2026-07-18"))
    matches.append(_m("F-01",  "Final",        "Gran Final",   "TBD","TBD","2026-07-19"))
    return matches


def get_mock_matches() -> list:
    return _generate_group_matches() + _generate_knockout_matches()


# ---------------------------------------------------------------------------
# Bracket propagation
# ---------------------------------------------------------------------------

STATUS_DONE = {"FT", "AET", "PEN"}
STATUS_LIVE = {"1H", "2H", "HT", "ET", "BT", "P", "INT"}

# Maps each future match → (home_source, away_source)
# Each source is (role: "winner"/"loser", match_id)
_BRACKET: dict[str, tuple] = {
    "QF-01": (("winner", "R16-01"), ("winner", "R16-02")),
    "QF-02": (("winner", "R16-03"), ("winner", "R16-04")),
    "QF-03": (("winner", "R16-05"), ("winner", "R16-06")),
    "QF-04": (("winner", "R16-07"), ("winner", "R16-08")),
    "SF-01": (("winner", "QF-01"),  ("winner", "QF-02")),
    "SF-02": (("winner", "QF-03"),  ("winner", "QF-04")),
    "TP-01": (("loser",  "SF-01"),  ("loser",  "SF-02")),
    "F-01":  (("winner", "SF-01"),  ("winner", "SF-02")),
}

_ROUND_SHORT = {"R16": "Oct", "QF": "Ctos", "SF": "Semi"}


def _bracket_label(role: str, src_id: str) -> str:
    prefix, num = src_id.split("-")
    rnd = _ROUND_SHORT.get(prefix, prefix)
    role_es = "G." if role == "winner" else "Sub."
    return f"{role_es} {rnd} {int(num)}"


def _get_outcome(match: dict) -> tuple[str | None, str | None]:
    """Return (winner, loser) for a finished match, or (None, None) if undecided."""
    if match.get("status") not in STATUS_DONE:
        return None, None
    hs = match.get("home_score")
    as_ = match.get("away_score")
    if hs is None or as_ is None:
        return None, None
    home, away = match["home_team"], match["away_team"]
    if hs > as_:
        return home, away
    if as_ > hs:
        return away, home
    # Tied: check penalty_winner (set manually by admin; penalty goals don't count in stats)
    pw = match.get("penalty_winner")
    if pw == "home":
        return home, away
    if pw == "away":
        return away, home
    return None, None


def resolve_bracket(matches: list) -> list:
    """Replace TBD placeholders in knockout rounds with actual team names.

    Processes rounds in dependency order (R16→QF→SF→F) so cascading works.
    Adds 'bracket_home'/'bracket_away' labels on still-undecided slots.
    """
    result = [m.copy() for m in matches]
    by_id = {m["match_id"]: m for m in result}

    for match_id, ((role_h, src_h), (role_a, src_a)) in _BRACKET.items():
        target = by_id.get(match_id)
        if not target:
            continue

        for side, role, src_id, label_key in (
            ("home_team", role_h, src_h, "bracket_home"),
            ("away_team", role_a, src_a, "bracket_away"),
        ):
            if target[side] != "TBD":
                continue
            target[label_key] = _bracket_label(role, src_id)
            src_m = by_id.get(src_id)
            if not src_m:
                continue
            winner, loser = _get_outcome(src_m)
            name = winner if role == "winner" else loser
            if name:
                target[side] = name
                target.pop(label_key, None)

    return result


def get_group_standings(matches: list) -> dict:
    """Returns {group_label: [(team, stats_dict), ...]} sorted by Pts/GD/GF."""
    table: dict[str, dict[str, dict]] = {}

    # Pre-populate with all group teams (so teams with 0 games appear)
    for letter, teams in GROUPS.items():
        grp = f"Grupo {letter}"
        table[grp] = {t: {"P": 0, "G": 0, "E": 0, "P_": 0,
                           "GF": 0, "GC": 0, "DG": 0, "Pts": 0}
                      for t in teams}

    for m in matches:
        grp = m.get("group", "")
        if not grp.startswith("Grupo "):
            continue
        if m["status"] not in STATUS_DONE | STATUS_LIVE:
            continue
        if m["home_score"] is None or m["away_score"] is None:
            continue

        h, a  = m["home_team"], m["away_team"]
        hs, as_ = m["home_score"], m["away_score"]

        if grp not in table:
            table[grp] = {}
        for t in (h, a):
            if t not in table[grp]:
                table[grp][t] = {"P": 0, "G": 0, "E": 0, "P_": 0,
                                  "GF": 0, "GC": 0, "DG": 0, "Pts": 0}

        s_h = table[grp][h]; s_a = table[grp][a]
        s_h["P"] += 1; s_a["P"] += 1
        s_h["GF"] += hs; s_h["GC"] += as_
        s_a["GF"] += as_; s_a["GC"] += hs

        if hs > as_:
            s_h["G"] += 1; s_h["Pts"] += 3; s_a["P_"] += 1
        elif as_ > hs:
            s_a["G"] += 1; s_a["Pts"] += 3; s_h["P_"] += 1
        else:
            s_h["E"] += 1; s_h["Pts"] += 1
            s_a["E"] += 1; s_a["Pts"] += 1

    # Compute GD and sort
    result = {}
    for grp, teams in table.items():
        for s in teams.values():
            s["DG"] = s["GF"] - s["GC"]
        result[grp] = sorted(
            teams.items(),
            key=lambda x: (-x[1]["Pts"], -x[1]["DG"], -x[1]["GF"], x[0])
        )
    return result


# ---------------------------------------------------------------------------
# API-Football integration
# ---------------------------------------------------------------------------

WC_LEAGUE_ID = 1
WC_SEASON    = 2026

_DEFAULT_URL = "https://v3.football.api-sports.io"


def _api_config() -> tuple[str, str]:
    """Returns (api_key, base_url) from Streamlit secrets."""
    try:
        key = st.secrets.get("API_FOOTBALL_KEY", "")
        url = st.secrets.get("API_FOOTBALL_URL", _DEFAULT_URL).rstrip("/")
        return key, url
    except Exception:
        return "", _DEFAULT_URL


def _build_headers(key: str, url: str) -> dict:
    """
    API-Football has two auth methods depending on where you signed up:
      • api-sports.io  (direct) → header: x-apisports-key
      • rapidapi.com   (marketplace) → headers: x-rapidapi-key + x-rapidapi-host
    We detect which one from the URL.
    """
    if "rapidapi" in url:
        host = url.replace("https://", "").replace("http://", "").split("/")[0]
        return {"x-rapidapi-key": key, "x-rapidapi-host": host}
    else:
        return {"x-apisports-key": key}


@st.cache_data(ttl=120)
def fetch_api_matches():
    key, url = _api_config()
    if not key:
        return None
    try:
        r = requests.get(
            f"{url}/fixtures",
            headers=_build_headers(key, url),
            params={"league": WC_LEAGUE_ID, "season": WC_SEASON},
            timeout=10,
        )
        if r.status_code != 200:
            return None
        data = r.json().get("response", [])
        return [_parse_fixture(f) for f in data] if data else None
    except Exception:
        return None


@st.cache_data(ttl=30)
def fetch_live_ids() -> set:
    key, url = _api_config()
    if not key:
        return set()
    try:
        r = requests.get(
            f"{url}/fixtures",
            headers=_build_headers(key, url),
            params={"league": WC_LEAGUE_ID, "season": WC_SEASON, "live": "all"},
            timeout=10,
        )
        if r.status_code == 200:
            return {str(f["fixture"]["id"]) for f in r.json().get("response", [])}
    except Exception:
        pass
    return set()


def _parse_fixture(f: dict) -> dict:
    fix    = f["fixture"]
    teams  = f["teams"]
    goals  = f["goals"]
    league = f["league"]

    # Normalize team names to Spanish app names
    home_raw = teams["home"]["name"]
    away_raw = teams["away"]["name"]
    home = API_NAME_MAP.get(home_raw, home_raw)
    away = API_NAME_MAP.get(away_raw, away_raw)

    # Resolve local match_id: group stage first, then knockout, then fall back to API id
    local_id = (
        _SCHEDULE_LOOKUP.get((home, away))
        or _SCHEDULE_LOOKUP_INV.get((home, away))
        or _KNOCKOUT_LOOKUP.get((home, away))
        or _KNOCKOUT_LOOKUP_INV.get((home, away))
        or _R16_LOOKUP.get((home, away))
        or _R16_LOOKUP_INV.get((home, away))
    )
    match_id = local_id if local_id else str(fix["id"])

    # Normalize round and group labels
    api_round = league.get("round", "")
    rnd   = _API_ROUND_MAP.get(api_round, api_round)
    group = _API_GROUP_MAP.get(api_round, api_round)   # "Group A" → "Grupo A"
    if not group.startswith("Grupo ") and local_id:
        # Derive group from the local match_id (e.g. "GS-A-MD1-2" → "Grupo A")
        parts = local_id.split("-")
        group = f"Grupo {parts[1]}" if len(parts) >= 2 else group

    return {
        "match_id":   match_id,
        "round":      rnd,
        "group":      group,
        "home_team":  home,
        "away_team":  away,
        "match_date": (fix["date"] or "")[:10],
        "status":     fix["status"]["short"],
        "home_score": goals["home"],
        "away_score": goals["away"],
        "minute":     fix["status"].get("elapsed"),
    }


def get_matches() -> list:
    """Mock is always the canonical fixture list (teams, IDs, dates).
    API data only overlays live status/scores onto matching match IDs."""
    mock = get_mock_matches()
    api  = fetch_api_matches()
    if not api:
        return mock
    api_by_id = {m["match_id"]: m for m in api}
    result = []
    for m in mock:
        mc = m.copy()
        a  = api_by_id.get(m["match_id"])
        if a:
            mc["status"]     = a["status"]
            mc["home_score"] = a["home_score"]
            mc["away_score"] = a["away_score"]
            mc["minute"]     = a["minute"]
        result.append(mc)
    return result


def get_live_ids() -> set:
    return fetch_live_ids()


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def calculate_points(ph, pa, ah, aa):
    """4=exact · 3=winner+GD · 2=winner or draw · 0=wrong · None=not played"""
    if ah is None or aa is None:
        return None
    if ph is None or pa is None:
        return 0
    if ph == ah and pa == aa:
        return 4
    pd = ph - pa; ad = ah - aa
    ps = (pd > 0) - (pd < 0); as_ = (ad > 0) - (ad < 0)
    if ps == as_:
        if ps == 0:
            return 2
        return 3 if pd == ad else 2
    return 0
