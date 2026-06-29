param(
  [string]$ZipPath,
  [string]$WorkRoot = ""
)

$ErrorActionPreference = "Stop"

if (-not $ZipPath) {
  throw "Pass -ZipPath with a local StorySeedClassroom release ZIP."
}

if ($WorkRoot) {
  New-Item -ItemType Directory -Force -Path $WorkRoot | Out-Null
  $tempBase = (Resolve-Path -LiteralPath $WorkRoot).Path
} else {
  $tempBase = [System.IO.Path]::GetTempPath()
}

$work = Join-Path $tempBase "StorySeedVerify-$([System.Guid]::NewGuid().ToString('N'))"
$extractDir = Join-Path $work "unzipped"
$dataDir = Join-Path $work "data"

function Remove-TempWork {
  if (-not (Test-Path -LiteralPath $work)) {
    return
  }
  $baseResolved = (Resolve-Path -LiteralPath $tempBase).Path
  $workResolved = (Resolve-Path -LiteralPath $work).Path
  if (-not $workResolved.StartsWith($baseResolved, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Refusing to remove path outside work root: $workResolved"
  }
  Remove-Item -LiteralPath $workResolved -Recurse -Force
}

try {
  New-Item -ItemType Directory -Force -Path $work, $extractDir, $dataDir | Out-Null
  $sourceZip = (Resolve-Path -LiteralPath $ZipPath).Path
  Expand-Archive -LiteralPath $sourceZip -DestinationPath $extractDir -Force

  $required = @(
    "START_StorySeed_WINDOWS.bat",
    "README.md",
    "LICENSE.md",
    ".github\ISSUE_TEMPLATE\bug_report.yml",
    ".github\ISSUE_TEMPLATE\prompt_feedback.yml",
    ".github\ISSUE_TEMPLATE\feature_request.yml",
    "docs\GITHUB_FEEDBACK.md",
    "docs\SELF_TEST_GAUNTLET.md",
    "docs\screenshots\storyseed-generate-desktop.png",
    "docs\screenshots\storyseed-generate-mobile-top.png",
    "docs\screenshots\storyseed-prompt-forge-mobile.png",
    "storyseed_app\app.py",
    "storyseed_app\engine.py",
    "storyseed_app\seeds\classroom_default.json",
    "storyseed_app\static\assets\manifest.json",
    "storyseed_app\static\assets\storyseed-app-icon.png",
    "storyseed_app\static\assets\storyseed-world-wallpaper.jpg",
    "storyseed_app\static\assets\storyseed-mission-lane.jpg",
    "storyseed_app\static\assets\storyseed-reuse-shelf.jpg",
    "storyseed_app\static\assets\storyseed-prompt-forge.jpg",
    "storyseed_app\static\assets\storyseed-route-map.jpg",
    "storyseed_app\static\assets\storyseed-zone-setup.jpg",
    "storyseed_app\static\assets\storyseed-zone-favourites.jpg",
    "storyseed_app\static\assets\storyseed-zone-generate.jpg",
    "storyseed_app\static\assets\storyseed-zone-review.jpg",
    "storyseed_app\static\assets\storyseed-zone-seeds.jpg",
    "storyseed_app\templates\index.html",
    "scripts\check_assets.py"
  )
  foreach ($relative in $required) {
    $path = Join-Path $extractDir $relative
    if (-not (Test-Path -LiteralPath $path)) {
      throw "Missing required release file: $relative"
    }
  }

  $forbidden = Get-ChildItem -LiteralPath $extractDir -Force -Recurse |
    Where-Object { $_.Name -in @(".git", "__pycache__", ".pytest_cache", "user-data") }
  if ($forbidden) {
    throw "Release ZIP contains forbidden generated files: $($forbidden[0].FullName)"
  }

  Push-Location $extractDir
  try {
    $env:STORYSEED_HOME = $dataDir
    python -m storyseed_app.app --doctor | Out-Host
    if ($LASTEXITCODE -ne 0) {
      throw "Doctor command failed."
    }
    python scripts\check_assets.py | Out-Host
    if ($LASTEXITCODE -ne 0) {
      throw "Asset check failed."
    }
  } finally {
    Pop-Location
    Remove-Item Env:\STORYSEED_HOME -ErrorAction SilentlyContinue
  }

  Write-Host "StorySeed release ZIP verified: $sourceZip"
} finally {
  Remove-TempWork
}
