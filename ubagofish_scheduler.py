
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 2.1 – Flexible Randomizer Day Selector + Detailed Summary")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

# Initialize session state
for key in ["clients", "buyers", "appointments", "locked_manual"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key != "locked_manual" else set()
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
            st.session_state.locked_manual = set(tuple(a) for a in data.get("locked_manual", []))
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
            "locked_manual": list(st.session_state.locked_manual),
            "start_hour": st.session_state.start_hour,
            "end_hour": st.session_state.end_hour,
            "lunch_start": st.session_state.lunch_start,
            "lunch_end": st.session_state.lunch_end,
            "selected_days": st.session_state.selected_days,
            "time_windows": st.session_state.time_windows
        }, f)

def autosave(): save_data()

load_data()

def is_in_lunch_break(time_str):
    return HOURS.index(st.session_state.lunch_start) <= HOURS.index(time_str) < HOURS.index(st.session_state.lunch_end)

def is_slot_free(client, buyer, day, time):
    for (c,b,d,t) in st.session_state.appointments:
        if d == day and t == time and (c == client or b == buyer):
            return False
    return True

def get_time_slots(start, end, interval):
    start_idx, end_idx = HOURS.index(start), HOURS.index(end)
    return [h for h in HOURS[start_idx:end_idx] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0]

# Sidebar
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

st.sidebar.subheader("Días de la semana")
st.session_state.selected_days = st.sidebar.multiselect("Seleccionar días", DAYS, default=st.session_state.selected_days)
autosave()

with st.sidebar.expander("🗑️ Borrar Citas"):
    buyer_to_clear = st.selectbox("Seleccionar Buyer para borrar", [""] + st.session_state.buyers)
    if st.button("Borrar citas de Buyer") and buyer_to_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[1] != buyer_to_clear]
        st.session_state.locked_manual = {a for a in st.session_state.locked_manual if a[1] != buyer_to_clear}
        autosave()
        st.success(f"Citas de {buyer_to_clear} eliminadas.")
    client_to_clear = st.selectbox("Seleccionar Client para borrar", [""] + st.session_state.clients)
    if st.button("Borrar citas de Client") and client_to_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[0] != client_to_clear]
        st.session_state.locked_manual = {a for a in st.session_state.locked_manual if a[0] != client_to_clear}
        autosave()
        st.success(f"Citas de {client_to_clear} eliminadas.")
    st.markdown("---")
    day_to_clear = st.selectbox("Seleccionar día", st.session_state.selected_days or DAYS)
    confirm_clear = st.checkbox("Confirmar eliminación de todas las citas de este día")
    if st.button("Borrar citas del día seleccionado") and confirm_clear:
        st.session_state.appointments = [a for a in st.session_state.appointments if a[2] != day_to_clear]
        st.session_state.locked_manual = {a for a in st.session_state.locked_manual if a[2] != day_to_clear}
        autosave()
        st.success(f"Todas las citas de {day_to_clear} eliminadas.")

# Tabs
tab_random, tab_manual = st.tabs(["🎲 Generador Aleatorio", "📝 Agendar Manualmente"])

with tab_random:
    st.subheader("🎲 Generar y Optimizar Citas")
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

    st.markdown("### Configurar Ventanas Horarias (opcional)")
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
    days_to_randomize = st.multiselect("Seleccionar días para esta corrida", st.session_state.selected_days, default=st.session_state.selected_days)

    if st.button("🔀 Generar y Optimizar Citas"):
        manual_appts = list(st.session_state.locked_manual)
        random_appts = [(c,b,d,t) for (c,b,d,t) in st.session_state.appointments if (c,b,d,t) not in st.session_state.locked_manual]
        for buyer in selected_buyers:
            for client in selected_clients:
                for day in days_to_randomize:
                    random_appts.append((client,buyer,day,None))

        st.session_state.appointments = manual_appts.copy()
        moved_appts, skipped = [], []
        day_summary = {d: {"added":0, "moved":0, "skipped":0} for d in days_to_randomize}

        for buyer in selected_buyers:
            for day in days_to_randomize:
                appts = [(c,buyer,day,t) for (c,b,d,t) in random_appts if b==buyer and d==day]
                if not appts: continue
                start = st.session_state.time_windows.get(buyer,{}).get(day,{}).get("start", st.session_state.start_hour)
                end = st.session_state.time_windows.get(buyer,{}).get(day,{}).get("end", st.session_state.end_hour)
                slots = get_time_slots(start,end,interval)
                slots.sort(key=lambda h: HOURS.index(h))
                for (c,b,d,t) in appts:
                    assigned = False
                    for slot in slots:
                        if is_slot_free(c,buyer,day,slot):
                            new_t = slot
                            if t is None:
                                day_summary[day]["added"] += 1
                            elif t != new_t:
                                moved_appts.append((c,buyer,day,new_t))
                                day_summary[day]["moved"] += 1
                            st.session_state.appointments.append((c,buyer,day,new_t))
                            slots.remove(slot)
                            assigned = True
                            break
                    if not assigned:
                        skipped.append((c,buyer,day))
                        day_summary[day]["skipped"] += 1
        autosave()

        # Display per-day summary
        summary_lines = [f"**{d}**: {v['added']} nuevas, {v['moved']} movidas, {v['skipped']} sin espacio" for d,v in day_summary.items()]
        st.success("Citas optimizadas.\n" + "\n".join(summary_lines))

with tab_manual:
    st.subheader("📝 Agendar Manualmente (Bloqueadas)")
    col_left, col_right = st.columns([1,1])
    with col_left:
        buyer_manual = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
        client_manual = st.selectbox("Client", st.session_state.clients, key="client_manual")
    with col_right:
        dia_manual = st.selectbox("Día", st.session_state.selected_days or DAYS, key="dia_manual")
        hora_manual = st.selectbox("Hora", [h for h in HOURS if HOURS.index(st.session_state.start_hour) <= HOURS.index(h) < HOURS.index(st.session_state.end_hour)], key="hora_manual")
        if st.button("Agendar cita manual"):
            if is_in_lunch_break(hora_manual):
                st.warning("No se pueden agendar citas durante el almuerzo.")
            elif not is_slot_free(client_manual,buyer_manual,dia_manual,hora_manual):
                st.warning(f"No hay espacio disponible para {buyer_manual} con {client_manual} el día {dia_manual}.")
            else:
                appt = (client_manual,buyer_manual,dia_manual,hora_manual)
                if appt in st.session_state.appointments:
                    st.warning("Esta cita ya está agendada.")
                else:
                    st.session_state.appointments.append(appt)
                    st.session_state.locked_manual.add(appt)
                    autosave()
                    st.success("Cita agendada (bloqueada).")

# Calendar
st.markdown("---")
st.subheader("📅 Calendario semanal de citas")
if st.session_state.appointments:
    table_data = []
    for day in st.session_state.selected_days or DAYS:
        row = {"Hora": day}
        day_appointments = [(c,b,d,t) for (c,b,d,t) in st.session_state.appointments if d==day]
        for time in HOURS:
            cell = []
            for (c,b,d,t) in day_appointments:
                if t == time:
                    label = f"{c} - {b}"
                    if (c,b,d,t) not in st.session_state.locked_manual:
                        label += " (moved)"
                    cell.append(label)
            row[time] = "; ".join(cell)
        table_data.append(row)
    df = pd.DataFrame(table_data).set_index("Hora").T
    df = df.loc[df.index[(df.index >= st.session_state.start_hour) & (df.index < st.session_state.end_hour)]]
    st.dataframe(df, use_container_width=True)
else:
    st.info("No hay citas programadas aún.")

# Excel export
def style_excel(workbook,lunch_start,lunch_end):
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
                if row_idx == 1:
                    cell.fill = blue_fill
                    cell.font = white_font
                if row_idx > 1:
                    time_cell = sheet.cell(row=row_idx,column=1).value
                    if isinstance(time_cell,str) and lunch_start <= time_cell < lunch_end:
                        cell.fill = grey_fill

def export_schedule():
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for entity_type in ["Buyers", "Clients"]:
            for day in st.session_state.selected_days or DAYS:
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
