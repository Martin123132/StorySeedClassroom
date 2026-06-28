param(
  [string]$Version = ""
)

$ErrorActionPreference = "Stop"

$repoRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path

function Get-StorySeedVersion {
  $initPath = Join-Path $repoRoot "storyseed_app\__init__.py"
  $initText = Get-Content -Raw -LiteralPath $initPath
  $match = [regex]::Match($initText, '__version__\s*=\s*"([^"]+)"')
  if (-not $match.Success) {
    throw "Could not read StorySeed version from $initPath"
  }
  return "v$($match.Groups[1].Value)"
}

if (-not $Version) {
  $Version = Get-StorySeedVersion
}

$dist = Join-Path $repoRoot "dist"
$packageName = "StorySeedClassroom-$Version"
$stage = Join-Path $dist $packageName
$zipPath = Join-Path $dist "$packageName.zip"
$excludedNames = @(".git", "__pycache__", ".pytest_cache", "dist", "build", "user-data", ".venv", "venv")

New-Item -ItemType Directory -Force -Path $dist | Out-Null

function Remove-If-In-Dist($PathToRemove) {
  if (-not (Test-Path -LiteralPath $PathToRemove)) {
    return
  }
  $distResolved = (Resolve-Path -LiteralPath $dist).Path
  $targetResolved = (Resolve-Path -LiteralPath $PathToRemove).Path
  if (-not $targetResolved.StartsWith($distResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside dist: $targetResolved"
  }
  Remove-Item -LiteralPath $targetResolved -Recurse -Force
}

Remove-If-In-Dist $stage
if (Test-Path -LiteralPath $zipPath) {
  Remove-Item -LiteralPath $zipPath -Force
}

New-Item -ItemType Directory -Force -Path $stage | Out-Null

$files = Get-ChildItem -LiteralPath $repoRoot -Force -Recurse -File |
  Where-Object {
    $relative = $_.FullName.Substring($repoRoot.Length).TrimStart("\")
    $parts = $relative -split "\\"
    -not ($parts | Where-Object { $_ -in $excludedNames })
  }

foreach ($file in $files) {
  $relative = $file.FullName.Substring($repoRoot.Length).TrimStart("\")
  $target = Join-Path $stage $relative
  $targetDir = Split-Path -Parent $target
  New-Item -ItemType Directory -Force -Path $targetDir | Out-Null
  Copy-Item -LiteralPath $file.FullName -Destination $target -Force
}

Compress-Archive -Path (Join-Path $stage "*") -DestinationPath $zipPath -Force

$size = [math]::Round((Get-Item -LiteralPath $zipPath).Length / 1KB, 1)
Write-Host "Created $zipPath ($size KB)"

