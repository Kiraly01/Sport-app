import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo v6", page_icon="⚽", layout="centered")

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
    
    .stat-box {
        background-color: #1E252B; border-left: 3px solid #FACC15;
        padding: 10px; margin-bottom: 15px; border-radius: 4px;
    }
    .stat-label { color: #A0AAB5; font-size: 0.85em; }
    .stat-value { color: #FACC15; font-size: 1.1em; font-weight: bold; }
    .value-bet { color: #22C55E; font-weight: bold; }
    
    /* Tippmix stílusú nagy gombok */
    div[data-testid="column"] {
        background-color: #242B33;
        border-radius: 6px;
        padding: 5px;
        border: 1px solid #333;
    }
    div[data-testid="column"]:hover { border-color: #FACC15; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Elemzo (v6)</h1>", unsafe_allow_html=True)

# ==========================================
# ÓRA
# ==========================================
hu_tz = pytz.timezone('Europe/Budapest')
aktualis_ido = datetime.now(hu_tz)
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A lista a **legjobb jövőbeli foci meccseket** mutatja (10% teszt), statisztikákkal!")

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
FOOTBALL_API_KEY = "ae5c4a38a960b9d414fccc18d7f1434d"
KUSZOB_MIN = 0.10  # Teszt küszöb
KUSZOB_KIEMELKEDO = 0.75  
MAX_LISTA = 3  
MAX_KOMBI = 3  

# Session state inicializálása a kiválasztott tippekhez
if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = [] # Töröljük a kiválasztást frissítéskor

try:
    jeloltek = []
    most_hu = datetime.now(hu_tz)
    
    with st.spinner("1. lépés: Jövőbeli foci meccsek letöltése..."):
        url_base = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
        valasz = requests.get(url_base)
        
        if valasz.status_code == 200:
            meccsek = valasz.json()
            
            for m in meccsek:
                idopont_nyers = m.get('commence_time', '')
                if not idopont_nyers: continue
                
                # Szűrés: csak a jövőbeli meccsek
                try:
                    kezdes_utc = datetime.strptime(idopont_nyers, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    kezdes_hu = kezdes_utc.astimezone(hu_tz)
                    if kezdes_hu <= most_hu: continue
                except: continue
                
                legjobb_esely = 0
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
                
                if legjobb_esely >= KUSZOB_MIN:
                    m['legjobb_esely_1x2'] = legjobb_esely
                    m['kezdes_hu'] = kezdes_hu
                    jeloltek.append(m)
            
            jeloltek.sort(key=lambda x: x['legjobb_esely_1x2'], reverse=True)
            top_3_meccs = jeloltek[:MAX_LISTA]
        else:
            st.error(f"Hiba a The Odds API-nál: {valasz.status_code}")
            top_3_meccs = []

    vegso_lista = []
    if top_3_meccs:
        with st.spinner("2. lépés: Opciók és statisztikák letöltése..."):
            for m in top_3_meccs:
                hazai = m['home_team']
                vendeg = m['away_team']
                
                # --- API-FOOTBALL STATISZTIKÁK ---
                forma_hazai = "Nincs adat"
                forma_vendeg = "Nincs adat"
                h2h_szoveg = "Nincs adat"
                stat_esely_hazai = None
                
                headers = {'x-rapidapi-key': FOOTBALL_API_KEY, 'x-rapidapi-host': 'v3.football.api-sports.io'}
                
                try:
                    url_form_h = f"https://v3.football.api-sports.io/fixtures?team={hazai}&last=5"
                    url_form_v = f"https://v3.football.api-sports.io/fixtures?team={vendeg}&last=5"
                    
                    res_h = requests.get(url_form_h, headers=headers).json()
                    res_v = requests.get(url_form_v, headers=headers).json()
                    
                    def szamol_gyozelem(res, csapat_nev):
                        if 'response' not in res or not res['response']: return "Nincs adat", 0
                        gyozelem = 0
                        for fixture in res['response']:
                            if fixture['teams']['home']['name'] == csapat_nev:
                                if fixture['teams']['home']['winner']: gyozelem += 1
                            else:
                                if fixture['teams']['away']['winner']: gyozelem += 1
                        return f"{gyozelem} győzelem / 5", gyozelem
                        
                    forma_hazai, gyozelem_h = szamol_gyozelem(res_h, hazai)
                    forma_vendeg, gyozelem_v = szamol_gyozelem(res_v, vendeg)
                    
                    if gyozelem_h + gyozelem_v > 0:
                        stat_esely_hazai = gyozelem_h / (gyozelem_h + gyozelem_v)
                except Exception: pass
                
                try:
                    url_h2h = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={hazai}-{vendeg}&last=5"
                    res_h2h = requests.get(url_h2h, headers=headers).json()
                    if 'response' in res_h2h and res_h2h['response']:
                        h_gy = 0; v_gy = 0
                        for fixture in res_h2h['response']:
                            if fixture['teams']['home']['name'] == hazai:
                                if fixture['teams']['home']['winner']: h_gy += 1
                                elif fixture['teams']['away']['winner']: v_gy += 1
                            else:
                                if fixture['teams']['away']['winner']: h_gy += 1
                                elif fixture['teams']['home']['winner']: v_gy += 1
                        h2h_szoveg = f"H: {h_gy} - V: {v_gy}"
                except Exception: pass

                # Opciók kinyerése az 1X2-höz
                h2h_odds = {}
                for iroda in m.get('bookmakers', []):
                    for market in iroda.get('markets', []):
                        if market['key'] == 'h2h':
                            for k in market['outcomes']:
                                if k['name'] == hazai: h2h_odds['hazai'] = k['price']
                                elif k['name'] == vendeg: h2h_odds['vendeg'] = k['price']
                                elif k['name'] == "Draw": h2h_odds['dontetlen'] = k['price']

                szint = 1 if m['legjobb_esely_1x2'] >= KUSZOB_KIEMELKEDO else 2
                idopont_formazott = m['kezdes_hu'].strftime("%Y-%m-%d %H:%M")
                
                vegso_lista.append({
                    'meccs': f"{hazai} - {vendeg}",
                    'kezdes': idopont_formazott,
                    'legjobb_esely': m['legjobb_esely_1x2'],
                    'szint': szint,
                    'stat_esely': stat_esely_hazai,
                    'forma_h': forma_hazai,
                    'forma_v': forma_vendeg,
                    'h2h': h2h_szoveg,
                    'oddsok': h2h_odds,
                    'hazai': hazai,
                    'vendeg': vendeg
                })

    if not vegso_lista:
        st.warning(f"📭 Nincs olyan jövőbeli foci opció, aminek az esélye elérné a {int(KUSZOB_MIN*100)}%-ot.")
    else:
        st.success(f"✅ A legjobb {len(vegso_lista)} jövőbeli foci meccs:")
        
        for i, j in enumerate(vegso_lista, 1):
            jelzes = "⭐ Kiemelkedő" if j['szint'] == 1 else "🟡 Jó lehetőség"
            cim = f"{jelzes} | {j['meccs']}  —  {j['legjobb_esely']*100:.1f}%"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 0.9em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                st.markdown(f"""
                    <div class="stat-box">
                        <div style="margin-bottom: 5px;"><span class="stat-label">📊 Forma (utolsó 5 meccs):</span></div>
                        <div>🏠 {j['forma_h']} &nbsp;|&nbsp; ✈️ {j['forma_v']}</div>
                        <div style="margin-top: 5px;"><span class="stat-label">⚔️ Egymás ellen (H2H):</span> <span class="stat-value">{j['h2h']}</span></div>
                        {f"<div style='margin-top: 5px;'><span class='value-bet'>💡 Statisztikai esély (Hazai): {j['stat_esely']*100:.1f}%</span></div>" if j['stat_esely'] is not None else ""}
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("<div style='text-align:center; margin-bottom: 10px; color:#A0AAB5;'>Válassz kimenetelt:</div>", unsafe_allow_html=True)
                
                # Tippmix stílusú nagy gombok
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Hazai</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('hazai', '-')}", key=f"h_{i}"):
                        if "hazai" not in [t['opcio'] for t in st.session_state.kivalasztott_tippek if t['meccs'] == j['meccs']]:
                            st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': 'hazai', 'odds': j['oddsok'].get('hazai', 0), 'szazalek': 0.0})
                with col2:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Döntetlen</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('dontetlen', '-')}", key=f"d_{i}"):
                        if "dontetlen" not in [t['opcio'] for t in st.session_state.kivalasztott_tippek if t['meccs'] == j['meccs']]:
                            st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': 'dontetlen', 'odds': j['oddsok'].get('dontetlen', 0), 'szazalek': 0.0})
                with col3:
                    st.markdown(f"<div style='text-align:center; font-size:0.8em; color:#A0AAB5;'>Vendég</div>", unsafe_allow_html=True)
                    if st.button(f"{j['oddsok'].get('vendeg', '-')}", key=f"v_{i}"):
                        if "vendeg" not in [t['opcio'] for t in st.session_state.kivalasztott_tippek if t['meccs'] == j['meccs']]:
                            st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': 'vendeg', 'odds': j['oddsok'].get('vendeg', 0), 'szazalek': 0.0})

                st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")

    # --- KOMBINÁCIÓS SZELVÉNY ---
    if len(st.session_state.kivalasztott_tippek) > 0:
        st.markdown("---")
        st.header("🧾 Kombinációs Szelvény")
        
        if len(st.session_state.kivalasztott_tippek) > MAX_KOMBI:
            st.error(f"⚠️ **FIGYELEM!** Túl sok opciót választottál ki. Maximum {MAX_KOMBI} opció javasolt!")
        else:
            ossz_odds = 1.0
            for t in st.session_state.kivalasztott_tippek:
                st.write(f"- {t['meccs']} ➡️ **{t['opcio'].capitalize()}** (Odds: {t['odds']})")
                ossz_odds *= t['odds']
            
            st.info(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.success(f"💰 **Várható Nyeremény (1000 Ft-ból):** {1000 * ossz_odds:.0f} Ft")
            
            if st.button("🗑️ Kiválasztott tippek törlése"):
                st.session_state.kivalasztott_tippek = []
                st.experimental_rerun()

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
