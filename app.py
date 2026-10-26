import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz  # <-- Ez kell az időzónához

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
        font-size: 2em;
        color: #00D4FF;
        background-color: #1E2129;
        padding: 15px 40px;
        border-radius: 12px;
        border: 2px solid #333;
        font-weight: bold;
        letter-spacing: 2px;
        box-shadow: 0px 4px 15px rgba(0, 212, 255, 0.1);
    }
    </style>
""", unsafe_allow_html=True)

# Középre igazított cím
st.markdown("<h1>⚽ Napi Sport Elemzo</h1>", unsafe_allow_html=True)

# ==========================================
# ÉLŐ ÓRA KÖZÉPEN (Python oldali idő)
# ==========================================
# Beállítjuk a magyar időzónát
hu_tz = pytz.timezone('Europe/Budapest')
aktualis_ido = datetime.now(hu_tz)
datum_szoveg = aktualis_ido.strftime("%Y-%m-%d")
ido_szoveg = aktualis_ido.strftime("%H:%M:%S")

st.markdown(f"""
    <div class="clock-container">
        <div class="live-clock">📅 {datum_szoveg} | ⏰ {ido_szoveg}</div>
    </div>
""", unsafe_allow_html=True)

st.write("A kártyákon látszik a meccs kezdete és várható vége, valamint hogy magában vagy kombinációban érdemes-e megtenni.")

# --- BEALLITASOK ---
# ... (A többi kód ugyanaz marad!) ...
