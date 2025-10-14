@echo off
echo Starting Django with WebSocket support using Daphne...
echo.
echo Setting Django settings module...
set DJANGO_SETTINGS_MODULE=AirplaneDJ.settings

echo Starting Daphne ASGI server on port 8000...
daphne -p 8000 AirplaneDJ.asgi:application

echo.
echo If you see errors, make sure you have daphne installed:
echo pip install daphne
echo.
pause