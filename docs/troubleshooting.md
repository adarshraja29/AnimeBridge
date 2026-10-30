# Troubleshooting Guide for Dantotsu & AnimeBridge

This guide provides practical solutions for common errors encountered when hosting, installing, or executing extensions in **Dantotsu**.

---

## 1. Repository Rejected by Dantotsu

### Symptom:
When pasting the repository URL into Dantotsu's **Add Repository** prompt, the app displays:
`"Failed to add repository"` or `"Invalid repository URL"`.

### Root Causes & Fixes:
1. **Incorrect URL Format**:
   - **Correct URL**: Ensure you are using the **raw** GitHub link pointing directly to `index.min.json`:
     ```text
     https://raw.githubusercontent.com/<OWNER>/AnimeBridge/main/repo/index.min.json
     ```
   - **Incorrect URL**: Do not enter GitHub web links like `https://github.com/<OWNER>/AnimeBridge/blob/main/repo/index.min.json` (these return an HTML webpage instead of raw JSON).
2. **Repository is Private**:
   - Dantotsu cannot authenticate against private GitHub repositories without an access token. Ensure your repository or publication branch is set to **Public**.
3. **Branch Name Mismatch**:
   - Check whether your primary branch is `main` or `master`. Replace the branch name in the URL accordingly.

---

## 2. Empty Extension List in Available Tab

### Symptom:
The repository is accepted, but the **Available Extensions** list remains completely blank.

### Root Causes & Fixes:
1. **LibVersion Filtering in Dantotsu**:
   - Dantotsu strictly validates extension versions using:
     ```kotlin
     val libVersion = versionName.substringBeforeLast('.').toDoubleOrNull()
     if (libVersion == null || libVersion < ANIME_LIB_VERSION_MIN || libVersion > ANIME_LIB_VERSION_MAX) {
         // Silently drops extension from list!
     }
     ```
   - **Fix**: Check `version` in `manifest.json`. It **must** start with `14.` (or between `12.` and `15.`). For example: `14.1`. Versions like `1.0.0` or `2.1` will be discarded immediately by Dantotsu.
2. **Duplicate Package Name**:
   - If an extension with the same package name (e.g., `eu.kanade.tachiyomi.animeextension.en.openmovies`) is already installed or listed in another repository, Dantotsu deduplicates it.
3. **Invalid JSON in `index.min.json`**:
   - Verify `repo/index.min.json` by running:
     ```bash
     python -m json.tool repo/index.min.json
     ```

---

## 3. Installation Failures (APK Not Installed)

### Symptom:
Tapping **Install** downloads the APK, but Android reports `"App not installed"` or `"Package corrupted"`.

### Root Causes & Fixes:
1. **Package Architecture & Signing**:
   - Android requires APKs to be signed (even with a test key). Unsigned APKs cannot be installed by Android's package manager.
   - For local builds, compile via Gradle (`./gradlew assembleRelease`) or ensure the debug key is used.
2. **Conflicting Signatures**:
   - If an older version was installed with a different keystore, Android will block the update.
   - **Fix**: Uninstall the existing extension from Android Settings $\rightarrow$ Apps $\rightarrow$ [Extension Name], then re-install.
3. **Missing Android Permissions**:
   - Ensure Dantotsu has the `"Install unknown apps"` permission enabled in Android App Settings.

---

## 4. Extension Load Errors / Crash on Open

### Symptom:
The extension installs successfully, but opening it displays:
`"Extension load error"` or `"Class not found"`.

### Root Causes & Fixes:
1. **Manifest Meta-Data Mismatch**:
   - In `AndroidManifest.xml`, check the meta-data value:
     ```xml
     <meta-data
         android:name="tachiyomi.animeextension.class"
         android:value="eu.kanade.tachiyomi.animeextension.en.openmovies.OpenMovies" />
     ```
   - The value must match the exact Fully Qualified Class Name (FQCN) of your compiled Kotlin class.
2. **Class Not Implementing `AnimeSource`**:
   - The entry class must extend `eu.kanade.tachiyomi.animesource.online.AnimeHttpSource` or implement `eu.kanade.tachiyomi.animesource.AnimeSource`.

---

## 5. Connector Timeouts & Network Failures

### Symptom:
Browsing or searching displays `"Network timeout"` or spinner spins indefinitely.

### Root Causes & Fixes:
1. **Cloudflare / Anti-Bot Protection**:
   - Some streaming platforms block OkHttpClient default headers.
   - Ensure custom User-Agent headers are set in `override val headers`.
2. **Connection Timeout Settings**:
   - In your Kotlin class, configure generous timeouts:
     ```kotlin
     override val client: OkHttpClient = OkHttpClient.Builder()
         .connectTimeout(20, TimeUnit.SECONDS)
         .readTimeout(20, TimeUnit.SECONDS)
         .build()
     ```
3. **SSL / TLS Certificate Issues**:
   - If the source website uses outdated SSL ciphers, OkHttp on older Android versions may reject the connection.

---

## 6. Missing Metadata or Blank Episodes

### Symptom:
Anime details page loads, but episodes list is empty.

### Root Causes & Fixes:
1. **HTML Structure Change**:
   - For `ParsedAnimeHttpSource`, the target site may have altered its DOM structure.
   - Run tests against updated HTML fixtures to verify CSS selectors.
2. **Reversed Episode Ordering**:
   - Aniyomi expects episode lists ordered with the latest episode first. If episodes appear in reverse order, call `.reversed()` in `episodeListParse()`.
