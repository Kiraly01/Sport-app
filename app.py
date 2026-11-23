import streamlit as st
import requests
from datetime import datetime, timedelta
import pytz
import statistics
import json

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
.smart-money { background-color: #0D2818; border-left: 3px solid #22C55E; padding: 8px; margin-top: 8px; border-radius: 4px; font-size: 0.85em; color: #22C55E; font-weight: bold; }
.odds-drop { background-color: #3D1400; border-left: 3px solid #FF4444; padding: 8px; margin-top: 8px; border-radius: 4px; font-size: 0.85em; color: #FF4444; font-weight: bold; }
.stats-box { background-color: #1E252B; border: 1px solid #444; border-radius: 8px; padding: 15px; margin-top: 20px; }
.stats-title { color: #FACC15; font-size: 1.3em; font-weight: 800; margin-bottom: 10px; }
