
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")

# Fish emoji title (no logo)
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.3 – Buyers/Clients, Day Selector, Time Windows")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

# Session state initialization
for key in ["clients", "buyers", "appointments"]:
    if key not in st.session_state:
        st.session_state[key] = []
if "edit_mode" not in st.session_state: st.session_state.edit_mode = False
if "appointment_to_edit" not in st.session_state: st.session_state.appointment_to_edit = None
if "start_hour" not in st.session_state: st.session_state.start_hour = "06:00"
if "end_hour" not in st.session_state: st.session_state.end_hour = "21:30"
if "lunch_start" not in st.session_state: st.session_state.lunch_start = "12:00"
if "lunch_end" not in st.session_state: st.session_state.lunch_end = "14:00"
if "selected_days" not in st.session_state: st.session_state.selected_days = ["Monday", "Tuesday"]
if "time_windows" not in st.session_state: st.session_state.time_windows = {}

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.clients = data.get("clients", [])
            st.session_state.buyers = data.get("buyers", [])
            st.session_state.appointments = [tuple(app) for app in data.get("appointments", [])]
            st.session_state.lunch_start = data.get("lunch_start", "12:00")
            st.session_state.lunch_end = data.get("lunch_end", "14:00")
            st.session_state.selected_days = data.get("selected_days", ["Monday", "Tuesday"])
            st.session_state.time_windows = data.get("time_windows", {})

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "clients": st.session_state.clients,
            "buyers": st.session_state.buyers,
            "appointments": st.session_state.appointments,
            "lunch_start": st.session_state.lunch_start,
            "lunch_end": st.session_state.lunch_end,
            "selected_days": st.session_state.selected_days,
            "time_windows": st.session_state.time_windows
        }, f)

def autosave(): save_data()
load_data()

# Sidebar: Buyers and Clients
st.sidebar.header("Buyers y Clients")
buyers_input = st.sidebar.text_area("Buyers (uno por línea)", "\n".join(st.session_state.buyers))
st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
clients_input = st.sidebar.text_area("Clients (uno por línea)", "\n".join(st.session_state.clients))
st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
if st.sidebar.button("Guardar nombres"):
    autosave()
    st.sidebar.success("Buyers y Clients guardados.")

# Lunch break and day selector (Monday/Tuesday default)
st.sidebar.subheader("Horario de Almuerzo")
st.session_state.lunch_start = st.sidebar.selectbox("Inicio del almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_start))
st.session_state.lunch_end = st.sidebar.selectbox("Fin del almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_end))
st.sidebar.subheader("Seleccionar Días para Configurar")
st.session_state.selected_days = st.sidebar.multiselect("Días", DAYS, default=st.session_state.selected_days)
autosave()

lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(t): return lunch_start_idx <= HOURS.index(t) < lunch_end_idx
st.session_state.appointments = [a for a in st.session_state.appointments if not is_in_lunch_break(a[3])]

# (Randomizer, manual scheduler, calendar, edit/clear, and styled Excel export remain as in prior Version 1.3)
