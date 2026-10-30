<#
.SYNOPSIS
    Deploys an extension APK to a physical Android device without launching emulators.

.DESCRIPTION
    Optimized for low-spec laptops:
    1. Zero emulator overhead.
    2. Auto-detects physical phone via USB debugging using local Android SDK adb.
    3. If USB is not connected, offers instant zero-RAM Wi-Fi browser transfer.

.PARAMETER ApkName
    The filename of the APK inside repo/apk/. Default: 'aniyomi-en.openmovies-v14.1.apk'.

.PARAMETER Mode
    'auto' (default: try adb then fallback), 'adb' (force adb), or 'wifi' (start lightweight HTTP server).

.EXAMPLE
    .\scripts\deploy_to_device.ps1
#>

param(
    [string]$ApkName = "aniyomi-en.openmovies-v14.1.apk",
    [ValidateSet("auto", "adb", "wifi")]
    [string]$Mode = "auto"
)

$ErrorActionPreference = "Stop"

$ApkPath = Join-Path "repo\apk" $ApkName
if (-not (Test-Path $ApkPath)) {
    Write-Error "APK artifact not found at: $ApkPath. Run .\scripts\build_single_extension.ps1 first."
}

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " AnimeBridge - Physical Device Deployment (Zero Emulator Overhead)" -ForegroundColor Cyan
Write-Host " Target APK: $ApkPath" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Locate adb.exe
$AdbExe = "adb"
$SdkAdb = "C:\Users\Adarsh\AppData\Local\Android\Sdk\platform-tools\adb.exe"
if (Test-Path $SdkAdb) {
    $AdbExe = $SdkAdb
}

# 2. Check for Connected Physical Android Devices
$DeviceFound = $false
if ($Mode -ne "wifi") {
    try {
        $DevicesOutput = & $AdbExe devices 2>$null
        $Lines = $DevicesOutput | Where-Object { $_ -match "\bdevice\b" -and $_ -notmatch "List of devices" }
        if ($Lines) {
            $DeviceFound = $true
            Write-Host "[+] Detected connected physical Android device(s):" -ForegroundColor Green
            $Lines | ForEach-Object { Write-Host "    - $_" -ForegroundColor Green }
        }
    } catch {
        Write-Host "[i] ADB daemon not responding or device not connected." -ForegroundColor DarkGray
    }
}

# 3. Deploy via ADB if available
if ($DeviceFound -and $Mode -ne "wifi") {
    Write-Host "[+] Installing APK onto connected device..." -ForegroundColor Cyan
    & $AdbExe install -r $ApkPath
    if ($LASTEXITCODE -eq 0) {
        Write-Host "`n[SUCCESS] Extension installed successfully onto your Android phone!" -ForegroundColor Green
        Write-Host "[i] Now open Dantotsu -> Extensions -> Installed to verify Open Movies." -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "[!] ADB install returned code $LASTEXITCODE. Falling back to Wi-Fi transfer options." -ForegroundColor Yellow
    }
}

# 4. Fallback / Alternative: Local Wi-Fi File Transfer
Write-Host "`n[OPTION 1] USB Cable File Transfer:" -ForegroundColor White
Write-Host "  1. Connect your Android phone to this laptop with a USB cable." -ForegroundColor Gray
Write-Host "  2. Set USB mode on your phone to 'File Transfer (MTP)'." -ForegroundColor Gray
Write-Host "  3. Copy '$ApkPath' to your phone's 'Download' folder." -ForegroundColor Gray
Write-Host "  4. On your phone, tap the APK in Files / Downloads to install." -ForegroundColor Gray

Write-Host "`n[OPTION 2] Zero-Memory Local Wi-Fi Transfer:" -ForegroundColor White
$IpAddress = (Get-NetIPAddress -AddressFamily IPv4 | Where-Object { $_.InterfaceAlias -match "Wi-Fi|Ethernet" -and $_.IPAddress -notmatch "^169\." -and $_.IPAddress -notmatch "^127\." } | Select-Object -First 1).IPAddress
if (-not $IpAddress) { $IpAddress = "localhost" }

Write-Host "  Download URL for phone browser:" -ForegroundColor Green
Write-Host "  http://$($IpAddress):8080/apk/$ApkName" -ForegroundColor Yellow -NoNewline
Write-Host "`n  Repository index URL for Dantotsu:" -ForegroundColor Green
Write-Host "  http://$($IpAddress):8080/index.min.json" -ForegroundColor Yellow

Write-Host "`nTo start the lightweight local transfer server on port 8080, run:" -ForegroundColor Cyan
Write-Host "  python -m http.server 8080 --directory repo" -ForegroundColor White
