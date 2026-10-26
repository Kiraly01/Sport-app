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
    h1, h2, h3 { color: #ffffff; font-family: 'Helvetica Neue', sans-serif; font-weight: 700; }
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
    </style>
""", unsafe_allow_html=True)

st.title("⚽ Napi Sport Elemzo")
st.write("Jelöld ki a kártyákon a négyzeteket, ha kombinációt (szelvényt) szeretnél rakni!")

# --- BEALLITASOK ---
API_KEY = "058f2a77969ebea27f4dcdeb19290442"
SPORT = "soccer"
KUSZOB = 0.70  
MAX_LISTA = 10 

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

try:
    holnap = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom={holnap}T00:00:00Z&commenceTimeTo={holnap}T23:59:59Z"
    
    with st.spinner("Adatok letöltése..."):
        valasz = requests.get(url)
    
    if valasz.status_code == 200:
        meccsek = valasz.json()
        jeloltek = []
        
        for m in meccsek:
            legjobb_opcio = None
            idopont_nyers = m.get('commence_time', '')
            idopont_formazott = idopont_nyers.replace("T", " ")[:16] if idopont_nyers else "Nincs idopont"
            
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
                                            'sorszam': m.get('id', 'Nincs sorszam'),
                                            'ido': idopont_formazott
                                        }
            if legjobb_opcio:
                jeloltek.append(legjobb_opcio)
        
        jeloltek.sort(key=lambda x: x['szazalek'], reverse=True)
        jeloltek = jeloltek[:MAX_LISTA]
        
        # Itt fogjuk gyűjteni a bepipált meccseket
        kivalasztott_meccsek = []

        if not jeloltek:
            st.warning(f"📭 Ma nincs {int(KUSZOB*100)}% feletti biztonsagos meccs a listan.")
        else:
            st.success(f"✅ Ma {len(jeloltek)} meccs felel meg a felteteleknek.")
            
            for i, j in enumerate(jeloltek, 1):
                cim = f"{i}. {j['meccs']}  —  {j['szazalek']*100:.1f}%"
                
                with st.expander(cim, expanded=True):
                    # A pipálható négyzet
                    kivalasztva = st.checkbox(f"Kiválasztás kombinációhoz", key=f"cb_{i}")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown(f"📅 **Időpont:** {j['ido']}")
                        st.markdown(f"🎯 **Tipp:** {j['opcio']}")
                        st.markdown(f"📊 **Esély:** {j['szazalek']*100:.1f}%")
                    with col2:
                        st.markdown(f"💰 **Odds:** {j['odds']:.2f}")
                        st.markdown(f"🏦 **Iroda:** {j['iroda']}")
                        st.markdown(f"🔢 **Sorszám:** `{j['sorszam']}`")
                    
                    if kivalasztva:
                        kivalasztott_meccsek.append(j)

        # ==========================================
        # KOMBINÁCIÓS KALKULÁTOR (Ha van bepipált meccs)
        # ==========================================
        if len(kivalasztott_meccsek) > 0:
            st.markdown("---")
            st.header("🧾 Kombinációs Szelvény")
            
            # Össz odds kiszámítása (a kiválasztottak oddsainak szorzata)
            ossz_odds = 1.0
            for m in kivalasztott_meccsek:
                ossz_odds *= m['odds']
            
            # Tét megadása a kombinációhoz
            komb_tet = st.number_input("Tét összege a kombinációra (Ft):", min_value=100, value=1000, step=500, key="komb_tet")
            varhato_nyeremeny = komb_tet * ossz_odds
            
            # Kiírás
            st.info(f"Kiválasztott események száma: **{len(kivalasztott_meccsek)} db**")
            
            # Listázás
            for m in kivalasztott_meccsek:
                st.write(f"- {m['meccs']} ({m['opcio']}) | Sorszám: `{m['sorszam']}` | Odds: {m['odds']}")
            
            st.success(f"📈 **Összesített Odds:** {ossz_odds:.2f}")
            st.success(f"💰 **Várható Nyeremény:** {varhato_nyeremeny:.0f} Ft (Nettó: +{varhato_nyeremeny - komb_tet:.0f} Ft)")
            
    else:
        st.error("Hiba az API-val: " + valasz.text)
        
except Exception as e:
    st.error("Hiba: " + str(e))
