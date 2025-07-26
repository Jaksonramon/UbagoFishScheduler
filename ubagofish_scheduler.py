
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler v1.4", layout="wide")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.4 – Unified Export, Light Sidebar, Clear Tools")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

for key in ["clients", "buyers", "appointments"]:
    if key not in st.session_state: st.session_state[key] = []
if "edit_expander_open" not in st.session_state: st.session_state.edit_expander_open = False
if "start_hour" not in st.session_state: st.session_state.start_hour = "08:00"
if "end_hour" not in st.session_state: st.session_state.end_hour = "18:00"
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
            st.session_state.start_hour = data.get("start_hour", "08:00")
            st.session_state.end_hour = data.get("end_hour", "18:00")
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
            "start_hour": st.session_state.start_hour,
            "end_hour": st.session_state.end_hour,
            "lunch_start": st.session_state.lunch_start,
            "lunch_end": st.session_state.lunch_end,
            "selected_days": st.session_state.selected_days,
            "time_windows": st.session_state.time_windows}, f)
def autosave(): save_data()
load_data()

lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(t): return lunch_start_idx <= HOURS.index(t) < lunch_end_idx
st.session_state.appointments = [a for a in st.session_state.appointments if not is_in_lunch_break(a[3])]

with st.sidebar:
    st.header("Buyers & Clients")
    buyers_input = st.text_area("Buyers (uno por línea)", "\n".join(st.session_state.buyers))
    st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
    clients_input = st.text_area("Clients (uno por línea)", "\n".join(st.session_state.clients))
    st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
    if st.button("Guardar nombres"): autosave(); st.success("Datos guardados.")

    st.subheader("Configuración de Día")
    st.session_state.start_hour = st.selectbox("Inicio del día", HOURS, index=HOURS.index(st.session_state.start_hour))
    st.session_state.end_hour = st.selectbox("Fin del día", HOURS, index=HOURS.index(st.session_state.end_hour))
    st.session_state.lunch_start = st.selectbox("Inicio almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_start))
    st.session_state.lunch_end = st.selectbox("Fin almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_end))
    st.session_state.selected_days = st.multiselect("Días a programar", DAYS, default=st.session_state.selected_days)

    with st.expander("🗑️ Borrar Citas"):
        if st.button("Borrar todas las citas"):
            st.session_state.appointments.clear()
            autosave()
            st.warning("Todas las citas fueron eliminadas.")
        buyer_clear = st.selectbox("Borrar citas de Buyer", [""]+st.session_state.buyers)
        if st.button("Borrar citas de Buyer seleccionado") and buyer_clear:
            st.session_state.appointments = [a for a in st.session_state.appointments if a[1]!=buyer_clear]
            autosave()
            st.warning(f"Citas de {buyer_clear} eliminadas.")
        client_clear = st.selectbox("Borrar citas de Client", [""]+st.session_state.clients)
        if st.button("Borrar citas de Client seleccionado") and client_clear:
            st.session_state.appointments = [a for a in st.session_state.appointments if a[0]!=client_clear]
            autosave()
            st.warning(f"Citas de {client_clear} eliminadas.")

tab_random, tab_manual = st.tabs(["🎲 Generador Aleatorio", "✏️ Agendar Manualmente"])

with tab_random:
    st.subheader("🎲 Generar citas aleatorias")
    selected_buyers = []
    col1, col2 = st.columns([1,1])
    with col1:
        if "buyers_random" not in st.session_state: st.session_state.buyers_random = [""]
        for i,_ in enumerate(st.session_state.buyers_random):
            buyer = st.selectbox(f"Buyer {i+1}", st.session_state.buyers, key=f"buyer_random_{i}")
            selected_buyers.append(buyer)
        if st.button("Agregar otro Buyer"): st.session_state.buyers_random.append("")
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
    if st.button("Generar citas aleatorias"):
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
                            st.session_state.appointments.append((client,buyer,day,t))
                            break
                        attempts += 1
        autosave(); st.success("Citas generadas (sin borrar citas previas).")

with tab_manual:
    st.subheader("✏️ Agendar Manualmente")
    buyer_manual = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
    client_manual = st.selectbox("Client", st.session_state.clients, key="client_manual")
    dia_manual = st.selectbox("Día", DAYS, key="dia_manual")
    hora_manual = st.selectbox("Hora", [h for h in HOURS if HOURS.index(st.session_state.start_hour) <= HOURS.index(h) < HOURS.index(st.session_state.end_hour)], key="hora_manual")
    if st.button("Agendar cita manual"):
        if is_in_lunch_break(hora_manual): st.warning("No se pueden agendar durante el almuerzo.")
        else:
            appt = (client_manual,buyer_manual,dia_manual,hora_manual)
            if appt in st.session_state.appointments: st.warning("Esta cita ya está agendada.")
            else:
                st.session_state.appointments.append(appt); autosave(); st.success("Cita agendada exitosamente.")

st.subheader("📅 Calendario de Citas")
if st.session_state.appointments:
    data=[]
    for day in DAYS:
        row={"Hora":day}; appts=[a for a in st.session_state.appointments if a[2]==day]
        for time in HOURS[HOURS.index(st.session_state.start_hour):HOURS.index(st.session_state.end_hour)]:
            if is_in_lunch_break(time): row[time]="LUNCH BREAK"
            else:
                row[time]="; ".join([f"{b} - {c}" for c,b,d,t in appts if t==time])
        data.append(row)
    df=pd.DataFrame(data).set_index("Hora").T
    st.dataframe(df, use_container_width=True)
else: st.info("No hay citas programadas aún.")

# Export logic remains unchanged (Clients & Buyers unified format, lunch greyed, totals, summaries)
# (Copy from last approved export implementation here, omitted for brevity)
