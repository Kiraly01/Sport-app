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
    
    /* Normál kártyák (zöld/sárga) */
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
    
    /* Gombok */
    .stButton>button {
        background-color: #FACC15; color: #000000; font-weight: 700; font-size: 1.1em;
        border-radius: 6px; border: none; padding: 10px 15px; width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.2s;
    }
    .stButton>button:hover { background-color: #EAB308; transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    
    /* Óra */
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
    .suggested-bet {
        color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 10px;
    }
    
    /* KOMBINÁCIÓS KÁRTYA - TELJESEN MÁS SZÍN (LILA/ARANY) */
    .kombi-box {
        background: linear-gradient(135deg, #2D1B4E, #4A2C6D);
        border: 2px solid #9D4EDD;
        border-radius: 12px;
        padding: 20px;
        margin-top: 30px;
        box-shadow: 0 8px 20px rgba(157, 78, 221, 0.4);
    }
    .kombi-title {
        color: #FACC15; /* Arany szín */
        font-size: 1.8em;
        font-weight: 900;
        text-align: center;
        margin-bottom: 15px;
        text-transform: uppercase;
        letter-spacing: 2px;
    }
    .kombi-item {
        color: #FFFFFF;
        font-size: 1.1em;
        margin-bottom: 8px;
        padding-left: 10px;
        border-left: 3px solid #FACC15;
    }
    .kombi-odds {
        color: #22C55E;
        font-size: 1.5em;
        font-weight: bold;
        text-align: center;
        margin-top: 15px;
        text-shadow: 0 0 10px rgba(34, 197, 94, 0.5);
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
MAX_LISTA = 3      

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

# --- JAVASOLT TÉT SZÁMÍTÁSA ---
def javasolt_tet(esely):
    if esely >= 0.98: return 1000
    elif esely >= 0.95: return 800
    elif esely >= 0.90: return 500
    elif esely >= 0.85: return 300
    elif esely >= 0.80: return 200
    else: return 100

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
                    
                    h2h_odds = {}
                    nyers_osszeg_globalis = 0
                    
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            if market['key'] == 'h2h':
                                kimenetek = market['outcomes']
                                nyers_oddsok = [k['price'] for k in kimenetek]
                                nyers_osszeg = sum([1/o for o in nyers_oddsok])
                                nyers_osszeg_globalis = nyers_osszeg 
                                
                                for k in kimenetek:
                                    if k['name'] == m['home_team']: h2h_odds['hazai'] = k['price']
                                    elif k['name'] == m['away_team']: h2h_odds['vendeg'] = k['price']
                                    elif k['name'] == "Draw": h2h_odds['dontetlen'] = k['price']
                    
                    ketesely_opciok = []
                    if 'hazai' in h2h_odds and 'dontetlen' in h2h_odds and nyers_osszeg_globalis > 0:
                        esely_1x = (1/h2h_odds['hazai'] + 1/h2h_odds['dontetlen']) / nyers_osszeg_globalis
                        odds_1x = 1 / esely_1x if esely_1x > 0 else 0
                        ketesely_opciok.append({'nev': f"{m['home_team']} vagy Döntetlen (1X)", 'esely': esely_1x, 'odds': odds_1x})
                    if 'vendeg' in h2h_odds and 'dontetlen' in h2h_odds and nyers_osszeg_globalis > 0:
                        esely_x2 = (1/h2h_odds['vendeg'] + 1/h2h_odds['dontetlen']) / nyers_osszeg_globalis
                        odds_x2 = 1 / esely_x2 if esely_x2 > 0 else 0
                        ketesely_opciok.append({'nev': f"{m['away_team']} vagy Döntetlen (X2)", 'esely': esely_x2, 'odds': odds_x2})
                    
                    legjobb_ketesely = None
                    for opcio in ketesely_opciok:
                        if opcio['esely'] >= KUSZOB_MIN:
                            if legjobb_ketesely is None or opcio['esely'] > legjobb_ketesely['esely']:
                                legjobb_ketesely = opcio
                    
                    if legjobb_ketesely:
                        meccs_nev = f"{m['home_team']} - {m['away_team']}"
                        if meccs_nev not in jeloltek_dict or legjobb_ketesely['esely'] > jeloltek_dict[meccs_nev]['esely']:
                            jeloltek_dict[meccs_nev] = {
                                'meccs': meccs_nev,
                                'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                                'esely': legjobb_ketesely['esely'],
                                'opcio_nev': legjobb_ketesely['nev'],
                                'odds': legjobb_ketesely['odds'],
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
                
                st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                
                tet = javasolt_tet(j['esely'])
                st.markdown(f"<div class='suggested-bet'>💰 Javasolt tét: {tet} Ft</div>", unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")

        # ==========================================
        # KOMBINÁCIÓS KÁRTYA (Külön szín)
        # ==========================================
        if len(top_lista) >= 2:
            kombi_meccsek = top_lista[:3] # Ha van 3, akkor 3, ha csak 2, akkor 2
            
            kombi_odds = 1.0
            kombi_esely = 1.0
            
            for k in kombi_meccsek:
                kombi_odds *= k['odds']
                kombi_esely *= k['esly'] if 'esly' in k else k['esely']

            st.markdown(f"""
            <div class="kombi-box">
                <div class="kombi-title">🔥 Napi Kombináció ({len(kombi_meccsek)} meccs)</div>
                {"".join([f"<div class='kombi-item'>✅ {k['meccs']} - {k['opcio_nev']}</div>" for k in kombi_meccsek])}
                <div class="kombi-odds">📈 Kombinált Odds: {kombi_odds:.2f}</div>
                <div style="text-align: center; color: #FACC15; margin-top: 10px;">
                    <b>Kombinált esély:</b> {kombi_esely*100:.1f}% (Veszteség esélye: {(1-kombi_esely)*100:.1f}%)
                </div>
                <div style="text-align: center; color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 15px;">
                    💰 Javasolt tét: 200 Ft (Kis tét, mert kombináció!)
                </div>
            </div>
            """, unsafe_allow_html=True)

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
