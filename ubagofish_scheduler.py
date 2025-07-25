
import streamlit as st
import pandas as pd
import json, os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler - Minimalist Table", layout="wide")

# Minimalist CSS
st.markdown("""
    <style>
        body {background-color: #F7F7F7;}
        .main {background-color: #F7F7F7;}
        .block-container {font-family: 'Nunito', sans-serif;}
        /* Buttons */
        div.stButton > button:first-child {border-radius: 6px; padding: 0.4rem 1rem; font-weight: 600;
                                           background-color: #4DB8FF; color: white; border:none;}
        div.stButton > button:first-child:hover {background-color: #2A9ED3;}
        /* Table */
        .dataframe {font-size: 13px; border-radius: 6px; overflow: hidden;}
        .dataframe thead th {background: #4DB8FF; color: white; font-weight: bold; position: sticky; top:0;}
        .dataframe tbody tr:nth-child(even) {background-color: #FAFAFA;}
        .dataframe tbody tr:hover {background-color: #E6FFF5 !important;}
    </style>
""", unsafe_allow_html=True)

st.title("UbagoFish Scheduler – Minimalist Table")
st.caption("Single-page interactive schedule with inline editing and filters (v1.4 features)")

# Constants & state
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday"]
HOURS = [f"{h:02d}:{m:02d}" for h in range(6, 22) for m in (0,30)]
DATA_FILE = "ubagofish_data.json"

for key in ["clients", "buyers", "appointments"]:
    if key not in st.session_state: st.session_state[key] = []
if "lunch_start" not in st.session_state: st.session_state.lunch_start = "12:00"
if "lunch_end" not in st.session_state: st.session_state.lunch_end = "14:00"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.clients = data.get("clients", [])
            st.session_state.buyers = data.get("buyers", [])
            st.session_state.appointments = [tuple(app) for app in data.get("appointments", [])]
            st.session_state.lunch_start = data.get("lunch_start", "12:00")
            st.session_state.lunch_end = data.get("lunch_end", "14:00")
def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({"clients": st.session_state.clients, "buyers": st.session_state.buyers,
                   "appointments": st.session_state.appointments,
                   "lunch_start": st.session_state.lunch_start,
                   "lunch_end": st.session_state.lunch_end}, f)
def autosave(): save_data()
load_data()

# Lunch break utility
lunch_start_idx, lunch_end_idx = HOURS.index(st.session_state.lunch_start), HOURS.index(st.session_state.lunch_end)
def is_in_lunch_break(t): return lunch_start_idx <= HOURS.index(t) < lunch_end_idx
st.session_state.appointments = [a for a in st.session_state.appointments if not is_in_lunch_break(a[3])]

# Sidebar for Buyers & Clients
with st.sidebar:
    st.header("Buyers & Clients")
    buyers_input = st.text_area("Buyers (uno por línea)", "\n".join(st.session_state.buyers))
    st.session_state.buyers = [b.strip() for b in buyers_input.splitlines() if b.strip()]
    clients_input = st.text_area("Clients (uno por línea)", "\n".join(st.session_state.clients))
    st.session_state.clients = [c.strip() for c in clients_input.splitlines() if c.strip()]
    if st.button("Guardar nombres"): autosave(); st.success("Datos guardados.")

# Filter bar
col_f1, col_f2, col_f3 = st.columns(3)
buyer_filter = col_f1.selectbox("Filtrar por Buyer", ["Todos"] + st.session_state.buyers)
client_filter = col_f2.selectbox("Filtrar por Client", ["Todos"] + st.session_state.clients)
day_filter = col_f3.selectbox("Filtrar por Día", ["Todos"] + DAYS)

def apply_filters():
    filtered = st.session_state.appointments
    if buyer_filter != "Todos":
        filtered = [a for a in filtered if a[1] == buyer_filter]
    if client_filter != "Todos":
        filtered = [a for a in filtered if a[0] == client_filter]
    if day_filter != "Todos":
        filtered = [a for a in filtered if a[2] == day_filter]
    return filtered

# Toolbar buttons
col_b1, col_b2, col_b3, col_b4 = st.columns(4)
with col_b1:
    if st.button("➕ Agregar cita"):
        if st.session_state.buyers and st.session_state.clients:
            default_appt = (st.session_state.clients[0], st.session_state.buyers[0], DAYS[0], HOURS[0])
            st.session_state.appointments.append(default_appt); autosave()
with col_b2:
    if st.button("🔀 Randomizar"):
        if st.session_state.buyers and st.session_state.clients:
            for buyer in st.session_state.buyers:
                for client in st.session_state.clients:
                    for day in DAYS[:2]:
                        slots = [h for h in HOURS if not is_in_lunch_break(h)]
                        if slots:
                            t = choice(slots)
                            appt = (client, buyer, day, t)
                            if appt not in st.session_state.appointments:
                                st.session_state.appointments.append(appt)
            autosave()
with col_b3:
    if st.button("❌ Limpiar filtros"):
        buyer_filter, client_filter, day_filter = "Todos", "Todos", "Todos"
with col_b4:
    if st.button("📤 Exportar Excel"):
        df_all = pd.DataFrame(st.session_state.appointments, columns=["Client","Buyer","Día","Hora"])
        output = BytesIO()
        def style_ws(ws):
            header_fill=PatternFill("solid",fgColor="305496"); header_font=Font(color="FFFFFF",bold=True,name="Calibri",size=11)
            lunch_fill=PatternFill("solid",fgColor="D9D9D9"); border=Border(left=Side(style="thin"),right=Side(style="thin"),top=Side(style="thin"),bottom=Side(style="thin"))
            for r,row in enumerate(ws.iter_rows(min_row=1,max_row=ws.max_row,max_col=ws.max_column),start=1):
                for cell in row:
                    cell.border=border; cell.font=Font(name="Calibri",size=11)
                    if r==1: cell.fill=header_fill; cell.font=header_font; cell.alignment=Alignment(horizontal="center",vertical="center")
                    if cell.value=="LUNCH BREAK": cell.fill=lunch_fill
                    cell.alignment=Alignment(horizontal="center",vertical="center")
            for col in ws.columns:
                max_len=max(len(str(c.value)) if c.value else 0 for c in col)
                ws.column_dimensions[col[0].column_letter].width=max_len+2
        def write_sheet(writer,prefix,key,group):
            for day in df_all["Día"].unique():
                df_day=df_all[df_all["Día"]==day]; times=HOURS
                result=pd.DataFrame({"Time":times})
                for item in st.session_state[key]:
                    cells=[]; sub=df_day[df_day[group]==item]
                    for t in times:
                        if is_in_lunch_break(t): cells.append("LUNCH BREAK")
                        else:
                            sub_row=sub[sub["Hora"]==t]; cells.append(", ".join(sub_row["Buyer" if group=="Client" else "Client"].tolist()) if not sub_row.empty else "")
                    result[item]=cells
                result.to_excel(writer,sheet_name=f"{prefix}_{day}",index=False)
        def write_summary(writer,prefix,column):
            counts=df_all[column].value_counts().reset_index()
            counts.columns=[column,"Total Citas"]
            counts.to_excel(writer,sheet_name=f"Summary_{prefix}",index=False)
        with pd.ExcelWriter(output,engine="openpyxl") as writer:
            write_sheet(writer,"Clients","clients","Client")
            write_sheet(writer,"Buyers","buyers","Buyer")
            write_summary(writer,"Clients","Client")
            write_summary(writer,"Buyers","Buyer")
        output.seek(0); wb=load_workbook(output)
        for ws in wb.worksheets: style_ws(ws)
        final=BytesIO(); wb.save(final); final.seek(0)
        st.download_button("Descargar Horario Completo", data=final,
                           file_name="UbagoFish_Schedule_Minimalist.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# Interactive editable table
appointments = apply_filters()
if appointments:
    df = pd.DataFrame(appointments, columns=["Client","Buyer","Día","Hora"])
    edited = st.experimental_data_editor(df, num_rows="dynamic")
    if not edited.equals(df):
        st.session_state.appointments = [tuple(r) for r in edited.to_numpy()]
        autosave()
else:
    st.info("No hay citas programadas o coincidentes con los filtros.")
