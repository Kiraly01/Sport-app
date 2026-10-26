import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# MODERN KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo", page_icon="🏆", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #0E1117; }
    h1, h2, h3 { color: #ffffff; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; text-align: center; }
    
    .streamlit-expanderHeader {
        background-color: #1E2129 !important; border-radius: 10px !important;
        color: #00D4FF !important; font-weight: bold !important; font-size: 1.1em !important;
        border: 1px solid #333 !important; padding: 10px !important;
    }
    .streamlit-expanderContent {
        background-color: #161A22 !important; border: 1px solid #333 !important;
        border-top: none !important; border-bottom-left-radius: 10px !important; border-bottom-right-radius: 10px !important;
        padding: 15px !important;
    }
    .stButton>button {
        background-color: #00D4FF; color: #000000; font-weight: bold; border-radius: 8px;
        border: none; padding: 10px 24px; transition: 0.3s;
    }
    .stButton>button:hover { background-color: #0099cc; color: #ffffff; }
    .stNumberInput>div>div>input {
        background-color: #1E2129; color: white; border: 1px solid #00D4FF; border-radius: 5px;
    }
    .stAlert { background-color: #1c3322; color: #4ade80; border: 1px solid #4ade80; border-radius: 8px; }
    
    .clock-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    .live-clock {
        font-family: 'Courier New', Courier, monospace;
        font-size: 1.2em;
        color: #00D4FF;
        background-color: #1E2129;
        padding: 15px 30px;
        border-radius: 12px;
        border: 2px solid #333;
        font-weight: bold;
        letter-spacing: 1px;
        box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.1);
    }
    
    .hazai { color: #4ade80; font-weight: bold; }
    .dontetlen { color: #facc15; font-weight: bold; }
    .vendeg { color: #f87171; font-weight: bold; }
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1>🏆 Napi Sport Elemzo</h1>", unsafe_allow_html=True)

# ==========================================
# ÓRA
# ==========================================
aktualis_ido = datetime.now()
st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
""", unsafe_allow_html=True)

st.write("Pipáld ki a kívánt fogadási opciókat! (A lista a holnapi meccseket mutatja)")

# --- BEALLITASOK ---
API_KEY = "058f2a77969ebea27f4dcdeb19290442"
KUSZOB = 0.10 # 50%-ra állítva, hogy biztosan lássunk meccseket
MAX_LISTA = 10 
MAX_KOMBI = 3  

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

try:
    holnap_datum = (datetime.utcnow() + timedelta(days=1))
    holnap_str = holnap_datum.strftime("%Y-%m-%d")
    
    sports_url = f"https://api.the-odds-api.com/v4/sports/?apiKey={API_KEY}"
    sports_valasz = requests.get(sports_url)
    
    if sports_valasz.status_code == 200:
        osszes_sport = sports_valasz.json()
        aktiv_sportok = [s['key'] for s in osszes_sport if not s.get('has_outrights', True)]
    else:
        aktiv_sportok = []

    jeloltek = []
    
    with st.spinner("Adatok letöltése az összes sportágból..."):
        for sport in aktiv_sportok:
            # Focira kérjük a gólokat és BTTS-t is, másra csak az 1X2-t
            markets_to_fetch = "h2h,totals,btts" if sport == "soccer" else "h2h"
            url = f"https://api.the-odds-api.com/v4/sports/{sport}/odds/?apiKey={API_KEY}&regions=eu&markets={markets_to_fetch}&oddsFormat=decimal&commenceTimeFrom={holnap_str}T00:00:00Z&commenceTimeTo={holnap_str}T23:59:59Z"
            
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
                    
                    opciok_listaja = []
                    h2h_szazalekok = {}
                    
                    for iroda in m.get('bookmakers', []):
                        for market in iroda.get('markets', []):
                            kimenetek = market['outcomes']
                            nyers_oddsok = [k['price'] for k in kimenetek]
                            nyers_osszeg = sum([1/o for o in nyers_oddsok])
                            
                            for k in kimenetek:
                                valoszinuseg = (1 / k['price']) / nyers_osszeg
                                
                                kimenetel_nev = k['name']
                                if market['key'] == 'totals':
                                    kimenetel_nev = f"{k['name']} {k.get('point', '')} gól"
                                elif market['key'] == 'btts':
                                    kimenetel_nev = f"Mindkét csapat szerez gólt: {k['name']}"
                                elif market['key'] == 'h2h':
                                    if k['name'] == m['home_team']:
                                        h2h_szazalekok['hazai'] = (k['name'], valoszinuseg)
                                    elif k['name'] == "Draw":
                                        h2h_szazalekok['dontetlen'] = (k['name'], valoszinuseg)
                                    else:
                                        h2h_szazalekok['vendeg'] = (k['name'], valoszinuseg)
                                
                                # Csak a küszöb feletti opciók kerülnek be a listába
                                if valoszinuseg >= KUSZOB:
                                    opciok_listaja.append({
                                        'opcio_nev': kimenetel_nev,
                                        'szazalek': valoszinuseg,
                                        'odds': k['price'],
                                        'iroda': iroda['title']
                                    })
                    
                    if opciok_listaja:
                        opciok_listaja.sort(key=lambda x: x['szazalek'], reverse=True)
                        jeloltek.append({
                            'sport_nev': sport.replace('_', ' ').title(),
                            'meccs': f"{m['home_team']} - {m['away_team']}",
                            'kezdes': kezdes_formazott,
                            'befejezes': befejezes_formazott,
                            'opciok': opciok_listaja,
                            'h2h_adatok': h2h_szazalekok
                        })
    
    jeloltek.sort(key=lambda x: x['opciok'][0]['szazalek'], reverse=True)
    jeloltek = jeloltek[:MAX_LISTA]
    
    kivalasztott_meccsek = []

    if not jeloltek:
        st.warning(f"📭 Holnap nincs olyan meccs, aminek az esélye elérné az {int(KUSZOB*100)}%-ot.")
    else:
        st.success(f"✅ Holnap {len(jeloltek)} kiemelkedő meccs felel meg a felteteleknek.")
        
        for i, j in enumerate(jeloltek, 1):
            legjobb = j['opciok'][0]
            cim = f"{i}. [{j['sport_nev']}] {j['meccs']}  —  {legjobb['szazalek']*100:.1f}%"
            
            with st.expander(cim, expanded=True):
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"📅 **Kezdés:** {j['kezdes']}")
                    st.markdown(f"🏁 **Várható vége:** {j['befejezes']}")
                with col2:
                    st.markdown(f"🏦 **Iroda:** {legjobb['iroda']}")
                
                st.markdown("---")
                st.write(f"🎯 **Választható opciók ({int(KUSZOB*100)}% felett):**")
                
                # Itt jelennek meg egymás alatt a pipálható opciók
                for idx, opcio in enumerate(j['opciok']):
                    cb_key = f"cb_{i}_{idx}"
                    label = f"{opcio['opcio_nev']} — {opcio['szazalek']*100:.1f}% (odds: {opcio['odds']})"
                    
                    if st.checkbox(label, key=cb_key):
                        kivalasztott_meccsek.append({
                            'meccs': j['meccs'],
                            'valasztott_opcio': opcio['opcio_nev'],
                            'szazalek': opcio['szazalek'],
                            'odds': opcio['odds']
                        })
                
                st.markdown("---")
                st.markdown("**1X2 Elemzés (Hazai / Döntetlen / Vendég):**")
                
                h2h = j['h2h_adatok']
                if 'hazai' in h2h:
                    st.markdown(f"<span class='hazai'>🏠 {h2h['hazai'][0]}: {h2h['hazai'][1]*100:.1f}%</span>", unsafe_allow_html=True)
                if 'dontetlen' in h2h:
                    st.markdown(f"<span class='dontetlen'>🤝 Döntetlen: {h2h['dontetlen'][1]*100:.1f}%</span>", unsafe_allow_html=True)
                if 'vendeg' in h2h:
                    st.markdown(f"<span class='vendeg'>✈️ {h2h['vendeg'][0]}: {h2h['vendeg'][1]*100:.1f}%</span>", unsafe_allow_html=True)

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
