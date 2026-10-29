import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo v4", page_icon="⚽", layout="centered")

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
    
    .stCheckbox { background-color: #242B33; padding: 8px; border-radius: 4px; margin-bottom: 5px; border: 1px solid #333; }
    .stCheckbox:hover { border: 1px solid #FACC15; }
    
    .clock-container { display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 20px; }
    .live-clock {
        font-family: 'Courier New', monospace; font-size: 1.2em; color: #FACC15;
        background-color: #1E252B; padding: 10px 20px; border-radius: 4px;
        border: 1px solid #333; font-weight: bold;
    }
    
    .stat-box {
        background-color: #1E252B;
        border-left: 3px solid #FACC15;
        padding: 10px;
        margin-bottom: 10px;
        border-radius: 4px;
    }
    .stat-label { color: #A0AAB5; font-size: 0.85em; }
    .stat-value { color: #FACC15; font-size: 1.1em; font-weight: bold; }
    .value-bet { color: #22C55E; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Elemzo (v4 Teszt)</h1>", unsafe_allow_html=True)

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

st.write("A lista a **legjobb jövőbeli foci meccseket** mutatja (10% teszt küszöb), statisztikákkal!")

# --- BEALLITASOK ---
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
FOOTBALL_API_KEY = "ae5c4a38a960b9d414fccc18d7f1434d"
KUSZOB_MIN = 0.10  # 10%-ra levéve a teszthez
KUSZOB_KIEMELKEDO = 0.75  
MAX_LISTA = 3  
MAX_KOMBI = 3  

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

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
        with st.spinner("2. lépés: Opciók és statisztikák (Forma, H2H) letöltése..."):
            for m in top_3_meccs:
                event_id = m['id']
                hazai = m['home_team']
                vendeg = m['away_team']
                
                opciok_dict = {}
                legjobb_opcio_esely = 0
                
                url_event = f"https://api.the-odds-api.com/v4/sports/soccer/events/{event_id}/odds/?apiKey={ODDS_API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal"
                valasz_event = requests.get(url_event)
                
                if valasz_event.status_code == 200:
                    event_data = valasz_event.json()
                    for iroda in event_data.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            kimenetek = market['outcomes']
                            nyers_oddsok = [k['price'] for k in kimenetek]
                            nyers_osszeg = sum([1/o for o in nyers_oddsok])
                            
                            for k in kimenetek:
                                valoszinuseg = (1 / k['price']) / nyers_osszeg
                                kimenetel_nev = ""
                                if market['key'] == 'totals': kimenetel_nev = f"⚽ [Gólszám] {k['name']} {k.get('point', '')} gól"
                                elif market['key'] == 'btts': kimenetel_nev = f"🥅 [BTTS] Mindkét csapat szerez gólt: {k['name']}"
                                elif market['key'] == 'h2h': kimenetel_nev = f"🏆 [1X2] {k['name']}"
                                
                                if valoszinuseg > legjobb_opcio_esely: legjobb_opcio_esely = valoszinuseg
                                if kimenetel_nev not in opciok_dict:
                                    opciok_dict[kimenetel_nev] = {'opcio_nev': kimenetel_nev, 'szazalek': valoszinuseg, 'odds': k['price'], 'iroda': iroda['title']}
                else:
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            if market['key'] == 'h2h':
                                kimenetek = market['outcomes']
                                nyers_oddsok = [k['price'] for k in kimenetek]
                                nyers_osszeg = sum([1/o for o in nyers_oddsok])
                                for k in kimenetek:
                                    valoszinuseg = (1 / k['price']) / nyers_osszeg
                                    kimenetel_nev = f"🏆 [1X2] {k['name']}"
                                    if valoszinuseg > legjobb_opcio_esely: legjobb_opcio_esely = valoszinuseg
                                    if kimenetel_nev not in opciok_dict:
                                        opciok_dict[kimenetel_nev] = {'opcio_nev': kimenetel_nev, 'szazalek': valoszinuseg, 'odds': k['price'], 'iroda': iroda['title']}
                
                opciok_listaja = list(opciok_dict.values())
                opciok_listaja.sort(key=lambda x: x['szazalek'], reverse=True)
                
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
                        return f"{gyozelem} győzelem / 5 meccs", gyozelem
                        
                    forma_hazai, gyozelem_h = szamol_gyozelem(res_h, hazai)
                    forma_vendeg, gyozelem_v = szamol_gyozelem(res_v, vendeg)
                    
                    if gyozelem_h + gyozelem_v > 0:
                        stat_esely_hazai = gyozelem_h / (gyozelem_h + gyozelem_v)
                        
                except Exception:
                    pass
                
                try:
                    url_h2h = f"https://v3.football.api-sports.io/fixtures/headtohead?h2h={hazai}-{vendeg}&last=5"
                    res_h2h = requests.get(url_h2h, headers=headers).json()
                    if 'response' in res_h2h and res_h2h['response']:
                        h_gyozelem = 0
                        v_gyozelem = 0
                        for fixture in res_h2h['response']:
                            if fixture['teams']['home']['name'] == hazai:
                                if fixture['teams']['home']['winner']: h_gyozelem += 1
                                elif fixture['teams']['away']['winner']: v_gyozelem += 1
                            else:
                                if fixture['teams']['away']['winner']: h_gyozelem += 1
                                elif fixture['teams']['home']['winner']: v_gyozelem += 1
                        h2h_szoveg = f"H: {h_gyozelem} - V: {v_gyozelem}"
                except Exception:
                    pass
                
                szint = 1 if legjobb_opcio_esely >= KUSZOB_KIEMELKEDO else 2
                idopont_formazott = m['kezdes_hu'].strftime("%Y-%m-%d %H:%M")
                
                vegso_lista.append({
                    'meccs': f"{hazai} - {vendeg}",
                    'kezdes': idopont_formazott,
                    'legjobb_esely': legjobb_opcio_esely,
                    'opciok': opciok_listaja,
                    'szint': szint,
                    'stat_esely': stat_esely_hazai,
                    'forma_h': forma_hazai,
                    'forma_v': forma_vendeg,
                    'h2h': h2h_szoveg
                })

    kivalasztott_meccsek = []

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
                
                for idx, opcio in enumerate(j['opciok']):
                    if opcio['szazalek'] >= 0.75: javaslat = "<span style='color:#22C55E;font-size:0.8em;font-weight:bold;'>MAGÁBAN JAVASOLT</span>"
                    elif opcio['szazalek'] >= 0.10: javaslat = "<span style='color:#FACC15;font-size:0.8em;font-weight:bold;'>KOMBINÁLHATÓ</span>"
                    else: javaslat = "<span style='color:#EF4444;font-size:0.8em;font-weight:bold;'>CSAK KOMBINÁCIÓBAN</span>"
                    
                    cb_key = f"cb_{i}_{idx}"
                    col_check, col_info, col_odds = st.columns([1, 6, 2])
                    
                    with col_check:
                        if st.checkbox("", key=cb_key, label_visibility="collapsed"):
                            kivalasztott_meccsek.append({
                                'meccs': j['meccs'],
                                'valasztott_opcio': opcio['opcio_nev'],
                                'szazalek': opcio['szazalek'],
                                'odds': opcio['odds']
                            })
                    
                    with col_info:
                        st.markdown(f"<div style='font-size: 1em; color: #FFFFFF; margin-bottom: 2px;'>{opcio['opcio_nev']}</div>", unsafe_allow_html=True)
                        st.markdown(f"{javaslat} <span style='color:#A0AAB5;font-size:0.8em;'>| Esély: {opcio['szazalek']*100:.1f}%</span>", unsafe_allow_html=True)
                        
                    with col_odds:
                        st.markdown(f"<div style='font-size: 1.3em; font-weight: bold; color: #FACC15; text-align: right;'>{opcio['odds']:.2f}</div>", unsafe_allow_html=True)
                        
                    st.markdown("<hr style='margin: 5px 0; border-color: #333;'>", unsafe_allow_html=True)

                st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")

    if len(kivalasztott_meccsek) > 0:
        st.markdown("---")
        st.header("🧾 Kombinációs Szelvény")
        
        if len(kivalasztott_meccsek) > MAX_KOMBI:
            st.error(f"⚠️ **FIGYELEM!** Túl sok opciót választottál ki ({len(kivalasztott_meccsek)} db). A biztonságos kombinációhoz **maximum {MAX_KOMBI} opció** javasolt!")
        else:
            if len(kivalasztott_meccsek) == 1:
                st.write("ℹ️ **Szimpla fogadás** (1 esemény)")
                komb_esely = kivalasztott_meccsek[0]['szazalek']
                ossz_odds = kivalasztott_meccsek[0]['odds']
            else:
                st.write(f"ℹ️ **Kombinációs fogadás** ({len(kivalasztott_meccsek)} esemény)")
                komb_esely = 1.0
                ossz_odds = 1.0
                for m in kivalasztott_meccsek:
                    komb_esely *= m['szazalek']
                    ossz_odds *= m['odds']
            
            komb_tet = st.number_input("Tét összege (Ft):", min_value=100, value=1000, step=500, key="komb_tet")
            varhato_nyeremeny = komb_tet * ossz_odds
            
            for m in kivalasztott_meccsek:
                st.write(f"- {m['meccs']} ➡️ **{m['valasztott_opcio']}** (Esély: {m['szazalek']*100:.1f}%)")
            
            st.info(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.info(f"🎯 **Kombinált Esély (%):** {komb_esely*100:.1f}% (Veszteség esélye: {(1-komb_esely)*100:.1f}%)")
            st.success(f"💰 **Várható Nyeremény:** {varhato_nyeremeny:.0f} Ft (Nettó: +{varhato_nyeremeny - komb_tet:.0f} Ft)")

except Exception as e:
    st.error("Váratlan hiba történt: " + str(e))
