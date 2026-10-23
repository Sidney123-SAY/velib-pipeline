@echo off
cd /d C:\Users\Sidney\Documents\velib-pipeline
.venv\Scripts\python.exe ingest.py >> logs\ingest.log 2>&1
