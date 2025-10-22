@echo off
echo 🧪 AirportProject Docker Tests
echo ================================
echo.

echo 1. Container Status:
docker-compose ps
echo.

echo 2. Database Connection:
docker-compose exec db psql -U airportuser -d airportdb -c "SELECT version();"
echo.

echo 3. Redis Connection:
docker-compose exec redis redis-cli PING
echo.

echo 4. Django Tests:
docker-compose exec web python manage.py test --parallel
echo.

echo 5. Code Quality:
docker-compose exec web ruff check . --statistics
echo.

echo ✅ All tests completed!
pause
