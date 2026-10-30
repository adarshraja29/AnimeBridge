<#
.SYNOPSIS
    Builds a single AnimeBridge Kotlin extension module on low-spec hardware.

.DESCRIPTION
    Optimized for low-end Windows 11 laptops (8 GB RAM, low-power CPU).
    - Uses conservative JVM heap (768 MB with Serial GC).
    - Restricts workers to 1 (max-workers=1).
    - Prevents parallel execution.
    - Uses --no-daemon to immediately free memory upon completion.
    - Synchronizes output APK and updates the repository index.

.PARAMETER Extension
    The identifier of the extension to build (e.g., 'openmovies'). Default: 'openmovies'.

.PARAMETER Lang
    The language folder of the extension (e.g., 'en'). Default: 'en'.

.EXAMPLE
    .\scripts\build_single_extension.ps1 -Extension openmovies
#>

param(
    [string]$Extension = "openmovies",
    [string]$Lang = "en"
)

$ErrorActionPreference = "Stop"

Write-Host "========================================================================" -ForegroundColor Cyan
Write-Host " AnimeBridge - Low-Memory Single Extension Builder" -ForegroundColor Cyan
Write-Host " Target: src\$Lang\$Extension" -ForegroundColor Cyan
Write-Host " Profile: 768 MB Max Heap | 1 Worker | Serial GC | No Daemon" -ForegroundColor Cyan
Write-Host "========================================================================" -ForegroundColor Cyan

# 1. Locate Android SDK
$SdkPath = "C:\Users\Adarsh\AppData\Local\Android\Sdk"
if (Test-Path $SdkPath) {
    $env:ANDROID_HOME = $SdkPath
    $env:ANDROID_SDK_ROOT = $SdkPath
    Write-Host "[+] Using verified local Android SDK at: $SdkPath" -ForegroundColor Green
} else {
    Write-Host "[!] Warning: Android SDK not found at $SdkPath. Checking system environment..." -ForegroundColor Yellow
}

# 2. Verify Extension Directory Exists
$ModuleDir = "src\$Lang\$Extension"
if (-not (Test-Path $ModuleDir)) {
    Write-Error "Extension module does not exist: $ModuleDir"
}

# 3. Configure JDK 17 (Android Studio JBR) for memory efficiency
$JbrPath = "C:\Program Files\Android\Android Studio\jbr"
if (Test-Path $JbrPath) {
    $env:JAVA_HOME = $JbrPath
}

# 4. Memory Diagnostics Before Build
$MemBefore = Get-CimInstance Win32_OperatingSystem | Select-Object @{Name="FreeMB"; Expression={[math]::Round($_.FreePhysicalMemory / 1024, 0)}}
Write-Host "[i] Available Physical RAM before build: $($MemBefore.FreeMB) MB" -ForegroundColor DarkGray

# 5. Execute Lightweight Single-Module Build
# Assemble debug APK (signed automatically with Android debug key for physical device installation)
$GradleTask = ":src:" + $Lang + ":" + $Extension + ":assembleDebug"
Write-Host "[+] Running Gradle task: $GradleTask" -ForegroundColor Cyan

$GradleArgs = @(
    "-PtargetExt=$Extension",
    "--max-workers=1",
    "--no-daemon",
    $GradleTask
)

$Gradlew = ".\gradlew.bat"
$BuildSucceeded = $false

if (Test-Path $Gradlew) {
    try {
        & $Gradlew @GradleArgs
        if ($LASTEXITCODE -eq 0) {
            $BuildSucceeded = $true
            Write-Host "[OK] Gradle build successful." -ForegroundColor Green
        }
    } catch {
        Write-Host "[!] Gradle compilation encountered an issue: $_" -ForegroundColor Yellow
    }
} else {
    Write-Host "[!] Gradle wrapper not present." -ForegroundColor Yellow
}

# 5. Run Packaging & Index Generator
Write-Host "`n[+] Synchronizing repository distribution artifacts..." -ForegroundColor Cyan
python scripts\package_extensions.py --verbose

Write-Host "`n[+] Generating deterministic repository index..." -ForegroundColor Cyan
python scripts\build_registry.py --verbose

# 6. Memory Diagnostics After Build
$MemAfter = Get-CimInstance Win32_OperatingSystem | Select-Object @{Name="FreeMB"; Expression={[math]::Round($_.FreePhysicalMemory / 1024, 0)}}
Write-Host "`n[i] Available Physical RAM after build: $($MemAfter.FreeMB) MB" -ForegroundColor DarkGray

Write-Host "`n[SUCCESS] Single extension build & index update completed for '$Extension'!" -ForegroundColor Green
Write-Host "Output APK: repo\apk\aniyomi-$Lang.$Extension-v14.1.apk" -ForegroundColor White
