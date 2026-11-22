plugins { id("com.android.application") version "9.0.1" }

android {
    namespace = "app.blackbg"
    compileSdk { version = release(36) { minorApiLevel = 1 } }
    defaultConfig {
        applicationId = "app.blackbg"
        minSdk = 36
        targetSdk = 36
        versionCode = 1
        versionName = "1.0"
    }
}
