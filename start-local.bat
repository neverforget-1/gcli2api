@echo off
setlocal
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo The local environment is not installed yet.
  echo Open Codex and ask it to repair the gcli2api installation.
  pause
  exit /b 1
)

for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"

powershell.exe -NoProfile -Command "$listener = Get-NetTCPConnection -State Listen -LocalPort %PORT% -ErrorAction SilentlyContinue; if ($listener) { exit 0 } else { exit 1 }" >nul 2>&1
if not errorlevel 1 (
  echo GCLI2API is already listening on port %PORT%; no second instance was started.
  exit /b 0
)

echo GCLI2API is starting at http://127.0.0.1:%PORT%
echo Keep this window open while using the API.
".venv\Scripts\python.exe" web.py

echo.
echo GCLI2API has stopped.
pause
