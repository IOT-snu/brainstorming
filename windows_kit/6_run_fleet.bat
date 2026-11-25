@echo off
set /p PORTS=COM ports of ALL three boards, separated by spaces (for example COM10 COM11 COM12):
set /p RUN=Name for this run (for example idle1):
echo Logging all boards to logs\%RUN%  (Ctrl+C to stop)
python firmware\laptop\collector.py logs\%RUN% --serial %PORTS%
pause
