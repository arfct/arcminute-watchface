import java.util.Properties

plugins {
    id("com.android.application")
}

// Upload-key signing: wear/keystore.properties + wear/upload-keystore.jks,
// both gitignored. Release builds fall back to unsigned when absent (CI).
val keystoreProps = Properties().apply {
    val f = rootProject.file("keystore.properties")
    if (f.exists()) f.inputStream().use { load(it) }
}

android {
    namespace = "com.artifact.arcminute.wff"
    compileSdk = 36

    defaultConfig {
        applicationId = "com.artifact.arcminute.wff"
        // Tied to the Watch Face Format version in the manifest: format 4
        // needs Wear OS 6.
        minSdk = 36
        targetSdk = 36
        versionCode = 3
        versionName = "1.2.0"
    }

    signingConfigs {
        if (keystoreProps.isNotEmpty()) {
            create("upload") {
                storeFile = rootProject.file(keystoreProps.getProperty("storeFile").removePrefix("../"))
                storePassword = keystoreProps.getProperty("storePassword")
                keyAlias = keystoreProps.getProperty("keyAlias")
                keyPassword = keystoreProps.getProperty("keyPassword")
            }
        }
    }

    buildTypes {
        release {
            // R8 strips the empty generated classes: a WFF package with
            // minSdk >= 33 must contain no dex files (bundletool enforces it)
            isMinifyEnabled = true
            isShrinkResources = false
            if (keystoreProps.isNotEmpty()) {
                signingConfig = signingConfigs.getByName("upload")
            }
        }
    }
}
