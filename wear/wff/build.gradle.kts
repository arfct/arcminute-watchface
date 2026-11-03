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
        targetSdk = 36
        versionName = "1.3.0"
    }

    // One flavor per Watch Face Format version, released together. Play
    // serves each watch the highest versionCode it can install, so format4
    // must keep the higher code. minSdk is tied to the format: Play filters
    // by it, and a watch whose runtime is older than the format cannot
    // render the face. Bump both versionCodes for every upload.
    flavorDimensions += "format"
    productFlavors {
        create("format3") {
            dimension = "format"
            minSdk = 35
            versionCode = 7
            manifestPlaceholders["wffVersion"] = "3"
        }
        create("format4") {
            dimension = "format"
            minSdk = 36
            versionCode = 8
            manifestPlaceholders["wffVersion"] = "4"
        }
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
