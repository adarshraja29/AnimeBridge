pluginManagement {
    repositories {
        google()
        mavenCentral()
        gradlePluginPortal()
    }
}

dependencyResolutionManagement {
    repositoriesMode.set(RepositoriesMode.PREFER_PROJECT)
    repositories {
        google()
        mavenCentral()
        maven { url = java.net.URI("https://jitpack.io") }
    }
}

rootProject.name = "AnimeBridge"

include(":core")
include(":lib:playlistutils")

// -----------------------------------------------------------------------------
// Low-Memory Optimization: Selective Module Loading
// When targetExt is provided via CLI (-PtargetExt=name) or environment variable,
// Gradle loads ONLY the specified extension into memory.
// -----------------------------------------------------------------------------
val targetExt: String? = (extra.properties["targetExt"] as? String)
    ?: System.getenv("ANIMEBRIDGE_TARGET_EXT")

if (!targetExt.isNullOrBlank()) {
    var found = false
    file("src").listFiles()?.filter { it.isDirectory }?.forEach { langDir ->
        val extDir = File(langDir, targetExt)
        if (extDir.exists() && File(extDir, "build.gradle.kts").exists()) {
            include(":src:${langDir.name}:${extDir.name}")
            found = true
        }
    }
    if (!found) {
        println("[AnimeBridge] Warning: Target extension '$targetExt' not found under src/*/$targetExt. Falling back to 'openmovies'.")
        include(":src:en:openmovies")
    }
} else {
    // Multi-module discovery mode (used by CI or full repository builds)
    file("src").listFiles()?.filter { it.isDirectory }?.forEach { langDir ->
        langDir.listFiles()?.filter { it.isDirectory && File(it, "build.gradle.kts").exists() }?.forEach { extDir ->
            include(":src:${langDir.name}:${extDir.name}")
        }
    }
}
