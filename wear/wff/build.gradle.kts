plugins {
    id("com.android.application")
}

android {
    namespace = "com.artifact.chronology.wff"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.artifact.chronology.wff"
        minSdk = 33
        targetSdk = 34
        versionCode = 1
        versionName = "1.0.0"
    }

    buildTypes {
        release {
            isMinifyEnabled = false
        }
    }
}
