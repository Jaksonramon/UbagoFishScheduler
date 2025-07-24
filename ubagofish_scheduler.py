# Full UbagoFish Scheduler app, deployable version.
# Generates a ready-to-upload ZIP (with scripts, README, and dependencies) for GitHub + Streamlit Cloud.

import streamlit as st
import pandas as pd
import datetime
import json
import os
from io import BytesIO
from random import choice
import zipfile

# Local testing quick start:
# pip install -r requirements.txt
# streamlit run ubagofish_scheduler.py

# Generate a deployable ZIP for GitHub deployment
if st.sidebar.button("📦 Descargar paquete ZIP listo para GitHub"):
    zip_path = "ubagofish_scheduler_bundle.zip"
    readme_content = (
        "# UbagoFish Scheduler\n\n"
        "Streamlit app for scheduling and exporting meeting calendars.\n\n"
        "## How to Deploy\n"
        "1. Upload these files (README.md, ubagofish_scheduler.py, requirements.txt, run_local.bat, run_local.sh) to GitHub.\n"
        "2. Go to [Streamlit Cloud](https://share.streamlit.io/) and link the repo.\n"
        "3. Set branch to `main` and file to `ubagofish_scheduler.py`, then deploy.\n"
        "4. The app will be live with a shareable URL.\n\n"
        "## Test Locally\n"
        "Windows: Double-click `run_local.bat`.\n"
        "Mac/Linux: Run `chmod +x run_local.sh && ./run_local.sh`.\n"
    )
    windows_script = (
        "@echo off\n"
        "echo Installing dependencies...\n"
        "pip install -r requirements.txt\n"
        "echo Launching UbagoFish Scheduler...\n"
        "streamlit run ubagofish_scheduler.py\n"
        "pause\n"
    )
    linux_script = (
        "#!/bin/bash\n"
        "echo 'Installing dependencies...'\n"
        "pip install -r requirements.txt\n"
        "echo 'Launching UbagoFish Scheduler...'\n"
        "streamlit run ubagofish_scheduler.py\n"
    )
    with zipfile.ZipFile(zip_path, 'w') as zipf:
        with open(__file__, 'r') as appfile:
            zipf.writestr("ubagofish_scheduler.py", appfile.read())
        zipf.writestr("requirements.txt", "streamlit\npandas\nxlsxwriter\nopenpyxl\n")
        zipf.writestr("README.md", readme_content)
        zipf.writestr("run_local.bat", windows_script)
        zipf.writestr("run_local.sh", linux_script)
    with open(zip_path, "rb") as f:
        st.download_button("Descargar paquete completo (ZIP)", f, file_name=zip_path)
