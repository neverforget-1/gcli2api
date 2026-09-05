@echo off
setlocal
cd /d "%~dp0"

echo This is the safe local launcher. It does not fetch or reset the repository.
call "%~dp0start-local.bat"
exit /b %ERRORLEVEL%
