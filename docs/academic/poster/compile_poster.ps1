# Script PowerShell para Compilação Modular do Pôster Acadêmico UNIFEI
$ErrorActionPreference = "Stop"

$PosterDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $PosterDir

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "Compilando Pôster Acadêmico Modular: main.tex -> poster_simposio.pdf" -ForegroundColor Cyan
Write-Host "Diretório: $PosterDir" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# Verifica pdflatex
$pdflatex = Get-Command pdflatex -ErrorAction SilentlyContinue
if (-not $pdflatex) {
    Write-Error "pdflatex não foi encontrado no PATH do sistema."
    exit 1
}

# Passo 1
Write-Host "`n[Passo 1/2] Executando pdflatex..." -ForegroundColor Yellow
$proc1 = Start-Process -FilePath "pdflatex.exe" -ArgumentList "-interaction=nonstopmode", "-jobname=poster_simposio", "main.tex" -NoNewWindow -PassThru -Wait
if ($proc1.ExitCode -ne 0) {
    Write-Error "Erro durante o Passo 1 da compilação. Consulte poster_simposio.log."
    exit $proc1.ExitCode
}

# Passo 2
Start-Sleep -Milliseconds 800
if (Test-Path "poster_simposio.pdf") {
    Remove-Item "poster_simposio.pdf" -Force -ErrorAction SilentlyContinue
}
Write-Host "`n[Passo 2/2] Finalizando layout, numerações e referências com pdflatex..." -ForegroundColor Yellow
$proc2 = Start-Process -FilePath "pdflatex.exe" -ArgumentList "-interaction=nonstopmode", "-jobname=poster_simposio", "main.tex" -NoNewWindow -PassThru -Wait
if ($proc2.ExitCode -ne 0) {
    Write-Error "Erro durante o Passo 2 da compilação. Consulte poster_simposio.log."
    exit $proc2.ExitCode
}

# Limpeza de arquivos temporários
Write-Host "`nLimpando arquivos temporários (.aux, .out, .synctex.gz, .log)..." -ForegroundColor Gray
$tempExtensions = @("*.aux", "*.out", "*.synctex.gz", "*.log")
foreach ($ext in $tempExtensions) {
    Get-ChildItem -Path $PosterDir -Filter $ext | Remove-Item -Force -ErrorAction SilentlyContinue
}

# Validação do PDF
$pdfPath = Join-Path $PosterDir "poster_simposio.pdf"
if (Test-Path $pdfPath) {
    $pdfItem = Get-Item $pdfPath
    Write-Host "`n==========================================================" -ForegroundColor Green
    Write-Host "Pôster modular compilado com sucesso!" -ForegroundColor Green
    Write-Host "Arquivo: $($pdfItem.FullName)" -ForegroundColor Green
    Write-Host "Tamanho: $([math]::Round($pdfItem.Length / 1MB, 2)) MB" -ForegroundColor Green
    Write-Host "==========================================================" -ForegroundColor Green
} else {
    Write-Error "O arquivo poster_simposio.pdf não foi gerado."
    exit 1
}
