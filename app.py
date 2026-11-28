import streamlit as st
import requests
import statistics
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import time

# ============================================================
# OLDAL
# ============================================================
st.set_page_config(page_title="⚽ Napi Foci Tipp – Modell", page_icon="⚽", layout="wide")
st.title("⚽ Napi Foci Tipp – Modellalapú")
st.caption("Poisson + piaci odds kombináció. Csak akkor tippel, ha mindkét modell egyetért.")

# ============================================================
# KONFIG
# ============================================================
TOP_KUSZOB      = 0.82
FIGYELO_KUSZOB  = 0.75
MIN_IRODAK      = 3
MIN_ODDS        = 1.08
MAX_ODDS        = 1.60
MAX_ODDS_SPREAD = 0.50
MAX_FAVORIT     = 2.20
KELLY_FRAKCIO   = 0.25
BANKROLL        = 10000

# Piaci vs. statisztikai súly (összeg = 1.0)
W_PIAC = 0.55
W_STAT = 0.45

# Poisson: hány meccsből számoljon erősséget
POISSON_MECCS_SZAM = 30
# minimum különbség a két modell között (kiszámíthatóság)
MIN_EGYEZES = 0.20   # 5 százalékpont

LIGAK = [
    "soccer_epl",
    "soccer_spain_la_liga",
    "soccer_italy_serie_a",
    "soccer_germany_bundesliga",
    "soccer_france_ligue_one",
]

# football-data.org liga kódok (ingyenes csomag)
FD_LIGAK = {
    "soccer_epl": "PL",
    "soccer_spain_la_liga": "PD",
    "soccer_italy_serie_a": "SA",
    "soccer_germany_bundesliga": "BL1",
    "soccer_france_ligue_one": "FL1",
}

TZ = ZoneInfo("Europe/Budapest")

# ============================================================
# KULCSOK
# ============================================================
try:
    ODDS_KEY = st.secrets["ODDS_API_KEY"]
except Exception:
    st.error("❌ ODDS_API_KEY hiányzik a secrets-ből.")
    st.stop()

try:
    FD_KEY = st.secrets["FOOTBALL_DATA_KEY"]
except Exception:
    FD_KEY = None
    st.warning("⚠️ FOOTBALL_DATA_KEY hiányzik – a Poisson-modell kimarad, csak piaci mód.")

# ============================================================
# API – ODDS
# ============================================================
@st.cache_data(ttl=900, show_spinner=False)
def leker_liga(liga: str):
    most = datetime.now(ZoneInfo("UTC"))
    kezdo = most.strftime("%Y-%m-%dT00:00:00Z")
    veg   = (most + timedelta(days=5)).strftime("%Y-%m-%dT23:59:59Z")
    url = (
        f"https://api.the-odds-api.com/v4/sports/{liga}/odds/"
        f"?apiKey={ODDS_KEY}&regions=eu,uk&markets=h2h&oddsFormat=decimal"
        f"&commenceTimeFrom={kezdo}&commenceTimeTo={veg}"
    )
    try:
        r = requests.get(url, timeout=20)
        kvota = r.headers.get("x-requests-remaining", "?")
        if r.status_code == 401:
            st.warning(f"🔑 Rossz odds API kulcs ({liga})."); return [], kvota
        if r.status_code == 429:
            st.warning(f"⏳ Odds API kvóta túllépve ({liga})."); return [], kvota
        r.raise_for_status()
        return r.json(), kvota
    except Exception as e:
        st.warning(f"⚠️ Odds hiba ({liga}): {e}")
        return [], "?"


@st.cache_data(ttl=900, show_spinner=False)
def leker_osszes_odds():
    osszes, kvota = [], "?"
    for liga in LIGAK:
        adat, kvota = leker_liga(liga)
        if isinstance(adat, list):
            osszes.extend(adat)
        time.sleep(0.2)
    return osszes, kvota

# ============================================================
# API – FOOTBALL-DATA (statisztika a Poisson-modellhez)
# ============================================================
@st.cache_data(ttl=3600, show_spinner=False)
def leker_csapat_meccsek(fd_liga: str):
    """Lekéri a liga összes befejezett meccsét az idényben (max 100)."""
    if not FD_KEY:
        return []
    url = f"https://api.football-data.org/v4/competitions/{fd_liga}/matches?status=FINISHED"
    try:
        r = requests.get(url, headers={"X-Auth-Token": FD_KEY}, timeout=20)
        if r.status_code == 403:
            st.warning(f"🔑 Football-data kulcs jogosultság hiba ({fd_liga}).")
            return []
        if r.status_code == 429:
            st.warning(f"⏳ Football-data kvóta túllépve ({fd_liga}).")
            return []
        r.raise_for_status()
        return r.json().get("matches", [])
    except Exception as e:
        st.warning(f"⚠️ Football-data hiba ({fd_liga}): {e}")
        return []


@st.cache_data(ttl=3600, show_spinner=False)
def epit_erősség():
    """
    Minden ligára kiszámolja a csapatok támadó/védekező erősségét.
    Visszaad: {liga_kulcs: {"team_name": (att_erő, def_erő), ...}, "liga_átlag_gól": float}
    """
    ero = {}
    liga_atlag = {}
    for odds_kulcs, fd_kulcs in FD_LIGAK.items():
        meccsek = leker_csapat_meccsek(fd_kulcs)
        if not meccsek:
            continue

        # Csapatonkénti gólok
        golt_rugott = defaultdict(list)
        golt_kapott = defaultdict(list)

        for m in meccsek:
            if m.get("status") != "FINISHED":
                continue
            ft = m.get("score", {}).get("fullTime", {})
            hg, ag = ft.get("home"), ft.get("away")
            if hg is None or ag is None:
                continue
            hazai = m["homeTeam"]["name"]
            vendeg = m["awayTeam"]["name"]
            golt_rugott[hazai].append(hg)
            golt_kapott[hazai].append(ag)
            golt_rugott[vendeg].append(ag)
            golt_kapott[vendeg].append(hg)

        if not golt_rugott:
            continue

        # Ligaátlag (meccsenkénti gól / 2 csapat)
        osszes_gol = sum(sum(v) for v in golt_rugott.values())
        osszes_meccs = len(meccsek)
        if osszes_meccs == 0:
            continue
        liga_meccs_atlag = osszes_gol / osszes_meccs  # egy meccsen összesen
        liga_csapat_atlag = liga_meccs_atlag / 2      # egy csapatra

        liga_atlag[odds_kulcs] = liga_csapat_atlag
        ero[odds_kulcs] = {}

        for csapat in golt_rugott:
            rugott = golt_rugott[csapat]
            kapott = golt_kapott[csapat]
            if len(rugott) < 5:  # túl kevés meccs → kihagyjuk
                continue
            att = (sum(rugott) / len(rugott)) / liga_csapat_atlag if liga_csapat_atlag > 0 else 1.0
            deff = (sum(kapott) / len(kapott)) / liga_csapat_atlag if liga_csapat_atlag > 0 else 1.0
            ero[odds_kulcs][csapat] = (att, deff)

    return ero, liga_atlag

# ============================================================
# POISSON MODELL
# ============================================================
def poisson_pmf(k, lam):
    if lam <= 0:
        return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def poisson_1x2(lambda_h, lambda_v, max_gol=10):
    """Visszaad: (p_hazai, p_dontetlen, p_vendeg, p_1x, p_x2)"""
    p_h = p_d = p_v = 0.0
    for i in range(max_gol + 1):
        for j in range(max_gol + 1):
            p = poisson_pmf(i, lambda_h) * poisson_pmf(j, lambda_v)
            if i > j:
                p_h += p
            elif i == j:
                p_d += p
            else:
                p_v += p
    return p_h, p_d, p_v, p_h + p_d, p_v + p_d


def statisztikai_eselyek(meccs, ero, liga_atlag):
    """
    A meccshez tartozó statisztikai 1X2 és 1X/X2 valószínűségek.
    Ha nincs elég adat → None.
    """
    liga = meccs.get("sport_key")
    if liga not in ero:
        return None
    hazai = meccs.get("home_team")
    vendeg = meccs.get("away_team")
    if hazai not in ero[liga] or vendeg not in ero[liga]:
        return None

    att_h, def_h = ero[liga][hazai]
    att_v, def_v = ero[liga][vendeg]
    atlag = liga_atlag.get(liga)
    if not atlag or atlag <= 0:
        return None

    # Várható gólok (hazai pálya előny ~1.15)
    lambda_h = att_h * def_v * atlag * 1.15
    lambda_v = att_v * def_h * atlag * 0.95

    # Korlátok
    lambda_h = max(0.2, min(lambda_h, 4.0))
    lambda_v = max(0.2, min(lambda_v, 4.0))

    p_h, p_d, p_v, p_1x, p_x2 = poisson_1x2(lambda_h, lambda_v)
    return {
        "p_h": p_h, "p_d": p_d, "p_v": p_v,
        "p_1x": p_1x, "p_x2": p_x2,
        "lambda_h": lambda_h, "lambda_v": lambda_v,
    }

# ============================================================
# PIACI MODELL (medián + margin-eltávolítás)
# ============================================================
def piaci_eselyek(meccs):
    hazai, vendeg, dontetlen = [], [], []
    for iroda in meccs.get("bookmakers", []):
        for market in iroda.get("markets", []):
            if market.get("key") != "h2h":
                continue
            for o in market.get("outcomes", []):
                ar = o.get("price")
                if not isinstance(ar, (int, float)) or ar <= 1.0:
                    continue
                nev = o.get("name")
                if nev == meccs.get("home_team"):
                    hazai.append(ar)
                elif nev == meccs.get("away_team"):
                    vendeg.append(ar)
                elif nev == "Draw":
                    dontetlen.append(ar)

    if (len(hazai) < MIN_IRODAK or len(vendeg) < MIN_IRODAK
            or len(dontetlen) < MIN_IRODAK):
        return None, "keves_iroda"
    if max(hazai) - min(hazai) > MAX_ODDS_SPREAD:
        return None, "nagy_szoras"
    if max(vendeg) - min(vendeg) > MAX_ODDS_SPREAD:
        return None, "nagy_szoras"

    mh = statistics.median(hazai)
    mv = statistics.median(vendeg)
    md = statistics.median(dontetlen)
    if min(mh, mv) > MAX_FAVORIT:
        return None, "nagy_favorit"

    ih, iv, idd = 1/mh, 1/mv, 1/md
    osszeg = ih + iv + idd
    if osszeg <= 0:
        return None, "nincs_odds"

    return {
        "p_h": ih/osszeg, "p_v": iv/osszeg, "p_d": idd/osszeg,
        "p_1x": (ih + idd)/osszeg, "p_x2": (iv + idd)/osszeg,
        "mh": mh, "mv": mv, "md": md,
        "margin": osszeg - 1,
    }, None

# ============================================================
# KOMBINÁLÁS
# ============================================================
def kombinalt_esely(piac, stat):
    """Súlyozott átlag. Ha nincs stat → csak piac."""
    if stat is None:
        return piac, "csak_piac"
    p_1x = W_PIAC * piac["p_1x"] + W_STAT * stat["p_1x"]
    p_x2 = W_PIAC * piac["p_x2"] + W_STAT * stat["p_x2"]
    return {
        "p_1x": p_1x, "p_x2": p_x2,
        "piac_1x": piac["p_1x"], "piac_x2": piac["p_x2"],
        "stat_1x": stat["p_1x"], "stat_x2": stat["p_x2"],
    }, "kombinált"


def egyezik(piac_p, stat_p, kuszob=MIN_EGYEZES):
    """A két modell legalább kuszobnyit egyezzen (mindkettő ugyanarra a tippre)."""
    if stat_p is None:
        return True  # ha nincs stat, elfogadjuk
    return abs(piac_p - stat_p) <= kuszob or (piac_p > 0.5) == (stat_p > 0.5)

# ============================================================
# KELLY
# ============================================================
def kelly_tet(p, odds, bankroll=BANKROLL, frakcio=KELLY_FRAKCIO):
    if odds <= 1.0 or p <= 0 or p >= 1:
        return 0
    b = odds - 1
    f = (p * b - (1 - p)) / b
    return round(bankroll * f * frakcio, 0) if f > 0 else 0

# ============================================================
# IDŐ
# ============================================================
def ido_format(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(TZ).strftime("%m.%d %H:%M")
    except Exception:
        return "?"

# ============================================================
# FŐ FELDOLGOZÁS
# ============================================================
def feldolgoz(meccsek, ero, liga_atlag):
    tippek, figyelo = [], []
    kihagyva = defaultdict(int)
    csak_piac = 0
    kombinált_db = 0

    for m in meccsek:
        piac, hiba = piaci_eselyek(m)
        if piac is None:
            kihagyva[hiba] += 1
            continue

        stat = statisztikai_eselyek(m, ero, liga_atlag)
        komb, mod = kombinalt_esely(piac, stat)
        if mod == "csak_piac":
            csak_piac += 1
        else:
            kombinált_db += 1

        opciok = [
            ("1X", f"{m['home_team']} vagy döntetlen (1X)", komb["p_1x"],
             komb.get("piac_1x"), komb.get("stat_1x")),
            ("X2", f"{m['away_team']} vagy döntetlen (X2)", komb["p_x2"],
             komb.get("piac_x2"), komb.get("stat_x2")),
        ]

        legjobb = None
        for kod, nev, p, p_piac, p_stat in opciok:
            odds = 1 / p if p > 0 else 999
            if not (MIN_ODDS <= odds <= MAX_ODDS):
                continue
            # kiszámíthatóság: a két modell egyezzen
            if not egyezik(p_piac, p_stat):
                kihagyva["modellek_nem_egyeznek"] += 1
                continue
            if legjobb is None or p > legjobb["esely"]:
                legjobb = {
                    "kod": kod, "tip": nev, "esely": p, "odds": odds,
                    "p_piac": p_piac, "p_stat": p_stat,
                    "ev": (p * odds - 1) * 100,
                    "mod": mod,
                }

        if legjobb is None:
            continue

        adat = {
            "meccs": f"{m['home_team']} - {m['away_team']}",
            "liga": m.get("sport_title", m.get("sport_key", "?")),
            "ido": ido_format(m.get("commence_time", "")),
            "margin": piac["margin"],
            "kelly": kelly_tet(legjobb["esely"], legjobb["odds"]),
            **legjobb,
        }

        if legjobb["esely"] >= TOP_KUSZOB:
            tippek.append(adat)
        elif legjobb["esely"] >= FIGYELO_KUSZOB:
            figyelo.append(adat)

    tippek.sort(key=lambda x: (x["esely"], x["ev"]), reverse=True)
    figyelo.sort(key=lambda x: (x["esely"], x["ev"]), reverse=True)
    return tippek, figyelo, kihagyva, csak_piac, kombinált_db

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.header("⚙️ Modell")
    st.write(f"**Piaci súly:** {W_PIAC}")
    st.write(f"**Statisztikai súly:** {W_STAT}")
    st.write(f"**Min. egyezés:** {MIN_EGYEZES*100:.0f}%pont")
    st.write(f"**Poisson meccsek:** {POISSON_MECCS_SZAM}")
    st.divider()
    st.write(f"**Top:** {TOP_KUSZOB*100:.0f}%")
    st.write(f"**Figyelő:** {FIGYELO_KUSZOB*100:.0f}%")
    st.write(f"**Odds:** {MIN_ODDS}–{MAX_ODDS}")
    st.write(f"**Bankroll:** {BANKROLL:,} Ft")
    st.divider()
    if FD_KEY:
        st.success("✅ Poisson-modell aktív")
    else:
        st.warning("⚠️ Csak piaci mód (nincs FOOTBALL_DATA_KEY)")

# ============================================================
# FRISSÍTÉS
# ============================================================
c1, c2 = st.columns([1, 3])
with c1:
    if st.button("🔄 Frissítés", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# ============================================================
# BETÖLTÉS
# ============================================================
with st.spinner("Odds betöltése..."):
    meccsek, kvota = leker_osszes_odds()

with st.spinner("Statisztikai erősség számítása..."):
    ero, liga_atlag = epit_erősség() if FD_KEY else ({}, {})

with c2:
    st.caption(
        f"📡 Odds kvóta: **{kvota}** | "
        f"Meccsek: **{len(meccsek)}** | "
        f"Ligák erősség: **{len(ero)}**"
    )

if not meccsek:
    st.error("❌ Nincs meccs. Ellenőrizd az API kulcsot / kvótát.")
    st.stop()

# ============================================================
# FELDOLGOZÁS
# ============================================================
tippek, figyelo, kihagyva, csak_piac, komb_db = feldolgoz(meccsek, ero, liga_atlag)

# ============================================================
# STATISZTIKA
# ============================================================
with st.expander("📊 Feldolgozási statisztika", expanded=False):
    a, b, c, d = st.columns(4)
    a.metric("✅ Tipp", len(tippek))
    b.metric("🟡 Figyelő", len(figyelo))
    c.metric("🔀 Kombinált", komb_db)
    d.metric("📈 Csak piac", csak_piac)
    if kihagyva:
        st.write("**Kihagyási okok:**")
        for k, v in kihagyva.items():
            st.write(f"• {k}: {v}")

# ============================================================
# TOP TIPPEK
# ============================================================
st.subheader("⭐ TOP TIPPEK")
if not tippek:
    st.warning("Nincs megfelelő meccs.")
else:
    for t in tippek[:15]:
        cim = f"{t['meccs']} | {t['ido']} | {t['esely']*100:.1f}% | odds {t['odds']:.2f} | {t['mod']}"
        with st.expander(cim):
            x, y, z = st.columns(3)
            x.metric("Kombinált esély", f"{t['esely']*100:.1f}%")
            y.metric("Odds", f"{t['odds']:.2f}")
            z.metric("EV", f"{t['ev']:+.1f}%")
            st.write("**Tipp:**", t["tip"])
            st.write("**Liga:**", t["liga"])
            st.write("**Kezdés:**", t["ido"])
            st.write("**Margin:**", f"{t['margin']*100:.1f}%")
            if t["p_piac"] is not None:
                st.write(f"**Piaci esély:** {t['p_piac']*100:.1f}%")
            if t["p_stat"] is not None:
                st.write(f"**Statisztikai esély (Poisson):** {t['p_stat']*100:.1f}%")
            if t["kelly"] > 0:
                st.success(f"💰 Javasolt tét (¼ Kelly): **{t['kelly']:,.0f} Ft**")
            else:
                st.info("💰 Kelly szerint nincs él.")

# ============================================================
# FIGYELŐLISTA
# ============================================================
if figyelo:
    st.subheader("🟡 Figyelőlista")
    for t in figyelo[:10]:
        st.write(
            f"• **{t['meccs']}** ({t['ido']}) | {t['esely']*100:.1f}% | "
            f"odds {t['odds']:.2f} | EV {t['ev']:+.1f}%"
        )

# ============================================================
# KOMBI
# ============================================================
if len(tippek) >= 2:
    kombi = tippek[:2]
    ko, ke = 1.0, 1.0
    for m in kombi:
        ko *= m["odds"]
        ke *= m["esely"]
    st.subheader("🔥 Napi Kombi")
    for m in kombi:
        st.write(f"✅ {m['meccs']} – {m['tip']} (odds {m['odds']:.2f})")
    st.success(
        f"Kombi odds: **{ko:.2f}** | Becsült esély: **{ke*100:.1f}%** | "
        f"EV: **{(ke*ko-1)*100:+.1f}%**"
    )

st.divider()
st.caption(
    "Az esély a piaci (margin-eltávolított medián odds) és a Poisson-modell "
    f"súlyozott átlaga (piac {W_PIAC}, stat {W_STAT}). Csak akkor tippel, ha a két modell "
    f"legalább {MIN_EGYEZES*100:.0f}%ponton belül egyetért. Nem befektetési tanács."
       )
