@echo off
cd /d C:\tender-agent
call venv\Scripts\activate
python main.py
python whatsapp_group_sender.py
