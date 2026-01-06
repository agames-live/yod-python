param(
  [ValidateSet("testpypi", "pypi")]
  [string]$Repository = "testpypi",

  # If set, uploads the built artifacts. If not set, only builds + checks.
  [switch]$Upload
)

$ErrorActionPreference = "Stop"

function Fail([string]$Message) {
  Write-Host $Message -ForegroundColor Red
  exit 1
}

function Run([string]$Command) {
  Write-Host ">> $Command" -ForegroundColor Cyan
  Invoke-Expression $Command
  if ($LASTEXITCODE -ne 0) {
    Fail "Command failed with exit code $LASTEXITCODE: $Command"
  }
}

function Read-Secret([string]$Prompt) {
  $secure = Read-Host $Prompt -AsSecureString
  $bstr = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($secure)
  try {
    return [Runtime.InteropServices.Marshal]::PtrToStringBSTR($bstr)
  } finally {
    [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($bstr)
  }
}

Push-Location (Split-Path -Parent $PSCommandPath)
Pop-Location

# Ensure we run from sdk/ (this script lives in sdk/scripts/)
$sdkRoot = Resolve-Path (Join-Path (Split-Path -Parent $PSCommandPath) "..")
Push-Location $sdkRoot

try {
  if (Test-Path "dist") {
    Write-Host "Removing stale dist/ artifacts..." -ForegroundColor Yellow
    Remove-Item -Recurse -Force "dist"
  }

  Run "python -m pip install --upgrade build twine"
  Run "python -m build"
  Run "python -m twine check dist/*"

  if ($Upload) {
    if (-not $env:TWINE_USERNAME) { $env:TWINE_USERNAME = "__token__" }
    if (-not $env:TWINE_PASSWORD) {
      Write-Host "TWINE_PASSWORD not set. You can paste a PyPI/TestPyPI API token now (input is hidden)." -ForegroundColor Yellow
      $env:TWINE_PASSWORD = Read-Secret "PyPI token"
    }

    if ($Repository -eq "testpypi") {
      Run "python -m twine upload --repository-url https://test.pypi.org/legacy/ dist/*"
    } else {
      Run "python -m twine upload dist/*"
    }
  } else {
    Write-Host "Build complete. Re-run with -Upload to publish." -ForegroundColor Green
  }
} finally {
  Pop-Location
}


