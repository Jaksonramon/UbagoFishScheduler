
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="🐟UbagoFish Scheduler", layout="wide")

with col_title:
    st.title("🐟UbagoFish Scheduler")
st.caption("Version 1.3 – Buyers/Clients, Day Selector, Time Windows")

# Days, hours, and data file
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
if "selected_days" not in st.session_state: st.session_state.selected_days = DAYS
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
            st.session_state.selected_days = data.get("selected_days", DAYS)
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

# Sidebar: Buyers (Empresas) and Clients (Proveedores)
st.sidebar.header("Buyers y Clients")
buyers_input = st.sidebar.text_area("Buyers (uno por línea)", "\n".join(st.session_state.buyers))
st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
clients_input = st.sidebar.text_area("Clients (uno por línea)", "\n".join(st.session_state.clients))
st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
if st.sidebar.button("Guardar nombres"):
    autosave()
    st.sidebar.success("Buyers y Clients guardados.")

# Lunch break and days selector
st.sidebar.subheader("Horario de Almuerzo")
st.session_state.lunch_start = st.sidebar.selectbox("Inicio del almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_start))
st.session_state.lunch_end = st.sidebar.selectbox("Fin del almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_end))
st.sidebar.subheader("Seleccionar Días para Configurar")
st.session_state.selected_days = st.sidebar.multiselect("Días", DAYS, default=st.session_state.selected_days)
autosave()

lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(t): return lunch_start_idx <= HOURS.index(t) < lunch_end_idx
st.session_state.appointments = [a for a in st.session_state.appointments if not is_in_lunch_break(a[3])]

# Randomizer tab with per-day time windows (optional)
tab1, tab2 = st.tabs(["🎲 Generador Aleatorio", "📝 Agendar Manualmente"])
with tab1:
    st.subheader("🎲 Generar citas aleatorias")
    selected_buyers = []
    col1, col2 = st.columns([1,1])
    with col1:
        if "buyers_random" not in st.session_state:
            st.session_state.buyers_random = [""]
        for i,_ in enumerate(st.session_state.buyers_random):
            buyer = st.selectbox(f"Buyer {i+1}", options=st.session_state.buyers, key=f"buyer_random_{i}")
            selected_buyers.append(buyer)
        if st.button("➕ Agregar otro Buyer"):
            st.session_state.buyers_random.append("")
    with col2:
        selected_clients = st.multiselect("Seleccionar Clients", options=st.session_state.clients)

    st.markdown("### Configurar ventanas horarias (opcional)")
    for buyer in selected_buyers:
        st.markdown(f"**{buyer}**")
        st.session_state.time_windows.setdefault(buyer, {})
        for day in st.session_state.selected_days:
            col_from, col_to = st.columns(2)
            with col_from:
                start = st.selectbox(f"{day} desde", HOURS, key=f"{buyer}_{day}_start", index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)))
            with col_to:
                end = st.selectbox(f"{day} hasta", HOURS, key=f"{buyer}_{day}_end", index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)))
            st.session_state.time_windows[buyer][day] = {"start": start, "end": end}
    autosave()

    interval = st.selectbox("Duración de la cita (min)", [30, 60])
    if st.button("🔀 Generar citas aleatorias"):
        for buyer in selected_buyers:
            for client in selected_clients:
                for day in st.session_state.selected_days:
                    start = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)
                    end = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)
                    start_idx, end_idx = HOURS.index(start), HOURS.index(end)
                    slots = [h for h in HOURS[start_idx:end_idx] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0]
                    attempts = 0
                    while attempts < 5 and slots:
                        t = choice(slots)
                        if (client,buyer,day,t) not in st.session_state.appointments:
                            st.session_state.appointments.append((client,buyer,day,t))
                            break
                        attempts += 1
        autosave()
        st.success("Citas generadas.")

# (Manual scheduler, calendar, edit/clear, and styled Excel export logic from 1.2.1 remains unchanged but uses Buyers/Clients labels)
