# Verifica se o diretorio onedir do PyInstaller contem ficheiros criticos do Qt WebEngine e do Qt no Windows.
# Uso: .\scripts\verify-frozen-bundle.ps1 [-BundlePath dist\PyPub]

param(
    [string]$BundlePath = "dist\PyPub"
)

$ErrorActionPreference = "Stop"
$root = Resolve-Path -LiteralPath $BundlePath -ErrorAction SilentlyContinue
if (-not $root) {
    Write-Error "Pasta nao encontrada: $BundlePath (execute o build antes)."
    exit 1
}

$failures = @()

$mainExe = Join-Path $root "PyPub.exe"
if (-not (Test-Path -LiteralPath $mainExe)) {
    $failures += "Falta PyPub.exe na raiz do bundle."
}

$webProc = Get-ChildItem -LiteralPath $root -Filter "QtWebEngineProcess.exe" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $webProc) {
    $failures += "QtWebEngineProcess.exe nao encontrado (OAuth embutido nao funcionara)."
}

$paks = @(Get-ChildItem -LiteralPath $root -Filter "*.pak" -Recurse -File -ErrorAction SilentlyContinue)
if ($paks.Count -eq 0) {
    $failures += "Nenhum ficheiro .pak encontrado (recursos do Chromium/WebEngine em falta?)."
}

$qwindows = Get-ChildItem -LiteralPath $root -Filter "qwindows.dll" -Recurse -File -ErrorAction SilentlyContinue |
    Where-Object { $_.FullName -match "platforms[\\/]qwindows\.dll$" } |
    Select-Object -First 1
if (-not $qwindows) {
    $failures += "Plugin qwindows.dll (em .../platforms/) nao encontrado."
}

$shiboken = Get-ChildItem -LiteralPath $root -Filter "shiboken6*.dll" -Recurse -File -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $shiboken) {
    $failures += "Nenhuma shiboken6*.dll encontrada (bindings Qt em falta?)."
}

if ($failures.Count -gt 0) {
    Write-Host "Verificacao FALHOU para: $root" -ForegroundColor Red
    foreach ($f in $failures) { Write-Host " - $f" -ForegroundColor Yellow }
    exit 1
}

Write-Host "Bundle OK: $root" -ForegroundColor Green
Write-Host " - QtWebEngineProcess: $($webProc.FullName)"
Write-Host " - Ficheiros .pak: $($paks.Count)"
Write-Host " - qwindows.dll: $($qwindows.FullName)"
exit 0
