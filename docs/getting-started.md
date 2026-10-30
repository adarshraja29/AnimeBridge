# Getting Started with AnimeBridge

This guide explains how to set up your local development environment, compile Kotlin extension modules, run automated validation tests, and register your custom repository inside **Dantotsu**.

---

## 1. Prerequisites

Ensure your development machine has the following tools installed:

| Tool | Recommended Version | Purpose |
| :--- | :--- | :--- |
| **Java Development Kit (JDK)** | OpenJDK 17 or 21 LTS | Compiling Kotlin extension modules and Gradle builds |
| **Android SDK** | Platforms: API 34 (Android 14); Build Tools: 34.0.0 | Compiling Android application packages (APKs) |
| **Python** | 3.10, 3.11, or 3.12 | Running repository generators, manifest linters, and pytest |
| **Git** | 2.40+ | Version control and submodules |

---

## 2. Environment Setup

### 2.1 Clone Repository
```bash
git clone https://github.com/animebridge/animebridge.git
cd animebridge
```

### 2.2 Install Python Tooling Dependencies
The repository includes a standalone Python-based validator and contract testing harness:
```bash
python -m pip install --upgrade pip
pip install pytest jsonschema pyyaml pillow requests
```

---

## 3. Local Verification & Testing

Before building or publishing extensions, run the validation suite to ensure schema conformity and contract compliance:

### 3.1 Validate Site Configurations
```bash
python scripts/validate_sites.py --verbose
```
*Validates `config/sites.yaml` against `config/schema.json`, ensuring URL validity, capability enums, and module references.*

### 3.2 Validate Extension Manifests
```bash
python scripts/validate_manifests.py --verbose
```
*Scans all extensions in `src/<lang>/<name>`, verifying `manifest.json`, Dantotsu `libVersion` range (12–15), AndroidManifest.xml presence, and icon dimensions.*

### 3.3 Run Unit & Contract Tests
```bash
python -m pytest tests/ -v
```
*Executes all 26 test cases covering schema checks, manifest verification, search matching, empty result resilience, timeout simulation, malformed JSON handling, and index determinism.*

---

## 4. Building Extension APKs with Gradle

AnimeBridge uses a multi-project Gradle setup. You can compile all extensions or a specific module:

### 4.1 Compile the Reference Extension (Open Movies)
```bash
# On Linux / macOS:
./gradlew :src:en:openmovies:assembleRelease

# On Windows (PowerShell):
.\gradlew.bat :src:en:openmovies:assembleRelease
```
The compiled APK will be output to:
`src/en/openmovies/build/outputs/apk/release/aniyomi-en.openmovies-v14.1.apk`

---

## 5. Generating the Dantotsu Repository Index

Once extensions are ready, run the deterministic registry generator:

```bash
python scripts/build_registry.py --verbose
```

This script:
1. Validates all site configs and manifests.
2. Synchronizes APKs to `repo/apk/` and icons to `repo/icon/<pkg>.png`.
3. Compiles the minified `repo/index.min.json` and pretty `repo/index.json`.
4. Generates `repo/repo.json`.

---

## 6. Registering AnimeBridge in Dantotsu

1. Open **Dantotsu** on your Android device.
2. Tap the **Settings** icon (top right).
3. Navigate to **Extensions** $\rightarrow$ **Extension Repositories** (or tap the **+** / **GitHub** icon).
4. Enter the raw URL of your `index.min.json`:
   ```text
   https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/AnimeBridge/main/repo/index.min.json
   ```
   *(Or if using the dedicated `repo` publication branch: `https://raw.githubusercontent.com/<YOUR_GITHUB_USERNAME>/AnimeBridge/repo/index.min.json`).*
5. Tap **Add**. Dantotsu will fetch the index and populate your **Available Extensions** tab.
6. Find **Open Movies**, tap **Install**, and grant package installation permissions when prompted.
