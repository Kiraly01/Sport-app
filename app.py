import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Napi Sport Elemzo", page_icon="⚽")

st.title("⚽ Napi Sport Elemzo")
st.write("A lista a fogadoirodak szorzoibol szamolt valoszinusegeket mutatja. Nem garancia, csak statisztika!")

# --- BEALLITASOK ---
API_KEY = "058f2a77969ebea27f4dcdeb19290442"
SPORT = "soccer"
KUSZOB = 0.74  # Csak a 80% feletti meccseket mutatja
MAX_LISTA = 10 # Max ennyi meccset listáz

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
            
            for iroda in m.get('bookmakers', []):
                for market in iroda.get('markets', []):
                    if market['key'] == 'h2h':
                        kimenetek = market['outcomes']
                        if len(kimenetek) == 3:
                            # Víztelenítés (margin levonása)
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
                                            'iroda': iroda['title']
                                        }
            
            if legjobb_opcio:
                jeloltek.append(legjobb_opcio)
        
        # Rendezés esély szerint
        jeloltek.sort(key=lambda x: x['szazalek'], reverse=True)
        jeloltek = jeloltek[:MAX_LISTA]
        
        if not jeloltek:
            st.warning(f"📭 Ma nincs {int(KUSZOB*100)}% feletti biztonsagos meccs a listan. Az app azt javasolja: ma ne fogadj.")
        else:
            st.success(f"✅ Ma {len(jeloltek)} meccs felel meg a felteteleknek (80% felett).")
            
            for i, j in enumerate(jeloltek, 1):
                with st.expander(f"{i}. {j['meccs']} - {j['szazalek']*100:.1f}%", expanded=True):
                    st.write(f"**Tipp:** {j['opcio']}")
                    st.write(f"**Esely:** {j['szazalek']*100:.1f}%")
                    st.write(f"**Legjobb odds:** {j['odds']:.2f} ({j['iroda']})")
                    
                    tet = st.number_input(f"Tet osszege (Ft):", min_value=0, value=1000, step=500, key=f"tet_{i}")
                    if tet > 0:
                        visszakap = tet * j['odds']
                        netto = visszakap - tet
                        st.info(f"Ha nyer: Visszakapsz **{visszakap:.0f} Ft**-ot (Netto nyereseg: **+{netto:.0f} Ft**)")
    else:
        st.error("Hiba az API-val: " + valasz.text)
        
except Exception as e:
    st.error("Hiba: " + str(e))
