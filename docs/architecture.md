# AnimeBridge Architecture & Design Specification

> **Target System:** Dantotsu / ReDantotsu Android Client  
> **Runtime Environment:** Aniyomi Anime Extension SDK (JVM / Dalvik Executable / Android DEX)  
> **Repository Protocol:** Aniyomi v1/v2 Static JSON Index Protocol  

---

## 1. System Overview

AnimeBridge is a modular, decentralized repository of website extensions engineered specifically for **Dantotsu** and compatible Aniyomi-ecosystem Android media clients.

Unlike generic web scraping proxies, Dantotsu executes extensions **locally on the user's Android device**. Each extension is an independent, compiled Android application package (APK) implementing the Aniyomi `AnimeHttpSource` or `ParsedAnimeHttpSource` abstract interfaces.

```mermaid
graph TB
    subgraph Dantotsu Android Application
        UI[Dantotsu Browse / Search UI]
        EM[ExtensionLoader / ExtensionGithubApi]
        PCL[PathClassLoader]
    end

    subgraph AnimeBridge Distribution Repository
        IDX["repo/index.min.json<br/>(Catalog Index)"]
        APKS["repo/apk/<br/>(Compiled APKs)"]
        ICONS["repo/icon/<br/>(Extension Icons)"]
    end

    subgraph AnimeBridge Extension Module
        SRC["src/en/openmovies/<br/>(Kotlin Source)"]
        CORE[":core Module<br/>(Aniyomi SDK Stubs)"]
        MANIFEST["AndroidManifest.xml<br/>(Extension Meta-Data)"]
    end

    subgraph Remote Source
        WEB[Authorized Content Provider / Web API]
    end

    EM -->|1. Fetch index.min.json| IDX
    EM -->|2. Download APK| APKS
    EM -->|3. Fetch Icon| ICONS
    EM -->|4. Install & Load Dex| PCL
    PCL -->|5. Instantiate AnimeHttpSource| SRC
    SRC -->|6. Compile Against| CORE
    SRC -->|7. Query Media & Video Streams| WEB
```

---

## 2. Component Architecture

### 2.1 The `:core` Module (SDK Contracts)
Located in `core/`, this module supplies the authoritative Aniyomi interface definitions:
- **`AnimeSource` / `AnimeCatalogueSource`**: Base contracts for pagination, searching, and metadata.
- **`AnimeHttpSource`**: HTTP-driven base class with preconfigured `OkHttpClient`, standard headers, and request-builder lifecycle methods.
- **`ParsedAnimeHttpSource`**: Jsoup-enabled base class for DOM/CSS-selector extraction.
- **Models**:
  - `SAnime`: Canonical title, synopsis, status, genres, author, and poster URL.
  - `SEpisode`: Episode title, float episode number, release timestamp, and content URL.
  - `Video`: Direct playable stream URL, resolution label (`1080p`, `720p`, `4K`), HTTP headers, and subtitle tracks.
  - `Track`: Subtitle or secondary audio track URL and ISO language identifier.

### 2.2 Extension Modules (`src/<lang>/<extension>/`)
Each source integration lives in its own dedicated multi-project module:
```text
src/
└── en/
    └── openmovies/
        ├── AndroidManifest.xml       # Required Dantotsu manifest metadata
        ├── build.gradle.kts          # Gradle build script (AGP application plugin)
        ├── manifest.json             # Registry metadata descriptor
        ├── res/
        │   └── mipmap-xxxhdpi/
        │       └── ic_launcher.png   # 512x512 square extension icon
        └── src/
            └── eu/kanade/tachiyomi/animeextension/en/openmovies/
                └── OpenMovies.kt     # Concrete AnimeHttpSource implementation
```

### 2.3 Shared Utility Libraries (`lib/`)
Shared extractors (such as `lib/playlistutils`) provide reusable logic for parsing HLS (`.m3u8`) playlists and video embed hosts without duplicating code across extensions.

---

## 3. Extension Runtime Contract & Lifecycle

When a user searches or streams media in Dantotsu, the application executes the following lifecycle calls inside the loaded extension:

```mermaid
sequenceDiagram
    participant User as Dantotsu User
    participant App as Dantotsu Engine
    participant Ext as AnimeHttpSource (OpenMovies)
    participant Host as Source Server

    User->>App: Search for "Big Buck Bunny"
    App->>Ext: searchAnimeRequest(page=1, query="Big Buck Bunny")
    Ext->>Host: HTTP GET /catalog?q=Big+Buck+Bunny
    Host-->>Ext: JSON / HTML Response
    Ext->>Ext: searchAnimeParse(response) -> AnimesPage
    Ext-->>App: List<SAnime>
    App-->>User: Display Search Results

    User->>App: Tap Title to View Episodes
    App->>Ext: episodeListRequest(anime)
    Ext->>Host: HTTP GET /movie/details
    Host-->>Ext: Episode List Response
    Ext->>Ext: episodeListParse(response) -> List<SEpisode>
    Ext-->>App: List of Playable Episodes

    User->>App: Tap Episode to Play
    App->>Ext: videoListRequest(episode)
    Ext->>Host: HTTP GET /stream/endpoint
    Host-->>Ext: Direct Stream Links / HLS Manifest
    Ext->>Ext: videoListParse(response) -> List<Video>
    Ext-->>App: Quality Options (1080p, 720p, 4K) & Subtitles
    App->>User: Launch Video Player (ExoPlayer)
```

---

## 4. Repository Index Protocol

Dantotsu polls the repository index URL (`https://.../index.min.json`). The registry pipeline compiles this deterministically:

1. **Validation**: All manifests under `src/` are validated against `src/manifest.schema.json`.
2. **LibVersion Verification**: Confirms version code follows `<libVersion>.<extVersion>` with `libVersion` strictly within `12`–`15` (or up to `16` in modern builds).
3. **Artifact Sync**: APK files are compiled/packaged into `repo/apk/` and icons are synchronized to `repo/icon/<pkg>.png`.
4. **Deterministic Serializer**: Entries are sorted alphabetically by package ID (`pkg`) and serialized without arbitrary whitespace or random ordering into `repo/index.min.json`.

---

## 5. Security & Legal Boundaries

1. **Local Execution**: All requests originate directly from the user's device. No intermediate proxies or scraping proxies are utilized.
2. **Authorization Prerequisite**: Extensions are only developed for sources where data access is lawful, open, or explicitly permitted by terms.
3. **No Circumvention**: DRM decryption (Widevine/FairPlay), CAPTCHA solving bypasses, and paywall circumvention are prohibited.
4. **Secrets Isolation**: No user tokens, passwords, or private signing keys are embedded in source code.
