# StorySeed Classroom Self-Test Gauntlet

Use this when there is no outside tester available. It is the solo version of the phone-call test: prove the public ZIP works from a clean D-drive run.

## D-Drive Setup

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\StorySeedGauntletData, D:\StorySeedVerifyWork | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:STORYSEED_HOME = "D:\StorySeedGauntletData"
$env:STORYSEED_TEST_TMP = "D:\Temp"
```

## Automated Gate

```powershell
python -m unittest discover -s tests
python -m compileall storyseed_app tests scripts
python scripts\check_assets.py
python scripts\sample_prompts.py --count 12 --matrix
python -m storyseed_app.app --doctor
powershell -ExecutionPolicy Bypass -File scripts\make_release_zip.ps1
$zip = (Get-ChildItem dist\StorySeedClassroom-v*.zip | Sort-Object LastWriteTime -Descending | Select-Object -First 1).FullName
powershell -ExecutionPolicy Bypass -File scripts\verify_release_zip.ps1 -ZipPath $zip -WorkRoot D:\StorySeedVerifyWork
```

## Manual Gate

1. Unzip the latest release ZIP into a fresh D-drive folder.
2. Double-click `START_StorySeed_WINDOWS.bat`.
3. Confirm the browser opens without needing a terminal.
4. Press `Generate Prompt`.
5. Confirm the Generate page readout makes sense: Mode, Spark, Seed.
6. Open Review and switch between Student View and Teacher Notes.
7. Export HTML and press `Open Latest Worksheet`.
8. Export TXT.
9. Save the current prompt as a favourite.
10. Close the app window or terminal.
11. Relaunch and confirm the favourite is still there.
12. Confirm no runtime data was written into tracked app folders.

## Pass Standard

- First prompt can be generated in under one minute after launch.
- The user can follow green, amber, and red lights without reading docs.
- Exported files open from the app.
- Release ZIP verification passes.
- No server is left running after the development stage.
