# PLG Operator Quick Audit — Windows

A safe, read-only diagnostic helper for the Plan Life Grateful workflow.

## What it does

- Reports Windows version/build, RAM, and local disk free space.
- Checks whether common tools (Git, Python, FFmpeg, Node, winget, VS Code, Claude CLI) are available on PATH.
- Counts top-level items in common work folders.
- Lists the 15 largest files under Downloads so you can decide what to review.
- Tests basic TCP reachability to Microsoft's HTTPS endpoint.
- Writes a timestamped text report to Desktop (or your user folder if Desktop is unavailable).

## What it does NOT do

It does not install software, delete files, modify system settings, change execution policy, upload files, or publish content.

## How to use it

1. Open this file in GitHub: https://github.com/planlifegrateful-lang/Ugc-business-os/blob/main/tools/PLG-Operator-Quick-Audit.ps1
2. Review the script before running it.
3. Download the raw script from: https://raw.githubusercontent.com/planlifegrateful-lang/Ugc-business-os/main/tools/PLG-Operator-Quick-Audit.ps1
4. Save it in Downloads.
5. Open Windows PowerShell (not necessarily as Administrator) and run:

```powershell
$script = Join-Path $HOME 'Downloads\PLG-Operator-Quick-Audit.ps1'
Get-Content -LiteralPath $script
```

Read the script before running it. Then, if you are satisfied it matches the published version, execute it for this session only:

```powershell
& $script
```

If Windows blocks the script, do not disable security protections or set the execution policy to Unrestricted. Inspect the message first and ask for help if needed.

## Privacy

The generated report can contain the computer name, local folder paths, and installed-tool locations. Review it before sharing. It is designed to stay on your computer unless you deliberately share it.

## Next use

After reviewing the report, use the missing-tool results to decide which free capability is worth enabling next. Do not install everything. Prioritize the one tool needed for a specific outcome.
