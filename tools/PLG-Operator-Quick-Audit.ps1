# PLG Operator Quick Audit
# Read-only Windows inventory with a timestamped report.
# It does not install software, delete files, change settings, or contact external services.
# Compatible target: Windows PowerShell 5.1+.

$ErrorActionPreference = 'SilentlyContinue'
$stamp = Get-Date -Format 'yyyyMMdd-HHmmss'
$desktop = [Environment]::GetFolderPath('Desktop')
if ([string]::IsNullOrWhiteSpace($desktop) -or -not (Test-Path $desktop)) {
    $desktop = $HOME
}
$reportPath = Join-Path $desktop "PLG-Operator-Audit-$stamp.txt"
$lines = New-Object System.Collections.Generic.List[string]

function Add-Line([string]$Text) { $script:lines.Add($Text) }

Add-Line "PLAN LIFE GRATEFUL — OPERATOR QUICK AUDIT"
Add-Line "Generated: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"
Add-Line "Computer: $env:COMPUTERNAME"
Add-Line "User profile: $HOME"
Add-Line ""
Add-Line "=== WINDOWS ==="
try {
    $os = Get-CimInstance Win32_OperatingSystem
    Add-Line ("Caption: {0}" -f $os.Caption)
    Add-Line ("Version/build: {0} / {1}" -f $os.Version, $os.BuildNumber)
    Add-Line ("Last boot: {0}" -f $os.LastBootUpTime)
    Add-Line ("RAM total GB: {0}" -f [math]::Round($os.TotalVisibleMemorySize / 1MB, 2))
    Add-Line ("RAM free GB: {0}" -f [math]::Round($os.FreePhysicalMemory / 1MB, 2))
} catch { Add-Line "Windows details: unavailable in this session" }

Add-Line ""
Add-Line "=== DISK SPACE ==="
try {
    Get-CimInstance Win32_LogicalDisk -Filter "DriveType=3" | ForEach-Object {
        Add-Line ("{0}  total={1} GB  free={2} GB" -f $_.DeviceID, [math]::Round($_.Size/1GB,2), [math]::Round($_.FreeSpace/1GB,2))
    }
} catch { Add-Line "Disk details: unavailable" }

Add-Line ""
Add-Line "=== AVAILABLE TOOLING ==="
$commands = @('git','python','python3','py','ffmpeg','winget','node','npm','code','claude')
foreach ($name in $commands) {
    $cmd = Get-Command $name -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($cmd) { Add-Line ("{0}: FOUND — {1}" -f $name, $cmd.Source) }
    else { Add-Line ("{0}: not found on PATH" -f $name) }
}

Add-Line ""
Add-Line "=== USEFUL FOLDERS ==="
$folders = @(
    (Join-Path $HOME 'Downloads'),
    (Join-Path $HOME 'Documents'),
    (Join-Path $HOME 'Desktop'),
    (Join-Path $HOME 'Videos')
)
foreach ($folder in $folders) {
    if (Test-Path $folder) {
        $count = @(Get-ChildItem -LiteralPath $folder -Force -ErrorAction SilentlyContinue).Count
        Add-Line ("{0} — {1} top-level items" -f $folder, $count)
    } else {
        Add-Line ("{0} — not present" -f $folder)
    }
}

Add-Line ""
Add-Line "=== LARGEST DOWNLOADS (TOP 15; NO FILES MODIFIED) ==="
$downloads = Join-Path $HOME 'Downloads'
if (Test-Path $downloads) {
    $big = Get-ChildItem -LiteralPath $downloads -File -Recurse -ErrorAction SilentlyContinue |
        Sort-Object Length -Descending | Select-Object -First 15
    if ($big) {
        foreach ($file in $big) {
            Add-Line ("{0} MB | {1}" -f [math]::Round($file.Length/1MB,1), $file.FullName)
        }
    } else { Add-Line "No files found, or access was restricted." }
} else { Add-Line "Downloads folder not found." }

Add-Line ""
Add-Line "=== NETWORK CHECK (DNS/HTTPS REACHABILITY ONLY) ==="
try {
    $net = Test-NetConnection www.microsoft.com -Port 443 -WarningAction SilentlyContinue
    Add-Line ("HTTPS TCP reachable: {0}" -f $net.TcpTestSucceeded)
} catch { Add-Line "Network test unavailable" }

Add-Line ""
Add-Line "=== SAFETY NOTES ==="
Add-Line "This report is diagnostic only. No installs, deletions, settings changes, or external uploads were performed."
Add-Line "Review the report before sharing it; it can contain your computer name, local paths, and software locations."
$lines | Set-Content -LiteralPath $reportPath -Encoding UTF8
Write-Host ""
Write-Host "Audit finished. Report saved to:" -ForegroundColor Green
Write-Host $reportPath
Write-Host ""
Write-Host "No files were deleted or settings changed."
