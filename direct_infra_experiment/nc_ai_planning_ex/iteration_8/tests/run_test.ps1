# Run a specific derivation test
# Usage: .\run_test.ps1 -TestNum 01

param(
    [Parameter(Mandatory=$true)]
    [string]$TestNum,
    
    [switch]$KeepCheckpoints
)

$ErrorActionPreference = "Stop"
$TestDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ProjectDir = Split-Path -Parent $TestDir

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Running Derivation Test $TestNum" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# Validate test exists
$TestInputs = Join-Path $TestDir "inputs_test_$TestNum.json"
$TestInstruction = Join-Path $TestDir "test_$($TestNum)_*.txt"

if (-not (Test-Path $TestInputs)) {
    Write-Host "ERROR: Test inputs not found: $TestInputs" -ForegroundColor Red
    exit 1
}

$InstructionFile = Get-ChildItem $TestInstruction | Select-Object -First 1
if (-not $InstructionFile) {
    Write-Host "ERROR: Test instruction file not found: $TestInstruction" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Test Instruction: $($InstructionFile.Name)" -ForegroundColor Yellow
Write-Host "----------------------------------------"
Get-Content $InstructionFile.FullName | Write-Host -ForegroundColor Gray
Write-Host "----------------------------------------"
Write-Host ""

# Clear previous checkpoints (unless -KeepCheckpoints)
if (-not $KeepCheckpoints) {
    Write-Host "Clearing previous checkpoints..." -ForegroundColor Yellow
    
    $FilesToRemove = @(
        "progress.txt",
        "1_refined_instruction.txt",
        "2_extraction.json",
        "3_classifications.json",
        "4_dependency_tree.json",
        "ncds_output.ncds"
    )
    
    foreach ($file in $FilesToRemove) {
        $path = Join-Path $ProjectDir $file
        if (Test-Path $path) {
            Remove-Item $path -Force
            Write-Host "  Removed: $file" -ForegroundColor DarkGray
        }
    }
}

# Copy test inputs to repos
Write-Host ""
Write-Host "Setting up test inputs..." -ForegroundColor Yellow
$ReposInputs = Join-Path $ProjectDir "repos\inputs.json"
Copy-Item $TestInputs $ReposInputs -Force
Write-Host "  Copied: inputs_test_$TestNum.json -> repos/inputs.json" -ForegroundColor DarkGray

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "Test $TestNum ready!" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "  1. Reload the project in Canvas App (click reload button)" -ForegroundColor White
Write-Host "  2. Run the execution" -ForegroundColor White
Write-Host "  3. Check ncds_output.ncds for results" -ForegroundColor White
Write-Host ""

