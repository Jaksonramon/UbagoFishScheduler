
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from openpyxl import load_workbook
from openpyxl.styles import PatternFill, Font, Alignment, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 2.3 – Calendar Fix + Lunch Break Controls + All Features")

DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

for key in ["clients", "buyers", "appointments", "locked_manual", "moved"]:
    if key not in st.session_state:
        st.session_state[key] = [] if key not in ["locked_manual", "moved"] else set() if key=="locked_manual" else []
if "start_hour" not in st.session_state: st.session_state.start_hour = "06:00"
if "end_hour" not in st.session_state: st.session_state.end_hour = "21:30"
if "lunch_start" not in st.session_state: st.session_state.lunch_start = "12:00"
if "lunch_end" not in st.session_state: st.session_state.lunch_end = "14:00"
if "selected_days" not in st.session_state: st.session_state.selected_days = ["Monday", "Tuesday"]
if "time_windows" not in st.session_state: st.session_state.time_windows = {}
if "skipped_list" not in st.session_state: st.session_state.skipped_list = []

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
        if d==day and t==time and (c==client or b==buyer):
            return False
    return True

def get_time_slots(start,end,interval):
    start_idx, end_idx = HOURS.index(start), HOURS.index(end)
    return [h for h in HOURS[start_idx:end_idx] if not is_in_lunch_break(h) and HOURS.index(h) % (interval//30)==0]

# Sidebar
st.sidebar.header("Buyers & Clients")
buyers_input = st.sidebar.text_area("Buyers (one per line)", "\n".join(st.session_state.buyers))
st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
clients_input = st.sidebar.text_area("Clients (one per line)", "\n".join(st.session_state.clients))
st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
if st.sidebar.button("Guardar nombres"):
    autosave(); st.sidebar.success("Nombres guardados.")

# Day selector
st.sidebar.subheader("Seleccionar Días")
st.session_state.selected_days = st.sidebar.multiselect("Días para programar", DAYS, default=st.session_state.selected_days)

# Start and End of Day selectors
st.sidebar.subheader("Horario del Día")
st.session_state.start_hour = st.sidebar.selectbox("Inicio del Día", HOURS, index=HOURS.index(st.session_state.start_hour))
st.session_state.end_hour = st.sidebar.selectbox("Fin del Día", HOURS, index=HOURS.index(st.session_state.end_hour))

# Lunch Break selectors
st.sidebar.subheader("Horario de Almuerzo")
st.session_state.lunch_start = st.sidebar.selectbox("Inicio del Almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_start))
st.session_state.lunch_end = st.sidebar.selectbox("Fin del Almuerzo", HOURS, index=HOURS.index(st.session_state.lunch_end))

# Clear appointments expander
with st.sidebar.expander("🗑️ Borrar Citas"):
    if st.button("Borrar todas las citas"):
        st.session_state.appointments=[]; st.session_state.locked_manual.clear(); autosave(); st.success("Todas las citas borradas.")
    day_to_clear = st.selectbox("Borrar por Día", [""]+DAYS)
    if st.button("Borrar citas por Día") and day_to_clear:
        st.session_state.appointments=[a for a in st.session_state.appointments if a[2]!=day_to_clear]
        st.session_state.locked_manual={a for a in st.session_state.locked_manual if a[2]!=day_to_clear}
        autosave(); st.success(f"Citas de {day_to_clear} borradas.")
    buyer_to_clear = st.selectbox("Borrar por Buyer", [""]+st.session_state.buyers)
    if st.button("Borrar citas por Buyer") and buyer_to_clear:
        st.session_state.appointments=[a for a in st.session_state.appointments if a[1]!=buyer_to_clear]
        st.session_state.locked_manual={a for a in st.session_state.locked_manual if a[1]!=buyer_to_clear}
        autosave(); st.success(f"Citas de {buyer_to_clear} borradas.")
    client_to_clear = st.selectbox("Borrar por Client", [""]+st.session_state.clients)
    if st.button("Borrar citas por Client") and client_to_clear:
        st.session_state.appointments=[a for a in st.session_state.appointments if a[0]!=client_to_clear]
        st.session_state.locked_manual={a for a in st.session_state.locked_manual if a[0]!=client_to_clear}
        autosave(); st.success(f"Citas de {client_to_clear} borradas.")

# Tabs for scheduling
tab_random, tab_manual = st.tabs(["🎲 Generador Aleatorio", "📝 Agendar Manualmente"])

with tab_random:
    st.subheader("🎲 Optimizar citas (sin borrar previas)")
    selected_buyers, selected_clients = [], []
    col1,col2=st.columns([1,1])
    with col1:
        if "buyers_random" not in st.session_state: st.session_state.buyers_random = [""]
        for i,_ in enumerate(st.session_state.buyers_random):
            buyer = st.selectbox(f"Buyer {i+1}", st.session_state.buyers, key=f"buyer_random_{i}")
            selected_buyers.append(buyer)
        if st.button("➕ Agregar otro Buyer"): st.session_state.buyers_random.append("")
    with col2:
        selected_clients = st.multiselect("Seleccionar Clients", st.session_state.clients)

    for buyer in selected_buyers:
        st.session_state.time_windows.setdefault(buyer, {})
        for day in st.session_state.selected_days:
            c1,c2 = st.columns(2)
            with c1:
                start = st.selectbox(f"{buyer}-{day} desde", HOURS, key=f"{buyer}_{day}_start", index=HOURS.index(st.session_state.time_windows.get(buyer,{}).get(day,{}).get("start", st.session_state.start_hour)))
            with c2:
                end = st.selectbox(f"{buyer}-{day} hasta", HOURS, key=f"{buyer}_{day}_end", index=HOURS.index(st.session_state.time_windows.get(buyer,{}).get(day,{}).get("end", st.session_state.end_hour)))
            st.session_state.time_windows[buyer][day] = {"start": start, "end": end}

    interval = st.selectbox("Duración cita (min)", [30,60])
    days_run = st.multiselect("Días para esta corrida", st.session_state.selected_days, default=st.session_state.selected_days)

    if st.button("🔀 Optimizar Todo"):
        all_random = [(c,b,d,t) for (c,b,d,t) in st.session_state.appointments if (c,b,d,t) not in st.session_state.locked_manual]
        for b in selected_buyers:
            for c in selected_clients:
                for d in days_run:
                    all_random.append((c,b,d,None))

        st.session_state.moved = []
        skipped=[]; st.session_state.skipped_list=[]
        summary={d:{"kept":0,"added":0,"moved":0,"skipped":0} for d in days_run}

        for b in selected_buyers:
            for d in days_run:
                appts=[(c,b,d,t) for (c,b2,d2,t) in all_random if b2==b and d2==d]
                start = st.session_state.time_windows.get(b,{}).get(d,{}).get("start", st.session_state.start_hour)
                end = st.session_state.time_windows.get(b,{}).get(d,{}).get("end", st.session_state.end_hour)
                slots = get_time_slots(start,end,interval)
                slots.sort(key=lambda h:HOURS.index(h))

                for (c,b2,d2,t) in appts:
                    assigned=False
                    if t and t in slots and is_slot_free(c,b,d,t):
                        summary[d]["kept"]+=1
                        slots.remove(t)
                        continue
                    for s in slots:
                        if is_slot_free(c,b,d,s):
                            if t and t!=s:
                                st.session_state.moved.append((c,b,d,s)); summary[d]["moved"]+=1
                            elif t is None:
                                summary[d]["added"]+=1
                            slots.remove(s); assigned=True
                            for idx,(c0,b0,d0,t0) in enumerate(st.session_state.appointments):
                                if (c0,b0,d0,t0)==(c,b,d,t): st.session_state.appointments[idx]=(c,b,d,s); break
                            else: st.session_state.appointments.append((c,b,d,s))
                            break
                    if not assigned:
                        skipped.append((c,b,d)); st.session_state.skipped_list.append((c,b,d))
                        summary[d]["skipped"]+=1
        autosave()
        st.info(" | ".join([f"{d}: {v['kept']} kept, {v['added']} new, {v['moved']} moved, {v['skipped']} skipped" for d,v in summary.items()]))

with tab_manual:
    st.subheader("📝 Agendar Manual (Bloqueadas)")
    c1,c2=st.columns([1,1])
    with c1:
        buyer_m = st.selectbox("Buyer", st.session_state.buyers, key="buyer_manual")
        client_m = st.selectbox("Client", st.session_state.clients, key="client_manual")
    with c2:
        dia_m = st.selectbox("Día", st.session_state.selected_days or DAYS, key="dia_manual")
        hora_m = st.selectbox("Hora", [h for h in HOURS if HOURS.index(st.session_state.start_hour)<=HOURS.index(h)<HOURS.index(st.session_state.end_hour)], key="hora_manual")
        if st.button("Agendar manual"):
            if is_in_lunch_break(hora_m): st.warning("No citas en almuerzo.")
            elif not is_slot_free(client_m,buyer_m,dia_m,hora_m): st.warning(f"Slot ocupado {buyer_m}-{client_m} {dia_m}.")
            else:
                appt=(client_m,buyer_m,dia_m,hora_m)
                if appt in st.session_state.appointments: st.warning("Ya existe.")
                else:
                    st.session_state.appointments.append(appt); st.session_state.locked_manual.add(appt)
                    autosave(); st.success("Cita manual agendada.")

# Calendar view
st.markdown("---")
st.subheader("📅 Calendario")
if st.session_state.appointments and st.session_state.selected_days:
    table_data=[]
    for d in st.session_state.selected_days:
        row={"Hora":d}
        d_appts=[(c,b,dd,t) for (c,b,dd,t) in st.session_state.appointments if dd==d]
        for t in HOURS:
            cell=[]
            for (c,b,dd,tt) in d_appts:
                if tt==t:
                    label=f"{c} - {b}"
                    if (c,b,dd,tt) not in st.session_state.locked_manual and (c,b,dd,tt) in st.session_state.moved:
                        label+=" (moved)"
                    cell.append(label)
            row[t]="; ".join(cell)
        table_data.append(row)
    if table_data:
        df=pd.DataFrame(table_data).set_index("Hora").T
        df=df.loc[df.index[(df.index>=st.session_state.start_hour)&(df.index<st.session_state.end_hour)]]
        st.dataframe(df,use_container_width=True)
    else:
        st.info("No hay citas para mostrar.")
else:
    st.info("No hay citas.")

# Excel export styling
def style_excel(workbook,lunch_start,lunch_end):
    thin=Border(left=Side(style="thin"),right=Side(style="thin"),top=Side(style="thin"),bottom=Side(style="thin"))
    blue=PatternFill(start_color="305496",end_color="305496",fill_type="solid")
    white=Font(color="FFFFFF",bold=True)
    center=Alignment(horizontal="center",vertical="center")
    grey=PatternFill(start_color="DDDDDD",end_color="DDDDDD",fill_type="solid")
    for sheet in workbook.worksheets:
        sheet.freeze_panes="B2"
        for col in sheet.columns:
            maxlen=max(len(str(cell.value)) if cell.value else 0 for cell in col)
            sheet.column_dimensions[col[0].column_letter].width=maxlen+2
        for ridx,row in enumerate(sheet.iter_rows(),start=1):
            for cell in row:
                cell.alignment=center; cell.border=thin
                if ridx==1: cell.fill=blue; cell.font=white
                if ridx>1:
                    val=sheet.cell(row=ridx,column=1).value
                    if isinstance(val,str) and lunch_start<=val<lunch_end: cell.fill=grey

def export_schedule():
    output=BytesIO()
    with pd.ExcelWriter(output,engine="openpyxl") as writer:
        for typ in ["Buyers","Clients"]:
            for d in st.session_state.selected_days:
                cols=st.session_state.buyers if typ=="Buyers" else st.session_state.clients
                df_entity=pd.DataFrame(index=[h for h in HOURS if HOURS.index(st.session_state.start_hour)<=HOURS.index(h)<HOURS.index(st.session_state.end_hour)],columns=cols)
                for (c,b,dd,t) in st.session_state.appointments:
                    if dd==d and t in df_entity.index:
                        key=b if typ=="Buyers" else c
                        df_entity.at[t,key]=(c if typ=="Buyers" else b)
                totals=[df_entity[col].notna().sum() for col in df_entity.columns]
                total_row=pd.DataFrame([["TOTAL"]+totals],columns=["Time"]+list(df_entity.columns))
                df_export=pd.concat([total_row,df_entity.reset_index().rename(columns={"index":"Time"})])
                df_export.to_excel(writer,sheet_name=f"{typ}_{d}",index=False)
    wb=load_workbook(output)
    style_excel(wb,st.session_state.lunch_start,st.session_state.lunch_end)
    styled=BytesIO(); wb.save(styled); styled.seek(0); return styled

if st.button("📤 Exportar Excel"):
    data=export_schedule()
    st.download_button("Descargar",data,file_name="UbagoFish_Schedule.xlsx",mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
