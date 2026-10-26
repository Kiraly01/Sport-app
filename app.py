import streamlit as st
import requests
from datetime import datetime, timedelta

st.set_page_config(page_title="Napi Sport Elemzo", page_icon="⚽")

st.title("⚽ Napi Sport Elemzo")
st.write("A lista a fogadoirodak szorzoibol szamolt valoszinusegeket mutatja.")

API_KEY = "058f2a77969ebea27f4dcdeb19290442"
SPORT = "soccer"

try:
    holnap = (datetime.utcnow() + timedelta(days=1)).strftime("%Y-%m-%d")
    url = f"https://api.the-odds-api.com/v4/sports/{SPORT}/odds/?apiKey={API_KEY}&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom={holnap}T00:00:00Z&commenceTimeTo={holnap}T23:59:59Z"
    
    valasz = requests.get(url)
    
    if valasz.status_code == 200:
        meccsek = valasz.json()
        st.success(f"Sikeres letoltes! {len(meccsek)} meccs.")
        
        for m in meccsek[:10]:
            st.write(f"**{m['home_team']} - {m['away_team']}**")
            
            for iroda in m.get('bookmakers', []):
                for market in iroda.get('markets', []):
                    if market['key'] == 'h2h':
                        for k in market['outcomes']:
                            odds = k['price']
                            esely = (1 / odds) * 100
                            st.write(f"{k['name']}: {esely:.1f}% (odds: {odds})")
                        break
            st.divider()
    else:
        st.error("Hiba az API-val: " + valasz.text)
        
except Exception as e:
    st.error("Hiba: " + str(e))
