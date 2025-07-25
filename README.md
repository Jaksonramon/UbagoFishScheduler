
# UbagoFish Scheduler v1.4 Final

This is the **stable version** of the UbagoFish Scheduler app, running in **dark mode only**.

## Features
- Schedule appointments (random or manual).
- Persisted Buyers/Clients, lunch break, start/end of day, time windows.
- Collapsible appointment editing.
- Export to Excel (styled, per day with summary).

## Running Locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Run:
   ```bash
   streamlit run ubagofish_scheduler.py
   ```

## Deploying to Streamlit Cloud
1. Push these files to a GitHub repo (main branch).
2. On Streamlit Cloud, select **"Deploy a public app from GitHub"**.
3. Set `ubagofish_scheduler.py` as the main file.
