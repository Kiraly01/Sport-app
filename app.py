import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ==========================================
# MODERN, NAGY BETŰS KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Foci Szűrő - Biztonságos", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #12161A; color: #E0E0E0; }
    
    h1 { 
        color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.5em; 
        text-align: center; margin-bottom: 20px;
    }
    
    .streamlit-expanderHeader {
        background-color: #1E252B !important; border-radius: 8px !important;
        color: #FACC15 !important; font-weight: 800 !important; font-size: 1.4em !important; 
        border: 1px solid #444 !important; padding: 15px 20px !important; margin-bottom: 8px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    .streamlit-expanderContent {
        background-color: #161A1F !important; border: 1px solid #444 !important;
        border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important;
        padding: 15px !important;
    }
    
    .stButton>button {
        background-color: #FACC15; color: #000000; font-weight: 700; font-size: 1.1em;
        border-radius: 6px; border: none; padding: 10px 15px; width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.2s;
    }
    .stButton>button:hover { background-color: #EAB308; transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    
    .clock-container { display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 15px; }
    .live-clock {
        font-family: 'Courier New', monospace; font-size: 1.6em; color: #FACC15;
        background-color: #1E252B; padding: 10px 20px; border-radius: 8px;
        border: 1px solid #444; font-weight: 800; letter-spacing: 1px;
        box-shadow: 0 4px 8px rgba(0,0,0,0.3);
    }
    
    div[data-testid="column"] {
        background-color: #242B33; border-radius: 8px; padding: 10px; border: 1px solid #444;
        transition: all 0.2s;
    }
    div[data-testid="column"]:hover { border-color: #FACC15; transform: scale(1.02); }
    
    .stMarkdown p { font-size: 1.1em; }
    
    .warning-box {
        background-color: #332211; border-left: 4px solid #FACC15;
        padding: 10px; margin-bottom: 15px; border-radius: 4px; color: #E0E0E0;
        font-size: 0.9em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Biztonságos Foci Szűrő</h1>", unsafe_allow_html=True)

# ==========================================
# ÉLŐ ÓRA
# ==========================================
@st.fragment(run_every=1)
def ora_frissites():
    hu_tz = pytz.timezone('Europe/Budapest')
    aktualis_ido = datetime.now(hu_tz)
    st.markdown(f"""
        <div class="clock-container">
            <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
        </div>
    """, unsafe_allow_html=True)

ora_frissites()

st.markdown("""
<div class="warning-box">
⚠️ <b>FIGYELEM!</b> Ez az app csak a legbiztonságosabb tippeket mutatja (80% feletti esély, Kétesély opció). 
A sportfogadás kockázattal jár, soha ne tegyél fel többet, mint amit el tudsz veszíteni!
</div>
""", unsafe_allow_html=True)

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
KUSZOB_MIN = 0.80  # 80%-os szigorú minimum küszöb
MAX_LISTA = 3      # Maximum 3 meccs
MAX_TIPP = 3       # Maximum 3 tipp a szelvényen

if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = []

try:
    most_utc = datetime.now(pytz.utc)
    hu_tz = pytz.timezone('Europe/Budapest')
    
    ma_str = most_utc.strftime("%Y-%m-%d")
    holnap_str = (most_utc + timedelta(days=1)).strftime("%Y-%m-%d")
    
    jeloltek_dict = {}
    
    with st.spinner("Biztonságos foci meccsek keresése (80% felett)..."):
        for datum in [ma_str, holnap_str]:
            url = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom={datum}T00:00:00Z&commenceTimeTo={datum}T23:59:59Z"
            valasz = requests.get(url)
            
            if valasz.status_code == 200:
                meccsek = valasz.json()
                
                for m in meccsek:
                    idopont_nyers = m.get('commence_time', '')
                    if not idopont_nyers: continue
                    
                    try:
                        kezdes_utc = datetime.strptime(idopont_nyers, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                        if kezdes_utc <= most_utc: continue
                        kezdes_hu = kezdes_utc.astimezone(hu_tz)
                    except: continue
                    
                    # 1X2 és Kétesély esélyeinek kiszámítása
                    legjobb_h2h_esely = 0
                    legjobb_h2h_nev = ""
                    legjobb_h2h_odds = 0
                    h2h_odds = {}
                    
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            if market['key'] == 'h2h':
                                kimenetek = market['outcomes']
                                nyers_oddsok = [k['price'] for k in kimenetek]
                                nyers_osszeg = sum([1/o for o in nyers_oddsok])
                                
                                for k in kimenetek:
                                    esely = (1 / k['price']) / nyers_osszeg
                                    
                                    if k['name'] == m['home_team']:
                                        h2h_odds['hazai'] = k['price']
                                        if esely > legjobb_h2h_esely:
                                            legjobb_h2h_esely = esely
                                            legjobb_h2h_nev = f"{m['home_team']} (Hazai)"
                                            legjobb_h2h_odds = k['price']
                                    elif k['name'] == m['away_team']:
                                        h2h_odds['vendeg'] = k['price']
                                        if esely > legjobb_h2h_esely:
                                            legjobb_h2h_esely = esely
                                            legjobb_h2h_nev = f"{m['away_team']} (Vendég)"
                                            legjobb_h2h_odds = k['price']
                                    elif k['name'] == "Draw":
                                        h2h_odds['dontetlen'] = k['price']
                    
                    # Kétesély (1X, X2) esélyeinek kiszámítása
                    ketesely_opciok = []
                    if 'hazai' in h2h_odds and 'dontetlen' in h2h_odds:
                        # 1X (Hazai vagy Döntetlen) - a nyers valószínűségek összege
                        esely_1x = (1/h2h_odds['hazai'] + 1/h2h_odds['dontetlen']) / nyers_osszeg
                        odds_1x = 1 / esely_1x if esely_1x > 0 else 0
                        ketesely_opciok.append({
                            'nev': f"{m['home_team']} vagy Döntetlen (1X)",
                            'esely': esely_1x,
                            'odds': odds_1x
                        })
                    if 'vendeg' in h2h_odds and 'dontetlen' in h2h_odds:
                        # X2 (Vendég vagy Döntetlen)
                        esely_x2 = (1/h2h_odds['vendeg'] + 1/h2h_odds['dontetlen']) / nyers_osszeg
                        odds_x2 = 1 / esely_x2 if esely_x2 > 0 else 0
                        ketesely_opciok.append({
                            'nev': f"{m['away_team']} vagy Döntetlen (X2)",
                            'esely': esely_x2,
                            'odds': odds_x2
                        })
                    
                    # Kiválasztjuk a legjobb Kétesély opciót
                    legjobb_ketesely = None
                    for opcio in ketesely_opciok:
                        if opcio['esely'] >= KUSZOB_MIN:
                            if legjobb_ketesely is None or opcio['esely'] > legjobb_ketesely['esely']:
                                legjobb_ketesely = opcio
                    
                    # Ha van 80% feletti Kétesély, akkor bekerül a listára
                    if legjobb_ketesely:
                        meccs_nev = f"{m['home_team']} - {m['away_team']}"
                        if meccs_nev not in jeloltek_dict or legjobb_ketesely['esely'] > jeloltek_dict[meccs_nev]['esely']:
                            jeloltek_dict[meccs_nev] = {
                                'meccs': meccs_nev,
                                'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                                'esely': legjobb_ketesely['esly'] if 'esly' in legjobb_ketesely else legjobb_ketesely['esely'],
                                'opcio_nev': legjobb_ketesely['nev'],
                                'odds': legjobb_ketesely['odds'],
                                'hazai': m['home_team'],
                                'vendeg': m['away_team']
                            }
    
    jeloltek = list(jeloltek_dict.values())
    jeloltek.sort(key=lambda x: x['esely'], reverse=True)
    top_lista = jeloltek[:MAX_LISTA]

    if not top_lista:
        st.warning(f"📭 Nincs olyan jövőbeli foci meccs, ahol a Kétesély opció esélye elérné a {int(KUSZOB_MIN*100)}%-ot. Az app azt javasolja: ma ne fogadj.")
    else:
        st.success(f"✅ A legbiztonságosabb {len(top_lista)} foci meccs (80% feletti Kétesély):")
        
        for i, j in enumerate(top_lista, 1):
            cim = f"⭐ | {j['meccs']}  —  {j['opcio_nev']} ({j['esely']*100:.1f}%)"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 1em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                # Motivációs figyelmeztetés
                st.markdown(f"""
                <div class="warning-box">
                ⚠️ <b>Motivációs csapda:</b> Ellenőrizd, hogy az egyik csapatnak nincs-e "muszáj nyernie" helyzete (bajnoki cím, kiesés elleni harc), 
                mert az felülírhatja a statisztikákat!
                </div>
                """, unsafe_allow_html=True)
                
                st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                
                # Csak akkor engedi a kiválasztást, ha nincs tele a szelvény
                if len(st.session_state.kivalasztott_tippek) >= MAX_TIPP:
                    st.warning(f"⚠️ Elérted a napi limitet ({MAX_TIPP} tipp). Ne tegyél fel többet ma!")
                else:
                    if st.button(f"Kiválasztom: {j['opcio_nev']}", key=f"sel_{i}"):
                        st.session_state.kivalasztott_tippek.append({
                            'meccs': j['meccs'],
                            'opcio': j['opcio_nev'],
                            'odds': j['odds'],
                            'esely': j['esely']
                        })
                        st.experimental_rerun()

                st.markdown("---")
                st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")

    # --- KIVÁLASZTOTT TIPPEK (Napi limit) ---
    if len(st.session_state.kivalasztott_tippek) > 0:
        st.markdown("---")
        st.header(f"🧾 Kiválasztott tippek ({len(st.session_state.kivalasztott_tippek)}/{MAX_TIPP})")
        
        ossz_odds = 1.0
        for t in st.session_state.kivalasztott_tippek:
            st.write(f"- {t['meccs']} ➡️ **{t['opcio']}** (Odds: {t['odds']}, Esély: {t['esely']*100:.1f}%)")
            ossz_odds *= float(t['odds'])
        
        st.info(f"📈 **Összesített Odds (ha kombinálod):** {ossz_odds:.2f}")
        st.success(f"💰 **Várható Nyeremény (1000 Ft-ból):** {1000 * ossz_odds:.0f} Ft")
        
        if st.button("🗑️ Kiválasztott tippek törlése"):
            st.session_state.kivalasztott_tippek = []
            st.experimental_rerun()

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
