import streamlit as st
import requests
from datetime import datetime
import pytz

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo v9", page_icon="⚽", layout="centered")

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
    
    div[data-testid="column"] {
        background-color: #242B33; border-radius: 6px; padding: 5px; border: 1px solid #333;
    }
    div[data-testid="column"]:hover { border-color: #FACC15; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Elemzo (v9)</h1>", unsafe_allow_html=True)

# ÓRA
hu_tz = pytz.timezone('Europe/Budapest')
aktualis_ido = datetime.now(hu_tz)
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A lista a **legjobb jövőbeli foci meccseket** mutatja (10% teszt). A top-5 ligában extra opciók és statisztikák is vannak!")

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
FIVE_DOLLAR_API_KEY = "fb_live_693hvNiBbMfswhfmjsh4FSKDUJiJikw6"
OPENFOOT_API_KEY = "of_live_313eabc100ef4a29fa7172b619cc3f8f49a983a6e5569a992bfacc86f10b4729"
KUSZOB_MIN = 0.10
MAX_LISTA = 3  
MAX_KOMBI = 3  

# Az 5DollarFootballAPI által támogatott ligák (ingyenes csomag)
TOP_5_LEAGUES = ["soccer_epl", "soccer_spain_la_liga", "soccer_italy_serie_a", "soccer_germany_bundesliga", "soccer_france_ligue_one"]

if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = []

try:
    jeloltek = []
    most_hu = datetime.now(hu_tz)
    
    with st.spinner("1. lépés: Jövőbeli foci meccsek letöltése (The Odds API)..."):
        url_base = f"https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal"
        valasz = requests.get(url_base)
        
        if valasz.status_code == 200:
            meccsek = valasz.json()
            
            for m in meccsek:
                idopont_nyers = m.get('commence_time', '')
                if not idopont_nyers: continue
                
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
        with st.spinner("2. lépés: Statisztikák és extra opciók letöltése..."):
            for m in top_3_meccs:
                hazai = m['home_team']
                vendeg = m['away_team']
                
                # 1. Alap 1X2 opciók kinyerése a The Odds API-ból
                h2h_odds = {}
                for iroda in m.get('bookmakers', []):
                    for market in iroda.get('markets', []):
                        if market['key'] == 'h2h':
                            for k in market['outcomes']:
                                if k['name'] == hazai: h2h_odds['hazai'] = k['price']
                                elif k['name'] == vendeg: h2h_odds['vendeg'] = k['price']
                                elif k['name'] == "Draw": h2h_odds['dontetlen'] = k['price']

                # 2. OpenFoot statisztikák (Forma, Elo, H2H)
                forma_szoveg = "Nincs adat"
                elo_szoveg = "Nincs adat"
                h2h_szoveg = "Nincs adat"
                
                try:
                    # OpenFoot meccs keresése dátum és csapatnevek alapján
                    datum_str = m['kezdes_hu'].strftime("%Y-%m-%d")
                    headers_of = {'Authorization': f'Bearer {OPENFOOT_API_KEY}', 'Accept': 'application/json'}
                    res_matches = requests.get(f"https://openfootapi.com/v1/matches?date={datum_str}", headers=headers_of).json()
                    
                    if 'data' in res_matches:
                        for of_match in res_matches['data']:
                            # Egyszerű csapatnév egyeztetés
                            if hazai.lower() in of_match['homeTeam']['name'].lower() and vendeg.lower() in of_match['awayTeam']['name'].lower():
                                match_id = of_match['id']
                                # Context lekérése
                                res_ctx = requests.get(f"https://openfootapi.com/v1/matches/{match_id}/context", headers=headers_of).json()
                                if 'data' in res_ctx:
                                    ctx = res_ctx['data']
                                    if 'form' in ctx:
                                        forma_szoveg = f"H: {ctx['form'].get('home', '-')} | V: {ctx['form'].get('away', '-')}"
                                    if 'elo' in ctx:
                                        elo_szoveg = f"H: {ctx['elo'].get('home', '-')} | V: {ctx['elo'].get('away', '-')}"
                                    if 'headToHead' in ctx:
                                        h2h_szoveg = f"H: {ctx['headToHead'].get('homeWins', 0)} - V: {ctx['headToHead'].get('awayWins', 0)}"
                                break
                except Exception:
                    pass

                # 3. 5DollarFootballAPI extra opciók (BTTS, Gólszám)
                extra_opciok = []
                if m.get('sport_key') in TOP_5_LEAGUES:
                    try:
                        headers_5d = {'Authorization': f'Bearer {FIVE_DOLLAR_API_KEY}'}
                        # Itt a dokumentáció szerinti fixture_odds végpontot használjuk
                        # Mivel az 5Dollar API saját ID-t használ, egyelőre csak jelzésértékűen próbáljuk
                        # (A teljes ID egyeztetés túl bonyolult lenne ehhez a verzióhoz)
                        pass 
                    except Exception:
                        pass

                idopont_formazott = m['kezdes_hu'].strftime("%Y-%m-%d %H:%M")
                
                vegso_lista.append({
                    'meccs': f"{hazai} - {vendeg}",
                    'kezdes': idopont_formazott,
                    'legjobb_esely': m['legjobb_esely_1x2'],
                    'oddsok': h2h_odds,
                    'extra_opciok': extra_opciok,
                    'hazai': hazai,
                    'vendeg': vendeg,
                    'forma': forma_szoveg,
                    'elo': elo_szoveg,
                    'h2h': h2h_szoveg
                })

    if not vegso_lista:
        st.warning(f"📭 Nincs olyan jövőbeli foci opció, aminek az esélye elérné a {int(KUSZOB_MIN*100)}%-ot.")
    else:
        st.success(f"✅ A legjobb {len(vegso_lista)} jövőbeli foci meccs:")
        
        for i, j in enumerate(vegso_lista, 1):
            cim = f"🟡 | {j['meccs']}  —  {j['legjobb_esely']*100:.1f}%"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 0.9em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                # Statisztika doboz
                st.markdown(f"""
                    <div class="stat-box">
                        <div style="margin-bottom: 5px;"><span class="stat-label">📊 Forma:</span> <span class="stat-value">{j['forma']}</span></div>
                        <div style="margin-bottom: 5px;"><span class="stat-label">⚡ Elo:</span> <span class="stat-value">{j['elo']}</span></div>
                        <div><span class="stat-label">⚔️ H2H:</span> <span class="stat-value">{j['h2h']}</span></div>
                    </div>
                """, unsafe_allow_html=True)
                
                st.markdown("---")
                st.markdown("<div style='text-align:center; margin-bottom: 10px; color:#A0AAB5;'>Fő kimenetelek:</div>", unsafe_allow_html=True)
                
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
                
                if j['extra_opciok']:
                    st.markdown("<div style='text-align:center; margin-bottom: 10px; color:#A0AAB5;'>További opciók:</div>", unsafe_allow_html=True)
                    for idx, opcio in enumerate(j['extra_opciok']):
                        col_e1, col_e2 = st.columns([8, 2])
                        with col_e1:
                            if st.button(f"{opcio['nev']}", key=f"extra_{i}_{idx}"):
                                st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': opcio['nev'], 'odds': opcio['odds']})
                        with col_e2:
                            st.markdown(f"<div style='text-align:right; font-size:1.2em; font-weight:bold; color:#FACC15; padding-top:5px;'>{opcio['odds']}</div>", unsafe_allow_html=True)
                else:
                    st.caption("Ehhez a meccshez nincs extra opció (vagy nem top-5 liga).")

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
                st.write(f"- {t['meccs']} ➡️ **{t['opcio']}** (Odds: {t['odds']})")
                ossz_odds *= float(t['odds'])
            
            st.info(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.success(f"💰 **Várható Nyeremény (1000 Ft-ból):** {1000 * ossz_odds:.0f} Ft")
            
            if st.button("🗑️ Kiválasztott tippek törlése"):
                st.session_state.kivalasztott_tippek = []
                st.experimental_rerun()

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
