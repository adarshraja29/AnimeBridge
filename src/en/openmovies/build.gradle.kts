plugins {
    id("com.android.application")
    kotlin("android")
    kotlin("plugin.serialization")
}

val extName = "Open Movies"
val extClass = ".OpenMovies"
val extVersionCode = 1
val libVersion = "14"

android {
    namespace = "eu.kanade.tachiyomi.animeextension.en.openmovies"
    compileSdk = 35

    defaultConfig {
        minSdk = 21
        targetSdk = 35
        applicationId = "eu.kanade.tachiyomi.animeextension.en.openmovies"
        versionCode = extVersionCode
        versionName = "$libVersion.$extVersionCode"

        base {
            archivesName.set("aniyomi-en.openmovies-v$versionName")
        }

        manifestPlaceholders["appName"] = "Aniyomi: $extName"
        manifestPlaceholders["extClass"] = "eu.kanade.tachiyomi.animeextension.en.openmovies.OpenMovies"
        manifestPlaceholders["nsfw"] = 0
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
        freeCompilerArgs += "-opt-in=kotlinx.serialization.ExperimentalSerializationApi"
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
    implementation(project(":lib:playlistutils"))
    compileOnly("com.squareup.okhttp3:okhttp:4.12.0")
    compileOnly("org.jetbrains.kotlinx:kotlinx-serialization-json:1.6.3")
    compileOnly("org.jsoup:jsoup:1.17.2")
}
