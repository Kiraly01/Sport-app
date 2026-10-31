import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Foci Szűrő", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #12161A; color: #E0E0E0; }
    h1, h2, h3 { color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-weight: 600; text-align: center; }
    
    .streamlit-expanderHeader {
        background-color: #1E252B !important; border-radius: 4px !important;
        color: #FACC15 !important; font-weight: 600 !important; font-size: 1.1em !important;
        border: 1px solid #333 !important; padding: 12px 15px !important; margin-bottom: 5px;
    }
    .streamlit-expanderContent {
        background-color: #161A1F !important; border: 1px solid #333 !important;
        border-top: none !important; border-bottom-left-radius: 4px !important; border-bottom-right-radius: 4px !important;
        padding: 15px !important;
    }
    
    .stButton>button {
        background-color: #FACC15; color: #000000; font-weight: bold; border-radius: 4px;
        border: none; padding: 10px 24px; width: 100%;
    }
    .stButton>button:hover { background-color: #EAB308; color: #000000; }
    
    .clock-container { display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 20px; }
    .live-clock {
        font-family: 'Courier New', monospace; font-size: 1.2em; color: #FACC15;
        background-color: #1E252B; padding: 10px 20px; border-radius: 4px;
        border: 1px solid #333; font-weight: bold;
    }
    
    div[data-testid="column"] {
        background-color: #242B33; border-radius: 6px; padding: 5px; border: 1px solid #333;
    }
    div[data-testid="column"]:hover { border-color: #FACC15; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Szűrő</h1>", unsafe_allow_html=True)

# ÓRA
hu_tz = pytz.timezone('Europe/Budapest')
aktualis_ido = datetime.now(hu_tz)
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A lista a **mai és holnapi** legjobb esélyű foci meccseket mutatja (max 10).")

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
MAX_LISTA = 10  

if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = []

try:
    most_hu = datetime.now(hu_tz)
    most_utc = datetime.now(pytz.utc)
    
    # Dátumok: mai és holnapi
    ma_str = most_utc.strftime("%Y-%m-%d")
    holnap_str = (most_utc + timedelta(days=1)).strftime("%Y-%m-%d")
    
    jeloltek = []
    
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
                        if kezdes_utc <= most_utc: continue
                        kezdes_hu = kezdes_utc.astimezone(hu_tz)
                    except: continue
                    
                    # Kiszámoljuk a legjobb esélyt (1X2)
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
                    
                    if legjobb_esely > 0:
                        jeloltek.append({
                            'meccs': f"{m['home_team']} - {m['away_team']}",
                            'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                            'legjobb_esely': legjobb_esely,
                            'oddsok': h2h_odds,
                            'hazai': m['home_team'],
                            'vendeg': m['away_team']
                        })
    
    # Rendezés a legjobb esély szerint, és a top 10
    jeloltek.sort(key=lambda x: x['legjobb_esely'], reverse=True)
    top_lista = jeloltek[:MAX_LISTA]

    if not top_lista:
        st.warning("📭 Nincs olyan foci meccs a mai és holnapi napon, ami megfelelne a feltételeknek.")
    else:
        st.success(f"✅ A legjobb {len(top_lista)} foci meccs (mai és holnapi):")
        
        for i, j in enumerate(top_lista, 1):
            cim = f"🟡 | {j['meccs']}  —  {j['legjobb_esely']*100:.1f}%"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 0.9em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Hazai</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('hazai', '-')}", key=f"h_{i}"):
                        st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': f"{j['hazai']} (Hazai)", 'odds': j['oddsok'].get('hazai', 1.0)})
                with col2:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Döntetlen</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('dontetlen', '-')}", key=f"d_{i}"):
                        st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': "Döntetlen", 'odds': j['oddsok'].get('dontetlen', 1.0)})
                with col3:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Vendég</div>", unsafe_allow_html=True)
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
