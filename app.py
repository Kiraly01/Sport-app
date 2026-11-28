import streamlit as st
import requests
import statistics
import math
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo
from collections import defaultdict
import time

# ============================================================
# OLDAL ÉS MODERN DIZÁJN (FEKETE HÁTTÉR)
# ============================================================
st.set_page_config(page_title="⚽ Napi Foci Tipp – Modell", page_icon="⚽", layout="wide")

st.markdown("""
<style>
.stApp { background-color: #000000; color: #e2e8f0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
h1, h2, h3 { color: #ffffff; font-weight: 800; letter-spacing: 1px; }
p, span, div { font-size: 1.05rem; }
.modern-card { background: #111111; border: 1px solid #333333; border-radius: 16px; padding: 20px; margin-bottom: 20px; box-shadow: 0 10px 25px rgba(0,0,0,0.8); transition: transform 0.2s ease, box-shadow 0.2s ease; }
.modern-card:hover { transform: translateY(-4px); box-shadow: 0 15px 30px rgba(0,0,0,1); border-color: #555555; }
.top-card { background: #111111; border-left: 6px solid #3b82f6; }
.top-card-header { display: flex; justify-content: space-between; align-items: center; border-bottom: 1px solid #333333; padding-bottom: 12px; margin-bottom: 15px; }
.top-card-title { font-size: 1.4rem; font-weight: 900; color: #ffffff; }
.top-card-percent { font-size: 1.6rem; font-weight: 900; color: #10b981; text-shadow: 0 0 10px rgba(16, 185, 129, 0.4); }
.badge { background: #3b82f6; color: white; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }
.data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-top: 15px; }
.data-item { background: #1a1a1a; padding: 10px; border-radius: 8px; border: 1px solid #222222; }
.data-label { font-size: 0.85rem; color: #94a3b8; text-transform: uppercase; font-weight: bold; }
.data-value { font-size: 1.2rem; font-weight: bold; color: #ffffff; }
.tip-text { color: #60a5fa; font-weight: bold; font-size: 1.1rem; margin-top: 10px; display: block;}

/* Szimulált kártya dizájn */
.szimulalt-card { background: #111111; border-left: 6px solid #eab308; }
.szimulalt-badge { background: #eab308; color: #000000; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: bold; text-transform: uppercase; }

.watch-card { background: #111111; border-left: 6px solid #eab308; }
.warn-box { background: rgba(234, 179, 8, 0.1); border: 1px solid #eab308; color: #fef08a; padding: 15px; border-radius: 10px; margin-bottom: 20px; font-weight: 600; }
.danger-box { background: rgba(239, 68, 68, 0.1); border: 1px solid #ef4444; color: #fca5a5; padding: 10px; border-radius: 8px; margin-top: 10px; font-size: 0.9rem; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Tipp – Prémium Modell</h1>", unsafe_allow_html=True)

# ============================================================
# KONFIG
# ============================================================
TOP_KUSZOB      = 0.82
FIGYELO_KUSZOB  = 0.75
MIN_IRODAK      = 3
MIN_ODDS        = 1.08
MAX_ODDS        = 1.60
MAX_ODDS_SPREAD = 2.00
MAX_FAVORIT     = 2.20
KELLY_FRAKCIO   = 0.25
BANKROLL        = 10000
W_PIAC = 0.55
W_STAT = 0.45
POISSON_MECCS_SZAM = 30
MIN_EGYEZES = 0.10

LIGAK = [
    "soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a",
    "soccer_germany_bundesliga", "soccer_france_ligue_one",
]

FD_LIGAK = {
    "soccer_epl": "PL", "soccer_spain_la_liga": "PD",
    "soccer_italy_serie_a": "SA", "soccer_germany_bundesliga": "BL1",
    "soccer_france_ligue_one": "FL1",
}

KUPAS_KULCSSZAVAK = ['cup', 'copa', 'kupa', 'trophy', 'playoff', 'play-off', 'clausura', 'apertura', 'qualification', 'knockout', 'round of', 'supercopa']
TZ = ZoneInfo("Europe/Budapest")

# ============================================================
# API KULCSOK
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

# ============================================================
# API LEKÉRDEZÉSEK
# ============================================================
@st.cache_data(ttl=900, show_spinner=False)
def leker_liga(liga: str):
    most = datetime.now(ZoneInfo("UTC"))
    kezdo = most.strftime("%Y-%m-%dT00:00:00Z")
    veg   = (most + timedelta(days=5)).strftime("%Y-%m-%dT23:59:59Z")
    url = (f"https://api.the-odds-api.com/v4/sports/{liga}/odds/"
           f"?apiKey={ODDS_KEY}&regions=eu,uk&markets=h2h&oddsFormat=decimal"
           f"&commenceTimeFrom={kezdo}&commenceTimeTo={veg}")
    try:
        r = requests.get(url, timeout=20)
        kvota = r.headers.get("x-requests-remaining", "?")
        if r.status_code in [401, 429]: return [], kvota
        r.raise_for_status()
        return r.json(), kvota
    except Exception:
        return [], "?"

@st.cache_data(ttl=900, show_spinner=False)
def leker_osszes_odds():
    osszes, kvota = [], "?"
    for liga in LIGAK:
        adat, kvota = leker_liga(liga)
        if isinstance(adat, list): osszes.extend(adat)
        time.sleep(0.2)
    return osszes, kvota

@st.cache_data(ttl=3600, show_spinner=False)
def leker_csapat_meccsek(fd_liga: str):
    if not FD_KEY: return []
    url = f"https://api.football-data.org/v4/competitions/{fd_liga}/matches?status=FINISHED"
    try:
        r = requests.get(url, headers={"X-Auth-Token": FD_KEY}, timeout=20)
        if r.status_code != 200: return []
        return r.json().get("matches", [])[-POISSON_MECCS_SZAM:]
    except Exception:
        return []

@st.cache_data(ttl=3600, show_spinner=False)
def epit_erősség():
    ero, liga_atlag = {}, {}
    for odds_kulcs, fd_kulcs in FD_LIGAK.items():
        meccsek = leker_csapat_meccsek(fd_kulcs)
        if not meccsek: continue

        golt_rugott, golt_kapott = defaultdict(list), defaultdict(list)
        for m in meccsek:
            if m.get("status") != "FINISHED": continue
            ft = m.get("score", {}).get("fullTime", {})
            hg, ag = ft.get("home"), ft.get("away")
            if hg is None or ag is None: continue
            hazai, vendeg = m["homeTeam"]["name"], m["awayTeam"]["name"]
            golt_rugott[hazai].append(hg); golt_kapott[hazai].append(ag)
            golt_rugott[vendeg].append(ag); golt_kapott[vendeg].append(hg)

        if not golt_rugott: continue
        osszes_gol = sum(sum(v) for v in golt_rugott.values())
        if len(meccsek) == 0: continue
        
        liga_csapat_atlag = (osszes_gol / len(meccsek)) / 2
        liga_atlag[odds_kulcs] = liga_csapat_atlag
        ero[odds_kulcs] = {}

        for csapat in golt_rugott:
            rugott, kapott = golt_rugott[csapat], golt_kapott[csapat]
            if len(rugott) < 5: continue
            att = (sum(rugott) / len(rugott)) / liga_csapat_atlag if liga_csapat_atlag > 0 else 1.0
            deff = (sum(kapott) / len(kapott)) / liga_csapat_atlag if liga_csapat_atlag > 0 else 1.0
            ero[odds_kulcs][csapat] = (att, deff)
    return ero, liga_atlag

# ============================================================
# MODELLEK
# ============================================================
def poisson_pmf(k, lam):
    if lam <= 0: return 1.0 if k == 0 else 0.0
    return math.exp(-lam) * (lam ** k) / math.factorial(k)

def poisson_1x2(lambda_h, lambda_v, max_gol=10):
    p_h = p_d = p_v = 0.0
    for i in range(max_gol + 1):
        for j in range(max_gol + 1):
            p = poisson_pmf(i, lambda_h) * poisson_pmf(j, lambda_v)
            if i > j: p_h += p
            elif i == j: p_d += p
            else: p_v += p
    return p_h, p_d, p_v, p_h + p_d, p_v + p_d

def statisztikai_eselyek(meccs, ero, liga_atlag):
    liga = meccs.get("sport_key")
    if liga not in ero: return None
    hazai, vendeg = meccs.get("home_team"), meccs.get("away_team")
    if hazai not in ero[liga] or vendeg not in ero[liga]: return None

    att_h, def_h = ero[liga][hazai]
    att_v, def_v = ero[liga][vendeg]
    atlag = liga_atlag.get(liga)
    if not atlag or atlag <= 0: return None

    lambda_h = max(0.2, min(att_h * def_v * atlag * 1.15, 4.0))
    lambda_v = max(0.2, min(att_v * def_h * atlag * 0.95, 4.0))
    p_h, p_d, p_v, p_1x, p_x2 = poisson_1x2(lambda_h, lambda_v)
    return {"p_h": p_h, "p_d": p_d, "p_v": p_v, "p_1x": p_1x, "p_x2": p_x2}

def szimulalt_poisson(piac):
    p_h, p_d, p_v = piac["p_h"], piac["p_d"], piac["p_v"]
    ossz_gol = 2.7
    if p_h + p_v > 0:
        arany = p_h / (p_h + p_v)
        lambda_h = ossz_gol * arany * 1.1
        lambda_v = ossz_gol * (1 - arany) * 0.9
    else:
        lambda_h, lambda_v = 1.35, 1.35
    lambda_h = max(0.2, min(lambda_h, 4.0))
    lambda_v = max(0.2, min(lambda_v, 4.0))
    p_h, p_d, p_v, p_1x, p_x2 = poisson_1x2(lambda_h, lambda_v)
    return {"p_h": p_h, "p_d": p_d, "p_v": p_v, "p_1x": p_1x, "p_x2": p_x2, "szimulalt": True}

def piaci_eselyek(meccs):
    hazai, vendeg, dontetlen = [], [], []
    for iroda in meccs.get("bookmakers", []):
        for market in iroda.get("markets", []):
            if market.get("key") != "h2h": continue
            for o in market.get("outcomes", []):
                ar = o.get("price")
                if not isinstance(ar, (int, float)) or ar <= 1.0: continue
                nev = o.get("name")
                if nev == meccs.get("home_team"): hazai.append(ar)
                elif nev == meccs.get("away_team"): vendeg.append(ar)
                elif nev == "Draw": dontetlen.append(ar)

    if len(hazai) < MIN_IRODAK or len(vendeg) < MIN_IRODAK or len(dontetlen) < MIN_IRODAK:
        return None, "keves_iroda"
    if max(hazai) - min(hazai) > MAX_ODDS_SPREAD or max(vendeg) - min(vendeg) > MAX_ODDS_SPREAD:
        return None, "nagy_szoras"

    mh, mv, md = statistics.median(hazai), statistics.median(vendeg), statistics.median(dontetlen)
    if min(mh, mv) > MAX_FAVORIT: return None, "nagy_favorit"

    ih, iv, idd = 1/mh, 1/mv, 1/md
    osszeg = ih + iv + idd
    return {
        "p_h": ih/osszeg, "p_v": iv/osszeg, "p_d": idd/osszeg,
        "p_1x": (ih + idd)/osszeg, "p_x2": (iv + idd)/osszeg,
        "mh": mh, "mv": mv, "md": md, "margin": osszeg - 1
    }, None

def kombinalt_esely(piac, stat):
    if stat is None: return piac, "csak_piac"
    return {
        "p_1x": W_PIAC * piac["p_1x"] + W_STAT * stat["p_1x"],
        "p_x2": W_PIAC * piac["p_x2"] + W_STAT * stat["p_x2"],
        "piac_1x": piac["p_1x"], "piac_x2": piac["p_x2"],
        "stat_1x": stat["p_1x"], "stat_x2": stat["p_x2"],
    }, "kombinált"

def egyezik(piac_p, stat_p, kuszob=MIN_EGYEZES):
    if stat_p is None: return False
    return abs(piac_p - stat_p) <= kuszob

def kelly_tet(p, odds, bankroll=BANKROLL, frakcio=KELLY_FRAKCIO):
    if odds <= 1.0 or p <= 0 or p >= 1: return 0
    b = odds - 1
    f = (p * b - (1 - p)) / b
    return round(bankroll * f * frakcio, 0) if f > 0 else 0

def ido_format(iso_str):
    try:
        dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return dt.astimezone(TZ).strftime("%m.%d %H:%M")
    except Exception: return "?"

def kieseses_meccs_e(sport_title):
    sport_title_lower = sport_title.lower()
    return any(kulcsszo in sport_title_lower for kulcsszo in KUPAS_KULCSSZAVAK)

# ============================================================
# FELDOLGOZÁS
# ============================================================
def feldolgoz(meccsek, ero, liga_atlag):
    premium_tippek, szimulalt_tippek, figyelo = [], [], []
    diag = defaultdict(int)
    
    for m in meccsek:
        piac, hiba = piaci_eselyek(m)
        if piac is None:
            diag[hiba] += 1
            continue

        stat = statisztikai_eselyek(m, ero, liga_atlag)
        is_szimulalt = False
        
        if stat is None:
            diag["szimulalt_statisztika"] += 1
            stat = szimulalt_poisson(piac)
            is_szimulalt = True
        else:
            diag["valos_statisztika"] += 1
            
        komb, mod = kombinalt_esely(piac, stat)
        is_kieseses = kieseses_meccs_e(m.get("sport_title", ""))

        opciok = [
            ("1X", f"{m['home_team']} vagy döntetlen (1X)", komb["p_1x"], komb.get("piac_1x"), komb.get("stat_1x")),
            ("X2", f"{m['away_team']} vagy döntetlen (X2)", komb["p_x2"], komb.get("piac_x2"), komb.get("stat_x2")),
        ]

        legjobb = None
        for kod, nev, p, p_piac, p_stat in opciok:
            odds = 1 / p if p > 0 else 999
            if not (MIN_ODDS <= odds <= MAX_ODDS): 
                diag["rossz_odds"] += 1
                continue
                
            if not egyezik(p_piac, p_stat): 
                diag["modellek_nem_egyeznek"] += 1
                continue

            if legjobb is None or p > legjobb["esely"]:
                legjobb = {"kod": kod, "tip": nev, "esely": p, "odds": odds,
                           "p_piac": p_piac, "p_stat": p_stat, "ev": (p * odds - 1) * 100, "mod": mod,
                           "szimulalt": is_szimulalt}

        if legjobb is None: continue

        adat = {
            "meccs": f"{m['home_team']} - {m['away_team']}", "liga": m.get("sport_title", m.get("sport_key", "?")),
            "ido": ido_format(m.get("commence_time", "")), "margin": piac["margin"],
            "kelly": kelly_tet(legjobb["esely"], legjobb["odds"]), "kieseses": is_kieseses, **legjobb,
        }

        # Szétválasztás: Prémium (valós) vs Szimulált
        if not is_kieseses:
            if legjobb["esely"] >= TOP_KUSZOB:
                if is_szimulalt:
                    szimulalt_tippek.append(adat)
                else:
                    premium_tippek.append(adat)
            elif legjobb["esely"] >= FIGYELO_KUSZOB:
                figyelo.append(adat)
            else:
                diag["kuszob_alatt"] += 1
        else:
            # Kieséses meccsek csak figyelőlistára
            if legjobb["esely"] >= FIGYELO_KUSZOB:
                figyelo.append(adat)

    premium_tippek.sort(key=lambda x: (x["esely"], x["ev"]), reverse=True)
    szimulalt_tippek.sort(key=lambda x: (x["esely"], x["ev"]), reverse=True)
    figyelo.sort(key=lambda x: (x["esely"], x["ev"]), reverse=True)
    
    return premium_tippek, szimulalt_tippek, figyelo, diag

# ============================================================
# FUTTATÁS
# ============================================================
with st.sidebar:
    st.header("⚙️ Beállítások")
    if FD_KEY: st.success("✅ Valós adatok elérhetők")
    else: st.warning("⚠️ Csak szimulált statisztika")
    st.divider()
    if st.button("🔄 Adatok frissítése", use_container_width=True, type="primary"):
        st.cache_data.clear()
        st.rerun()

with st.spinner("Odds és statisztikák betöltése..."):
    meccsek, kvota = leker_osszes_odds()
    ero, liga_atlag = epit_erősség() if FD_KEY else ({}, {})

if not meccsek:
    st.error("❌ Nincs meccs. Ellenőrizd az API kulcsot / kvótát.")
    st.stop()

premium, szimulalt, figyelo, diag = feldolgoz(meccsek, ero, liga_atlag)

st.markdown(f"<div style='color:#94a3b8; margin-bottom: 20px;'>📡 API Kvóta: <b>{kvota}</b> | Meccsek: <b>{len(meccsek)}</b> | Ligák: <b>{len(ero)}</b></div>", unsafe_allow_html=True)

with st.sidebar:
    st.divider()
    st.subheader("🔍 Diagnosztika")
    st.write(f"Összes meccs: **{len(meccsek)}**")
    if diag:
        for k, v in diag.items():
            st.write(f"• {k}: {v}")

# ============================================================
# MEGJELENÍTÉS - PRÉMIUM (VALÓS)
# ============================================================
st.markdown("<h2 style='margin-top: 30px;'>⭐ Prémium Tippek (Valós statisztika)</h2>", unsafe_allow_html=True)

if not premium:
    st.markdown("<div class='warn-box'>Jelenleg nincs olyan valós statisztikával rendelkező meccs, ami elérte a 82%-os biztonsági küszöböt és a modellek is egyetértenek.</div>", unsafe_allow_html=True)
else:
    for t in premium[:10]:
        kies_warn = "<div class='danger-box'>⚠️ KIESÉSES MECCS - Csak óvatosan!</div>" if t['kieseses'] else ""
        stat_val = f"{t['p_stat']*100:.1f}%"
        
        html_card = f"""
        <div class="modern-card top-card">
            <div class="top-card-header">
                <div>
                    <div class="top-card-title">{t['meccs']}</div>
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 5px;">📅 {t['ido']} | 🏆 {t['liga']}</div>
                </div>
                <div class="top-card-percent">{t['esely']*100:.1f}%</div>
            </div>
            <span class="tip-text">👉 Tipp: {t['tip']}</span>
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">Odds</div>
                    <div class="data-value">{t['odds']:.2f}</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Várható Érték (EV)</div>
                    <div class="data-value" style="color: #10b981;">{t['ev']:+.1f}%</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Piaci Esély</div>
                    <div class="data-value">{t['p_piac']*100:.1f}%</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Statisztikai (Poisson)</div>
                    <div class="data-value">{stat_val}</div>
                </div>
            </div>
            <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                <span class="badge">{t['mod']}</span>
                <span style="font-size: 1.2rem; color: #10b981; font-weight: bold;">💰 Tét: {t['kelly']:,.0f} Ft</span>
            </div>
            {kies_warn}
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

# ============================================================
# MEGJELENÍTÉS - SZIMULÁLT
# ============================================================
if szimulalt:
    st.markdown("<h2 style='margin-top: 40px;'>⚠️ Szimulált Statisztikás Tippek</h2>", unsafe_allow_html=True)
    st.markdown("<div class='warn-box'>Ezeknél a meccseknél a valós statisztika nem elérhető, ezért a piaci oddsokból lett becsülve a Poisson modell. Kevesebb biztonságot nyújtanak!</div>", unsafe_allow_html=True)
    
    for t in szimulalt[:10]:
        stat_val = f"{t['p_stat']*100:.1f}%"
        
        html_card = f"""
        <div class="modern-card szimulalt-card">
            <div class="top-card-header">
                <div>
                    <div class="top-card-title">{t['meccs']}</div>
                    <div style="color: #94a3b8; font-size: 0.9rem; margin-top: 5px;">📅 {t['ido']} | 🏆 {t['liga']}</div>
                </div>
                <div class="top-card-percent" style="color: #eab308;">{t['esely']*100:.1f}%</div>
            </div>
            <span class="tip-text">👉 Tipp: {t['tip']}</span>
            <div style="margin-top: 10px; margin-bottom: 5px;">
                <span class="szimulalt-badge">SZIMULÁLT STATISZTIKA</span>
            </div>
            <div class="data-grid">
                <div class="data-item">
                    <div class="data-label">Odds</div>
                    <div class="data-value">{t['odds']:.2f}</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Várható Érték (EV)</div>
                    <div class="data-value" style="color: #eab308;">{t['ev']:+.1f}%</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Piaci Esély</div>
                    <div class="data-value">{t['p_piac']*100:.1f}%</div>
                </div>
                <div class="data-item">
                    <div class="data-label">Becsült Poisson</div>
                    <div class="data-value" style="color: #eab308;">{stat_val} (szim.)</div>
                </div>
            </div>
            <div style="margin-top: 15px; display: flex; justify-content: space-between; align-items: center;">
                <span class="badge" style="background-color: #eab308; color: #000;">{t['mod']}</span>
                <span style="font-size: 1.2rem; color: #eab308; font-weight: bold;">💰 Tét: {t['kelly']:,.0f} Ft</span>
            </div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

# ============================================================
# MEGJELENÍTÉS - FIGYELŐLISTA
# ============================================================
if figyelo:
    st.markdown("<h2 style='margin-top: 40px;'>🟡 Figyelőlista</h2>", unsafe_allow_html=True)
    for t in figyelo[:10]:
        kies_warn = "<div class='danger-box' style='padding: 5px; margin-top: 5px;'>⚠️ KIESÉSES MECCS</div>" if t['kieseses'] else ""
        stat_text = "Szimulált" if t.get('szimulalt') else f"Stat: {t['p_stat']*100:.1f}%"
        
        html_card = f"""
        <div class="modern-card watch-card">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <div style="font-size: 1.1rem; font-weight: bold; color: #f8fafc;">{t['meccs']}</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">📅 {t['ido']} | {t['tip']} | {stat_text}</div>
                </div>
                <div style="text-align: right;">
                    <div style="font-size: 1.3rem; font-weight: bold; color: #eab308;">{t['esely']*100:.1f}%</div>
                    <div style="color: #94a3b8; font-size: 0.85rem;">Odds: {t['odds']:.2f}</div>
                </div>
            </div>
            {kies_warn}
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

st.divider()
st.caption("Az esély a piaci és a Poisson-modell súlyozott átlaga. Nem befektetési tanács.")
