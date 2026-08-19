@echo off
echo ===================================================
echo   Compiling Galactic Focus into Standalone Windows Executable (.exe)
echo ===================================================

python -m PyInstaller --noconfirm --onefile --windowed --icon="icon.ico" --name "GalacticFocus" --collect-all flet --collect-all flet_desktop --add-data "galactic_focus;galactic_focus" --add-data "%USERPROFILE%\.flet\client\flet-desktop-full-0.86.5\flet;flet_client" main.py

copy /Y "dist\GalacticFocus.exe" ".\GalacticFocus.exe" >nul
rmdir /S /Q "build" 2>nul

echo.
echo ===================================================
echo   Build Complete!
echo   Standalone executable updated with custom icon: GalacticFocus.exe
echo ===================================================
pause
