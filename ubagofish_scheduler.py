
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler - Pastel Friendly", layout="wide")

# Pastel-friendly CSS styling
st.markdown("""
    <style>
        body {background-color: #FFF9E6;}
        .main {background-color: #FFF9E6;}
        .block-container {font-family: 'Nunito', sans-serif;}
        /* Card containers */
        .card {background-color: #FFFFFF; padding: 1.5rem; margin-bottom: 1.5rem; 
               border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.08); transition: all 0.2s ease-in-out;}
        .card:hover {box-shadow: 0 6px 16px rgba(0,0,0,0.15);}
        /* Sidebar styling */
        section[data-testid="stSidebar"] {background-color: #FFF9E6;}
        section[data-testid="stSidebar"] .stButton>button {border-radius: 8px; background-color: #4DB8FF; color: white; font-weight: 600;}
        /* Buttons */
        div.stButton > button:first-child {border-radius: 8px; padding: 0.5rem 1rem; font-weight: 600; background-color: #4DB8FF; color: white; border:none;}
        div.stButton > button:first-child:hover {background-color: #2A9ED3;}
        /* Dataframe styling */
        .dataframe {font-size: 13px; border-radius: 8px; overflow: hidden;}
        .dataframe thead th {background: #4DB8FF; color: white; font-weight: bold;}
        /* Hover effect on rows */
        .dataframe tbody tr:hover {background-color: #E6FFF5 !important;}
    </style>
""", unsafe_allow_html=True)

st.title("UbagoFish Scheduler – Pastel & Friendly")
st.caption("Playful styled version with all v1.4 features")

# Constants and session state
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

for key in ["clients", "buyers", "appointments"]:
    if key not in st.session_state: st.session_state[key] = []
if "edit_expander_open" not in st.session_state: st.session_state.edit_expander_open = False
if "filter_buyer" not in st.session_state: st.session_state.filter_buyer = None
if "filter_client" not in st.session_state: st.session_state.filter_client = None
if "show_compact" not in st.session_state: st.session_state.show_compact = False
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
        json.dump({"clients": st.session_state.clients, "buyers": st.session_state.buyers, "appointments": st.session_state.appointments,
                   "lunch_start": st.session_state.lunch_start, "lunch_end": st.session_state.lunch_end,
                   "selected_days": st.session_state.selected_days, "time_windows": st.session_state.time_windows}, f)
def autosave(): save_data()
load_data()

# Utility
lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(t): return lunch_start_idx <= HOURS.index(t) < lunch_end_idx
st.session_state.appointments = [a for a in st.session_state.appointments if not is_in_lunch_break(a[3])]

# Sidebar
with st.sidebar:
    with st.expander("Buyers & Clients", expanded=True):
        buyers_input = st.text_area("Buyers (uno por línea)", "\n".join(st.session_state.buyers))
        st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
        clients_input = st.text_area("Clients (uno por línea)", "\n".join(st.session_state.clients))
        st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
        if st.button("Guardar nombres"): autosave(); st.success("Datos guardados.")
    with st.expander("Settings", expanded=True):
        st.session_state.lunch_start = st.selectbox("Inicio almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_start))
        st.session_state.lunch_end = st.selectbox("Fin almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_end))
        st.session_state.selected_days = st.multiselect("Días a programar", DAYS, default=st.session_state.selected_days)
    with st.expander("Tools", expanded=False):
        sel_buyer_clear = st.selectbox("Limpiar Buyer", ["Ninguno"] + st.session_state.buyers)
        sel_client_clear = st.selectbox("Limpiar Client", ["Ninguno"] + st.session_state.clients)
        if st.button("Limpiar seleccionadas"):
            if sel_buyer_clear != "Ninguno":
                st.session_state.appointments = [a for a in st.session_state.appointments if a[1] != sel_buyer_clear]
            if sel_client_clear != "Ninguno":
                st.session_state.appointments = [a for a in st.session_state.appointments if a[0] != sel_client_clear]
            autosave(); st.success("Citas limpiadas.")
        if st.button("Limpiar TODO"):
            st.session_state.appointments = []; autosave(); st.success("Todas las citas eliminadas.")

# Tabs for scheduling
tab_random, tab_manual = st.tabs(["🎲 Generador Aleatorio", "📝 Agendar Manualmente"])

with tab_random:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("🎲 Generador Aleatorio")
    selected_buyers = []
    col1, col2 = st.columns([1,1])
    with col1:
        if "buyers_random" not in st.session_state: st.session_state.buyers_random = [""]
        for i,_ in enumerate(st.session_state.buyers_random):
            buyer = st.selectbox(f"Buyer {i+1}", st.session_state.buyers, key=f"buyer_random_{i}")
            selected_buyers.append(buyer)
        if st.button("➕ Agregar otro Buyer"): st.session_state.buyers_random.append("")
    with col2:
        selected_clients = st.multiselect("Seleccionar Clients", st.session_state.clients)

    st.markdown("### Ventanas Horarias (opcional)")
    for buyer in selected_buyers:
        st.markdown(f"**{buyer}**")
        st.session_state.time_windows.setdefault(buyer, {})
        for day in st.session_state.selected_days:
            col_from, col_to = st.columns(2)
            with col_from:
                start = st.selectbox(f"{day} desde", HOURS, key=f"{buyer}_{day}_start",
                                     index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)))
            with col_to:
                end = st.selectbox(f"{day} hasta", HOURS, key=f"{buyer}_{day}_end",
                                   index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)))
            st.session_state.time_windows[buyer][day] = {"start": start, "end": end}
    autosave()

    interval = st.selectbox("Duración de cita (min)", [30, 60])
    if st.button("🔀 Generar citas aleatorias"):
        for buyer in selected_buyers:
            for client in selected_clients:
                for day in st.session_state.selected_days:
                    start = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)
                    end = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)
                    slots = [h for h in HOURS[HOURS.index(start):HOURS.index(end)] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0]
                    attempts = 0
                    while attempts < 5 and slots:
                        t = choice(slots)
                        if (client,buyer,day,t) not in st.session_state.appointments:
                            st.session_state.appointments.append((client,buyer,day,t)); break
                        attempts += 1
        autosave(); st.success("Citas generadas.")
    st.markdown('</div>', unsafe_allow_html=True)

with tab_manual:
    st.markdown('<div class="card">', unsafe_allow_html=True)
    st.subheader("📝 Agendar Manualmente")
    buyer_manual = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
    client_manual = st.selectbox("Client", st.session_state.clients, key="client_manual")
    dia_manual = st.selectbox("Día", DAYS, key="dia_manual")
    hora_manual = st.selectbox("Hora", HOURS, key="hora_manual")
    if st.button("➕ Agendar cita manual"):
        if is_in_lunch_break(hora_manual): st.warning("No se pueden agendar durante el almuerzo.")
        else:
            appt = (client_manual,buyer_manual,dia_manual,hora_manual)
            if appt in st.session_state.appointments: st.warning("Esta cita ya está agendada.")
            else:
                st.session_state.appointments.append(appt); autosave(); st.success("Cita agendada exitosamente.")
    st.markdown('</div>', unsafe_allow_html=True)

# Calendar and Summary below tabs (always visible)
st.markdown('<div class="card">', unsafe_allow_html=True)
st.subheader("📊 Resumen y Calendario de Citas")
total_b = len(st.session_state.buyers)
total_c = len(st.session_state.clients)
total_a = len(st.session_state.appointments)
colB, colC, colA = st.columns(3)
colB.metric("Buyers", total_b)
colC.metric("Clients", total_c)
colA.metric("Total Citas", total_a)
st.session_state.show_compact = st.checkbox("Modo compacto (solo franjas con citas)", value=st.session_state.show_compact)

if st.session_state.appointments:
    visible_hours = HOURS[HOURS.index(st.session_state.start_hour):HOURS.index(st.session_state.end_hour)]
    data=[]
    for day in DAYS:
        row={"Hora":day}; appts=[a for a in st.session_state.appointments if a[2]==day]
        for time in visible_hours:
            if st.session_state.show_compact and not any(a[3]==time for a in appts): continue
            if is_in_lunch_break(time): row[time]="LUNCH BREAK"
            else: row[time]="; ".join([f"<span style='color:#009688'><b>{b}</b></span> - <span style='color:#FF7F50'>{c}</span>" for c,b,d,t in appts if t==time])
        data.append(row)
    df=pd.DataFrame(data).set_index("Hora").T
    st.write(df.to_html(escape=False), unsafe_allow_html=True)
else: st.info("No hay citas programadas aún.")
st.markdown('</div>', unsafe_allow_html=True)
