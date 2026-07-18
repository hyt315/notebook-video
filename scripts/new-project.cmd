@echo off
setlocal
node "%~dp0notebook-video.mjs" new-project %*
exit /b %ERRORLEVEL%
