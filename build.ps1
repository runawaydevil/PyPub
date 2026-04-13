# pyproject.toml deve estar instalado
# Execute isso em um PowerShell como Admin ou ambiente virtual ativado

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

Write-Host "Instalando dependencias de build..."
pip install -e .[dev]

Write-Host "Rodando test suite de sanidade..."
python -m pytest -v

if ($LASTEXITCODE -ne 0) {
    Write-Host "Falha nos testes, abortando build." -ForegroundColor Red
    exit 1
}

Write-Host "Iniciando PyInstaller..."
if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
if (Test-Path "build") { Remove-Item -Recurse -Force "build" }

python -m PyInstaller pypub.spec

Write-Host "Build concluido na pasta dist\!" -ForegroundColor Green
