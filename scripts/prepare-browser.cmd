@echo off
setlocal
node "%~dp0notebook-video.mjs" prepare-browser %*
exit /b %ERRORLEVEL%
