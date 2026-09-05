@echo off
setlocal
cd /d "%~dp0"

echo Updating with rebase; local commits are replayed on top, files are never reset.
git pull --rebase
if errorlevel 1 (
  echo Update was skipped or could not be applied. Your local files were not reset.
  pause
  exit /b 1
)

where uv.exe >nul 2>&1
if errorlevel 1 (
  echo uv.exe was not found. Starting with the existing environment.
) else (
  uv sync
  if errorlevel 1 (
    echo Dependency sync failed; the existing environment was left in place.
    pause
    exit /b 1
  )
)

call "%~dp0start-local.bat"
exit /b %ERRORLEVEL%
