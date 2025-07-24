#!/bin/bash
echo 'Installing dependencies...'
pip install -r requirements.txt
echo 'Launching UbagoFish Scheduler...'
streamlit run ubagofish_scheduler.py
