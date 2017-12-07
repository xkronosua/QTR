@ECHO OFF
SET BINDIR=%~dp0
CD /D "%BINDIR%"
"C:\Anaconda3\python.exe" ./QTR.py --qt4
