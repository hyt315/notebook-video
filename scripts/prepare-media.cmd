@echo off
setlocal
where py >nul 2>nul
if %ERRORLEVEL%==0 (py -3 "%~dp0prepare-media.py" %*) else (python "%~dp0prepare-media.py" %*)
exit /b %ERRORLEVEL%
