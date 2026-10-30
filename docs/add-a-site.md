# How to Add a Website Integration to AnimeBridge

This guide explains how to propose, implement, test, and package a new website integration for AnimeBridge.

---

## 1. Architectural Rule: Configuration vs. Implementation

> [!IMPORTANT]
> **Adding a URL to `config/sites.yaml` DOES NOT implement an integration in Dantotsu.**
> 
> A website configuration entry registers metadata and authorization status. A functional integration requires creating and compiling a dedicated Kotlin extension module implementing `AnimeHttpSource` or `ParsedAnimeHttpSource`.

---

## 2. Step 1: Register the Request in `config/sites.yaml`

Add an entry to `config/sites.yaml` under the `sites:` list:

```yaml
  - id: "my-source"
    name: "My Source Catalog"
    homepage: "https://mysource.example.org"
    connector_id: "mysource"
    enabled: false # Keep false until implementation and tests are complete
    authorization:
      type: "open_api" # Or creative_commons, public_domain, developer_owned
      license: "Open API Data License"
      notes: "Public read-only REST API provided by the platform for third-party client integrations."
    capabilities:
      - "search"
      - "metadata"
      - "episodes"
      - "playback"
      - "health_check"
    language:
      code: "en"
      name: "English"
    connector_version: "14.1"
    status: "beta"
```

Validate your YAML changes:
```bash
python scripts/validate_sites.py --file config/sites.yaml
```

---

## 3. Step 2: Create the Kotlin Extension Module

Create the directory structure under `src/<lang>/<connector_id>`:

```bash
mkdir -p src/en/mysource/src/eu/kanade/tachiyomi/animeextension/en/mysource
mkdir -p src/en/mysource/res/mipmap-xxxhdpi
```

### 3.1 Create `src/en/mysource/build.gradle.kts`
```kotlin
plugins {
    id("com.android.application")
    kotlin("android")
    kotlin("plugin.serialization")
}

val extName = "My Source"
val extClass = ".MySource"
val extVersionCode = 1
val libVersion = "14"

android {
    namespace = "eu.kanade.tachiyomi.animeextension.en.mysource"
    compileSdk = 34

    defaultConfig {
        minSdk = 21
        targetSdk = 34
        applicationId = "eu.kanade.tachiyomi.animeextension.en.mysource"
        versionCode = extVersionCode
        versionName = "$libVersion.$extVersionCode"

        base {
            archivesName.set("aniyomi-en.mysource-v$versionName")
        }

        manifestPlaceholders["appName"] = "Aniyomi: $extName"
        manifestPlaceholders["extClass"] = "eu.kanade.tachiyomi.animeextension.en.mysource.MySource"
        manifestPlaceholders["nsfw"] = 0
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }

    sourceSets {
        getByName("main") {
            manifest.srcFile("AndroidManifest.xml")
            java.srcDirs("src")
            res.srcDirs("res")
        }
    }
}

dependencies {
    compileOnly(files("$rootDir/core/libs/extensions-lib-14.jar"))
    compileOnly("com.squareup.okhttp3:okhttp:4.12.0")
    compileOnly("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
    compileOnly("org.jsoup:jsoup:1.17.2")
}
```

### 3.2 Create `src/en/mysource/AndroidManifest.xml`
```xml
<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="eu.kanade.tachiyomi.animeextension.en.mysource">

    <application
        android:label="Aniyomi: My Source"
        android:icon="@mipmap/ic_launcher">

        <meta-data
            android:name="tachiyomi.animeextension.class"
            android:value="eu.kanade.tachiyomi.animeextension.en.mysource.MySource" />

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

### 3.3 Create `src/en/mysource/manifest.json`
```json
{
  "id": "mysource",
  "name": "My Source",
  "pkg": "eu.kanade.tachiyomi.animeextension.en.mysource",
  "version": "14.1",
  "code": 1,
  "lang": "en",
  "nsfw": 0,
  "class": "eu.kanade.tachiyomi.animeextension.en.mysource.MySource",
  "sources": [
    {
      "id": 1928374829102,
      "name": "My Source Catalog",
      "lang": "en",
      "baseUrl": "https://mysource.example.org"
    }
  ],
  "capabilities": ["search", "metadata", "episodes", "playback", "health_check"],
  "apk": "aniyomi-en.mysource-v14.1.apk",
  "icon": "res/mipmap-xxxhdpi/ic_launcher.png",
  "description": "Integration for My Source authorized catalog."
}
```

### 3.4 Place Icon
Place a square 512x512 PNG at `src/en/mysource/res/mipmap-xxxhdpi/ic_launcher.png`.

---

## 4. Step 3: Implement the Source Class in Kotlin

Implement your class extending `AnimeHttpSource` (for JSON APIs) or `ParsedAnimeHttpSource` (for HTML scraping):

```kotlin
package eu.kanade.tachiyomi.animeextension.en.mysource

import eu.kanade.tachiyomi.animesource.model.AnimeFilterList
import eu.kanade.tachiyomi.animesource.model.AnimesPage
import eu.kanade.tachiyomi.animesource.model.SAnime
import eu.kanade.tachiyomi.animesource.model.SEpisode
import eu.kanade.tachiyomi.animesource.model.Video
import eu.kanade.tachiyomi.animesource.online.AnimeHttpSource
import okhttp3.Request
import okhttp3.Response

class MySource : AnimeHttpSource() {
    override val name = "My Source"
    override val baseUrl = "https://mysource.example.org"
    override val lang = "en"
    override val supportsLatest = true

    override fun popularAnimeRequest(page: Int): Request =
        Request.Builder().url("$baseUrl/api/popular?page=$page").build()

    override fun popularAnimeParse(response: Response): AnimesPage {
        // Parse JSON or HTML
        return AnimesPage(emptyList(), false)
    }

    override fun latestUpdatesRequest(page: Int): Request =
        Request.Builder().url("$baseUrl/api/latest?page=$page").build()

    override fun latestUpdatesParse(response: Response): AnimesPage =
        popularAnimeParse(response)

    override fun searchAnimeRequest(page: Int, query: String, filters: AnimeFilterList): Request =
        Request.Builder().url("$baseUrl/api/search?q=$query&page=$page").build()

    override fun searchAnimeParse(response: Response): AnimesPage =
        popularAnimeParse(response)

    override fun animeDetailsParse(response: Response): SAnime {
        // Extract metadata
        return SAnime.create().apply {
            title = "Title"
            initialized = true
        }
    }

    override fun episodeListParse(response: Response): List<SEpisode> {
        // Extract episodes
        return emptyList()
    }

    override fun videoListParse(response: Response): List<Video> {
        // Return direct playable streams with quality labels
        return emptyList()
    }
}
```

---

## 5. Step 4: Validate, Compile & Package

1. Validate the new manifest:
   ```bash
   python scripts/validate_manifests.py
   ```
2. Set `enabled: true` in `config/sites.yaml`.
3. Build the repository index:
   ```bash
   python scripts/build_registry.py --verbose
   ```
4. Verify that `repo/index.min.json` contains your new extension and `repo/apk/aniyomi-en.mysource-v14.1.apk` is present.
5. Test in Dantotsu on an Android device to confirm search, details, and video playback work as expected.
