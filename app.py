import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# TIPPMIX PRO-S SÖTÉT KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo", page_icon="⚽", layout="centered")

st.markdown("""
    <style>
    /* Általános sötét háttér */
    .stApp {
        background-color: #12161A;
        color: #E0E0E0;
    }
    
    /* Címek letisztítása */
    h1, h2, h3 {
        color: #FFFFFF;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        font-weight: 600;
        text-align: center;
    }
    
    /* A kártyák (expanderek) - Tippmix stílusú sötét dobozok */
    .streamlit-expanderHeader {
        background-color: #1E252B !important;
        border-radius: 4px !important;
        color: #FACC15 !important; /* Tippmix sárga */
        font-weight: 600 !important;
        font-size: 1.05em !important;
        border: 1px solid #333 !important;
        padding: 12px 15px !important;
        margin-bottom: 5px;
    }
    
    .streamlit-expanderContent {
        background-color: #1A1F24 !important;
        border: 1px solid #333 !important;
        border-top: none !important;
        border-bottom-left-radius: 4px !important;
        border-bottom-right-radius: 4px !important;
        padding: 15px !important;
    }
    
    /* Gombok */
    .stButton>button {
        background-color: #FACC15; /* Tippmix sárga */
        color: #000000;
        font-weight: bold;
        border-radius: 4px;
        border: none;
        padding: 10px 24px;
        width: 100%;
    }
    .stButton>button:hover {
        background-color: #EAB308;
        color: #000000;
    }
    
    /* Checkboxok (pipák) */
    .stCheckbox {
        background-color: #242B33;
        padding: 10px;
        border-radius: 4px;
        margin-bottom: 5px;
        border: 1px solid #333;
    }
    .stCheckbox:hover {
        border: 1px solid #FACC15;
    }
    
    /* Óra */
    .clock-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 20px;
    }
    .live-clock {
        font-family: 'Courier New', Courier, monospace;
        font-size: 1.2em;
        color: #FACC15;
        background-color: #1E252B;
        padding: 10px 20px;
        border-radius: 4px;
        border: 1px solid #333;
        font-weight: bold;
    }
    
    /* Javaslat színek */
    .magaban { color: #22C55E; font-size: 0.85em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;}
    .kombi { color: #FACC15; font-size: 0.85em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;}
    .csak_kombi { color: #EF4444; font-size: 0.85em; font-weight: bold; text-transform: uppercase; letter-spacing: 1px;}
    
    /* Info dobozok */
    .stAlert {
        background-color: #1E252B;
        color: #E0E0E0;
        border-left: 4px solid #FACC15;
        border-radius: 4px;
    }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Elemzo</h1>", unsafe_allow_html=True)

# ==========================================
# ÓRA
# ==========================================
aktualis_ido = datetime.now()
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A lista a legbiztonságosabb holnapi foci tippeket mutatja. A küszöb **65%**.")

# --- BEALLITASOK ---
API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
KUSZOB_MIN = 0.40  # 65%-ra levittük!
KUSZOB_KIEMELKEDO = 0.75  # 75% felett kiemelkedő
MAX_LISTA = 10 
MAX_KOMBI = 3  

SPORTS_TO_FETCH = ["soccer"]

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

try:
    holnap_datum = (datetime.utcnow() + timedelta(days=1))
    holnap_str = holnap_datum.strftime("%Y-%m-%d")
    
    jeloltek = []
    
    with st.spinner("Foci adatok letöltése..."):
        for sport in SPORTS_TO_FETCH:
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h,totals,btts&oddsFormat=decimal&commenceTimeFrom={holnap_str}T00:00:00Z&commenceTimeTo={holnap_str}T23:59:59Z"
            
            valasz = requests.get(url)
            
            if valasz.status_code == 200:
                meccsek = valasz.json()
                
                for m in meccsek:
                    idopont_nyers = m.get('commence_time', '')
                    if idopont_nyers:
                        try:
                            kezdes_dt = datetime.strptime(idopont_nyers, "%Y-%m-%dT%H:%M:%SZ")
                            befejezes_dt = kezdes_dt + timedelta(hours=2)
                            kezdes_formazott = kezdes_dt.strftime("%Y-%m-%d %H:%M")
                            befejezes_formazott = befejezes_dt.strftime("%H:%M")
                        except Exception:
                            kezdes_formazott = idopont_nyers
                            befejezes_formazott = "?"
                    else:
                        kezdes_formazott = "Nincs idopont"
                        befejezes_formazott = "?"
                    
                    opciok_dict = {}
                    legjobb_opcio_esely = 0
                    legjobb_opcio_neve = ""
                    
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            if market['key'] not in ['h2h', 'totals', 'btts']: 
                                continue
                                
                            kimenetek = market['outcomes']
                            nyers_oddsok = [k['price'] for k in kimenetek]
                            nyers_osszeg = sum([1/o for o in nyers_oddsok])
                            
                            for k in kimenetek:
                                valoszinuseg = (1 / k['price']) / nyers_osszeg
                                
                                kimenetel_nev = ""
                                if market['key'] == 'totals':
                                    kimenetel_nev = f"⚽ [Gólszám] {k['name']} {k.get('point', '')} gól"
                                elif market['key'] == 'btts':
                                    kimenetel_nev = f"🥅 [BTTS] Mindkét csapat szerez gólt: {k['name']}"
                                elif market['key'] == 'h2h':
                                    kimenetel_nev = f"🏆 [1X2] {k['name']}"
                                
                                if valoszinuseg > legjobb_opcio_esely:
                                    legjobb_opcio_esely = valoszinuseg
                                    legjobb_opcio_neve = kimenetel_nev
                                
                                if kimenetel_nev not in opciok_dict:
                                    opciok_dict[kimenetel_nev] = {
                                        'opcio_nev': kimenetel_nev,
                                        'szazalek': valoszinuseg,
                                        'odds': k['price'],
                                        'iroda': iroda['title']
                                    }
                    
                    if legjobb_opcio_esely >= KUSZOB_MIN:
                        opciok_listaja = list(opciok_dict.values())
                        opciok_listaja.sort(key=lambda x: x['szazalek'], reverse=True)
                        
                        szint = 1 if legjobb_opcio_esely >= KUSZOB_KIEMELKEDO else 2
                        
                        jeloltek.append({
                            'sport_nev': 'Foci',
                            'meccs': f"{m['home_team']} - {m['away_team']}",
                            'kezdes': kezdes_formazott,
                            'befejezes': befejezes_formazott,
                            'legjobb_esely': legjobb_opcio_esely,
                            'legjobb_opcio_neve': legjobb_opcio_neve,
                            'opciok': opciok_listaja,
                            'szint': szint
                        })
    
    jeloltek.sort(key=lambda x: (x['szint'], -x['legjobb_esely']))
    jeloltek = jeloltek[:MAX_LISTA]
    
    kivalasztott_meccsek = []

    if not jeloltek:
        st.warning(f"📭 Holnap nincs olyan foci opció, aminek az esélye elérné a {int(KUSZOB_MIN*100)}%-ot.")
    else:
        kiemelkedo_db = sum(1 for j in jeloltek if j['szint'] == 1)
        jo_db = sum(1 for j in jeloltek if j['szint'] == 2)
        st.success(f"✅ Holnap {kiemelkedo_db} kiemelkedő (⭐) és {jo_db} jó lehetőség (🟡) van a listán.")
        
        for i, j in enumerate(jeloltek, 1):
            jelzes = "⭐ Kiemelkedő" if j['szint'] == 1 else "🟡 Jó lehetőség"
            cim = f"{jelzes} | {j['meccs']}  —  {j['legjobb_opcio_neve']} ({j['legjobb_esely']*100:.1f}%)"
            
            with st.expander(cim, expanded=False):
                st.markdown(f"<div style='font-size: 0.9em; color: #A0AAB5; margin-bottom: 10px;'>📅 Kezdés: <b>{j['kezdes']}</b> &nbsp;|&nbsp; 🏦 Legjobb iroda: <b>{j['opciok'][0]['iroda']}</b></div>", unsafe_allow_html=True)
                
                st.markdown("---")
                
                for idx, opcio in enumerate(j['opciok']):
                    if opcio['szazalek'] >= 0.75:
                        javaslat = "<span class='magaban'>Magában javasolt</span>"
                    elif opcio['szazalek'] >= 0.65:
                        javaslat = "<span class='kombi'>Kombinálható</span>"
                    else:
                        javaslat = "<span class='csak_kombi'>Csak kombinációban</span>"
                    
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
                        st.markdown(f"<div style='font-size: 1em; color: #FFFFFF;'>{opcio['opcio_nev']}</div>", unsafe_allow_html=True)
                        st.markdown(f"{javaslat} &nbsp;|&nbsp; <span style='color:#A0AAB5;'>Esély: {opcio['szazalek']*100:.1f}%</span>", unsafe_allow_html=True)
                        
                    with col_odds:
                        st.markdown(f"<div style='font-size: 1.2em; font-weight: bold; color: #FACC15; text-align: right;'>{opcio['odds']:.2f}</div>", unsafe_allow_html=True)
                        
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
