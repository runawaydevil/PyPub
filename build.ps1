# pyproject.toml deve estar instalado
# Execute isso em um PowerShell como Admin ou ambiente virtual ativado
#
# Parametros:
#   -SkipInstall  Nao executa pip install -e .[dev] (venv ja preparado)
#   -SkipTests    Nao executa pytest (apenas empacotamento)
#   -Fast         Equivale a -SkipInstall -SkipTests (iteracao rapida)

param(
    [switch]$SkipInstall,
    [switch]$SkipTests,
    [switch]$Fast
)

if ($Fast) {
    $SkipInstall = $true
    $SkipTests = $true
}

Write-Host "Extraindo versao unica do codigo-fonte..."
$initFile = "src\pypub\__init__.py"
$version = ""
if (Test-Path $initFile) {
    $content = Get-Content $initFile
    foreach ($line in $content) {
        if ($line -match '__version__\s*=\s*"([^"]+)"') {
            $version = $matches[1]
            break
        }
    }
}
if (!$version) { $version = "0.0.1" }
Write-Host "Versao detectada: $version" -ForegroundColor Cyan

Write-Host "Injetando no Installer..."
(Get-Content installer.iss) -replace 'AppVersion=.*', "AppVersion=$version" | Set-Content installer.iss
(Get-Content installer.iss) -replace 'OutputBaseFilename=PyPub-Setup-.*', "OutputBaseFilename=PyPub-Setup-$version" | Set-Content installer.iss

if (-not $SkipInstall) {
    Write-Host "Instalando dependencias de build..."
    pip install -e .[dev]
} else {
    Write-Host "Ignorando pip install (-SkipInstall / -Fast)." -ForegroundColor DarkYellow
}

if (-not $SkipTests) {
    Write-Host "Rodando test suite de sanidade..."
    python -m pytest -v

    if ($LASTEXITCODE -ne 0) {
        Write-Host "Falha nos testes, abortando build." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "Ignorando pytest (-SkipTests / -Fast). Use build completo antes de release." -ForegroundColor DarkYellow
}

$distRoot = Resolve-Path "."
$distDir = Join-Path $distRoot "dist"
$stageDistDir = Join-Path $distRoot "dist_stage"
$stageBuildDir = Join-Path $distRoot "build_stage"
$currentBundle = Join-Path $distDir "PyPub"
$backupBundle = Join-Path $distDir "PyPub_previous"
$stageBundle = Join-Path $stageDistDir "PyPub"
$stageExe = Join-Path $stageBundle "PyPub.exe"

Write-Host "Iniciando PyInstaller em staging..."
if (Test-Path $stageDistDir) { Remove-Item -LiteralPath $stageDistDir -Recurse -Force }
if (Test-Path $stageBuildDir) { Remove-Item -LiteralPath $stageBuildDir -Recurse -Force }

python -m PyInstaller --noconfirm --distpath $stageDistDir --workpath $stageBuildDir pypub.spec

if ($LASTEXITCODE -ne 0) {
    Write-Host "Falha no PyInstaller, abortando promocao do pacote." -ForegroundColor Red
    exit 1
}

Write-Host "Verificando ficheiros Qt/WebEngine no bundle..."
$verifyScript = Join-Path $PSScriptRoot "scripts\verify-frozen-bundle.ps1"
& $verifyScript -BundlePath $stageBundle
if ($LASTEXITCODE -ne 0) {
    Write-Host "Verificacao do bundle falhou." -ForegroundColor Red
    exit 1
}

Write-Host "Executando smoke do executavel empacotado..."
$process = Start-Process -FilePath $stageExe -PassThru
Start-Sleep -Seconds 5
$process.Refresh()
if ($process.HasExited) {
    Write-Host "Smoke falhou: o executavel encerrou com codigo $($process.ExitCode)." -ForegroundColor Red
    exit 1
}
Stop-Process -Id $process.Id -Force

Write-Host "Promovendo staging para dist\\PyPub..."
if (-not (Test-Path $distDir)) {
    New-Item -ItemType Directory -Path $distDir | Out-Null
}
if (Test-Path $backupBundle) {
    Remove-Item -LiteralPath $backupBundle -Recurse -Force
}
if (Test-Path $currentBundle) {
    Move-Item -LiteralPath $currentBundle -Destination $backupBundle -Force
}
Move-Item -LiteralPath $stageBundle -Destination $currentBundle -Force

Write-Host "Build concluido na pasta dist\\PyPub com smoke validado." -ForegroundColor Green
