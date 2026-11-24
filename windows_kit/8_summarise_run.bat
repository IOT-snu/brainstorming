@echo off
set /p RUN=Name of the run to summarise (for example idle1):
python firmware\laptop\collector.py logs\%RUN% --summarise
pause
