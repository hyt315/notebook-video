@echo off
setlocal
node "%~dp0notebook-video.mjs" render %*
exit /b %ERRORLEVEL%
