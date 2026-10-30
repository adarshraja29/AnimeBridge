# Low-Spec Hardware Optimization Guide

> **Hardware Target:** Windows 11 Laptop  
> **Memory:** 8 GB RAM (~700 MB to 1.5 GB free physical memory)  
> **Graphics / Compute:** AMD Integrated GPU & Low-Power CPU  

This document outlines the performance profiles, memory constraints, and exact PowerShell commands designed to keep AnimeBridge fast, responsive, and crash-free without triggering disk thrashing or Out-Of-Memory (OOM) errors.

---

## 1. Summary of Optimizations

| Constraint | Optimization Strategy | Implementation |
| :--- | :--- | :--- |
| **8 GB RAM Limit** | Restrict Gradle JVM heap to **768 MB** using Serial GC | `gradle.properties`: `-Xmx768m -XX:+UseSerialGC` |
| **Low-Power CPU** | Strictly disable multi-worker parallelism | `gradle.properties`: `org.gradle.parallel=false`, `workers.max=1` |
| **Background Processes** | Disable persistent daemons & file watchers | `org.gradle.vfs.watch=false`, `idletimeout=60000`, `--no-daemon` |
| **No Android Emulators** | Physical phone testing over USB (ADB) or Wi-Fi | `scripts/deploy_to_device.ps1` |
| **Single-Module Builds** | Only compile the target extension into memory | `settings.gradle.kts`: selective `-PtargetExt` |
| **No Bloat / Frameworks** | Zero Node/Docker/Heavy database dependencies | Lightweight Python standard library + pytest + pillow |
| **Reuse Existing SDK** | Connect directly to pre-installed Android SDK | `local.properties`: `sdk.dir=...\AppData\Local\Android\Sdk` |
| **Offload Heavy Builds** | Delegate full-repo release builds to GitHub | `.github/workflows/ci.yml` (free 16 GB RAM GitHub runner) |

---

## 2. Low-Memory Gradle Profile (`gradle.properties`)

```ini
# Low-memory JVM allocation with single-threaded Serial GC (ideal for 8GB RAM laptops)
org.gradle.jvmargs=-Xmx768m -XX:+UseSerialGC -XX:SoftRefLRUPolicyMSPerMB=50 -Dfile.encoding=UTF-8

# Limit Kotlin compilation daemon
kotlin.daemon.jvmargs=-Xmx512m -XX:+UseSerialGC
kotlin.incremental=true

# Single worker thread (prevents CPU thermal throttling and memory spikes)
org.gradle.parallel=false
org.gradle.workers.max=1

# Disable memory-hungry background file watcher
org.gradle.vfs.watch=false

# Automatically terminate daemon after 60s of inactivity to return RAM to Windows
org.gradle.daemon.idletimeout=60000

# Cache build artifacts across sessions
org.gradle.caching=true
```

---

## 3. How to Build One Extension at a Time

Never build the entire multi-project repository locally on an 8 GB laptop. Instead, build only the module you are modifying.

### PowerShell Command:
```powershell
# Build only Open Movies in 1 worker with 768 MB RAM limit
.\scripts\build_single_extension.ps1 -Extension openmovies
```

This command:
1. Tells Gradle to load **only** `:src:en:openmovies` into memory.
2. Uses `--max-workers=1` and `--no-daemon`.
3. Synchronizes the compiled APK to `repo/apk/` and icon to `repo/icon/`.
4. Updates `repo/index.min.json` deterministically.
5. Displays available physical RAM before and after the build.

---

## 4. Testing on a Physical Android Phone (Zero Emulator Overhead)

Android emulators consume 3 GB–4 GB of system RAM and cause heavy GPU/CPU overhead. AnimeBridge strictly avoids emulators.

### Method A: Direct USB Installation (ADB)
1. Enable **Developer Options** and **USB Debugging** on your Android phone.
2. Connect your phone to your laptop with a USB cable.
3. Run in PowerShell:
   ```powershell
   .\scripts\deploy_to_device.ps1
   ```
   *The script automatically detects `adb.exe` in your pre-installed Android SDK and installs the APK directly.*

### Method B: Zero-Memory Local Wi-Fi Browser Transfer
If you don't have a USB cable handy, launch a lightweight transfer server:
```powershell
python -m http.server 8080 --directory repo
```
On your Android phone's web browser, open:
```text
http://<YOUR_LAPTOP_IP>:8080/apk/aniyomi-en.openmovies-v14.1.apk
```
Tap **Download** and **Install**.

---

## 5. Running Tests Locally

All 26 automated unit and contract tests run in ~1.0 second and consume less than 80 MB of RAM:

```powershell
python -m pytest tests/ -v
```

---

## 6. Full Release Builds in GitHub Actions

When you commit changes to the `main` branch, GitHub Actions executes the full compilation and distribution pipeline:
- Runs on a dedicated cloud runner with **16 GB RAM** and **4 vCPUs**.
- Validates all schemas and tests.
- Packages all extensions and builds `index.min.json`.
- Deploys release artifacts to the `repo` publication branch.
- **Cost:** 100% Free under standard GitHub open-source repositories.
