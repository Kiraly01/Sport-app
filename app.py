import streamlit as st
import requests
from datetime import datetime, timedelta

# ==========================================
# MODERN KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Sport Elemzo", page_icon="⚽", layout="centered")

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
    </style>
""", unsafe_allow_html=True)

# Középre igazított cím
st.markdown("<h1>⚽ Napi Sport Elemzo</h1>", unsafe_allow_html=True)

# ==========================================
# ÉLŐ ÓRA (JavaScript - másodpercenként frissül)
# ==========================================
st.markdown("""
    <div class="clock-container">
        <div class="live-clock" id="clock">Betöltés...</div>
    </div>
    <script>
        function updateClock() {
            const now = new Date();
            const options = { year: 'numeric', month: '2-digit', day: '2-digit' };
            const date = now.toLocaleDateString('hu-HU', options);
            const time = now.toLocaleTimeString('hu-HU');
            document.getElementById('clock').innerHTML = "📅 " + date + " | ⏰ " + time;
        }
        setInterval(updateClock, 1000);
        updateClock();
    </script>
""", unsafe_allow_html=True)

st.write("A kártyákon látszik a meccs kezdete és várható vége, valamint hogy magában vagy kombinációban érdemes-e megtenni.")

# --- BEALLITASOK ---
API_KEY = "058f2a77969ebea27f4dcdeb19290442"
SPORT = "soccer"

# IDEIGLENESEN 0.01-re vettük, hogy MINDENT kiírjon, ami az API-ból jön!
KUSZOB = 0.01  
MAX_LISTA = 10 

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

try:
    holnap_datum = (datetime.utcnow() + timedelta(days=1))
    holnap_str = holnap_datum.strftime("%Y-%m-%d")
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom={holnap_str}T00:00:00Z&commenceTimeTo={holnap_str}T23:59:59Z"
    
    with st.spinner("Adatok letöltése..."):
        valasz = requests.get(url)
    
    if valasz.status_code == 200:
        meccsek = valasz.json()
        jeloltek = []
        
        for m in meccsek:
            legjobb_opcio = None
            idopont_nyers = m.get('commence_time', '')
            
            if idopont_nyers:
                try:
                    kezdes_dt = datetime.strptime(idopont_nyers, "%Y-%m-%dT%H:%M:%SZ")
                    befejezes_dt = kezdes_dt + timedelta(hours=2)
                    
                    kezdes_formazott = kezdes_dt.strftime("%Y-%m-%d %H:%M")
                    befejezes_formazott = befejezes_dt.strftime("%H:%M")
                except Exception as e:
                    kezdes_formazott = idopont_nyers
                    befejezes_formazott = "?"
            else:
                kezdes_formazott = "Nincs idopont"
                befejezes_formazott = "?"
            
            for iroda in m.get('bookmakers', []):
                for market in iroda.get('markets', []):
                    if market['key'] == 'h2h':
                        kimenetek = market['outcomes']
                        if len(kimenetek) == 3:
                            nyers_oddsok = [k['price'] for k in kimenetek]
                            nyers_osszeg = sum([1/o for o in nyers_oddsok])
                            
                            for k in kimenetek:
                                valoszinuseg = (1 / k['price']) / nyers_osszeg
                                if valoszinuseg >= KUSZOB:
                                    if legjobb_opcio is None or valoszinuseg > legjobb_opcio['szazalek']:
                                        legjobb_opcio = {
                                            'meccs': f"{m['home_team']} - {m['away_team']}",
                                            'opcio': k['name'],
                                            'szazalek': valoszinuseg,
                                            'odds': k['price'],
                                            'iroda': iroda['title'],
                                            'kezdes': kezdes_formazott,
                                            'befejezes': befejezes_formazott
                                        }
            if legjobb_opcio:
                jeloltek.append(legjobb_opcio)
        
        jeloltek.sort(key=lambda x: x['szazalek'], reverse=True)
        jeloltek = jeloltek[:MAX_LISTA]
        
        kivalasztott_meccsek = []

        if not jeloltek:
            st.warning("📭 Ma nincs meccs a listán (az API nem adott vissza adatot).")
        else:
            st.success(f"✅ Ma {len(jeloltek)} meccs felel meg a felteteleknek.")
            
            for i, j in enumerate(jeloltek, 1):
                cim = f"{i}. {j['meccs']}  —  {j['szazalek']*100:.1f}%"
                
                with st.expander(cim, expanded=True):
                    
                    if j['szazalek'] >= 0.80:
                        st.info("💡 **Javaslat:** Ezt a tippet **magában** érdemes megtenni.")
                        javasolt_kombinacio = False
                    elif j['szazalek'] >= 0.75:
                        st.warning("💡 **Javaslat:** **Magában is jó**, de kombinálható.")
                        javasolt_kombinacio = True
                    else:
                        st.warning("💡 **Javaslat:** Ezt a tippet **csak kombinációban** érdemes megtenni.")
                        javasolt_kombinacio = True
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"📅 **Kezdés:** {j['kezdes']}")
                        st.markdown(f"🏁 **Várható vége:** {j['befejezes']}")
                        st.markdown(f"🎯 **Tipp:** {j['opcio']}")
                    with col2:
                        st.markdown(f"📊 **Esély:** {j['szazalek']*100:.1f}%")
                        st.markdown(f"💰 **Odds:** {j['odds']:.2f}")
                        st.markdown(f"🏦 **Iroda:** {j['iroda']}")
                    
                    st.markdown("---")
                    
                    if javasolt_kombinacio:
                        st.write("➕ **Kombinációs opció:**")
                        kivalasztva = st.checkbox(f"Beteszem a kombinációba", key=f"cb_{i}")
                        if kivalasztva:
                            kivalasztott_meccsek.append(j)
                    else:
                        st.caption("Ez a tipp annyira biztos, hogy külön szelvényen is megállja a helyét.")

        if len(kivalasztott_meccsek) > 0:
            st.markdown("---")
            st.header("🧾 Kombinációs Szelvény")
            
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
                st.write(f"- {m['meccs']} ({m['opcio']})")
            
            st.info(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.info(f"🎯 **Kombinált Esély (%):** {komb_esely*100:.1f}% (Veszteség esélye: {(1-komb_esely)*100:.1f}%)")
            st.success(f"💰 **Várható Nyeremény:** {varhato_nyeremeny:.0f} Ft (Nettó: +{varhato_nyeremeny - komb_tet:.0f} Ft)")
            
    else:
        st.error("Hiba az API-val: " + valasz.text)
        
except Exception as e:
    st.error("Hiba: " + str(e))
