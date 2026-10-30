# AnimeBridge

[![CI & Extension Build Pipeline](https://github.com/animebridge/animebridge/actions/workflows/ci.yml/badge.svg)](https://github.com/animebridge/animebridge/actions/workflows/ci.yml)
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Compatibility](https://img.shields.io/badge/Dantotsu-Verified%20Compatible-brightgreen.svg)](docs/compatibility.md)
[![Aniyomi SDK](https://img.shields.io/badge/Aniyomi%20Extension%20Lib-v14-orange.svg)](docs/compatibility.md)

**AnimeBridge** is a modular, decentralized repository of website connectors and extensions compatible with the **Dantotsu** Android client (and compatible Aniyomi-ecosystem clients).

Unlike fragile scraping proxies, AnimeBridge provides **first-class Kotlin Android extensions** that compile into APKs, load dynamically via Dantotsu's Dex ClassLoader runtime, and query media directly on the user's device.

---

## 🚀 Quick Start: Adding to Dantotsu

To browse and install AnimeBridge extensions inside Dantotsu:

1. Open **Dantotsu**.
2. Go to **Settings** $\rightarrow$ **Extensions** $\rightarrow$ **Extension Repositories** (or tap the **+** / **GitHub** icon).
3. Paste the raw repository index URL:
   ```text
   https://raw.githubusercontent.com/<OWNER>/AnimeBridge/main/repo/index.min.json
   ```
4. Confirm. The catalog of available extensions will populate in your app.

---

## 🌟 Key Features

- **Strict Dantotsu Compatibility**: Implements the official Aniyomi `AnimeHttpSource` and `ParsedAnimeHttpSource` interfaces verified against Dantotsu's `ExtensionGithubApi` and `ExtensionLoader`.
- **Enforced LibVersion Boundaries**: Complies with Dantotsu's accepted extension library range (`12`–`15`), preventing silent drops or missing extensions.
- **Deterministic Registry Generation**: Compiles `repo/index.min.json` and `repo/index.json` with strict sorting and deduplication.
- **Automated Validation Pipeline**: Python-powered linters and a 26-test suite verify schemas, package naming, icon sizes, and connector contracts before any extension is published.
- **Production Reference Extension**: Includes **Open Movies Archive** (`src/en/openmovies`), a fully functional, legally authorized extension providing Creative Commons open-source films (Big Buck Bunny, Sintel, etc.) with 1080p/720p/4K streams and subtitles.
- **Zero-Cloud Hosting**: Free to build and host using GitHub's native features and GitHub Actions.

---

## 📁 Repository Structure

```text
AnimeBridge/
├── config/
│   ├── schema.json               # Strict schema for sites.yaml
│   ├── sites.yaml                # Active site configuration registry
│   └── sites.example.yaml        # Documented configuration template
├── core/                         # Kotlin Aniyomi Extension Core Library
│   ├── build.gradle.kts
│   └── src/main/kotlin/eu/kanade/tachiyomi/animesource/
│       ├── AnimeSource.kt        # Core extension contracts
│       ├── model/Models.kt       # SAnime, SEpisode, Video, Track
│       └── online/               # AnimeHttpSource, ParsedAnimeHttpSource
├── lib/
│   └── playlistutils/            # Shared HLS/M3U8 extraction utilities
├── src/                          # Multi-project Kotlin extension modules
│   ├── manifest.schema.json      # Schema for extension manifests
│   └── en/
│       └── openmovies/           # Reference Open Movies extension
│           ├── AndroidManifest.xml
│           ├── build.gradle.kts
│           ├── manifest.json
│           ├── res/mipmap-xxxhdpi/ic_launcher.png
│           └── src/.../OpenMovies.kt
├── repo/                         # Distribution repository (consumed by Dantotsu)
│   ├── index.min.json            # Minified JSON index
│   ├── index.json                # Pretty-printed index
│   ├── repo.json                 # Repository metadata
│   ├── apk/                      # Distribution APK files
│   └── icon/                     # Distribution PNG icons
├── scripts/                      # Automated validation & publishing CLI
│   ├── validate_sites.py         # Validates config/sites.yaml
│   ├── validate_manifests.py     # Validates src/**/manifest.json
│   ├── package_extensions.py     # Packages APKs and icons to repo/
│   └── build_registry.py         # Generates deterministic index.min.json
├── tests/                        # 26 automated unit & contract tests
├── tools/                        # Python testing contracts & mock models
├── docs/                         # Authoritative documentation
│   ├── compatibility.md          # Verified Dantotsu specifications
│   ├── architecture.md           # Architecture, data flow & sequence diagrams
│   ├── getting-started.md        # Prerequisites and local setup
│   ├── add-a-site.md             # Guide to implementing new Kotlin extensions
│   ├── sites-to-add.md           # 9-step integration evaluation lifecycle
│   └── troubleshooting.md        # Solutions for common Dantotsu errors
├── .github/workflows/
│   └── ci.yml                    # Automated build, test, and release pipeline
├── CONTRIBUTING.md               # Contribution workflow & PR checklist
├── SECURITY.md                   # Vulnerability reporting & secrets policy
└── LICENSE                       # Apache License 2.0
```

---

## 🛠️ Development & Testing (Low-Spec Windows 11 Profile)

Optimized for **8 GB RAM laptops** with single-worker execution, Serial GC (768 MB heap), and zero emulator overhead:

### 1. Build a Single Extension (Low Memory)
```powershell
.\scripts\build_single_extension.ps1 -Extension openmovies
```

### 2. Deploy to a Physical Android Phone (Zero Emulator)
```powershell
# Auto-detects phone via USB (ADB) or provides instant local Wi-Fi download link:
.\scripts\deploy_to_device.ps1
```

### 3. Run Automated Validation & Test Suite (< 80 MB RAM, ~1 sec)
```bash
# Validate configurations and manifests
python scripts/validate_sites.py --verbose
python scripts/validate_manifests.py --verbose

# Run all 26 unit and contract tests
python -m pytest tests/ -v
```

### 4. Generate the Repository Index
```bash
python scripts/build_registry.py --verbose
```

---

## 📖 Documentation Quick Links

- [Dantotsu Compatibility Findings & Source Analysis](docs/compatibility.md)
- [Low-Spec Windows 11 Optimization Guide](docs/low-spec-optimization.md)
- [Architecture & Data Flow Specification](docs/architecture.md)
- [Local Setup & Build Instructions](docs/getting-started.md)
- [How to Add a New Website Extension](docs/add-a-site.md)
- [Integration Request Queue & Evaluation Lifecycle](docs/sites-to-add.md)
- [Troubleshooting & FAQ](docs/troubleshooting.md)
- [Contributing Guidelines](CONTRIBUTING.md)
- [Security Policy](SECURITY.md)

---

## ⚖️ Legal & Security Compliance

- **No DRM Circumvention**: AnimeBridge does not bypass DRM (Widevine, FairPlay, PlayReady) or copyright protections.
- **No Paywalls or Authentication Bypasses**: Bypassing logins, paid subscriptions, or CAPTCHA gates is strictly forbidden.
- **Authorized Sources Only**: The included reference connector sources media from the Blender Foundation open-source movies archive released under Creative Commons Attribution (CC-BY).
- **Privacy & Secrets**: No user tokens, tracking identifiers, or private keys are stored.

---

## 📄 License

AnimeBridge is licensed under the [Apache License 2.0](LICENSE).
