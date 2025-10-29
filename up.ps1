param([switch]$Rebuild)


$ErrorActionPreference = "Stop"

function Test-Docker {
  try {
    docker version | Out-Null
    return $true
  } catch {
    return $false
  }
}

function Ensure-Docker {
  if (Test-Docker) { return }

  Write-Host "🐳 Docker Desktop не запущен — пробую стартовать..." -ForegroundColor Yellow
  $dockerExe = "C:\Program Files\Docker\Docker\Docker Desktop.exe"
  if (Test-Path $dockerExe) {
    Start-Process -FilePath $dockerExe | Out-Null
  } else {
    throw "Не найден Docker Desktop: $dockerExe"
  }

  # ждём готовности демона (до ~90 сек)
  $deadline = (Get-Date).AddSeconds(90)
  do {
    Start-Sleep -Seconds 3
    if (Test-Docker) { return }
  } while ((Get-Date) -lt $deadline)

  throw "Docker Desktop не успел стартовать: демон недоступен"
}

function Get-Health($name) {
  $id = docker ps -a --format "{{.Names}}" | Where-Object { $_ -like "*$name*" } | Select-Object -First 1
  if (-not $id) { return "not-found" }
  try {
    $hc = docker inspect --format='{{.State.Health.Status}}' $id 2>$null
    if ($hc) { return $hc } else { return "running" } # если healthcheck не задан
  } catch {
    return "unknown"
  }
}

# --- старт ---
Ensure-Docker

if ($Rebuild) {
  Write-Host "🔄 Полная пересборка образов..." -ForegroundColor Yellow
  docker compose build --no-cache | Out-Null
}

Write-Host "🚀 Запускаю контейнеры (detached)..." -ForegroundColor Yellow
docker compose up -d | Out-Null

# Ждём базовые сервисы
$services = @("db","redis","mongo","rabbitmq","app","worker")
Write-Host "`n⏳ Жду инициализации (healthcheck)..." -ForegroundColor Yellow
$deadline = (Get-Date).AddMinutes(3)
do {
  Start-Sleep -Seconds 3
  $states = @{}
  foreach ($s in $services) { $states[$s] = Get-Health $s }
  $allDone = ($states.Values -notcontains "starting") -and ($states.Values -notcontains "unhealthy")
} while (-not $allDone -and (Get-Date) -lt $deadline)

Write-Host "`n=== Статус контейнеров ==="
foreach ($kvp in $states.GetEnumerator()) {
  $name = $kvp.Key; $st = $kvp.Value
  if ($st -eq "healthy" -or $st -eq "running") {
    Write-Host ("✅ {0}: {1}" -f $name, $st) -ForegroundColor Green
  } elseif ($st -eq "starting") {
    Write-Host ("⏳ {0}: {1}" -f $name, $st) -ForegroundColor Yellow
  } else {
    Write-Host ("❌ {0}: {1}" -f $name, $st) -ForegroundColor Red
  }
}

Write-Host "`nЛоги: .\logs\app\app.log и .\logs\worker\worker.log" -ForegroundColor Cyan
