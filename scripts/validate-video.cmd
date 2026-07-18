@echo off
setlocal
node "%~dp0notebook-video.mjs" validate-video %*
exit /b %ERRORLEVEL%
