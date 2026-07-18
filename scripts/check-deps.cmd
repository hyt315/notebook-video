@echo off
setlocal
node "%~dp0notebook-video.mjs" check-deps %*
exit /b %ERRORLEVEL%
