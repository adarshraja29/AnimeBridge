# Contributing to AnimeBridge

Thank you for contributing to **AnimeBridge**! We welcome modular extensions, bug fixes, and documentation improvements.

---

## 1. Code of Conduct & Legal Boundaries

Before contributing, ensure your proposed integration adheres to our mandatory legal and security standards:

- **Authorized Sources Only**: Only submit extensions for websites you own, authorized partners, public domain archives, or sources explicitly permitting automated programmatic access under open licenses (e.g., Creative Commons, CC0).
- **Strictly Prohibited**:
  - No DRM circumvention (Widevine, FairPlay, PlayReady).
  - No paywall bypass or subscription hacking.
  - No Cloudflare Turnstile, CAPTCHA, or anti-bot circumvention mechanisms.
  - No credential theft or token scraping.
  - No distribution of copyright-infringing commercial broadcasts.

---

## 2. Development Workflow

1. **Fork the Repository** on GitHub.
2. **Create a Feature Branch**:
   ```bash
   git checkout -b feature/add-source-xyz
   ```
3. **Register Site Request in `config/sites.yaml`**:
   Ensure all fields (id, name, homepage, authorization, license, capabilities) are provided.
4. **Create the Extension Module in `src/<lang>/<source_id>/`**:
   - `build.gradle.kts`: Declares `applicationId = "eu.kanade.tachiyomi.animeextension.<lang>.<source_id>"` and version `<libVersion>.<extVersion>`.
   - `AndroidManifest.xml`: Declares entry class and metadata flags.
   - `manifest.json`: Follows `src/manifest.schema.json`.
   - `res/mipmap-xxxhdpi/ic_launcher.png`: Clean, square 512x512 PNG icon.
   - `src/eu/kanade/tachiyomi/animeextension/<lang>/<source_id>/...`: Concrete Kotlin source extending `AnimeHttpSource` or `ParsedAnimeHttpSource`.
5. **Run Validation and Tests**:
   ```bash
   python scripts/validate_sites.py
   python scripts/validate_manifests.py
   python -m pytest tests/ -v
   ```
6. **Compile the Repository Registry**:
   ```bash
   python scripts/build_registry.py --verbose
   ```
7. **Commit and Push**:
   ```bash
   git commit -m "feat(extension): add xyz source extension"
   git push origin feature/add-source-xyz
   ```
8. **Open a Pull Request**.

---

## 3. Pull Request Checklist

Before submitting your PR, verify each item:

- [ ] All new code is written in **Kotlin** and targets the Aniyomi `AnimeHttpSource` or `ParsedAnimeHttpSource` contract.
- [ ] Package name follows `eu.kanade.tachiyomi.animeextension.<lang>.<identifier>`.
- [ ] Extension version follows `<libVersion>.<extVersion>` where `libVersion` is between `12` and `15`.
- [ ] `config/sites.yaml` is updated with full legal authorization rationale.
- [ ] An icon is provided as a square 512x512 PNG in `res/mipmap-xxxhdpi/ic_launcher.png`.
- [ ] `python scripts/validate_sites.py` succeeds without errors.
- [ ] `python scripts/validate_manifests.py` succeeds without errors.
- [ ] `python -m pytest tests/ -v` passes 100%.
- [ ] The extension has been tested on a device or Android emulator running Dantotsu.
- [ ] No hardcoded passwords, tokens, API secrets, or cookies are committed.
