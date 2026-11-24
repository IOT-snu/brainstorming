@echo off
echo Attack modes: flood (real attack), boiling (slow poisoning), decoy (freeze attack), pulse
set /p IP=IP address of Node 1 (from its BOOT line, ip=...):
set /p MODE=Mode (flood / boiling / decoy / pulse):
set /p DUR=Duration in seconds (for example 60):
python firmware\laptop\poisoner.py --node %IP% --mode %MODE% --duration %DUR%
pause
