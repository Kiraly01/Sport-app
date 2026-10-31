import streamlit as st
import requests
from datetime import datetime
import pytz

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Foci Elemzo v12", page_icon="⚽", layout="centered")

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
        font-size: 0.9em;
    }
    .stat-label { color: #A0AAB5; }
    .stat-value { color: #FACC15; font-weight: bold; }
    
    div[data-testid="column"] {
        background-color: #242B33; border-radius: 6px; padding: 5px; border: 1px solid #333;
    }
    div[data-testid="column"]:hover { border-color: #FACC15; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Elemzo (v12)</h1>", unsafe_allow_html=True)

# ÓRA
hu_tz = pytz.timezone('Europe/Budapest')
aktualis_ido = datetime.now(hu_tz)
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A lista a **top-5 liga legbiztosabb meccseit** mutatja, tabella, forma és H2H statisztikákkal!")

# --- BEALLITASOK ---
FIVE_DOLLAR_API_KEY = "fb_live_693hvNiBbMfswhfmjsh4FSKDUJiJikw6"
KUSZOB_MIN = 0.10  # Teszt küszöb (később emelhetjük)
MAX_LISTA = 3  
MAX_KOMBI = 3  

# A top-5 liga ID-i az 5Dollar API-nál (ezeket a /v1/leagues végpontról lehetne pontosítani, de a dokumentáció alapján ezek a fő ligák)
# Mivel a free tier csak ezekre működik, itt fixáljuk őket
TOP_LEAGUES = {
    "Premier League": 1,  # Példa ID, a valóságban a /v1/leagues-ből kellene lekérni
    "La Liga": 2,
    "Serie A": 3,
    "Bundesliga": 4,
    "Ligue 1": 5
}

if "kivalasztott_tippek" not in st.session_state:
    st.session_state.kivalasztott_tippek = []

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()
    st.session_state.kivalasztott_tippek = []

try:
    headers = {'Authorization': f'Bearer {FIVE_DOLLAR_API_KEY}'}
    most_hu = datetime.now(hu_tz)
    
    jeloltek = []
    
    with st.spinner("1. lépés: Top-5 liga meccseinek letöltése (5Dollar API)..."):
        # Lekérjük a mai és holnapi meccseket a top-5 ligából
        # A dokumentáció szerint a /v1/fixtures?start_time=... adja a meccseket
        datum_str = most_hu.strftime("%Y-%m-%d")
        url_fixtures = f"https://api.5dollarfootballapi.com/v1/fixtures?start_time={datum_str}"
        res_fixtures = requests.get(url_fixtures, headers=headers)
        
        if res_fixtures.status_code == 200:
            fixtures_data = res_fixtures.json()
            if 'data' in fixtures_data:
                for fix in fixtures_data['data']:
                    # Szűrés: csak a top-5 liga (a league_id alapján)
                    league_id = fix.get('league', {}).get('id')
                    if league_id not in TOP_LEAGUES.values():
                        continue
                    
                    # Szűrés: csak a jövőbeli meccsek
                    kezdes_str = fix.get('kickoff', '')
                    if not kezdes_str: continue
                    try:
                        kezdes_dt = datetime.fromisoformat(kezdes_str.replace('Z', '+00:00'))
                        if kezdes_dt <= datetime.now(pytz.utc): continue
                    except: continue
                    
                    jeloltek.append(fix)
        
        # Ha nincs elég meccs, próbáljunk holnapra is
        if len(jeloltek) < 5:
            holnap_str = (most_hu + timedelta(days=1)).strftime("%Y-%m-%d")
            url_fixtures_holnap = f"https://api.5dollarfootballapi.com/v1/fixtures?start_time={holnap_str}"
            res_fixtures_holnap = requests.get(url_fixtures_holnap, headers=headers)
            if res_fixtures_holnap.status_code == 200:
                fixtures_data_holnap = res_fixtures_holnap.json()
                if 'data' in fixtures_data_holnap:
                    for fix in fixtures_data_holnap['data']:
                        league_id = fix.get('league', {}).get('id')
                        if league_id not in TOP_LEAGUES.values():
                            continue
                        kezdes_str = fix.get('kickoff', '')
                        if not kezdes_str: continue
                        try:
                            kezdes_dt = datetime.fromisoformat(kezdes_str.replace('Z', '+00:00'))
                            if kezdes_dt <= datetime.now(pytz.utc): continue
                        except: continue
                        jeloltek.append(fix)

    # 2. lépés: A legjobb meccsek kiválasztása és statisztikák lekérése
    vegso_lista = []
    if jeloltek:
        with st.spinner("2. lépés: Statisztikák (tabella, forma) letöltése..."):
            # Első körben rendezzük a meccseket a hazai csapat tabella helyezése alapján
            # Ehhez le kell kérnünk a tabellákat
            tabellak = {}
            for liga_nev, liga_id in TOP_LEAGUES.items():
                try:
                    res_table = requests.get(f"https://api.5dollarfootballapi.com/v1/standings?league={liga_id}", headers=headers)
                    if res_table.status_code == 200:
                        table_data = res_table.json()
                        if 'data' in table_data and 'standings' in table_data['data']:
                            tabellak[liga_id] = table_data['data']['standings']
                except: pass
            
            for fix in jeloltek[:MAX_LISTA * 2]:  # Többet nézünk, hogy legyen miből válogatni
                hazai = fix['teams']['home']['name']
                vendeg = fix['teams']['away']['name']
                hazai_id = fix['teams']['home']['id']
                vendeg_id = fix['teams']['away']['id']
                league_id = fix['league']['id']
                
                # Tabella adatok
                hazai_tabla = "Nincs adat"
                vendeg_tabla = "Nincs adat"
                if league_id in tabellak:
                    for row in tabellak[league_id]:
                        if row['team']['id'] == hazai_id:
                            hazai_tabla = f"{row['position']}. hely, {row['points']} pont"
                        elif row['team']['id'] == vendeg_id:
                            vendeg_tabla = f"{row['position']}. hely, {row['points']} pont"
                
                # Forma lekérése (utolsó 5 meccs)
                forma_hazai = "Nincs adat"
                forma_vendeg = "Nincs adat"
                try:
                    res_form_h = requests.get(f"https://api.5dollarfootballapi.com/v1/teams/{hazai_id}/fixtures?status=finished&per_page=5", headers=headers)
                    if res_form_h.status_code == 200:
                        form_data = res_form_h.json()
                        if 'data' in form_data and form_data['data']:
                            # Egyszerű forma számítás: győzelmek száma
                            gyozelem = 0
                            for f in form_data['data'][:5]:
                                if f['teams']['home']['id'] == hazai_id:
                                    if f['teams']['home']['winner']: gyozelem += 1
                                else:
                                    if f['teams']['away']['winner']: gyozelem += 1
                            forma_hazai = f"{gyozelem} győzelem / 5"
                except: pass
                
                try:
                    res_form_v = requests.get(f"https://api.5dollarfootballapi.com/v1/teams/{vendeg_id}/fixtures?status=finished&per_page=5", headers=headers)
                    if res_form_v.status_code == 200:
                        form_data = res_form_v.json()
                        if 'data' in form_data and form_data['data']:
                            gyozelem = 0
                            for f in form_data['data'][:5]:
                                if f['teams']['home']['id'] == vendeg_id:
                                    if f['teams']['home']['winner']: gyozelem += 1
                                else:
                                    if f['teams']['away']['winner']: gyozelem += 1
                            forma_vendeg = f"{gyozelem} győzelem / 5"
                except: pass

                # Odds lekérése a meccshez
                h2h_odds = {}
                extra_opciok = []
                try:
                    res_odds = requests.get(f"https://api.5dollarfootballapi.com/v1/fixtures/{fix['id']}/odds", headers=headers)
                    if res_odds.status_code == 200:
                        odds_data = res_odds.json()
                        if 'data' in odds_data and 'bet365' in odds_data['data']:
                            b365 = odds_data['data']['bet365']
                            # 1X2
                            if '1x2' in b365 and b365['1x2'].get('closing'):
                                h2h_odds['hazai'] = b365['1x2']['closing'].get('home')
                                h2h_odds['dontetlen'] = b365['1x2']['closing'].get('draw')
                                h2h_odds['vendeg'] = b365['1x2']['closing'].get('away')
                            # BTTS
                            if 'btts' in b365 and b365['btts'].get('closing'):
                                extra_opciok.append({'nev': 'BTTS - Igen', 'odds': b365['btts']['closing'].get('yes')})
                                extra_opciok.append({'nev': 'BTTS - Nem', 'odds': b365['btts']['closing'].get('no')})
                            # Gólszám (2.5)
                            if 'goal_line' in b365 and b365['goal_line'].get('closing'):
                                gl = b365['goal_line']['closing']
                                if isinstance(gl, list) and len(gl) > 0:
                                    for line in gl:
                                        if line.get('line') == 2.5:
                                            extra_opciok.append({'nev': 'Több mint 2.5 gól', 'odds': line.get('over')})
                                            extra_opciok.append({'nev': 'Kevesebb mint 2.5 gól', 'odds': line.get('under')})
                except: pass
                
                if h2h_odds.get('hazai'):
                    # Kiszámoljuk a "biztonsági pontszámot" a tabella és forma alapján
                    # (Egyszerű logika: minél jobb a tabella helyezés és forma, annál magasabb)
                    biztonsagi_pont = 0
                    if "1. hely" in hazai_tabla or "2. hely" in hazai_tabla:
                        biztonsagi_pont += 2
                    if "1. hely" in vendeg_tabla or "2. hely" in vendeg_tabla:
                        biztonsagi_pont += 2
                    if "4 győzelem" in forma_hazai or "5 győzelem" in forma_hazai:
                        biztonsagi_pont += 1
                    if "4 győzelem" in forma_vendeg or "5 győzelem" in forma_vendeg:
                        biztonsagi_pont += 1
                    
                    vegso_lista.append({
                        'meccs': f"{hazai} - {vendeg}",
                        'kezdes': kezdes_dt.astimezone(hu_tz).strftime("%Y-%m-%d %H:%M"),
                        'oddsok': h2h_odds,
                        'extra_opciok': extra_opciok,
                        'hazai_tabla': hazai_tabla,
                        'vendeg_tabla': vendeg_tabla,
                        'forma_h': forma_hazai,
                        'forma_v': forma_vendeg,
                        'biztonsagi_pont': biztonsagi_pont,
                        'hazai': hazai,
                        'vendeg': vendeg
                    })
            
            # Rendezés a biztonsági pontszám szerint (csökkenő)
            vegso_lista.sort(key=lambda x: x['biztonsagi_pont'], reverse=True)
            vegso_lista = vegso_lista[:MAX_LISTA]

    if not vegso_lista:
        st.warning("📭 Nincs olyan top-5 ligás meccs, ami megfelelne a feltételeknek.")
    else:
        st.success(f"✅ A legbiztosabb {len(vegso_lista)} top-5 ligás meccs:")
        
        for i, j in enumerate(vegso_lista, 1):
            cim = f"🟡 | {j['meccs']}  —  Biztonsági pont: {j['biztonsagi_pont']}"
            
            with st.expander(cim, expanded=True):
                st.markdown(f"<div style='font-size: 0.9em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                
                # Statisztika doboz
                st.markdown(f"""
                    <div class="stat-box">
                        <div><span class="stat-label">🏆 Tabella:</span> <span class="stat-value">H: {j['hazai_tabla']} | V: {j['vendeg_tabla']}</span></div>
                        <div style="margin-top: 5px;"><span class="stat-label">📊 Forma:</span> <span class="stat-value">H: {j['forma_h']} | V: {j['forma_v']}</span></div>
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
                        if opcio['odds']:
                            col_e1, col_e2 = st.columns([8, 2])
                            with col_e1:
                                if st.button(f"{opcio['nev']}", key=f"extra_{i}_{idx}"):
                                    st.session_state.kivalasztott_tippek.append({'meccs': j['meccs'], 'opcio': opcio['nev'], 'odds': opcio['odds']})
                            with col_e2:
                                st.markdown(f"<div style='text-align:right; font-size:1.2em; font-weight:bold; color:#FACC15; padding-top:5px;'>{opcio['odds']}</div>", unsafe_allow_html=True)

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
