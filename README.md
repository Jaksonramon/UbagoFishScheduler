# UbagoFish Scheduler (Version 1.2)

This Streamlit app schedules, edits, and exports styled Excel schedules for Empresas and Proveedores.

## How to Deploy on Streamlit Cloud
1. Upload all files in this package to your GitHub repository.
2. In [Streamlit Cloud](https://share.streamlit.io/), create a new app.
3. Select your repository, branch `main`, and set the main file as `ubagofish_scheduler.py`.
4. Deploy – your app will auto-build and be accessible via a public link.

## Features
- Add, edit, clear, and manage appointments for Empresas and Proveedores.
- Greyed-out lunch-break rows that cannot be scheduled.
- Styled Excel export (Calibri, borders, blue headers, grey lunch rows).
- Autosave + manual save buttons for data and names.

## Local Testing
Windows: Double-click `run_local.bat`.
Mac/Linux: Run `chmod +x run_local.sh && ./run_local.sh`.
