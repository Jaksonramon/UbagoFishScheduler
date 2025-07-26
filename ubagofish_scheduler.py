
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.9 – Excel Styled (Dark Blue Headers, Borders, Lunch Grey)")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0, 30)]
DATA_FILE = "ubagofish_data.json"

# Session state init
for key in ["clients", "buyers", "appointments"]:
    if key not in st.session_state:
        st.session_state[key] = []
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
            st.session_state.appointments = [tuple(a) for a in data.get("appointments", [])]
            st.session_state.start_hour = data.get("start_hour", "06:00")
            st.session_state.end_hour = data.get("end_hour", "21:30")
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
            "time_windows": st.session_state.time_windows
        }, f)

def autosave():
    save_data()

load_data()

def is_in_lunch_break(time_str):
    return HOURS.index(st.session_state.lunch_start) <= HOURS.index(time_str) < HOURS.index(st.session_state.lunch_end)

def is_slot_free(client, buyer, day, time):
    for (c, b, d, t) in st.session_state.appointments:
        if d == day and t == time and (c == client or b == buyer):
            return False
    return True

def get_next_available_slots(start, end, interval):
    start_idx, end_idx = HOURS.index(start), HOURS.index(end)
    return [h for h in HOURS[start_idx:end_idx] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0]

# Sidebar setup
st.sidebar.header("Buyers & Clients")
buyers_input = st.sidebar.text_area("Buyers (one per line)", "\n".join(st.session_state.buyers))
st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
clients_input = st.sidebar.text_area("Clients (one per line)", "\n".join(st.session_state.clients))
st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
if st.sidebar.button("Guardar nombres"):
    autosave()
    st.sidebar.success("Buyers & Clients saved.")

st.sidebar.subheader("Horario de Jornada")
st.session_state.start_hour = st.sidebar.selectbox("Inicio del día", HOURS, index=HOURS.index(st.session_state.start_hour))
st.session_state.end_hour = st.sidebar.selectbox("Fin del día", HOURS, index=HOURS.index(st.session_state.end_hour))

st.sidebar.subheader("Lunch Break")
st.session_state.lunch_start = st.sidebar.selectbox("Start", HOURS, index=HOURS.index(st.session_state.lunch_start))
st.session_state.lunch_end = st.sidebar.selectbox("End", HOURS, index=HOURS.index(st.session_state.lunch_end))

with st.sidebar.expander("🗑️ Borrar Citas"):
    buyer_to_clear = st.selectbox("Seleccionar Buyer para borrar", [""] + st.session_state.buyers)
    if st.button("Borrar citas de Buyer") and buyer_to_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[1] != buyer_to_clear]
        autosave()
        st.success(f"Citas de {buyer_to_clear} eliminadas.")
    client_to_clear = st.selectbox("Seleccionar Client para borrar", [""] + st.session_state.clients)
    if st.button("Borrar citas de Client") and client_to_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[0] != client_to_clear]
        autosave()
        st.success(f"Citas de {client_to_clear} eliminadas.")
    st.markdown("---")
    st.markdown("### Borrar por Día")
    day_to_clear = st.selectbox("Seleccionar día", DAYS)
    confirm_clear = st.checkbox("Confirmar eliminación de todas las citas de este día")
    if st.button("Borrar citas del día seleccionado") and confirm_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[2] != day_to_clear]
        autosave()
        st.success(f"Todas las citas de {day_to_clear} eliminadas.")

# Tabs
tab_random, tab_manual = st.tabs(["🎲 Generador Aleatorio", "📝 Agendar Manualmente"])
with tab_random:
    st.subheader("🎲 Generar citas aleatorias")
    selected_buyers = []
    col1, col2 = st.columns([1,1])
    with col1:
        if "buyers_random" not in st.session_state: st.session_state.buyers_random = [""]
        for i,_ in enumerate(st.session_state.buyers_random):
            buyer = st.selectbox(f"Buyer {i+1}", options=st.session_state.buyers, key=f"buyer_random_{i}")
            selected_buyers.append(buyer)
        if st.button("➕ Agregar otro Buyer"): st.session_state.buyers_random.append("")
    with col2:
        selected_clients = st.multiselect("Seleccionar Clients", options=st.session_state.clients)
    st.markdown("### Ventanas horarias (opcional)")
    for buyer in selected_buyers:
        st.session_state.time_windows.setdefault(buyer, {})
        for day in st.session_state.selected_days:
            col_from, col_to = st.columns(2)
            with col_from:
                start = st.selectbox(f"{buyer} - {day} desde", HOURS, key=f"{buyer}_{day}_start", index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)))
            with col_to:
                end = st.selectbox(f"{buyer} - {day} hasta", HOURS, key=f"{buyer}_{day}_end", index=HOURS.index(st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)))
            st.session_state.time_windows[buyer][day] = {"start": start, "end": end}
    interval = st.selectbox("Duración de la cita (min)", [30, 60])
    if st.button("🔀 Generar citas aleatorias"):
        for buyer in selected_buyers:
            for client in selected_clients:
                for day in st.session_state.selected_days:
                    start = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("start", st.session_state.start_hour)
                    end = st.session_state.time_windows.get(buyer, {}).get(day, {}).get("end", st.session_state.end_hour)
                    slots = get_next_available_slots(start, end, interval)
                    if not slots:
                        st.warning(f"No hay espacio disponible para {buyer} con {client} el día {day}.")
                        continue
                    slots.sort(key=lambda h: HOURS.index(h))
                    attempts = 0
                    while attempts < 5 and slots:
                        t = slots.pop(0)
                        if is_slot_free(client, buyer, day, t):
                            st.session_state.appointments.append((client, buyer, day, t))
                            break
                        attempts += 1
        autosave()
        st.success("Citas generadas.")

with tab_manual:
    st.subheader("📝 Agendar Manualmente")
    col_left, col_right = st.columns([1,1])
    with col_left:
        buyer_manual = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
        client_manual = st.selectbox("Client", st.session_state.clients, key="client_manual")
    with col_right:
        dia_manual = st.selectbox("Día", DAYS, key="dia_manual")
        hora_manual = st.selectbox("Hora", [h for h in HOURS if HOURS.index(st.session_state.start_hour) <= HOURS.index(h) < HOURS.index(st.session_state.end_hour)], key="hora_manual")
        if st.button("Agendar cita manual"):
            if is_in_lunch_break(hora_manual):
                st.warning("No se pueden agendar citas durante el almuerzo.")
            elif not is_slot_free(client_manual, buyer_manual, dia_manual, hora_manual):
                st.warning(f"No hay espacio disponible para {buyer_manual} con {client_manual} el día {dia_manual} en este horario.")
            else:
                appt = (client_manual, buyer_manual, dia_manual, hora_manual)
                if appt in st.session_state.appointments:
                    st.warning("Esta cita ya está agendada.")
                else:
                    st.session_state.appointments.append(appt)
                    autosave()
                    st.success("Cita agendada exitosamente.")

with st.expander("✏️ Editar Citas"):
    if st.session_state.appointments:
        def sort_key(a):
            return (DAYS.index(a[2]), HOURS.index(a[3]), a[1], a[0])
        sorted_appts = sorted(st.session_state.appointments, key=sort_key)
        options = []
        last_day = None
        for (c,b,d,t) in sorted_appts:
            if d != last_day and last_day is not None:
                options.append("----")
            options.append(f"{d} - {t} | {b} - {c}")
            last_day = d
        selected_label = st.selectbox("Selecciona cita para editar", options, key="edit_selector")
        st.info(f"Seleccionaste: {selected_label}")
    else:
        st.info("No hay citas para editar.")

st.markdown("---")
st.subheader("📅 Calendario semanal de citas")
if st.session_state.appointments:
    table_data = []
    for day in DAYS:
        row = {"Hora": day}
        day_appointments = [(c, b, d, t) for (c, b, d, t) in st.session_state.appointments if d == day]
        for time in HOURS:
            cell = [f"{c} - {b}" for (c, b, d, t) in day_appointments if t == time]
            row[time] = "; ".join(cell)
        table_data.append(row)
    df = pd.DataFrame(table_data).set_index("Hora").T
    df = df.loc[df.index[(df.index >= st.session_state.start_hour) & (df.index < st.session_state.end_hour)]]
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay citas programadas aún.")

def style_excel(workbook, lunch_start, lunch_end):
    thin_border = Border(left=Side(style="thin"), right=Side(style="thin"), top=Side(style="thin"), bottom=Side(style="thin"))
    blue_fill = PatternFill(start_color="305496", end_color="305496", fill_type="solid")
    white_font = Font(color="FFFFFF", bold=True)
    center_align = Alignment(horizontal="center", vertical="center")
    grey_fill = PatternFill(start_color="DDDDDD", end_color="DDDDDD", fill_type="solid")
    for sheet in workbook.worksheets:
        sheet.freeze_panes = "B2"
        for col in sheet.columns:
            max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
            sheet.column_dimensions[col[0].column_letter].width = max_length + 2
        for row_idx, row in enumerate(sheet.iter_rows(), start=1):
            for cell in row:
                cell.alignment = center_align
                cell.border = thin_border
                # Header row styling
                if row_idx == 1:
                    cell.fill = blue_fill
                    cell.font = white_font
                # Lunch break row grey-out (skip header)
                if row_idx > 1:
                    time_cell = sheet.cell(row=row_idx, column=1).value
                    if isinstance(time_cell, str) and lunch_start <= time_cell < lunch_end:
                        cell.fill = grey_fill

def export_schedule():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for entity_type in ["Buyers", "Clients"]:
            for day in DAYS:
                cols = st.session_state.buyers if entity_type=="Buyers" else st.session_state.clients
                df_entity = pd.DataFrame(index=[h for h in HOURS if HOURS.index(st.session_state.start_hour) <= HOURS.index(h) < HOURS.index(st.session_state.end_hour)], columns=cols)
                for (c,b,d,t) in st.session_state.appointments:
                    if d == day and t in df_entity.index:
                        key = b if entity_type=="Buyers" else c
                        df_entity.at[t,key] = (c if entity_type=="Buyers" else b)
                totals = [df_entity[col].notna().sum() for col in df_entity.columns]
                totals_row = pd.DataFrame([["TOTAL"] + totals], columns=["Time"] + list(df_entity.columns))
                df_export = pd.concat([totals_row, df_entity.reset_index().rename(columns={"index":"Time"})])
                df_export.to_excel(writer, sheet_name=f"{entity_type}_{day}", index=False)
    workbook = load_workbook(output)
    style_excel(workbook, st.session_state.lunch_start, st.session_state.lunch_end)
    output_styled = BytesIO()
    workbook.save(output_styled)
    output_styled.seek(0)
    return output_styled

if st.button("📤 Exportar a Excel"):
    data = export_schedule()
    st.download_button(label="Descargar Excel", data=data, file_name="UbagoFish_Schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
