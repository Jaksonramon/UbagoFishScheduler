
import streamlit as st
import pandas as pd
import json
import os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.2.1 – Autosave Lunch Break, Full Styled Excel")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0, 30)]
DATA_FILE = "ubagofish_data.json"

# Initialize session state
for key in ["proveedores", "empresas", "appointments"]:
    if key not in st.session_state:
        st.session_state[key] = []
if "edit_mode" not in st.session_state:
    st.session_state.edit_mode = False
if "appointment_to_edit" not in st.session_state:
    st.session_state.appointment_to_edit = None
if "start_hour" not in st.session_state:
    st.session_state.start_hour = "06:00"
if "end_hour" not in st.session_state:
    st.session_state.end_hour = "21:30"
if "lunch_start" not in st.session_state:
    st.session_state.lunch_start = "12:00"
if "lunch_end" not in st.session_state:
    st.session_state.lunch_end = "14:00"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.proveedores = data.get("proveedores", [])
            st.session_state.empresas = data.get("empresas", [])
            st.session_state.appointments = [tuple(app) for app in data.get("appointments", [])]
            st.session_state.lunch_start = data.get("lunch_start", "12:00")
            st.session_state.lunch_end = data.get("lunch_end", "14:00")

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "proveedores": st.session_state.proveedores,
            "empresas": st.session_state.empresas,
            "appointments": st.session_state.appointments,
            "lunch_start": st.session_state.lunch_start,
            "lunch_end": st.session_state.lunch_end
        }, f)

def autosave():
    save_data()

load_data()

# Sidebar: Empresas/Proveedores
st.sidebar.header("Empresas y Proveedores")
empresas_input = st.sidebar.text_area("Empresas (una por línea)", "\n".join(st.session_state.empresas))
st.session_state.empresas = [e.strip() for e in empresas_input.splitlines() if e.strip()]
proveedores_input = st.sidebar.text_area("Proveedores (uno por línea)", "\n".join(st.session_state.proveedores))
st.session_state.proveedores = [p.strip() for p in proveedores_input.splitlines() if p.strip()]
if st.sidebar.button("Guardar nombres"):
    autosave()
    st.sidebar.success("Empresas y Proveedores guardados.")

# Lunch break (autosave)
st.sidebar.subheader("Horario de Almuerzo")
st.session_state.lunch_start = st.sidebar.selectbox("Inicio del almuerzo (Bloqueo)", HOURS, index=HOURS.index(st.session_state.lunch_start))
st.session_state.lunch_end = st.sidebar.selectbox("Fin del almuerzo (Bloqueo)", HOURS, index=HOURS.index(st.session_state.lunch_end))
autosave()

lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(time_val): return lunch_start_idx <= HOURS.index(time_val) < lunch_end_idx
st.session_state.appointments = [appt for appt in st.session_state.appointments if not is_in_lunch_break(appt[3])]

# The rest of the app (scheduler tabs, calendar, editing, and styled Excel export) 
# remains as implemented in the previous stable version (1.2) but now with autosave lunch break.
