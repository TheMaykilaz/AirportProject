# Complete Docker Setup Test Script
Write-Host "🧪 Testing AirportProject Docker Setup..." -ForegroundColor Green

# 1. Check container status
Write-Host "1. Checking container status..." -ForegroundColor Cyan
docker-compose ps

# 2. Run Django tests
Write-Host "2. Running Django tests..." -ForegroundColor Cyan
docker-compose exec web python manage.py test --parallel

# 3. Run linting
Write-Host "3. Running Ruff linting..." -ForegroundColor Cyan
docker-compose exec web ruff check . --statistics

# 4. Test database
Write-Host "4. Testing database connection..." -ForegroundColor Cyan
docker-compose exec db psql -U airportuser -d airportdb -c "SELECT COUNT(*) FROM auth_user;"

# 5. Test Redis
Write-Host "5. Testing Redis connection..." -ForegroundColor Cyan
docker-compose exec redis redis-cli PING

# 6. Check migrations
Write-Host "6. Checking Django migrations..." -ForegroundColor Cyan
docker-compose exec web python manage.py showmigrations

Write-Host "✅ All tests completed!" -ForegroundColor Green
