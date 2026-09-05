@echo off
setlocal
title gcli2api (proxy mode)
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
  echo gcli2api Python environment is missing.
  pause
  exit /b 1
)
if not exist ".env" (
  echo gcli2api .env file is missing.
  pause
  exit /b 1
)

rem Load the existing local configuration without printing secret values.
for /f "usebackq eol=# tokens=1,* delims==" %%A in (".env") do set "%%A=%%B"

rem Proxy settings are intentionally explicit for this alternate launcher.
set "HOST=0.0.0.0"
set "PORT=7861"
set "HTTP_PROXY=http://127.0.0.1:7890"
set "HTTPS_PROXY=http://127.0.0.1:7890"
set "NO_PROXY=127.0.0.1,localhost"

rem Do not create a second server when the canonical instance is already up.
powershell.exe -NoProfile -Command "$listener = Get-NetTCPConnection -State Listen -LocalPort %PORT% -ErrorAction SilentlyContinue; if ($listener) { exit 0 } else { exit 1 }" >nul 2>&1
if not errorlevel 1 (
  echo gcli2api is already listening on port %PORT%; no second instance was started.
  exit /b 0
)

rem Keep diagnostics, never credentials, in the local log.
set "GCLI_LOG=%~dp0start.log"
> "%GCLI_LOG%" echo start at %date% %time%
>> "%GCLI_LOG%" echo mode=proxy
>> "%GCLI_LOG%" echo host=%HOST%
>> "%GCLI_LOG%" echo port=%PORT%
>> "%GCLI_LOG%" echo proxy=127.0.0.1:7890

echo GCLI2API is starting at http://%HOST%:%PORT% (proxy mode)
".venv\Scripts\python.exe" -E web.py >> "%GCLI_LOG%" 2>&1
set "exit_code=%ERRORLEVEL%"

echo.
echo GCLI2API has stopped with exit code %exit_code%.
echo Details are in %GCLI_LOG% (secrets are not written).
pause
exit /b %exit_code%
