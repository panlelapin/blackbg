plugins { id("com.android.application") }

val signingMode = providers.environmentVariable("BLACKBG_SIGNING_MODE").orNull
if (signingMode == "personal") {
    layout.buildDirectory.set(layout.projectDirectory.dir("build/personal"))
}

android {
    namespace = "app.blackbg"
    ndkVersion = "30.0.16248370"
    compileSdk { version = release(37) { minorApiLevel = 1 } }
    defaultConfig {
        applicationId = "app.blackbg"
        minSdk = 36
        targetSdk = 37
        versionCode = 3
        versionName = "1.0.2"
        ndk { abiFilters += "arm64-v8a" }
    }
    externalNativeBuild {
        cmake {
            path = file("src/main/cpp/CMakeLists.txt")
            version = "3.22.1"
        }
    }
    signingConfigs {
        if (signingMode != null) create("localRelease") {
            require(signingMode in setOf("release", "personal"))
            val directory = file("${providers.environmentVariable("HOME").get()}/.android/blackbg-$signingMode")
            storeFile = directory.resolve("release.p12")
            val password = directory.resolve("password").readText().trim()
            storePassword = password
            keyAlias = "blackbg"
            keyPassword = password
        }
    }
    buildTypes {
        release {
            isMinifyEnabled = true
            isShrinkResources = true
            proguardFiles(getDefaultProguardFile("proguard-android-optimize.txt"))
            signingConfig = signingConfigs.findByName("localRelease")
        }
    }
}
