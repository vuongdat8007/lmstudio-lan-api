@echo off
REM Stop script for LM Studio LAN Gateway (Windows)

echo Stopping LM Studio LAN Gateway...

REM Find process running on port 8001
for /f "tokens=5" %%a in ('netstat -aon ^| findstr ":8001" ^| findstr "LISTENING"') do (
    set PID=%%a
    goto :found
)

echo No server found running on port 8001
exit /b 0

:found
echo Found server process: %PID%
echo Stopping process...

REM Gracefully terminate the process
taskkill /PID %PID% /T

if %ERRORLEVEL% EQU 0 (
    echo Server stopped successfully
) else (
    echo Failed to stop server
    echo Trying force kill...
    taskkill /F /PID %PID% /T
    if %ERRORLEVEL% EQU 0 (
        echo Server forcefully stopped
    ) else (
        echo Failed to stop server
        exit /b 1
    )
)

exit /b 0
