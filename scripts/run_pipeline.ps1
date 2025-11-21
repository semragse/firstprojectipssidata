# Complete pipeline: Extract, Transform, Load to PostgreSQL

param(
    [switch]$FullExtract = $false
)

Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan
Write-Host "🚀 Google Trends Analytics Pipeline" -ForegroundColor Green
Write-Host "=" -NoNewline -ForegroundColor Cyan
Write-Host ("=" * 59) -ForegroundColor Cyan

# Check if containers are running
Write-Host "`n📋 Checking services..." -ForegroundColor Yellow
$postgresRunning = podman ps --filter "name=trends_postgres" --format "{{.Names}}" 2>$null

if (-not $postgresRunning) {
    Write-Host "❌ PostgreSQL is not running. Start services first:" -ForegroundColor Red
    Write-Host "   podman-compose -f docker-compose-simple.yml up -d" -ForegroundColor White
    exit 1
}

Write-Host "✅ PostgreSQL: Running" -ForegroundColor Green

# Step 1: Extract data
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Step 1: Extract Google Trends Data" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan

$extractArgs = "--insecure"
if ($FullExtract) {
    $extractArgs += " --geo --comparison"
}

Write-Host "Running: python scripts/extract_to_postgres.py $extractArgs" -ForegroundColor Gray
python scripts/extract_to_postgres.py $extractArgs.Split()

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Extraction failed!" -ForegroundColor Red
    exit 1
}

# Wait a bit between API calls
Start-Sleep -Seconds 2

# Step 2: Transform data
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "Step 2: Transform & Analyze Data" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "Running: python scripts/transform_to_postgres.py" -ForegroundColor Gray
python scripts/transform_to_postgres.py

if ($LASTEXITCODE -ne 0) {
    Write-Host "`n❌ Transformation failed!" -ForegroundColor Red
    exit 1
}

# Step 3: Display summary
Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "📊 Data Summary" -ForegroundColor Yellow
Write-Host ("=" * 60) -ForegroundColor Cyan

$env:PGPASSWORD = "trends_pass"
$summaryQuery = @"
SELECT 
    'Raw Trends' as table_name, 
    COUNT(*) as record_count,
    MIN(date) as from_date,
    MAX(date) as to_date
FROM trends_raw
UNION ALL
SELECT 
    'ChatGPT Evolution', 
    COUNT(*),
    MIN(date),
    MAX(date)
FROM chatgpt_evolution
UNION ALL
SELECT 
    'AI Peaks', 
    COUNT(*),
    MIN(date),
    MAX(date)
FROM ai_peaks
UNION ALL
SELECT 
    'Geographic Data', 
    COUNT(*),
    NULL,
    NULL
FROM geo_distribution
UNION ALL
SELECT 
    'ML Comparison', 
    COUNT(*),
    MIN(date),
    MAX(date)
FROM ml_comparison
UNION ALL
SELECT 
    'AI Forecast', 
    COUNT(*),
    MIN(date),
    MAX(date)
FROM ai_forecast;
"@

Write-Host $summaryQuery | psql -h localhost -p 5432 -U trends_user -d trends_db -t

Write-Host "`n" -NoNewline
Write-Host ("=" * 60) -ForegroundColor Cyan
Write-Host "✅ Pipeline Complete!" -ForegroundColor Green
Write-Host ("=" * 60) -ForegroundColor Cyan

Write-Host "`n📊 Access Grafana at: " -NoNewline -ForegroundColor Yellow
Write-Host "http://localhost:3000" -ForegroundColor White
Write-Host "   Username: admin" -ForegroundColor Gray
Write-Host "   Password: admin" -ForegroundColor Gray

Write-Host "`n💾 PostgreSQL connection:" -ForegroundColor Yellow
Write-Host "   Host: localhost:5432" -ForegroundColor White
Write-Host "   Database: trends_db" -ForegroundColor White
Write-Host "   User: trends_user" -ForegroundColor White
Write-Host "   Password: trends_pass" -ForegroundColor White
