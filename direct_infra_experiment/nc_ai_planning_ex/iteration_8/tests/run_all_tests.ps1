# Run all derivation tests and collect results
# Usage: .\run_all_tests.ps1

$ErrorActionPreference = "Stop"
$TestDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $TestDir
$ResultsDir = Join-Path $TestDir "results"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Derivation Algorithm Test Suite" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Create results directory
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir | Out-Null
}

# Get all test files
$Tests = Get-ChildItem (Join-Path $TestDir "inputs_test_*.json") | Sort-Object Name

Write-Host "Found $($Tests.Count) tests to run" -ForegroundColor Yellow
Write-Host ""

$Summary = @()

foreach ($Test in $Tests) {
    $TestNum = $Test.Name -replace "inputs_test_(\d+)\.json", '$1'
    $InstructionFile = Get-ChildItem (Join-Path $TestDir "test_$($TestNum)_*.txt") | Select-Object -First 1
    
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    Write-Host "Test $TestNum: $($InstructionFile.BaseName)" -ForegroundColor Yellow
    Write-Host "----------------------------------------" -ForegroundColor DarkGray
    
    # This would need the canvas app to actually execute
    # For now, just prepare the test
    Write-Host "  Instruction: $($InstructionFile.Name)" -ForegroundColor Gray
    
    $Summary += [PSCustomObject]@{
        TestNum = $TestNum
        Name = $InstructionFile.BaseName
        InputsFile = $Test.Name
        Status = "Ready"
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Test Summary" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
$Summary | Format-Table -AutoSize

Write-Host ""
Write-Host "To run a specific test:" -ForegroundColor Cyan
Write-Host "  .\run_test.ps1 -TestNum 01" -ForegroundColor White
Write-Host ""

