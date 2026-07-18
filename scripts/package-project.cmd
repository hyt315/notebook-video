@echo off
setlocal
node "%~dp0notebook-video.mjs" package %*
exit /b %ERRORLEVEL%
