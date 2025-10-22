# Quick Docker Test Script - No execution policy needed
Write-Host "🧪 AirportProject Docker Tests" -ForegroundColor Green
Write-Host "================================" -ForegroundColor Yellow

# Check containers
Write-Host "1. Container Status:" -ForegroundColor Cyan
docker-compose ps

# Test database
Write-Host "2. Database Connection:" -ForegroundColor Cyan
docker-compose exec db psql -U airportuser -d airportdb -c "SELECT version();" | head -5

# Test Redis
Write-Host "3. Redis Connection:" -ForegroundColor Cyan
docker-compose exec redis redis-cli PING

# Test Django
Write-Host "4. Django Tests:" -ForegroundColor Cyan
docker-compose exec web python manage.py test --parallel

# Test linting
Write-Host "5. Code Quality:" -ForegroundColor Cyan
docker-compose exec web ruff check . --statistics

Write-Host "✅ All tests completed!" -ForegroundColor Green
