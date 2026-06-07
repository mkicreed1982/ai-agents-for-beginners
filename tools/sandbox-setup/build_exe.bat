@echo off
REM Build the Windows .exe for the sandbox setup tool.
REM Requires Python 3.9+ on PATH.

echo Installing PyInstaller (if needed)...
python -m pip install --upgrade pyinstaller || goto :error

echo Building sandbox-setup.exe...
python "%~dp0build_exe.py" || goto :error

echo.
echo Build complete. See: %~dp0dist\sandbox-setup.exe
goto :eof

:error
echo.
echo Build failed.
exit /b 1
