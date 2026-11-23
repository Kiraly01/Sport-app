import streamlit as st
import streamlit.components.v1 as components
import requests
from datetime import datetime, timedelta
import pytz
import statistics

st.set_page_config(page_title="Napi Foci Tipp", page_icon="⚽", layout="centered")

CSS = """
<style>
.stApp { background-color: #12161A; color: #E0E0E0; }
h1 { color: #FFFFFF; font-weight: 800; font-size: 2.2em; text-align: center; }
.top3-header { color: #FFD700; font-size: 1.8em; font-weight: 900; text-align: center; margin-top: 20px; }
.top3-card .streamlit-expanderHeader { background-color: #2D1B00 !important; color: #FFD700 !important; font-weight: 900 !important; border: 2px solid #FFD700 !important; }
.other-header { color: #A0AAB5; font-size: 1.3em; font-weight: 700; text-align: center; margin-top: 20px; }
.other-card .streamlit-expanderHeader { background-color: #1E252B !important; color: #A0AAB5 !important; border: 1px solid #444 !important; }
.stButton>button { background-color: #FACC15; color: #000; font-weight: 700; border-radius: 6px; width: 100%; }
.clock-container { text-align: center; margin: 10px 0; }
.live-clock { font-family: monospace; font-size: 1.4em; color: #FACC15; background: #1E252B; padding: 8px 16px; border-radius: 8px; display: inline-block; }
.warning-box { background: #332211; border-left: 4px solid #FACC15; padding: 10px; border-radius: 4px; margin-bottom: 15px; }
.suggested-bet { color: #22C55E; font-weight: bold; font-size: 1.1em; }
.kombi-box { background: linear-gradient(135deg, #2D1B4E, #4A2C6D); border: 2px solid #9D4EDD; border-radius: 12px; padding: 15px; margin-top: 20px; }
.kombi-title { color: #FACC15; font-size: 1.4em; font-weight: 900; text-align: center; }
.kombi-odds { color: #22C55E; font-size: 1.3em; font-weight: bold; text-align: center; margin-top: 10px; }
.copy-box { background: #1E252B; border: 1px solid #444; border-radius: 8px; padding: 12px; margin: 10px 0; font-family: monospace; font-size: 0.9em; color: #E0E0E0; }
.new-tip-badge { background: #22C55E; color: #000; padding: 2px 8px; border-radius: 4px; font-weight: bold; font-size: 0.8em; }
.stats-box { background: #1E252B; border: 1px solid #444; border-radius: 8px; padding: 12px; margin-top: 15px; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Tipp (72 óra)</h1>", unsafe_allow_html=True)

@st.fragment(run_every=1)
def ora_frissites():
    hu_tz = pytz.timezone('Europe/Budapest')
    ido = datetime.now(hu_tz)
    html = '<div class="clock-container"><div class="live-clock">📅 ' + ido.strftime('%Y-%m-%d') + ' | ⏰ ' + ido.strftime('%H:%M:%S') + '</div></div>'
    st.markdown(html, unsafe_allow_html=True)

ora_frissites()

st.markdown("""
<div class="warning-box">
⚠️ <b>FIGYELEM!</b> 82% feletti Kétesély tippek. Medián alapú számítás. 
🔔 <b>Új tipp értesítés</b> aktív (óránként ellenőriz). 
📋 <b>1 kattintásos másolás</b> a Tippmixhez.
A sportfogadás kockázattal jár!
</div>
""", unsafe_allow_html=True)

# ==========================================
# BEÁLLÍTÁSOK
# ==========================================
ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
KUSZOB_MIN = 0.82
MIN_IRODAK = 2
MAX_LISTA = 10

# Session state
if 'elozo_tippek' not in st.session_state:
    st.session_state.elozo_tippek = set()
if 'uj_tippek_szama' not in st.session_state:
    st.session_state.uj_tippek_szama = 0
if 'reggeli_mod' not in st.session_state:
    st.session_state.reggeli_mod = False

# ==========================================
# GOMBOK
# ==========================================
col1, col2 = st.columns(2)
with col1:
    if st.button("🔄 Manuális frissítés"):
        st.cache_data.clear()
        st.session_state.reggeli_mod = False
with col2:
    if st.button("🌅 Reggeli összefoglaló"):
        st.session_state.reggeli_mod = True
        st.cache_data.clear()

if st.session_state.reggeli_mod:
    st.info("🌅 Reggeli mód: A nap összes meccsét listázza")

# ==========================================
# VÁGÓLAPRA MÁSOLÁS FÜGGVÉNY
# ==========================================
def vagolapra_masolo_gomb(szoveg, gomb_szoveg="📋 Másolás"):
    js_code = """
    <script>
    function copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(function() {
            alert('Másolva!');
        }).catch(function() {
            prompt('Másold ki manuálisan:', text);
        });
    }
    </script>
    """
    components.html(js_code, height=0, width=0)
    if st.button(gomb_szoveg, key="copy_" + str(hash(szoveg))):
        st.code(szoveg, language="text")
        st.success("✅ Szöveg kész! Jelöld ki és másold (Ctrl+C)")

# ==========================================
# API LEKÉRDEZÉS
# ==========================================
@st.cache_data(ttl=3600)
def api_lekerdezes():
    most_utc = datetime.now(pytz.utc)
    kezdo = most_utc.strftime("%Y-%m-%dT00:00:00Z")
    veg = (most_utc + timedelta(days=2)).strftime("%Y-%m-%dT23:59:59Z")
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey=" + ODDS_API_KEY + "&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom=" + kezdo + "&commenceTimeTo=" + veg
    valasz = requests.get(url, timeout=10)
    if valasz.status_code == 200:
        return valasz.json()
    return []

# ==========================================
# HÁTTÉRFIGYELÉS (ÓRÁNKÉNT)
# ==========================================
@st.fragment(run_every=3600)
def hatter_figyeles():
    try:
        meccsek = api_lekerdezes()
        uj_tippek = []
        for m in meccsek:
            idopont = m.get('commence_time', '')
            if not idopont:
                continue
            try:
                kezdes_utc = datetime.strptime(idopont, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                if kezdes_utc <= datetime.now(pytz.utc):
                    continue
            except:
                continue
            
            hazai_oddsok = []
            vendeg_oddsok = []
            dontetlen_oddsok = []
            for iroda in m.get('bookmakers', []):
                for market in iroda.get('markets', []):
                    if market['key'] == 'h2h':
                        for k in market['outcomes']:
                            if k['name'] == m['home_team']:
                                hazai_oddsok.append(k['price'])
                            elif k['name'] == m['away_team']:
                                vendeg_oddsok.append(k['price'])
                            elif k['name'] == "Draw":
                                dontetlen_oddsok.append(k['price'])
            
            if len(hazai_oddsok) < MIN_IRODAK:
                continue
            
            mh = statistics.median(hazai_oddsok)
            mv = statistics.median(vendeg_oddsok)
            md = statistics.median(dontetlen_oddsok)
            nyers = (1/mh) + (1/mv) + (1/md)
            if nyers <= 0:
                continue
            
            esely_1x = (1/mh + 1/md) / nyers
            esely_x2 = (1/mv + 1/md) / nyers
            max_esely = max(esely_1x, esely_x2)
            
            if max_esely >= KUSZOB_MIN:
                meccs_key = m['home_team'] + "_" + m['away_team']
                if meccs_key not in st.session_state.elozo_tippek:
                    uj_tippek.append(m['home_team'] + " - " + m['away_team'])
                    st.session_state.elozo_tippek.add(meccs_key)
        
        if uj_tippek:
            st.session_state.uj_tippek_szama += len(uj_tippek)
            st.toast("🔔 ÚJ TIPP: " + ", ".join(uj_tippek[:3]), icon="🎯")
    except:
        pass

hatter_figyeles()

if st.session_state.uj_tippek_szama > 0:
    st.success("🔔 " + str(st.session_state.uj_tippek_szama) + " új tipp észlelve a háttérben!")

# ==========================================
# FŐ LOGIKA
# ==========================================
try:
    most_utc = datetime.now(pytz.utc)
    hu_tz = pytz.timezone('Europe/Budapest')
    meccsek = api_lekerdezes()
    
    jeloltek_dict = {}
    
    with st.spinner("Meccsek elemzése..."):
        for m in meccsek:
            idopont = m.get('commence_time', '')
            if not idopont:
                continue
            try:
                kezdes_utc = datetime.strptime(idopont, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                if kezdes_utc <= most_utc:
                    continue
                kezdes_hu = kezdes_utc.astimezone(hu_tz)
            except:
                continue
            
            hazai_oddsok = []
            vendeg_oddsok = []
            dontetlen_oddsok = []
            for iroda in m.get('bookmakers', []):
                for market in iroda.get('markets', []):
                    if market['key'] == 'h2h':
                        for k in market['outcomes']:
                            if k['name'] == m['home_team']:
                                hazai_oddsok.append(k['price'])
                            elif k['name'] == m['away_team']:
                                vendeg_oddsok.append(k['price'])
                            elif k['name'] == "Draw":
                                dontetlen_oddsok.append(k['price'])
            
            if len(hazai_oddsok) < MIN_IRODAK or len(vendeg_oddsok) < MIN_IRODAK or len(dontetlen_oddsok) < MIN_IRODAK:
                continue
            
            mh = statistics.median(hazai_oddsok)
            mv = statistics.median(vendeg_oddsok)
            md = statistics.median(dontetlen_oddsok)
            nyers = (1/mh) + (1/mv) + (1/md)
            if nyers <= 0:
                continue
            
            esely_1x = (1/mh + 1/md) / nyers
            odds_1x = 1/esely_1x if esely_1x > 0 else 0
            esely_x2 = (1/mv + 1/md) / nyers
            odds_x2 = 1/esely_x2 if esely_x2 > 0 else 0
            
            opciok = [
                {'nev': m['home_team'] + " vagy Döntetlen (1X)", 'esely': esely_1x, 'odds': odds_1x},
                {'nev': m['away_team'] + " vagy Döntetlen (X2)", 'esely': esely_x2, 'odds': odds_x2}
            ]
            
            legjobb = None
            for o in opciok:
                if o['esely'] >= KUSZOB_MIN:
                    if legjobb is None or o['esely'] > legjobb['esely']:
                        legjobb = o
            
            if legjobb:
                meccs_nev = m['home_team'] + " - " + m['away_team']
                if meccs_nev not in jeloltek_dict or legjobb['esely'] > jeloltek_dict[meccs_nev]['esely']:
                    jeloltek_dict[meccs_nev] = {
                        'meccs': meccs_nev,
                        'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                        'esely': legjobb['esely'],
                        'opcio_nev': legjobb['nev'],
                        'odds': legjobb['odds'],
                        'irodak': len(hazai_oddsok)
                    }
    
    jeloltek = sorted(jeloltek_dict.values(), key=lambda x: x['esely'], reverse=True)[:MAX_LISTA]
    
    if not jeloltek:
        st.warning("📭 Nincs " + str(int(KUSZOB_MIN*100)) + "% feletti meccs. Ma ne fogadj.")
    else:
        # ==========================================
        # VÁGÓLAPRA MÁSOLÁS - TERVLISTA
        # ==========================================
        tervlista_szoveg = "⚽ NAPI FOCI TIPP TERVLISTA\n"
        tervlista_szoveg += "========================\n"
        tervlista_szoveg += "Dátum: " + datetime.now(hu_tz).strftime("%Y-%m-%d %H:%M") + "\n\n"
        
        for i, j in enumerate(jeloltek[:3], 1):
            tet = 200 if j['esely'] >= 0.80 else 150
            tervlista_szoveg += str(i) + ". " + j['meccs'] + "\n"
            tervlista_szoveg += "   Tipp: " + j['opcio_nev'] + "\n"
            tervlista_szoveg += "   Esély: " + str(round(j['esely']*100, 1)) + "% | Odds: " + str(round(j['odds'], 2)) + "\n"
            tervlista_szoveg += "   Tét: " + str(tet) + " Ft\n\n"
        
        tervlista_szoveg += "🔥 KOMBINÁCIÓ (top 3):\n"
        kombi_odds = 1.0
        for k in jeloltek[:3]:
            kombi_odds *= k['odds']
        tervlista_szoveg += "   Össz odds: " + str(round(kombi_odds, 2)) + "\n"
        tervlista_szoveg += "   Tét: 200 Ft | Nyeremény: " + str(round(200 * kombi_odds)) + " Ft\n"
        
        st.markdown("### 📋 Tervlista (1 kattintásos másolás)")
        vagolapra_masolo_gomb(tervlista_szoveg, "📋 Tervlista másolása")
        
        # ==========================================
        # TOP 3 MEGJELENÍTÉS
        # ==========================================
        st.markdown("<div class='top3-header'>⭐ TOP 3 LEGJOBB TIPP ⭐</div>", unsafe_allow_html=True)
        
        for i, j in enumerate(jeloltek[:3], 1):
            st.markdown("<div class='top3-card'>", unsafe_allow_html=True)
            cim = "⭐ " + str(i) + " | " + j['meccs'] + " — " + j['opcio_nev'] + " (" + str(round(j['esely']*100, 1)) + "%)"
            with st.expander(cim, expanded=True):
                st.markdown("📅 **Kezdés:** " + j['kezdes'])
                st.markdown("**Tipp:** " + j['opcio_nev'])
                st.markdown("**Esély:** " + str(round(j['esely']*100, 1)) + "% | **Odds:** " + str(round(j['odds'], 2)))
                tet = 200 if j['esely'] >= 0.80 else 150
                st.markdown("<div class='suggested-bet'>💰 Tét: " + str(tet) + " Ft</div>", unsafe_allow_html=True)
                st.markdown("📈 Nyeremény: " + str(round(tet * j['odds'])) + " Ft (+" + str(round(tet * j['odds'] - tet)) + " Ft)")
                st.markdown("🔒 " + str(j['irodak']) + " iroda mediánja")
                st.markdown("[🔍 Tippmix](https://www.tippmix.hu/mobil/elo)")
            st.markdown("</div>", unsafe_allow_html=True)
        
        # További meccsek
        if len(jeloltek) > 3:
            st.markdown("<div class='other-header'>További meccsek</div>", unsafe_allow_html=True)
            for j in jeloltek[3:]:
                st.markdown("<div class='other-card'>", unsafe_allow_html=True)
                cim = "🟡 " + j['meccs'] + " — " + j['opcio_nev'] + " (" + str(round(j['esely']*100, 1)) + "%)"
                with st.expander(cim, expanded=False):
                    st.markdown("📅 **Kezdés:** " + j['kezdes'])
                    st.markdown("**Tipp:** " + j['opcio_nev'])
                    st.markdown("**Esély:** " + str(round(j['esely']*100, 1)) + "% | **Odds:** " + str(round(j['odds'], 2)))
                    tet = 200 if j['esely'] >= 0.80 else 150
                    st.markdown("💰 Tét: " + str(tet) + " Ft")
                    st.markdown("📈 Nyeremény: " + str(round(tet * j['odds'])) + " Ft")
                    st.markdown("[🔍 Tippmix](https://www.tippmix.hu/mobil/elo)")
                st.markdown("</div>", unsafe_allow_html=True)
        
        # Kombináció
        if len(jeloltek) >= 2:
            kombi = jeloltek[:3]
            kombi_odds = 1.0
            kombi_esely = 1.0
            kombi_html = ""
            for k in kombi:
                kombi_odds *= k['odds']
                kombi_esely *= k['esely']
                kombi_html += "<div style='color:white; margin:5px 0;'>✅ " + k['meccs'] + " - " + k['opcio_nev'] + " (" + str(round(k['esely']*100, 1)) + "%)</div>"
            
            html = '<div class="kombi-box">'
            html += '<div class="kombi-title">🔥 Napi Kombináció (' + str(len(kombi)) + ' meccs)</div>'
            html += kombi_html
            html += '<div class="kombi-odds">📈 Odds: ' + str(round(kombi_odds, 2)) + '</div>'
            html += '<div style="text-align:center; color:#FACC15; margin-top:10px;"><b>Esély:</b> ' + str(round(kombi_esely*100, 1)) + '%</div>'
            html += '<div style="text-align:center; color:#22C55E; font-weight:bold; margin-top:10px;">💰 Tét: 200 Ft | Nyeremény: ' + str(round(200 * kombi_odds)) + ' Ft</div>'
            html += '</div>'
            st.markdown(html, unsafe_allow_html=True)
        
        # Statisztika
        st.markdown("<div class='stats-box'>", unsafe_allow_html=True)
        st.markdown("### 📊 Statisztika")
        st.markdown("- **Aktuális tippek:** " + str(len(jeloltek)))
        st.markdown("- **Átlag esély:** " + str(round(sum(x['esely'] for x in jeloltek) / len(jeloltek) * 100, 1)) + "%")
        st.markdown("- **Háttérfigyelés:** ✅ Aktív (óránként)")
        st.markdown("- **Új tippek észlelve:** " + str(st.session_state.uj_tippek_szama))
        st.markdown("- **Medián számítás:** ✅")
        st.markdown("</div>", unsafe_allow_html=True)

except Exception as e:
    st.error("Hiba: " + str(e))
