import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import statistics
import json

st.set_page_config(page_title="Napi Foci Tipp", page_icon="⚽", layout="centered")

CSS = """
<style>
.stApp { background-color: #12161A; color: #E0E0E0; }
h1 { color: #FFFFFF; font-family: 'Segoe UI', sans-serif; font-weight: 800; font-size: 2.5em; text-align: center; margin-bottom: 20px; }
.top3-header { color: #FFD700; font-size: 2em; font-weight: 900; text-align: center; margin-top: 30px; margin-bottom: 20px; text-shadow: 0 0 10px rgba(255, 215, 0, 0.5); }
.top3-card .streamlit-expanderHeader { background-color: #2D1B00 !important; border-radius: 8px !important; color: #FFD700 !important; font-weight: 900 !important; font-size: 1.4em !important; border: 2px solid #FFD700 !important; padding: 15px 20px !important; margin-bottom: 8px; }
.top3-card .streamlit-expanderContent { background-color: #1A1000 !important; border: 2px solid #FFD700 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 20px !important; }
.other-header { color: #A0AAB5; font-size: 1.5em; font-weight: 700; text-align: center; margin-top: 30px; margin-bottom: 20px; }
.other-card .streamlit-expanderHeader { background-color: #1E252B !important; border-radius: 8px !important; color: #A0AAB5 !important; font-weight: 600 !important; font-size: 1.1em !important; border: 1px solid #444 !important; padding: 12px 15px !important; margin-bottom: 5px; }
.other-card .streamlit-expanderContent { background-color: #161A1F !important; border: 1px solid #444 !important; border-top: none !important; border-bottom-left-radius: 8px !important; border-bottom-right-radius: 8px !important; padding: 15px !important; }
.stButton>button { background-color: #FACC15; color: #000000; font-weight: 700; font-size: 1.1em; border-radius: 6px; border: none; padding: 10px 15px; width: 100%; }
.clock-container { display: flex; justify-content: center; align-items: center; margin-top: 10px; margin-bottom: 15px; }
.live-clock { font-family: 'Courier New', monospace; font-size: 1.6em; color: #FACC15; background-color: #1E252B; padding: 10px 20px; border-radius: 8px; border: 1px solid #444; font-weight: 800; }
.warning-box { background-color: #332211; border-left: 4px solid #FACC15; padding: 10px; margin-bottom: 15px; border-radius: 4px; color: #E0E0E0; font-size: 0.9em; }
.suggested-bet { color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 10px; }
.kombi-box { background: linear-gradient(135deg, #2D1B4E, #4A2C6D); border: 2px solid #9D4EDD; border-radius: 12px; padding: 20px; margin-top: 30px; }
.kombi-title { color: #FACC15; font-size: 1.8em; font-weight: 900; text-align: center; margin-bottom: 15px; text-transform: uppercase; letter-spacing: 2px; }
.kombi-item { color: #FFFFFF; font-size: 1.1em; margin-bottom: 8px; padding-left: 10px; border-left: 3px solid #FACC15; display: flex; justify-content: space-between; }
.kombi-percent { color: #22C55E; font-weight: bold; }
.kombi-odds { color: #22C55E; font-size: 1.5em; font-weight: bold; text-align: center; margin-top: 15px; }
.median-info { background-color: #1E252B; border-left: 3px solid #FACC15; padding: 8px; margin-top: 10px; border-radius: 4px; font-size: 0.85em; color: #A0AAB5; }
.smart-money { background-color: #0D2818; border-left: 3px solid #22C55E; padding: 8px; margin-top: 8px; border-radius: 4px; font-size: 0.85em; color: #22C55E; font-weight: bold; }
.odds-drop { background-color: #3D1400; border-left: 3px solid #FF4444; padding: 8px; margin-top: 8px; border-radius: 4px; font-size: 0.85em; color: #FF4444; font-weight: bold; }
.stats-box { background-color: #1E252B; border: 1px solid #444; border-radius: 8px; padding: 15px; margin-top: 20px; }
.stats-title { color: #FACC15; font-size: 1.3em; font-weight: 800; margin-bottom: 10px; }
.stats-row { display: flex; justify-content: space-between; padding: 5px 0; border-bottom: 1px solid #333; }
.stats-label { color: #A0AAB5; }
.stats-value { color: #FFFFFF; font-weight: bold; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

st.markdown("<h1>⚽ Napi Foci Tipp (72 óra)</h1>", unsafe_allow_html=True)

@st.fragment(run_every=1)
def ora_frissites():
    hu_tz = pytz.timezone('Europe/Budapest')
    aktualis_ido = datetime.now(hu_tz)
    clock_html = "<div class='clock-container'><div class='live-clock'>📅 " + aktualis_ido.strftime('%Y-%m-%d') + " | ⏰ " + aktualis_ido.strftime('%H:%M:%S') + "</div></div>"
    st.markdown(clock_html, unsafe_allow_html=True)

ora_frissites()

st.markdown("""
<div class="warning-box">
⚠️ <b>FIGYELEM!</b> Az app a következő 72 óra legbiztonságosabb tippjeit mutatja (<b>80% feletti esély</b>, Kétesély).
Az oddsok <b>medián</b> alapján számolódnak (több fogadóiroda). A <b style="color:#22C55E">zöld</b> jelzi az odds esést (smart money), a <b style="color:#FF4444">piros</b> az emelkedést.
A sportfogadás kockázattal jár!
</div>
""", unsafe_allow_html=True)

ODDS_API_KEY = "985c99f23fcd23aa4acce2ef5d3a99ba"
KUSZOB_MIN = 0.80
MIN_IRODAK = 2
MAX_LISTA = 10

if st.button("🔄 Adatok frissítése"):
    st.cache_data.clear()

def javasolt_tet(esely):
    if esely >= 0.98: return 1000
    elif esely >= 0.95: return 800
    elif esely >= 0.90: return 500
    elif esely >= 0.85: return 300
    elif esely >= 0.80: return 200
    elif esely >= 0.75: return 150
    else: return 100

def get_odds_from_api():
    most_utc = datetime.now(pytz.utc)
    kezdo_datum = most_utc.strftime("%Y-%m-%dT00:00:00Z")
    veg_datum = (most_utc + timedelta(days=2)).strftime("%Y-%m-%dT23:59:59Z")
    url = "https://api.the-odds-api.com/v4/sports/soccer/odds/?apiKey=" + ODDS_API_KEY + "&regions=eu&markets=h2h&oddsFormat=decimal&commenceTimeFrom=" + kezdo_datum + "&commenceTimeTo=" + veg_datum
    valasz = requests.get(url)
    if valasz.status_code == 200:
        return valasz.json()
    else:
        st.error("API hiba: " + str(valasz.status_code))
        return []

def szamolj_mediant(lista):
    if not lista:
        return 0
    return statistics.median(lista)

def szamolj_szorast(lista):
    if len(lista) < 2:
        return 0
    return statistics.stdev(lista)

def odds_valtozas_uzenet(regi_odds, uj_odds):
    if regi_odds == 0 or uj_odds == 0:
        return ""
    valtozas_szazalek = ((uj_odds - regi_odds) / regi_odds) * 100
    if valtozas_szazalek < -3:
        return "<div class='smart-money'>📉 Smart Money: Az odds " + str(abs(round(valtozas_szazalek, 1))) + "%-ot esett (erősödő esély)</div>"
    elif valtozas_szazalek > 3:
        return "<div class='odds-drop'>📈 Figyelem: Az odds " + str(round(valtozas_szazalek, 1)) + "%-ot emelkedett (gyengülő esély)</div>"
    else:
        return "<div class='median-info'>➡️ Stabil odds (változás: " + str(round(valtozas_szazalek, 1)) + "%)</div>"

if 'elozo_oddsok' not in st.session_state:
    st.session_state.elozo_oddsok = {}

if 'statisztika' not in st.session_state:
    st.session_state.statisztika = {'tippek_szama': 0, 'nyert': 0, 'vesztett': 0}

try:
    most_utc = datetime.now(pytz.utc)
    hu_tz = pytz.timezone('Europe/Budapest')
    
    with st.spinner("Meccsek lekérdezése..."):
        meccsek = get_odds_from_api()
    
    jeloltek_dict = {}
    uj_oddsok = {}
    
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
        
        median_hazai = szamolj_mediant(hazai_oddsok)
        median_vendeg = szamolj_mediant(vendeg_oddsok)
        median_dontetlen = szamolj_mediant(dontetlen_oddsok)
        
        nyers_osszeg = (1/median_hazai) + (1/median_vendeg) + (1/median_dontetlen)
        
        if nyers_osszeg > 0:
            esely_1x = (1/median_hazai + 1/median_dontetlen) / nyers_osszeg
            odds_1x = 1 / esely_1x if esely_1x > 0 else 0
            
            esely_x2 = (1/median_vendeg + 1/median_dontetlen) / nyers_osszeg
            odds_x2 = 1 / esely_x2 if esely_x2 > 0 else 0
            
            ketesely_opciok = [
                {'nev': m['home_team'] + " vagy Döntetlen (1X)", 'esely': esely_1x, 'odds': odds_1x},
                {'nev': m['away_team'] + " vagy Döntetlen (X2)", 'esely': esely_x2, 'odds': odds_x2}
            ]
            
            legjobb = None
            for opcio in ketesely_opciok:
                if opcio['esely'] >= KUSZOB_MIN:
                    if legjobb is None or opcio['esely'] > legjobb['esely']:
                        legjobb = opcio
            
            if legjobb:
                meccs_nev = m['home_team'] + " - " + m['away_team']
                meccs_key = m['home_team'] + "_" + m['away_team']
                
                regi_odds = st.session_state.elozo_oddsok.get(meccs_key + "_" + legjobb['nev'], 0)
                uj_oddsok[meccs_key + "_" + legjobb['nev']] = legjobb['odds']
                
                if meccs_nev not in jeloltek_dict or legjobb['esely'] > jeloltek_dict[meccs_nev]['esely']:
                    jeloltek_dict[meccs_nev] = {
                        'meccs': meccs_nev,
                        'kezdes': kezdes_hu.strftime("%Y-%m-%d %H:%M"),
                        'esely': legjobb['esely'],
                        'opcio_nev': legjobb['nev'],
                        'odds': legjobb['odds'],
                        'irodak_szama': len(hazai_oddsok),
                        'szoras': szamolj_szorast(hazai_oddsok + vendeg_oddsok + dontetlen_oddsok),
                        'meccs_key': meccs_key,
                        'regi_odds': regi_odds
                    }
    
    st.session_state.elozo_oddsok = uj_oddsok
    
    jeloltek = list(jeloltek_dict.values())
    jeloltek.sort(key=lambda x: x['esely'], reverse=True)
    top_lista = jeloltek[:MAX_LISTA]
    
    if not top_lista:
        st.warning("📭 Nincs " + str(int(KUSZOB_MIN*100)) + "% feletti meccs. Ma ne fogadj.")
    else:
        st.markdown("<div class='top3-header'>⭐ TOP 3 LEGJOBB TIPP ⭐</div>", unsafe_allow_html=True)
        for i, j in enumerate(top_lista[:3], 1):
            st.markdown("<div class='top3-card'>", unsafe_allow_html=True)
            cim = "⭐ | " + j['meccs'] + " — " + j['opcio_nev'] + " (" + str(round(j['esely']*100, 1)) + "%)"
            with st.expander(cim, expanded=True):
                st.markdown("<div style='font-size: 1em; color: #FFD700; margin-bottom: 15px;'>📅 Kezdés: <b>" + j['kezdes'] + "</b></div>", unsafe_allow_html=True)
                st.markdown("**Javasolt tipp:** " + j['opcio_nev'])
                st.markdown("**Esély:** " + str(round(j['esely']*100, 1)) + "% | **Odds:** " + str(round(j['odds'], 2)))
                tet = javasolt_tet(j['esely'])
                varhato = tet * j['odds']
                netto = varhato - tet
                st.markdown("<div class='suggested-bet'>💰 Javasolt tét: " + str(tet) + " Ft</div>", unsafe_allow_html=True)
                st.markdown("<div style='color: #22C55E; font-weight: bold; font-size: 1.1em;'>📈 Várható nyeremény: " + str(round(varhato)) + " Ft (Nettó: +" + str(round(netto)) + " Ft)</div>", unsafe_allow_html=True)
                st.markdown("<div class='median-info'>🔒 " + str(j['irodak_szama']) + " fogadóiroda mediánja | Szórás: " + str(round(j['szoras'], 3)) + "</div>", unsafe_allow_html=True)
                if j['regi_odds'] > 0:
                    uzenet = odds_valtozas_uzenet(j['regi_odds'], j['odds'])
                    st.markdown(uzenet, unsafe_allow_html=True)
                st.markdown("---")
                st.markdown("[🔍 Tippmix](https://www.tippmix.hu/mobil/elo)")
            st.markdown("</div>", unsafe_allow_html=True)
        
        if len(top_lista) > 3:
            st.markdown("<div class='other-header'>További meccsek</div>", unsafe_allow_html=True)
            for j in top_lista[3:]:
                st.markdown("<div class='other-card'>", unsafe_allow_html=True)
                cim = "🟡 | " + j['meccs'] + " — " + j['opcio_nev'] + " (" + str(round(j['esely']*100, 1)) + "%)"
                with st.expander(cim, expanded=False):
                    st.markdown("<div style='font-size: 1em; color: #A0AAB5; margin-bottom: 15px;'>📅 Kezdés: <b>" + j['kezdes'] + "</b></div>", unsafe_allow_html=True)
                    st.markdown("**Tipp:** " + j['opcio_nev'])
                    st.markdown("**Esély:** " + str(round(j['esely']*100, 1)) + "% | **Odds:** " + str(round(j['odds'], 2)))
                    tet = javasolt_tet(j['esely'])
                    varhato = tet * j['odds']
                    netto = varhato - tet
                    st.markdown("<div class='suggested-bet'>💰 Tét: " + str(tet) + " Ft</div>", unsafe_allow_html=True)
                    st.markdown("<div style='color: #22C55E; font-weight: bold;'>📈 Nyeremény: " + str(round(varhato)) + " Ft (+ " + str(round(netto)) + " Ft)</div>", unsafe_allow_html=True)
                    st.markdown("<div class='median-info'>🔒 " + str(j['irodak_szama']) + " iroda | Szórás: " + str(round(j['szoras'], 3)) + "</div>", unsafe_allow_html=True)
                    if j['regi_odds'] > 0:
                        uzenet = odds_valtozas_uzenet(j['regi_odds'], j['odds'])
                        st.markdown(uzenet, unsafe_allow_html=True)
                    st.markdown("---")
                    st.markdown("[🔍 Tippmix](https://www.tippmix.hu/mobil/elo)")
                st.markdown("</div>", unsafe_allow_html=True)
        
        if len(top_lista) >= 2:
            kombi = top_lista[:3]
            kombi_odds = 1.0
            kombi_esely = 1.0
            kombi_html = ""
            for k in kombi:
                kombi_odds *= k['odds']
                kombi_esely *= k['esely']
                kombi_html += "<div class='kombi-item'><span>✅ " + k['meccs'] + " - " + k['opcio_nev'] + "</span> <span class='kombi-percent'>(" + str(round(k['esely']*100, 1)) + "%)</span></div>"
            kombi_tet = 200
            kombi_nyer = kombi_tet * kombi_odds
            kombi_box = "<div class='kombi-box'><div class='kombi-title'>🔥 Napi Kombináció (" + str(len(kombi)) + " meccs)</div>" + kombi_html + "<div class='kombi-odds'>📈 Kombinált Odds: " + str(round(kombi_odds, 2)) + "</div><div style='text-align: center; color: #FACC15; margin-top: 10px;'><b>Kombinált esély:</b> " + str(round(kombi_esely*100, 1)) + "% (Veszteség: " + str(round((1-kombi_esely)*100, 1)) + "%)</div><div style='text-align: center; color: #22C55E; font-weight: bold; font-size: 1.2em; margin-top: 15px;'>💰 Tét: " + str(kombi_tet) + " Ft</div><div style='text-align: center; color: #22C55E; font-weight: bold; font-size: 1.1em; margin-top: 5px;'>📈 Nyeremény: " + str(round(kombi_nyer)) + " Ft (+" + str(round(kombi_nyer - kombi_tet)) + " Ft)</div></div>"
            st.markdown(kombi_box, unsafe_allow_html=True)
        
        st.markdown("<div class='stats-box'><div class='stats-title'>📊 Statisztika (Smart Money követés)</div><div class='stats-row'><span class='stats-label'>Aktuális tippek száma:</span><span class='stats-value'>" + str(len(top_lista)) + "</span></div><div class='stats-row'><span class='stats-label'>Átlagos esély:</span><span class='stats-value'>" + str(round(sum(x['esely'] for x in top_lista) / len(top_lista) * 100, 1)) + "%</span></div><div class='stats-row'><span class='stats-label'>Odds mozgás figyelve:</span><span class='stats-value'>✅ Igen</span></div><div class='stats-row'><span class='stats-label'>Medián alapú számítás:</span><span class='stats-value'>✅ Igen</span></div><div class='stats-row'><span class='stats-label'>Minimum irodák:</span><span class='stats-value'>" + str(MIN_IRODAK) + "</span></div></div>", unsafe_allow_html=True)

except Exception as e:
    st.error("Hiba: " + str(e))
