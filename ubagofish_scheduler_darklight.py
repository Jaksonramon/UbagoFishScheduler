
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from datetime import datetime
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler - Dark/Light v1.4", layout="wide")

# Initialize session state for dark mode
if "dark_mode" not in st.session_state:
    st.session_state.dark_mode = False

# Sidebar toggle
with st.sidebar:
    toggle = st.checkbox("🌙 Activar modo oscuro", value=st.session_state.dark_mode)
    if toggle != st.session_state.dark_mode:
        st.session_state.dark_mode = toggle
        st.experimental_rerun()

# Dark/Light palettes
if st.session_state.dark_mode:
    palette = {
        "bg_color": "#1E293B",
        "text_color": "#FFFFFF",
        "header_color": "#F8FAFC",
        "card_color": "#334155",
        "alt_row_color": "#334155",
        "hover_color": "#475569",
        "sidebar_color": "#1E293B"
    }
else:
    palette = {
        "bg_color": "#F8FAFC",
        "text_color": "#1E293B",
        "header_color": "#1E293B",
        "card_color": "#FFFFFF",
        "alt_row_color": "#F2F6FA",
        "hover_color": "#E6FFF5",
        "sidebar_color": "#F1F5F9"
    }

# Load CSS and apply palette
with open("style.css") as f:
    css_template = f.read()
css = css_template.format(**palette)
st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)

# Title with fish emoji
st.title("🐟 UbagoFish Scheduler – Dark/Light v1.4")
st.caption(f"Current time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

# (The rest of the app: scheduler, calendar, export, edit — unchanged from previous working version)
# Copy the rest of the core logic here (appointments, randomizer, manual scheduler, calendar, etc.)
