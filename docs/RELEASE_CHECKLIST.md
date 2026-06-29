# StorySeed Classroom Release Checklist

Use this before publishing a public ZIP.

## Local Checks

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\StorySeedClassroomData, D:\StorySeedVerifyWork | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:STORYSEED_HOME = "D:\StorySeedClassroomData"
$env:STORYSEED_TEST_TMP = "D:\Temp"
python -m unittest discover -s tests
python -m compileall storyseed_app tests scripts
python scripts\sample_prompts.py --count 12 --matrix
python -m storyseed_app.app --doctor
```

## Manual Browser Smoke

```powershell
$env:STORYSEED_HOME = "D:\StorySeedFreshSmoke"
python -m storyseed_app.app --no-open --port 0
```

In the browser:

1. Generate a prompt.
2. Visit Class Setup.
3. Visit Generate and regenerate same seed.
4. Visit Review.
5. Switch between Student View and Teacher Notes.
6. Save favourite.
7. Export TXT.
8. Export HTML.
9. Press Open Latest Worksheet and confirm the worksheet opens.
10. Visit Seed Bank and check editors load.
11. Confirm Seed Bank Safety is green for the default data.

## Release ZIP

```powershell
powershell -ExecutionPolicy Bypass -File scripts\make_release_zip.ps1
$zip = (Get-ChildItem dist\StorySeedClassroom-v*.zip | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
powershell -ExecutionPolicy Bypass -File scripts\verify_release_zip.ps1 -ZipPath $zip -WorkRoot D:\StorySeedVerifyWork
```

Check the ZIP contains:

- `START_StorySeed_WINDOWS.bat`
- `README.md`
- `LICENSE.md`
- `storyseed_app\`
- `scripts\`
- `docs\`
- `tests\`
- `docs\screenshots\storyseed-generate-desktop.png`
- `docs\GITHUB_FEEDBACK.md`
- `docs\SELF_TEST_GAUNTLET.md`
- `.github\ISSUE_TEMPLATE\bug_report.yml`
- `.github\ISSUE_TEMPLATE\prompt_feedback.yml`
- `.github\ISSUE_TEMPLATE\feature_request.yml`

Check the ZIP does not contain:

- `.git\`
- `__pycache__\`
- `.pytest_cache\`
- `user-data\`
- local D-drive tester data
