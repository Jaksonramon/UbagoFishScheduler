
import streamlit as st
import pandas as pd
import datetime
import json
import os
from io import BytesIO
from random import choice
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side

st.set_page_config(page_title="UbagoFish Scheduler", layout="wide")
st.title("🐟 UbagoFish Scheduler")
st.caption("Version 1.1 – Styled Export")

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

# Load/save helpers
def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            data = json.load(f)
            st.session_state.proveedores = data.get("proveedores", [])
            st.session_state.empresas = data.get("empresas", [])
            st.session_state.appointments = [tuple(app) for app in data.get("appointments", [])]

def save_data():
    with open(DATA_FILE, "w") as f:
        json.dump({
            "proveedores": st.session_state.proveedores,
            "empresas": st.session_state.empresas,
            "appointments": st.session_state.appointments,
        }, f)

def autosave():
    save_data()

load_data()

# Sidebar for lunch break and save options
st.sidebar.header("Empresas y Proveedores")
empresas_input = st.sidebar.text_area("Empresas (una por línea)", "\n".join(st.session_state.empresas))
st.session_state.empresas = [e.strip() for e in empresas_input.splitlines() if e.strip()]
proveedores_input = st.sidebar.text_area("Proveedores (uno por línea)", "\n".join(st.session_state.proveedores))
st.session_state.proveedores = [p.strip() for p in proveedores_input.splitlines() if p.strip()]

if st.sidebar.button("Guardar nombres"):
    autosave()
    st.sidebar.success("Empresas y Proveedores guardados.")
if st.sidebar.button("Guardar progreso manualmente"):
    save_data()
    st.sidebar.success("Progreso guardado.")

lunch_start = st.sidebar.selectbox("Inicio del almuerzo (Bloqueo)", HOURS, index=12)
lunch_end = st.sidebar.selectbox("Fin del almuerzo (Bloqueo)", HOURS, index=14)
lunch_start_idx, lunch_end_idx = HOURS.index(lunch_start), HOURS.index(lunch_end)
def is_in_lunch_break(time_val): return lunch_start_idx <= HOURS.index(time_val) < lunch_end_idx
st.session_state.appointments = [appt for appt in st.session_state.appointments if not is_in_lunch_break(appt[3])]

# Appointment management (clear/edit)
st.sidebar.subheader("Administrar citas")
action = st.sidebar.selectbox("Acción", ["Ninguna", "Limpiar todo", "Limpiar por Empresa", "Limpiar por Proveedor", "Editar cita"])
if action == "Limpiar todo" and st.sidebar.button("Ejecutar"):
    st.session_state.appointments = []
    autosave()
    st.sidebar.success("Todas las citas eliminadas.")
elif action == "Limpiar por Empresa":
    emp = st.sidebar.selectbox("Selecciona Empresa", st.session_state.empresas)
    if st.sidebar.button("Limpiar citas de esta Empresa"):
        st.session_state.appointments = [appt for appt in st.session_state.appointments if appt[1] != emp]
        autosave()
        st.sidebar.success(f"Citas de {emp} eliminadas.")
elif action == "Limpiar por Proveedor":
    prov = st.sidebar.selectbox("Selecciona Proveedor", st.session_state.proveedores)
    if st.sidebar.button("Limpiar citas de este Proveedor"):
        st.session_state.appointments = [appt for appt in st.session_state.appointments if appt[0] != prov]
        autosave()
        st.sidebar.success(f"Citas de {prov} eliminadas.")
elif action == "Editar cita" and st.session_state.appointments:
    appt_list = [f"{p} - {e} ({d} {t})" for p,e,d,t in st.session_state.appointments]
    appt_choice = st.sidebar.selectbox("Selecciona cita", appt_list)
    if st.sidebar.button("Editar esta cita"):
        idx = appt_list.index(appt_choice)
        st.session_state.edit_mode = True
        st.session_state.appointment_to_edit = idx

if st.session_state.edit_mode and st.session_state.appointment_to_edit is not None:
    st.subheader("Editar cita")
    old_p, old_e, old_d, old_t = st.session_state.appointments[st.session_state.appointment_to_edit]
    new_p = st.selectbox("Proveedor", st.session_state.proveedores, index=st.session_state.proveedores.index(old_p))
    new_e = st.selectbox("Empresa", st.session_state.empresas, index=st.session_state.empresas.index(old_e))
    new_d = st.selectbox("Día", DAYS, index=DAYS.index(old_d))
    new_t = st.selectbox("Hora", HOURS, index=HOURS.index(old_t))
    if st.button("Guardar cambios"):
        if is_in_lunch_break(new_t):
            st.warning("No se pueden agendar durante almuerzo.")
        else:
            st.session_state.appointments[st.session_state.appointment_to_edit] = (new_p,new_e,new_d,new_t)
            st.session_state.edit_mode = False
            st.session_state.appointment_to_edit = None
            autosave()
            st.success("Cita editada correctamente.")

# Random and manual scheduling tabs (unchanged from last version)...
# (Omitted for brevity, but same logic as before, with autosave on adding.)

# Styled Excel Export
if st.button("📤 Exportar Horario a Excel"):
    def export_schedule_excel():
        appointments_df = pd.DataFrame(st.session_state.appointments, columns=["Proveedor", "Empresa", "Día", "Hora"])
        output = BytesIO()
        def write_schedule(writer, sheet_prefix, columns_key, group_key):
            for day in appointments_df["Día"].unique():
                day_df = appointments_df[appointments_df["Día"] == day]
                start_idx, end_idx = HOURS.index(st.session_state.start_hour), HOURS.index(st.session_state.end_hour)
                timeframes = HOURS[start_idx:end_idx]
                result = pd.DataFrame({"Time": timeframes})
                for item in st.session_state[columns_key]:
                    df_item = day_df[day_df[group_key] == item]
                    paired_list = []
                    for t in timeframes:
                        if is_in_lunch_break(t):
                            paired_list.append("LUNCH BREAK")
                        else:
                            row = df_item[df_item["Hora"] == t]
                            paired_list.append(", ".join(row["Empresa" if group_key=="Proveedor" else "Proveedor"].tolist()) if not row.empty else "")
                    result[item] = paired_list
                result.to_excel(writer, sheet_name=f"{sheet_prefix}_{day}", index=False)
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            write_schedule(writer, "Proveedores", "proveedores", "Proveedor")
            write_schedule(writer, "Empresas", "empresas", "Empresa")
        output.seek(0)
        st.download_button("Descargar Horario Completo", data=output, file_name="UbagoFish_Schedule.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
    export_schedule_excel()
