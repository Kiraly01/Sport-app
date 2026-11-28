import streamlit as st
import requests
import statistics
from datetime import datetime, timedelta
import pytz

st.set_page_config(
    page_title="⚽ Napi Foci Tipp",
    page_icon="⚽"
)

st.title("⚽ Napi Foci Tipp")

# --------------------------------
# BEÁLLÍTÁSOK
# --------------------------------

TOP_KUSZOB = 0.85
FIGYELO_KUSZOB = 0.78

MIN_IRODAK = 3

MIN_ODDS = 1.15
MAX_ODDS = 1.40

try:
    API_KEY = st.secrets["ODDS_API_KEY"]
except:
    st.error("ODDS_API_KEY nem található.")
    st.stop()

# --------------------------------
# API
# --------------------------------

@st.cache_data(ttl=900)
def leker_meccsek():

    most = datetime.now(pytz.utc)

    kezdo = most.strftime("%Y-%m-%dT00:00:00Z")

    veg = (
        most + timedelta(days=5)
    ).strftime("%Y-%m-%dT23:59:59Z")

    url = (
        "https://api.the-odds-api.com/v4/sports/soccer/odds/"
        f"?apiKey={API_KEY}"
        "&regions=eu,uk,us"
        "&markets=h2h"
        "&oddsFormat=decimal"
        f"&commenceTimeFrom={kezdo}"
        f"&commenceTimeTo={veg}"
    )

    try:
        r = requests.get(url, timeout=15)
        r.raise_for_status()
        return r.json()

    except:
        return []

# --------------------------------
# GOMB
# --------------------------------

if st.button("🔄 Frissítés"):
    st.cache_data.clear()

# --------------------------------
# SZŰRÉS
# --------------------------------

tippek = []
figyelo = []

meccsek = leker_meccsek()

for m in meccsek:

    hazai = []
    vendeg = []
    dontetlen = []

    for iroda in m.get("bookmakers", []):

        for market in iroda.get("markets", []):

            if market["key"] != "h2h":
                continue

            for o in market["outcomes"]:

                if o["name"] == m["home_team"]:
                    hazai.append(o["price"])

                elif o["name"] == m["away_team"]:
                    vendeg.append(o["price"])

                elif o["name"] == "Draw":
                    dontetlen.append(o["price"])

    if (
        len(hazai) < MIN_IRODAK
        or len(vendeg) < MIN_IRODAK
        or len(dontetlen) < MIN_IRODAK
    ):
        continue

    if max(hazai) - min(hazai) > 0.50:
        continue

    if max(vendeg) - min(vendeg) > 0.50:
        continue

    mh = statistics.median(hazai)
    mv = statistics.median(vendeg)
    md = statistics.median(dontetlen)

    favorit = min(mh, mv)

    if favorit > 2.20:
        continue

    osszeg = (
        1 / mh
        + 1 / mv
        + 1 / md
    )

    esely_1x = (
        (1 / mh) + (1 / md)
    ) / osszeg

    esely_x2 = (
        (1 / mv) + (1 / md)
    ) / osszeg

    opciok = [

        (
            f"{m['home_team']} vagy döntetlen (1X)",
            esely_1x,
            1 / esely_1x
        ),

        (
            f"{m['away_team']} vagy döntetlen (X2)",
            esely_x2,
            1 / esely_x2
        )
    ]

    legjobb = None

    for nev, esely, odds in opciok:

        if not (
            MIN_ODDS <= odds <= MAX_ODDS
        ):
            continue

        if legjobb is None:
            legjobb = (nev, esely, odds)

        elif esely > legjobblegjobb = (nev, esely, odds)

    if legjobb is None:
        continue

    adat = {
        "meccs":
            f"{m['home_team']} - {m['away_team']}",

        "tip":
            legjobb[0],

        "esely":
            legjobb[1],

        "odds":
            legjobb[2]
    }

    if legjobb[1] >= TOP_KUSZOB:
        tippek.append(adat)

    elif legjobb[1] >= FIGYELO_KUSZOB:
        figyelo.append(adat)

# --------------------------------
# RENDEZÉS
# --------------------------------

tippek.sort(
    key=lambda x: x["esely"],
    reverse=True
)

figyelo.sort(
    key=lambda x: x["esely"],
    reverse=True
)

# --------------------------------
# TOP TIPPEK
# --------------------------------

st.subheader("⭐ TOP TIPPEK")

if not tippek:
    st.warning("Nincs megfelelő meccs.")

for t in tippek[:10]:

    with st.expander(
        f"{t['meccs']} ({t['esely']*100:.1f}%)"
    ):

        st.write("Tipp:", t["tip"])
        st.write("Esély:", f"{t['esely']*100:.1f}%")
        st.write("Odds:", f"{t['odds']:.2f}")

# --------------------------------
# FIGYELŐLISTA
# --------------------------------

if figyelo:

    st.subheader("🟡 Figyelőlista")

    for t in figyelo[:10]:

        st.write(
            f"• {t['meccs']} | "
            f"{t['esely']*100:.1f}%"
        )

# --------------------------------
# KOMBI
# --------------------------------

if len(tippek) >= 2:

    kombi = tippek[:2]

    kombi_odds = 1

    for m in kombi:
        kombi_odds *= m["odds"]

    st.subheader("🔥 Napi Kombi")

    for m in kombi:
        st.write(
            f"✅ {m['meccs']}"
        )

    st.success(
        f"Kombi odds: {kombi_odds:.2f}"
    )
