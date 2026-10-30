# Dantotsu Compatibility & Ecosystem Specification

> **Status:** Verified against official Dantotsu / ReDantotsu source code and Aniyomi Extension SDK.
> **Last Verified:** October 2026

---

## 1. Executive Summary & Verification Scope

This document records the exact architectural requirements, runtime interfaces, repository indexing schemas, and package constraints required for extensions to be recognized, installed, and executed within **Dantotsu** and compatible Android applications (e.g., ReDantotsu, Aniyomi).

To guarantee strict compliance and avoid architectural assumptions, the findings below have been directly verified against the authoritative codebase of Dantotsu/ReDantotsu (`eu.kanade.tachiyomi.extension.api.ExtensionGithubApi` and `eu.kanade.tachiyomi.extension.util.ExtensionLoader`).

---

## 2. Verified Facts vs. Assumptions

| Domain | Verified Fact | Source Reference |
| :--- | :--- | :--- |
| **Target Architecture** | Dantotsu does **not** scrape anime websites internally; it utilizes the **Aniyomi Anime Extension runtime** via dynamic Android Dex loading (`dalvik.system.PathClassLoader`). | `ExtensionLoader.kt#L240-L245` |
| **Extension Language** | Extensions must be compiled to JVM/Dex bytecode targeting Android; Kotlin is the official and standard implementation language. Python is **not** supported natively on Android without embedding a heavy Python runtime (which is not present in Dantotsu). | Android Dex runtime / `ExtensionLoader.kt` |
| **Repository Discovery** | Dantotsu loads extension catalogs by requesting an `index.min.json` file over HTTP(S). If a repository URL lacks `index.min.json`, Dantotsu automatically appends `/index.min.json`. | `ExtensionGithubApi.kt#L107-L113` |
| **Repository Fallback** | When a GitHub raw request fails, Dantotsu falls back to `https://gcore.jsdelivr.net/gh/<owner>/<repo>@<branch>/index.min.json`. | `ExtensionGithubApi.kt#L117-L121` |
| **Lib Version Constraint** | Dantotsu parses the extension version name (`<libVersion>.<extVersion>`). It enforces `ANIME_LIB_VERSION_MIN = 12` and `ANIME_LIB_VERSION_MAX = 15` (up to 16 in latest builds). Any extension outside this range is silently discarded or rejected with a log entry. | `ExtensionGithubApi.kt#L41-L45`, `ExtensionLoader.kt#L64-L65, L225-L230` |
| **Package Naming** | Extension Android package names must follow the convention: `eu.kanade.tachiyomi.animeextension.<lang>.<identifier>`. | `ExtensionLoader.kt#L57` |
| **Name Prefix** | Dantotsu expects or strips the prefix `"Aniyomi: "` from the extension display name: `extName = pkgManager.getApplicationLabel(appInfo).toString().substringAfter("Aniyomi: ")`. | `ExtensionLoader.kt#L218` |
| **APK Hosting Path** | APK files are downloaded from `${repository.removeSuffix("index.min.json")}/apk/${extension.apkName}`. | `ExtensionGithubApi.kt#L145` |
| **Icon Hosting Path** | Icons are retrieved from `${repository.removeSuffix("/index.min.json")}/icon/${it.pkg}.png`. | `ExtensionGithubApi.kt#L59` |
| **Android Manifest Meta-Data** | Dantotsu reads source classes from `AndroidManifest.xml` via key `tachiyomi.animeextension.class`. It also checks `tachiyomi.animeextension.nsfw`, `tachiyomi.animeextension.hasReadme`, and `tachiyomi.animeextension.hasChangelog`. | `ExtensionLoader.kt#L59-L63, L248-L260` |

---

## 3. Extension Repository Protocol (The Index Schema)

Dantotsu parses repository indices using `kotlinx.serialization.json.Json` with the following data contract:

### 3.1 Repository Structure on GitHub / Static Host
```text
AnimeBridge/
├── repo/
│   ├── index.min.json     # Minified JSON index consumed by Dantotsu
│   ├── index.json         # Human-readable formatted index
│   ├── repo.json          # Repository metadata and signing key information
│   ├── apk/               # Compiled Android APKs (.apk)
│   │   └── aniyomi-en.openmovies-v14.1.apk
│   └── icon/              # Extension icons (.png)
│       └── eu.kanade.tachiyomi.animeextension.en.openmovies.png
```

### 3.2 `index.min.json` Item Schema
Each element in the root JSON array conforms to:

```json
[
  {
    "name": "Aniyomi: Open Movies",
    "pkg": "eu.kanade.tachiyomi.animeextension.en.openmovies",
    "apk": "aniyomi-en.openmovies-v14.1.apk",
    "lang": "en",
    "code": 1,
    "version": "14.1",
    "nsfw": 0,
    "hasReadme": 0,
    "hasChangelog": 0,
    "sources": [
      {
        "id": 841920391823901,
        "name": "Open Movies Archive",
        "lang": "en",
        "baseUrl": "https://download.blender.org"
      }
    ]
  }
]
```

#### Field Specifications:
- `name` *(string, required)*: Display title, prefixed with `Aniyomi: `.
- `pkg` *(string, required)*: Android Application ID matching `eu.kanade.tachiyomi.animeextension.<lang>.<id>`.
- `apk` *(string, required)*: Relative filename inside the `/apk/` folder.
- `lang` *(string, required)*: ISO 639-1 language code (e.g. `en`, `ja`, `all`).
- `code` *(integer, required)*: Android `versionCode` (monotonically increasing integer).
- `version` *(string, required)*: Must be formatted as `<libVersion>.<extVersion>` (e.g., `14.1`).
- `nsfw` *(integer, required)*: `0` for safe content, `1` for adult content.
- `hasReadme` *(integer, optional)*: `1` if repository hosts a readme document.
- `hasChangelog` *(integer, optional)*: `1` if repository hosts changelog metadata.
- `sources` *(array of objects, required)*: Array of catalog sources provided by this extension.
  - `id` *(integer/long, required)*: Unique 64-bit integer ID generated from the source name and language hash.
  - `name` *(string, required)*: Catalog display title.
  - `lang` *(string, required)*: Language identifier matching extension or sub-catalog.
  - `baseUrl` *(string, required)*: Base HTTP(S) URL of the source website without trailing slash.

---

## 4. Extension Android Package (APK) Specification

When an extension APK is installed, Android's `PackageManager` inspects `AndroidManifest.xml`. Dantotsu queries `appInfo.metaData` for specific keys:

### 4.1 Required `AndroidManifest.xml` Meta-Data
```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="eu.kanade.tachiyomi.animeextension.en.openmovies">

    <application
        android:label="Aniyomi: Open Movies"
        android:icon="@mipmap/ic_launcher">

        <!-- FQCN of the AnimeHttpSource or AnimeSourceFactory implementation -->
        <meta-data
            android:name="tachiyomi.animeextension.class"
            android:value="eu.kanade.tachiyomi.animeextension.en.openmovies.OpenMovies" />

        <!-- NSFW Flag: 0 = Clean, 1 = 18+ -->
        <meta-data
            android:name="tachiyomi.animeextension.nsfw"
            android:value="0" />

        <meta-data
            android:name="tachiyomi.animeextension.hasReadme"
            android:value="0" />

        <meta-data
            android:name="tachiyomi.animeextension.hasChangelog"
            android:value="0" />

    </application>
</manifest>
```

---

## 5. Runtime Interfaces & Kotlin SDK Contract

Extensions run inside Dantotsu's process using `PathClassLoader`. The entry class specified in `tachiyomi.animeextension.class` must extend `eu.kanade.tachiyomi.animesource.online.AnimeHttpSource` or `ParsedAnimeHttpSource`.

### 5.1 Key Lifecycle & Query Methods
```kotlin
package eu.kanade.tachiyomi.animesource.online

import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SEpisode
import eu.kanade.tachiyomi.animesource.model.Video
import okhttp3.OkHttpClient
import okhttp3.Request
import okhttp3.Response

abstract class AnimeHttpSource : AnimeCatalogueSource {
    abstract override val name: String
    abstract override val baseUrl: String
    abstract override val lang: String
    abstract override val supportsLatest: Boolean

    // Network client
    open val client: OkHttpClient

    // Catalog Methods
    abstract fun popularAnimeRequest(page: Int): Request
    abstract fun popularAnimeParse(response: Response): AnimesPage

    abstract fun latestUpdatesRequest(page: Int): Request
    abstract fun latestUpdatesParse(response: Response): AnimesPage

    abstract fun searchAnimeRequest(page: Int, query: String, filters: AnimeFilterList): Request
    abstract fun searchAnimeParse(response: Response): AnimesPage

    // Details & Episodes
    abstract fun animeDetailsParse(response: Response): SAnime
    abstract fun episodeListParse(response: Response): List<SEpisode>

    // Video Streams & Subtitles
    abstract fun videoListParse(response: Response): List<Video>
}
```

---

## 6. Registration Flow in Dantotsu

Users register custom repositories using the following verified in-app path:

1. Launch **Dantotsu**.
2. Tap the **Settings** icon (top right or navigation drawer).
3. Navigate to **Extensions** $\rightarrow$ **Extension Repositories** (or tap the **+** / **GitHub** icon).
4. Enter the raw URL pointing to `index.min.json`:
   ```text
   https://raw.githubusercontent.com/<OWNER>/AnimeBridge/main/repo/index.min.json
   ```
   *(Alternatively, entering `https://raw.githubusercontent.com/<OWNER>/AnimeBridge/main/repo` will automatically be resolved to `/index.min.json` by Dantotsu's URI normalizer).*
5. Dantotsu performs a `GET` request, decodes the JSON array, filters out incompatible `libVersion` entries, and populates the **Available Extensions** tab.
6. When the user taps **Install**, Dantotsu downloads the `.apk` from `/apk/<apkName>`, invokes Android's package installer, and initializes the extension via `PathClassLoader`.
