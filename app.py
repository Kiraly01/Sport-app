import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ==========================================
# MODERN, NAGY BETŰS KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Foci Szűrő", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #12161A; color: #E0E0E0; }
    
    /* Címek */
    h1 { 
        color: #FFFFFF; 
        font-family: 'Segoe UI', sans-serif; 
        font-weight: 800; 
        font-size: 2.8em; 
        text-align: center;
        margin-bottom: 20px;
    }
    
    /* Kártyák fejléce - meccsek nevei (nagyobb, kiemeltebb) */
    .streamlit-expanderHeader {
        background-color: #1E252B !important; 
        border-radius: 8px !important;
        color: #FACC15 !important; 
        font-weight: 800 !important; 
        font-size: 1.6em !important; 
        border: 1px solid #444 !important; 
        padding: 18px 20px !important; 
        margin-bottom: 8px;
        text-shadow: 1px 1px 2px rgba(0,0,0,0.5);
    }
    
    /* Kártyák tartalma */
    .streamlit-expanderContent {
        background-color: #161A1F !important; 
        border: 1px solid #444 !important;
        border-top: none !important; 
        border-bottom-left-radius: 8px !important; 
        border-bottom-right-radius: 8px !important;
        padding: 20px !important;
    }
    
    /* Gombok - kicsit kisebb, letisztultabb */
    .stButton>button {
        background-color: #FACC15; 
        color: #000000; 
        font-weight: 700; 
        font-size: 1.1em;
        border-radius: 6px;
        border: none; 
        padding: 10px 15px; 
        width: 100%;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        transition: all 0.2s;
    }
    .stButton>button:hover { 
        background-color: #EAB308; 
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Óra */
    .clock-container { 
        display: flex; 
        justify-content: center; 
        align-items: center; 
        margin-top: 20px; 
        margin-bottom: 30px; 
    }
    .live-clock {
        font-family: 'Courier New', monospace; 
        font-size: 2.2em; 
        color: #FACC15;
        background-color: #1E252B; 
        padding: 20px 40px; 
        border-radius: 12px;
        border: 2px solid #444; 
        font-weight: 900;
        letter-spacing: 3px;
        box-shadow: 0 8px 16px rgba(0,0,0,0.4);
    }
    
    /* Kártyák oszlopai */
    div[data-testid="column"] {
        background-color: #242B33; 
        border-radius: 8px; 
        padding: 10px; 
        border: 1px solid #444;
        transition: all 0.2s;
    }
    div[data-testid="column"]:hover { 
        border-color: #FACC15; 
        transform: scale(1.02);
    }
    
    /* Kártyákon belüli szövegek mérete */
    .stMarkdown p {
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Szűrő</h1>", unsafe_allow_html=True)

# ==========================================
# ÉLŐ ÓRA (st.fragment - csak az óra frissül!)
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

st.write("A lista a **45% feletti** legjobb esélyű, **még el nem kezdődött** foci meccseket mutatja (max 10).")

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
KUSZOB_MIN = 0.45  # 45%-os minimum küszöb
MAX_LISTA = 10  

if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = []

try:
    most_utc = datetime.now(pytz.utc)
    hu_tz = pytz.timezone('Europe/Budapest')
    
    # Dátumok: mai és holnapi
    ma_str = most_utc.strftime("%Y-%m-%d")
    holnap_str = (most_utc + timedelta(days=1)).strftime("%Y-%m-%d")
    
    jeloltek_dict = {}
    
    with st.spinner("Foci meccsek letöltése (The Odds API)..."):
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
                        
                        # ÉLŐ MECCSEK KISZŰRÉSE
                        if kezdes_utc <= most_utc:
                            continue
                            
                        kezdes_hu = kezdes_utc.astimezone(hu_tz)
                    except: continue
                    
                    legjobb_esely = 0
                    h2h_odds = {}
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            if market['key'] == 'h2h':
                                kimenetek = market['outcomes']
                                nyers_oddsok = [k['price'] for k in kimenetek]
                                nyers_osszeg = sum([1/o for o in nyers_oddsok])
                                for k in kimenetek:
                                    esely = (1 / k['price']) / nyers_osszeg
                                    if esely > legjobb_esely:
                                        legjobb_esely = esely
                                    if k['name'] == m['home_team']: h2h_odds['hazai'] = k['price']
                                    elif k['name'] == m['away_team']: h2h_odds['vendeg'] = k['price']
                                    elif k['name'] == "Draw": h2h_odds['dontetlen'] = k['price']
                    
                    if legjobb_esely >= KUSZOB_MIN:
                        meccs_nev = f"{m['home_team']} - {m['away_team']}"
                        if meccs_nev not in jeloltek_dict or legjobb_esely > jeloltek_dict[meccs_nev]['legjobb_esely']:
                            jeloltek_dict[meccs_nev] = {
                                'meccs': meccs_nev,
                                'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                                'legjobb_esely': legjobb_esely,
                                'oddsok': h2h_odds,
                                'hazai': m['home_team'],
                                'vendeg': m['away_team']
                            }
    
    jeloltek = list(jeloltek_dict.values())
    jeloltek.sort(key=lambda x: x['legjobb_esely'], reverse=True)
    top_lista = jeloltek[:MAX_LISTA]

    if not top_lista:
        st.warning(f"📭 Nincs olyan jövőbeli foci meccs, aminek az esélye elérné a {int(KUSZOB_MIN*100)}%-ot.")
    else:
        st.success(f"✅ A legjobb {len(top_lista)} jövőbeli foci meccs (45% felett):")
        
        for i, j in enumerate(top_lista, 1):
            cim = f"🟡 | {j['meccs']}  —  {j['legjobb_esely']*100:.1f}%"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 1em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div style='text-align:center; font-size:0.9em; color:#A0AAB5;'>Hazai</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('hazai', '-')}", key=f"h_{i}"):
                        st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': f"{j['hazai']} (Hazai)", 'odds': j['oddsok'].get('hazai', 1.0)})
                with col2:
                    st.markdown(f"<div style='text-align:center; font-size:0.9em; color:#A0AAB5;'>Döntetlen</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('dontetlen', '-')}", key=f"d_{i}"):
                        st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': "Döntetlen", 'odds': j['oddsok'].get('dontetlen', 1.0)})
                with col3:
                    st.markdown(f"<div style='text-align:center; font-size:0.9em; color:#A0AAB5;'>Vendég</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('vendeg', '-')}", key=f"v_{i}"):
                        st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': f"{j['vendeg']} (Vendég)", 'odds': j['oddsok'].get('vendeg', 1.0)})

                st.markdown("---")
                st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")

    # --- KOMBINÁCIÓS SZELVÉNY ---
    if len(st.session_state.kivalasztott_tippek) > 0:
        st.markdown("---")
        st.header("🧾 Kombinációs Szelvény")
        
        if len(st.session_state.kivalasztott_tippek) > 3:
            st.error("⚠️ **FIGYELEM!** Túl sok opciót választottál ki. Maximum 3 opció javasolt!")
        else:
            ossz_odds = 1.0
            for t in st.session_state.kivalasztott_tippek:
                st.write(f"- {t['meccs']} ➡️ **{t['opcio']}** (Odds: {t['odds']})")
                ossz_odds *= float(t['odds'])
            
            st.info(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.success(f"💰 **Várható Nyeremény (1000 Ft-ból):** {1000 * ossz_odds:.0f} Ft")
            
            if st.button("🗑️ Kiválasztott tippek törlése"):
                st.session_state.kivalasztott_tippek = []
                st.experimental_rerun()

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
