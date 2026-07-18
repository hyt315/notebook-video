@echo off
setlocal
node "%~dp0notebook-video.mjs" %*
exit /b %ERRORLEVEL%
