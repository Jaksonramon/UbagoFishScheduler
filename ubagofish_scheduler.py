
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler v1.6", layout="wide")

with open("style.css") as f:
    st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.6 – Back-to-Back Scheduling, Full Features")

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

def is_slot_free(client, buyer, day, time):
    for c, b, d, t in st.session_state.appointments:
        if d == day and t == time:
            if b == buyer or c == client:
                return False
    return True

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


        st.markdown("---")
        st.markdown("### Borrar por Día")
        day_to_clear = st.selectbox("Seleccionar día", DAYS)
        confirm_clear = st.checkbox("Confirmar eliminación de todas las citas de este día")
        if st.button("Borrar citas del día seleccionado") and confirm_clear:
            st.session_state.appointments = [a for a in st.session_state.appointments if a[2] != day_to_clear]
            autosave()
            st.success(f"Todas las citas de {day_to_clear} han sido eliminadas.")
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
                    slots = sorted([h for h in HOURS[HOURS.index(start):HOURS.index(end)] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0], key=lambda x: HOURS.index(x))
                    for t in slots:
                        if is_slot_free(client,buyer,day,t):
                            st.session_state.appointments.append((client,buyer,day,t))
                            break
        autosave(); st.success("Citas generadas (sin conflictos, priorizando bloques consecutivos).")

with tab_manual:
    st.subheader("✏️ Agendar Manualmente")
    buyer_manual = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
    client_manual = st.selectbox("Client", st.session_state.clients, key="client_manual")
    dia_manual = st.selectbox("Día", DAYS, key="dia_manual")
    hora_manual = st.selectbox("Hora", [h for h in HOURS if HOURS.index(st.session_state.start_hour) <= HOURS.index(h) < HOURS.index(st.session_state.end_hour)], key="hora_manual")
    if st.button("Agendar cita manual"):
        if is_in_lunch_break(hora_manual): st.warning("No se pueden agendar durante el almuerzo.")
        elif not is_slot_free(client_manual,buyer_manual,dia_manual,hora_manual): st.warning("El Buyer o Client ya tiene cita a esa hora.")
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

if st.button("📤 Exportar a Excel"):
    df_all = pd.DataFrame(st.session_state.appointments, columns=["Client","Buyer","Día","Hora"])
    output = BytesIO()
    def style_ws(ws):
        header_fill=PatternFill("solid",fgColor="305496")
        header_font=Font(color="FFFFFF",bold=True,name="Calibri",size=11)
        lunch_fill=PatternFill("solid",fgColor="D9D9D9")
        border=Border(left=Side(style="thin"),right=Side(style="thin"),top=Side(style="thin"),bottom=Side(style="thin"))
        for r,row in enumerate(ws.iter_rows(min_row=1,max_row=ws.max_row,max_col=ws.max_column),start=1):
            for cell in row:
                cell.border=border; cell.font=Font(name="Calibri",size=11)
                if r==1:
                    cell.fill=header_fill; cell.font=header_font; cell.alignment=Alignment(horizontal="center",vertical="center")
                if cell.value=="LUNCH BREAK":
                    cell.fill=lunch_fill; cell.alignment=Alignment(horizontal="center",vertical="center")
                cell.alignment=Alignment(horizontal="center",vertical="center")
        for col in ws.columns:
            max_len=max(len(str(c.value)) if c.value else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width=max_len+2
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        times=HOURS[HOURS.index(st.session_state.start_hour):HOURS.index(st.session_state.end_hour)]
        for day in df_all["Día"].unique():
            df_clients=pd.DataFrame({"Time":times})
            for client in st.session_state.clients:
                c_appts=df_all[(df_all["Client"]==client)&(df_all["Día"]==day)]
                df_clients[client]=["LUNCH BREAK" if is_in_lunch_break(t) else ", ".join(c_appts[c_appts["Hora"]==t]["Buyer"]) for t in times]
            totals=[df_all[(df_all["Client"]==c)&(df_all["Día"]==day)].shape[0] for c in st.session_state.clients]
            totals_row=["TOTAL"]+totals
            while len(totals_row)<len(df_clients.columns): totals_row.append(0)
            totals_row=totals_row[:len(df_clients.columns)]
            df_clients.loc[-1]=totals_row; df_clients.index+=1; df_clients=df_clients.sort_index()
            df_clients.to_excel(writer,sheet_name=f"Clients_{day}",index=False)
            df_buyers=pd.DataFrame({"Time":times})
            for buyer in st.session_state.buyers:
                b_appts=df_all[(df_all["Buyer"]==buyer)&(df_all["Día"]==day)]
                df_buyers[buyer]=["LUNCH BREAK" if is_in_lunch_break(t) else ", ".join(b_appts[b_appts["Hora"]==t]["Client"]) for t in times]
            totals_b=[df_all[(df_all["Buyer"]==b)&(df_all["Día"]==day)].shape[0] for b in st.session_state.buyers]
            totals_row_b=["TOTAL"]+totals_b
            while len(totals_row_b)<len(df_buyers.columns): totals_row_b.append(0)
            totals_row_b=totals_row_b[:len(df_buyers.columns)]
            df_buyers.loc[-1]=totals_row_b; df_buyers.index+=1; df_buyers=df_buyers.sort_index()
            df_buyers.to_excel(writer,sheet_name=f"Buyers_{day}",index=False)
        df_all["Count"]=1
        df_all.groupby("Client")["Count"].sum().reset_index().to_excel(writer,sheet_name="Summary_Clients",index=False)
        df_all.groupby("Buyer")["Count"].sum().reset_index().to_excel(writer,sheet_name="Summary_Buyers",index=False)
    output.seek(0)
    wb=load_workbook(output)
    for ws in wb.worksheets: style_ws(ws)
    final=BytesIO(); wb.save(final); final.seek(0)
    st.download_button("Descargar Horario Completo",data=final,file_name="UbagoFish_Schedule_v16.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with st.expander("🔧 Editar Citas", expanded=st.session_state.edit_expander_open):
    st.session_state.edit_expander_open=True
    if st.session_state.appointments:
        options=[f"{c} con {b} ({d} {h})" for c,b,d,h in st.session_state.appointments]
        sel=st.selectbox("Seleccionar cita para editar", options)
        if sel:
            idx=options.index(sel)
            c,b,d,h=st.session_state.appointments[idx]
            new_b=st.selectbox("Nuevo Buyer", st.session_state.buyers, index=st.session_state.buyers.index(b))
            new_c=st.selectbox("Nuevo Client", st.session_state.clients, index=st.session_state.clients.index(c))
            new_d=st.selectbox("Nuevo Día", DAYS, index=DAYS.index(d))
            new_h=st.selectbox("Nueva Hora", HOURS, index=HOURS.index(h))
            if st.button("Guardar cambios"):
                if is_in_lunch_break(new_h): st.warning("No se pueden agendar durante el almuerzo.")
                elif not is_slot_free(new_c,new_b,new_d,new_h): st.warning("El Buyer o Client ya tiene cita a esa hora.")
                else:
                    st.session_state.appointments[idx]=(new_c,new_b,new_d,new_h); autosave(); st.success("Cita editada.")

