import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import statistics

# ==========================================
# KINÉZET (CSS)
# ==========================================
st.set_page_config(page_title="Napi Foci Tipp", page_icon="⚽", layout="centered")
st.markdown("""
<style>
.stApp { background-color: #12161A; color: #E0E0E0; }
h1 { color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.5em; text-align: center; margin-bottom: 20px; }
.top3-header { color: #FFD700; font-size: 2em; font-weight: 900; text-align: center; margin-top: 30px; margin-bottom: 20px; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
.top3-card .streamlit-expanderHeader { background-color: #2D1B00 !important; border-radius: 8px !important; color: #FFD700 !important; font-weight: 900 !important; font-size: 1.4em !important; border: 2px solid #FFD700 !important; padding: 15px 20px !important; margin-bottom: 8px; }
.top3-card .streamlit-expanderContent { background-color: #1A1000 !important; border: 2px solid #FFD700 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 20px !important; }
.other-header { color: #A0AAB5; font-size: 1.5em; font-weight: 700; text-align: center; margin-top: 30px; margin-bottom: 20px; }
.other-card .streamlit-expanderHeader { background-color: #1E252B !important; border-radius: 8px !important; color: #A0AAB5 !important; font-weight: 600 !important; font-size: 1.1em !important; border: 1px solid #444 !important; padding: 12px 15px !important; margin-bottom: 5px; }
.other-card .streamlit-expanderContent { background-color: #161A1F !important; border: 1px solid #444 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 15px !important; }
.watch-header { color: #FACC15; font-size: 1.6em; font-weight: 700; text-align: center; margin-top: 30px; margin-bottom: 20px; }
.watch-card .streamlit-expanderHeader { background-color: #2B2A10 !important; border-radius: 8px !important; color: #FACC15 !important; font-weight: 600 !important; font-size: 1.1em !important; border: 1px solid #FACC15 !important; padding: 12px 15px !important; margin-bottom: 5px; }
.watch-card .streamlit-expanderContent { background-color: #1A1A0A !important; border: 1px solid #FACC15 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 15px !important; }
.risk-header { color: #FF8C00; font-size: 1.8em; font-weight: 900; text-align: center; margin-top: 30px; margin-bottom: 20px; text-shadow: 0 0 10px rgba(255, 140, 0, 0.5); }
.risk-card .streamlit-expanderHeader { background-color: #3D2400 !important; border-radius: 8px !important; color: #FF8C00 !important; font-weight: 700 !important; font-size: 1.2em !important; border: 2px solid #FF8C00 !important; padding: 15px 20px !important; margin-bottom: 8px; }
.risk-card .streamlit-expanderContent { background-color: #2A1900 !important; border: 2px solid #FF8C00 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 20px !important; }
.risk-warning { background-color: #4D2E00; border-left: 4px solid #FF8C00; padding: 10px; margin-bottom: 15px; border-radius: 4px; color: #FFD700; font-size: 0.9em; font-weight: bold; }
.stButton>button { background-color: #FACC15; color: #000000; font-weight: 700; font-size: 1.1em; border-radius: 6px; border: none; padding: 10px 15px; width: 100%; box-shadow: 0 2px 4px rgba(0,0,0,0.2); transition: all 0.2s; }
.stButton>button:hover { background-color: #EAB308; transform: translateY(-1px); box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
.clock-container { display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 15px; }
.live-clock { font-family: 'Courier New', monospace; font-size: 1.6em; color: #FACC15; background-color: #1E252B; padding: 10px 20px; border-radius: 8px; border: 1px solid #444; font-weight: 800; letter-spacing: 1px; box-shadow: 0 4px 8px rgba(0,0,0,0.3); }
.warning-box { background-color: #332211; border-left: 4px solid #FACC15; padding: 10px; margin-bottom: 15px; border-radius: 4px; color: #E0E0E0; font-size: 0.9em; }
.suggested-bet { color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 10px; }
.kombi-box { background: linear-gradient(135deg, #2D1B4E, #4A2C6D); border: 2px solid #9D4EDD; border-radius: 12px; padding: 20px; margin-top: 30px; box-shadow: 0 8px 20px rgba(157, 78, 221, 0.4); }
.kombi-title { color: #FACC15; font-size: 1.8em; font-weight: 900; text-align: center; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px; }
.kombi-item { color: #FFFFFF; font-size: 1.1em; margin-bottom: 8px; padding-left: 10px; border-left: 3px solid #FACC15; display: flex; justify-content: space-between; }
.kombi-percent { color: #22C55E; font-weight: bold; }
.kombi-odds { color: #22C55E; font-size: 1.5em; font-weight: bold; text-align: center; margin-top: 15px; text-shadow: 0 0 10px rgba(34, 197, 94, 0.5); }
.median-info { background-color: #1E252B; border-left: 3px solid #FACC15; padding: 8px; margin-top: 10px; border-radius: 4px; font-size: 0.85em; color: #A0AAB5; }
.tippmix-warn { color: #FF8C00; font-size: 0.85em; margin-top: 8px; font-style: italic; }
/* ÚJ: Kieséses meccs figyelmeztetés stílusa */
.kieseses-warn { background-color: #4A1C00; border-left: 4px solid #FF4500; padding: 10px; margin-top: 8px; border-radius: 4px; color: #FFA500; font-size: 0.9em; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Tipp (120 óra)</h1>", unsafe_allow_html=True)

# ==========================================
# ÉLŐ ÓRA
# ==========================================
@st.fragment(run_every=1)
def ora_frissites():
    hu_tz = pytz.timezone('Europe/Budapest')
    aktualis_ido = datetime.now(hu_tz)
    st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {aktualis_ido.strftime('%Y-%m-%d')} | ⏰ {aktualis_ido.strftime('%H:%M:%S')}</div>
    </div>
    """, unsafe_allow_html=True)

ora_frissites()

st.markdown("""
<div class="warning-box">
⚠️ <b>FIGYELEM!</b> Az app a következő <b>120 óra</b> legbiztonságosabb tippjeit mutatja.
A <b style="color: #FFD700;">TOP 3</b> a 82% feletti, a <b style="color: #FACC15;">Figyelőlista</b> a 75-82% közötti esélyű meccseket tartalmazza (Kétesély). 
Az oddsok <b>medián</b> alapján számolódnak (több fogadóiroda).
A <span style="color: #FF8C00; font-weight: bold;">narancs</span> színű meccsek rizikós ligákból vannak - fokozott óvatosság!
A <span style="color: #FF4500; font-weight: bold;">piros</span> figyelmeztetés kieséses/kupa mérkőzést jelez!
A sportfogadás kockázattal jár, soha ne tegyél fel többet, mint amit el tudsz veszíteni!
</div>
""", unsafe_allow_html=True)

# ==========================================
# BEÁLLÍTÁSOK
# ==========================================
try:
    ODDS_API_KEY = st.secrets["ODDS_API_KEY"]
except (KeyError, FileNotFoundError):
    ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"  # ← ÉLESBEN CSERÉLD KI / TÖRÖLD!

KUSZOB_MIN = 0.82
KUSZOB_FIGYELO = 0.75
MIN_IRODAK = 2
MAX_LISTA = 10

RIZIKOS_KULCSSZAVAK = [
    'friendly', 'baratsagos', 'amateur', 'youth', 'u19', 'u21', 'u17',
    'women', 'reserve', 'b team', 'b csapat', 'cup qualification', 'kupa selejtezo',
    'pre-season', 'felkeszules', 'brasileirao', 'copa libertadores', 'mls',
    'segunda', 'serie b', '2. bundesliga', 'championship'
]

# ÚJ: KIESÉSES / KUPA MÉRKŐZÉSEK KULCSSZAVAI
KUPAS_KULCSSZAVAK = [
    'cup', 'copa', 'kupa', 'trophy', 'playoff', 'play-off', 'play off',
    'clausura', 'apertura', 'final', 'döntő', 'qualification', 'selejtezo',
    'elimination', 'knockout', 'round of 16', 'nyolcaddöntő', 'quarterfinal',
    'negyeddöntő', 'semifinal', 'elődöntő', 'supercopa', 'szuperkupa',
    'libertadores', 'sudamericana', 'champions league', 'europa league',
    'conference league'
]

def kieseses_meccs_e(sport_title):
    """ÚJ: Ellenőrzi, hogy a liga kieséses/kupa jellegű-e"""
    sport_title_lower = sport_title.lower()
    for kulcsszo in KUPAS_KULCSSZAVAK:
        if kulcsszo in sport_title_lower:
            return True
    return False

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

def javasolt_tet(esely):
    if esely >= 0.98: return 1000
    elif esely >= 0.95: return 800
    elif esely >= 0.90: return 500
    elif esely >= 0.85: return 300
    elif esely >= 0.82: return 200
    elif esely >= 0.75: return 150
    else: return 100

def rizikos_liga_e(sport_title):
    sport_title_lower = sport_title.lower()
    for kulcsszo in RIZIKOS_KULCSSZAVAK:
        if kulcsszo in sport_title_lower:
            return True
    return False

# ==========================================
# FŐ LOGIKA
# ==========================================
try:
    most_utc = datetime.now(pytz.utc)
    hu_tz = pytz.timezone('Europe/Budapest')
    
    kezdo_datum = most_utc.strftime("%Y-%m-%dT00:00:00Z")
    veg_datum = (most_utc + timedelta(days=4)).strftime("%Y-%m-%dT23:59:59Z")
    
    url = (f"https://api.the-odds-api.com/v4/sports/soccer/odds/"
           f"?apiKey={ODDS_API_KEY}&regions=eu,uk,us&markets=h2h"
           f"&oddsFormat=decimal"
           f"&commenceTimeFrom={kezdo_datum}&commenceTimeTo={veg_datum}")
    
    jeloltek_dict = {}
    figyelolista_dict = {}
    rizikos_dict = {}
    
    with st.spinner("Biztonságos foci meccsek keresése (120 óra)..."):
        valasz = requests.get(url)
        
        if valasz.status_code == 200:
            meccsek = valasz.json()
            
            for m in meccsek:
                idopont_nyers = m.get('commence_time', '')
                if not idopont_nyers:
                    continue
                
                try:
                    kezdes_utc = datetime.strptime(idopont_nyers, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=pytz.utc)
                    if kezdes_utc <= most_utc:
                        continue
                    kezdes_hu = kezdes_utc.astimezone(hu_tz)
                except (ValueError, TypeError):
                    continue
                
                sport_title = m.get('sport_title', '')
                is_rizikos = rizikos_liga_e(sport_title)
                
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
                
                median_hazai = statistics.median(hazai_oddsok)
                median_vendeg = statistics.median(vendeg_oddsok)
                median_dontetlen = statistics.median(dontetlen_oddsok)
                
                nyers_osszeg = (1/median_hazai) + (1/median_vendeg) + (1/median_dontetlen)
                
                if nyers_osszeg > 0:
                    esely_1x = (1/median_hazai + 1/median_dontetlen) / nyers_osszeg
                    odds_1x = 1 / esely_1x if esely_1x > 0 else 0
                    
                    esely_x2 = (1/median_vendeg + 1/median_dontetlen) / nyers_osszeg
                    odds_x2 = 1 / esely_x2 if esely_x2 > 0 else 0
                    
                    ketesely_opciok = [
                        {'nev': f"{m['home_team']} vagy Döntetlen (1X)", 'esely': esely_1x, 'odds': odds_1x},
                        {'nev': f"{m['away_team']} vagy Döntetlen (X2)", 'esely': esely_x2, 'odds': odds_x2}
                    ]
                    
                    legjobb_ketesely = None
                    for opcio in ketesely_opciok:
                        if opcio['esely'] >= KUSZOB_FIGYELO:
                            if legjobb_ketesely is None or opcio['esely'] > legjobb_ketesely['esely']:
                                legjobb_ketesely = opcio
                    
                    if legjobb_ketesely:
                        meccs_nev = f"{m['home_team']} - {m['away_team']}"
                        meccs_adat = {
                            'meccs': meccs_nev,
                            'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                            'esely': legjobb_ketesely['esely'],
                            'opcio_nev': legjobb_ketesely['nev'],
                            'odds': legjobb_ketesely['odds'],
                            'irodak_szama': len(hazai_oddsok),
                            'liga': sport_title,
                            'kieseses': kieseses_meccs_e(sport_title)  # ÚJ
                        }
                        
                        if is_rizikos:
                            if meccs_nev not in rizikos_dict or legjobb_ketesely['esely'] > rizikos_dict[meccs_nev]['esely']:
                                rizikos_dict[meccs_nev] = meccs_adat
                        elif legjobb_ketesely['esely'] >= KUSZOB_MIN:
                            if meccs_nev not in jeloltek_dict or legjobb_ketesely['esely'] > jeloltek_dict[meccs_nev]['esely']:
                                jeloltek_dict[meccs_nev] = meccs_adat
                        else:
                            if meccs_nev not in figyelolista_dict or legjobb_ketesely['esely'] > figyelolista_dict[meccs_nev]['esely']:
                                figyelolista_dict[meccs_nev] = meccs_adat
        else:
            st.error(f"Hiba az API-val: {valasz.status_code} - {valasz.text}")
    
    # ==========================================
    # MEGJELENÍTÉS
    # ==========================================
    jeloltek = list(jeloltek_dict.values())
    jeloltek.sort(key=lambda x: x['esely'], reverse=True)
    top_lista = jeloltek[:MAX_LISTA]
    
    figyelo_lista = list(figyelolista_dict.values())
    figyelo_lista.sort(key=lambda x: x['esely'], reverse=True)
    figyelo_lista = figyelo_lista[:MAX_LISTA]
    
    rizikos_lista = list(rizikos_dict.values())
    rizikos_lista.sort(key=lambda x: x['esely'], reverse=True)
    
    if not top_lista and not figyelo_lista and not rizikos_lista:
        st.warning(f"📭 Nincs olyan jövőbeli foci meccs (120 órán belül), ahol a Kétesély opció esélye elérné a {int(KUSZOB_FIGYELO*100)}%-ot. Az app azt javasolja: ma ne fogadj.")
    else:
        # --- TOP 3 ---
        if top_lista:
            st.markdown("<div class='top3-header'>⭐ TOP 3 LEGJOBB TIPP (82% felett) ⭐</div>", unsafe_allow_html=True)
            for i, j in enumerate(top_lista[:3], 1):
                st.markdown("<div class='top3-card'>", unsafe_allow_html=True)
                cim = f"⭐ | {j['meccs']}  —  {j['opcio_nev']} ({j['esely']*100:.1f}%)"
                with st.expander(cim, expanded=True):
                    st.markdown(f"<div style='font-size: 1em; color: #FFD700; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                    st.markdown(f"**Liga:** {j['liga']}")
                    
                    # ÚJ: Kieséses figyelmeztetés
                    if j.get('kieseses', False):
                        st.markdown("<div class='kieseses-warn'>⚠️ KIESÉSES MÉRKŐZÉS! A döntetlen utáni hosszabbítás/továbbjutás befolyásolhatja a kimenetelt. Fogadj óvatosan!</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                    st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                    tet = javasolt_tet(j['esely'])
                    varhato_nyeremeny = tet * j['odds']
                    netto = varhato_nyeremeny - tet
                    st.markdown(f"<div class='suggested-bet'>💰 Javasolt tét: {tet} Ft</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #22C55E; font-weight: bold; font-size: 1.1em;'>📈 Várható nyeremény: {varhato_nyeremeny:.0f} Ft (Nettó: +{netto:.0f} Ft)</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='median-info'>🔒 Biztonság: {j['irodak_szama']} fogadóiroda mediánja alapján</div>", unsafe_allow_html=True)
                    st.markdown("<div class='tippmix-warn'>⚠️ Figyelem: Ez a Kétesély opció nem biztos, hogy elérhető a Tippmix Pro-n!</div>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")
                st.markdown("</div>", unsafe_allow_html=True)
            
            if len(top_lista) > 3:
                st.markdown("<div class='other-header'>További biztonságos meccsek (82% felett)</div>", unsafe_allow_html=True)
                for i, j in enumerate(top_lista[3:], 4):
                    st.markdown("<div class='other-card'>", unsafe_allow_html=True)
                    cim = f"🟡 | {j['meccs']}  —  {j['opcio_nev']} ({j['esely']*100:.1f}%)"
                    with st.expander(cim, expanded=False):
                        st.markdown(f"<div style='font-size: 1em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                        st.markdown(f"**Liga:** {j['liga']}")
                        
                        # ÚJ: Kieséses figyelmeztetés
                        if j.get('kieseses', False):
                            st.markdown("<div class='kieseses-warn'>⚠️ KIESÉSES MÉRKŐZÉS! A döntetlen utáni hosszabbítás/továbbjutás befolyásolhatja a kimenetelt. Fogadj óvatosan!</div>", unsafe_allow_html=True)
                        
                        st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                        st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                        tet = javasolt_tet(j['esely'])
                        varhato_nyeremeny = tet * j['odds']
                        netto = varhato_nyeremeny - tet
                        st.markdown(f"<div class='suggested-bet'>💰 Javasolt tét: {tet} Ft</div>", unsafe_allow_html=True)
                        st.markdown(f"<div style='color: #22C55E; font-weight: bold; font-size: 1.1em;'>📈 Várható nyeremény: {varhato_nyeremeny:.0f} Ft (Nettó: +{netto:.0f} Ft)</div>", unsafe_allow_html=True)
                        st.markdown(f"<div class='median-info'>🔒 Biztonság: {j['irodak_szama']} fogadóiroda mediánja alapján</div>", unsafe_allow_html=True)
                        st.markdown("<div class='tippmix-warn'>⚠️ Figyelem: Ez a Kétesély opció nem biztos, hogy elérhető a Tippmix Pro-n!</div>", unsafe_allow_html=True)
                        st.markdown("---")
                        st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")
                    st.markdown("</div>", unsafe_allow_html=True)
        
        # --- FIGYELŐLISTA ---
        if figyelo_lista:
            st.markdown("<div class='watch-header'>🟡 Figyelőlista (75-82% között)</div>", unsafe_allow_html=True)
            for j in figyelo_lista:
                st.markdown("<div class='watch-card'>", unsafe_allow_html=True)
                cim = f"🟡 | {j['meccs']}  —  {j['opcio_nev']} ({j['esely']*100:.1f}%)"
                with st.expander(cim, expanded=False):
                    st.markdown(f"<div style='font-size: 1em; color: #FACC15; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                    st.markdown(f"**Liga:** {j['liga']}")
                    
                    # ÚJ: Kieséses figyelmeztetés
                    if j.get('kieseses', False):
                        st.markdown("<div class='kieseses-warn'>⚠️ KIESÉSES MÉRKŐZÉS! A döntetlen utáni hosszabbítás/továbbjutás befolyásolhatja a kimenetelt. Fogadj óvatosan!</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                    st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                    tet = javasolt_tet(j['esely'])
                    varhato_nyeremeny = tet * j['odds']
                    netto = varhato_nyeremeny - tet
                    st.markdown(f"<div class='suggested-bet'>💰 Javasolt tét: {tet} Ft</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #22C55E; font-weight: bold; font-size: 1.1em;'>📈 Várható nyeremény: {varhato_nyeremeny:.0f} Ft (Nettó: +{netto:.0f} Ft)</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='median-info'>🔒 Biztonság: {j['irodak_szama']} fogadóiroda mediánja alapján</div>", unsafe_allow_html=True)
                    st.markdown("<div class='tippmix-warn'>⚠️ Figyelem: Ez a Kétesély opció nem biztos, hogy elérhető a Tippmix Pro-n!</div>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")
                st.markdown("</div>", unsafe_allow_html=True)
        
        # --- RIZIKÓS MECCSEK ---
        if rizikos_lista:
            st.markdown("<div class='risk-header'>⚠️ RIZIKÓS LIGÁK (fokozott óvatosság)</div>", unsafe_allow_html=True)
            for j in rizikos_lista:
                st.markdown("<div class='risk-card'>", unsafe_allow_html=True)
                cim = f"🟠 | {j['meccs']}  —  {j['opcio_nev']} ({j['esely']*100:.1f}%)"
                with st.expander(cim, expanded=False):
                    st.markdown(f"<div class='risk-warning'>⚠️ FIGYELEM: Ez a meccs rizikós ligából van ({j['liga']}). Csak saját felelősségre fogadj!</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='font-size: 1em; color: #FF8C00; margin-bottom: 15px;'>📅 Kezdés: <b>{j['kezdes']}</b></div>", unsafe_allow_html=True)
                    st.markdown(f"**Liga:** {j['liga']}")
                    
                    # ÚJ: Kieséses figyelmeztetés
                    if j.get('kieseses', False):
                        st.markdown("<div class='kieseses-warn'>⚠️ KIESÉSES MÉRKŐZÉS! A döntetlen utáni hosszabbítás/továbbjutás befolyásolhatja a kimenetelt. Fogadj óvatosan!</div>", unsafe_allow_html=True)
                    
                    st.markdown(f"**Javasolt tipp:** {j['opcio_nev']}")
                    st.markdown(f"**Esély:** {j['esely']*100:.1f}% | **Odds:** {j['odds']:.2f}")
                    tet = javasolt_tet(j['esely'])
                    varhato_nyeremeny = tet * j['odds']
                    netto = varhato_nyeremeny - tet
                    st.markdown(f"<div class='suggested-bet'>💰 Javasolt tét: {tet} Ft</div>", unsafe_allow_html=True)
                    st.markdown(f"<div style='color: #22C55E; font-weight: bold; font-size: 1.1em;'>📈 Várható nyeremény: {varhato_nyeremeny:.0f} Ft (Nettó: +{netto:.0f} Ft)</div>", unsafe_allow_html=True)
                    st.markdown(f"<div class='median-info'>🔒 Biztonság: {j['irodak_szama']} fogadóiroda mediánja alapján</div>", unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("[🔍 Ugrás a Tippmix oldalára](https://www.tippmix.hu/mobil/elo)")
                st.markdown("</div>", unsafe_allow_html=True)
        
        # --- KOMBINÁCIÓ ---
        if len(top_lista) >= 2:
            kombi_meccsek = top_lista[:2]
            kombi_odds = 1.0
            kombi_esely = 1.0
            kombi_html_elemek = ""
            for k in kombi_meccsek:
                kombi_odds *= k['odds']
                kombi_esely *= k['esely']
                kombi_html_elemek += f"<div class='kombi-item'><span>✅ {k['meccs']} - {k['opcio_nev']}</span> <span class='kombi-percent'>({k['esely']*100:.1f}%)</span></div>"
            kombi_tet = 200
            kombi_nyeremeny = kombi_tet * kombi_odds
            st.markdown(f"""
            <div class="kombi-box">
                <div class="kombi-title">🔥 Napi Kombináció ({len(kombi_meccsek)} meccs)</div>
                {kombi_html_elemek}
                <div class="kombi-odds">📈 Kombinált Odds: {kombi_odds:.2f}</div>
                <div style="text-align: center; color: #FACC15; margin-top: 10px;">
                    <b>Kombinált esély:</b> {kombi_esely*100:.1f}% (Veszteség esélye: {(1-kombi_esely)*100:.1f}%)
                </div>
                <div style="text-align: center; color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 15px;">
                    💰 Javasolt tét: {kombi_tet} Ft
                </div>
                <div style="text-align: center; color: #22C55E; font-weight: bold; font-size: 1.1em; margin-top: 5px;">
                    📈 Várható nyeremény: {kombi_nyeremeny:.0f} Ft
