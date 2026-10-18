@echo off
rem make-video.cmd - Windows wrapper: same Node implementation as scripts/make-video.mjs
node "%~dp0make-video.mjs" %*
exit /b %ERRORLEVEL%
