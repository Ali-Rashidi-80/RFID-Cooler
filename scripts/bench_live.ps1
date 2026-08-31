#Requires -Version 5.1
<#
.SYNOPSIS
  Live bench helper — COM detect, serial log, diagnostics (E).

.EXAMPLE
  .\scripts\bench_live.ps1
  .\scripts\bench_live.ps1 -Port COM3
  .\scripts\bench_live.ps1 -Port COM3 -Snapshot -SnapshotSeconds 10
#>
[CmdletBinding()]
param(
    [string] $Port = "",
    [switch] $Snapshot,
    [int] $SnapshotSeconds = 10
)

$ErrorActionPreference = "Continue"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Ensure-Tools {
    python -m mpremote --help 2>$null | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[bench] Installing mpremote + pyserial..." -ForegroundColor Yellow
        python -m pip install -q mpremote pyserial
    }
}

function Get-AllPorts {
    python (Join-Path $Root "scripts\bench_port_util.py") list
}

function Get-BestPort {
    param([string] $Preferred)
    $args = @("best")
    if ($Preferred) { $args += $Preferred }
    $out = python (Join-Path $Root "scripts\bench_port_util.py") @args 2>$null
    if ($out) { return $out.Trim() }
    return ""
}

function Show-Troubleshooting {
    param([string] $Com)
    Write-Host ""
    Write-Host "=== Troubleshooting (E) ===" -ForegroundColor Yellow
    if (-not $Com) {
        Write-Host "  [!] No ESP32 USB-serial port found on this PC right now."
        Write-Host "      1. Plug ESP32 with a DATA cable"
        Write-Host "      2. Device Manager -> Ports (COM & LPT) -> note COMx"
        Write-Host "      3. Install CH340 / CP210x driver if needed"
        Write-Host "      4. Re-run: .\scripts\bench_live.ps1 -Port COMx"
        Write-Host "  [i] COM1 'Communications Port' is NOT your ESP32."
    } else {
        Write-Host "  Port $Com selected. If monitor is silent:"
        Write-Host "      - Press EN/RST on board"
        Write-Host "      - Close other apps using the port (Arduino IDE, etc.)"
        Write-Host "      - Flash: .\scripts\flash_device.ps1 -Port $Com"
    }
    Write-Host ""
    Write-Host "  Expected serial lines after boot:"
    Write-Host "      [BOOT] RFID-Cooler ready"
    Write-Host "      [HW] RFID Initialized & Ready"
    Write-Host "      [SYS] Cloud WSS disabled  (or Online dual-mode enabled)"
    Write-Host "      [WS] Connected            (when mock/live backend up)"
    Write-Host ""
    Write-Host "  Mock backend (Phase 4):"
    Write-Host "      python scripts/integration/mock_ws_backend.py --interactive"
    Write-Host "      Edit config.bench.example.json -> server_host = your LAN IP"
    Write-Host "      .\scripts\flash_device.ps1 -Port $Com -IncludeConfig"
    Write-Host ""
}

function Read-SerialSnapshot {
    param([string] $Com, [int] $Seconds)
    $logFile = Join-Path $env:TEMP "rfid-cooler-bench-$Com.log"
    Write-Host "Capturing ${Seconds}s from $Com -> $logFile" -ForegroundColor Cyan
    python (Join-Path $Root "scripts\bench_serial_snapshot.py") $Com $Seconds $logFile
    if (Test-Path $logFile) {
        Write-Host ""
        Write-Host "--- Pattern check ---" -ForegroundColor Cyan
        $content = Get-Content $logFile -Raw -ErrorAction SilentlyContinue
        foreach ($pat in @('[BOOT]', '[HW]', '[SYS]', '[WS]', '[RFID]', '[CLOUD]')) {
            if ($content -match [regex]::Escape($pat)) {
                Write-Host "  OK  $pat" -ForegroundColor Green
            } else {
                Write-Host "  --  $pat (not seen)" -ForegroundColor DarkGray
            }
        }
    }
}

Ensure-Tools
Write-Host "=== RFID-Cooler bench live ===" -ForegroundColor Cyan
Write-Host "Repo: $Root`n"

Write-Host "--- COM ports ---" -ForegroundColor Cyan
$portLines = @(Get-AllPorts)
if ($portLines) { $portLines | ForEach-Object { Write-Host "  $_" } }
else { Write-Host "  (none)" }

$com = Get-BestPort -Preferred $Port
Write-Host ""
if ($com) {
    Write-Host "Selected: $com" -ForegroundColor Green
} else {
    Show-Troubleshooting -Com ""
    exit 1
}

Write-Host "`n--- mpremote ---" -ForegroundColor Cyan
python -m mpremote connect list 2>&1

Write-Host "`n--- LAN IPv4 (set config.bench server_host) ---" -ForegroundColor Cyan
Get-NetIPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue |
    Where-Object { $_.IPAddress -notlike "127.*" } |
    Select-Object -First 5 IPAddress, InterfaceAlias |
    Format-Table -AutoSize

if ($Snapshot) {
    Read-SerialSnapshot -Com $com -Seconds $SnapshotSeconds
    Show-Troubleshooting -Com $com
    exit 0
}

Write-Host "`n--- Interactive REPL (Ctrl+C to exit) ---" -ForegroundColor Cyan
Write-Host "Or re-run: .\scripts\bench_live.ps1 -Port $com -Snapshot`n"
python -m mpremote connect $com repl

Show-Troubleshooting -Com $com
