@echo off
setlocal
node "%~dp0notebook-video.mjs" sync %*
exit /b %ERRORLEVEL%
