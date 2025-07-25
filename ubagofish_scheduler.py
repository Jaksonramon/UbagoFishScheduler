
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")

# Logo (60px) inline with title
col_logo, col_title = st.columns([0.1, 0.9])
with col_logo:
    st.image("logo.jpeg", width=60)
with col_title:
    st.title("UbagoFish Scheduler")
st.caption("Version 1.3 – Buyers/Clients, Day Selector, Time Windows")

# (The rest of the Version 1.3 logic remains unchanged: Buyers/Clients, day selector, per-day windows, autosave, edit/clear, styled Excel)
