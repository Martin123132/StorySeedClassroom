# StorySeed Classroom Tester Script

This is the phone-call test. A teacher, parent, or tutor should be able to use
the app without opening a command prompt.

## What To Say

1. Open the StorySeed Classroom folder.
2. Double-click `START_StorySeed_WINDOWS.bat`.
3. When the browser opens, press `Generate Prompt`.
4. Check the traffic lights and click one of them.
5. Open the Review page.
6. Switch between Student View and Teacher Notes.
7. Export HTML, then press `Open Latest Worksheet`.
8. Export TXT if they want a plain text copy.

## What To Watch For

- Time from starting the call to first prompt.
- Did Python missing/install guidance make sense?
- Did the browser open by itself?
- Did the traffic lights explain the next step?
- Did clicking a traffic light open the page they expected?
- Did the separate pages feel calmer than a single busy screen?
- Did the Seed Bank Safety status make sense as green, amber, or red?
- Could they export and open the worksheet without help?
- Did the prompt feel teacher-safe?
- Did anything sound too technical?

## D-Drive Rehearsal Setup

```powershell
New-Item -ItemType Directory -Force -Path D:\Temp, D:\StorySeedTesterData | Out-Null
$env:TEMP = "D:\Temp"
$env:TMP = "D:\Temp"
$env:STORYSEED_HOME = "D:\StorySeedTesterData"
```
