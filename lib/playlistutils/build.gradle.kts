plugins {
    id("com.android.library")
    kotlin("android")
}

android {
    namespace = "eu.kanade.tachiyomi.lib.playlistutils"
    compileSdk = 35

    defaultConfig {
        minSdk = 21
    }

    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_1_8
        targetCompatibility = JavaVersion.VERSION_1_8
    }

    kotlinOptions {
        jvmTarget = "1.8"
    }
}

dependencies {
    compileOnly(files("$rootDir/core/libs/extensions-lib-14.jar"))
    compileOnly("com.squareup.okhttp3:okhttp:4.12.0")
}
