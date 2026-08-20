# Wear OS Port Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Port the Chronology Pebble watchface to Wear OS as a native Kotlin watch face, with the existing Pebble source moved to `pebble/` and the new Android project in `wear/`.

**Architecture:** A `WatchFaceService` using the androidx `CanvasRenderer2` draws the same geometry as the Pebble C code: a dial 3× the screen size whose center orbits opposite the current hour angle, so the rim (numerals + ticks) sweeps through the visible screen, plus a hand from the dial center to the current-hour rim point. All pure math (hour angle, orbit center, hand endpoints, 24h nearest-hour labels) lives in `DialMath.kt` and is unit tested. Styles (dial style, colors, transparent face) come from a `UserStyleSchema`; a minimal on-watch editor activity replaces Clay.

**Tech Stack:** Kotlin 2.0, AGP 8.x, `androidx.wear.watchface:watchface:1.2.1` + `watchface-editor:1.2.1`, minSdk 30, targetSdk 34. Bundled `Helvetica-Digits.ttf` for numerals.

## Global Constraints

- Rendering uses gabbro (260 px) as the reference coordinate space; all pixel constants below are gabbro values multiplied by `scale = screenMinDim / 260f`.
- Defaults must match Pebble defaults: background black, face black, hand `#FF0000`, transparent face ON, dial style = large numerals.
- 24h mode follows the system 24h setting and reproduces the Pebble "nearest absolute hour" label logic exactly.
- Redraw cadence: once per minute (like the Pebble version).
- Ambient mode: black background, transparent face, white text/hand, gray minor ticks.
- Package name: `com.artifact.chronology`.

---

### Task 1: Move Pebble source into `pebble/`

**Files:**
- Move: `src/`, `resources/`, `wscript`, `package.json`, `package-lock.json`, `.vscode/` → `pebble/`
- Modify: `AGENTS.md`, `README.md`
- Keep at root: `LICENSE`, `store/`, `.gitignore`, `.gitattributes`, `docs/`

**Steps:**

- [ ] `git mv src resources wscript package.json package-lock.json .vscode pebble/` (creating `pebble/` first)
- [ ] Update `AGENTS.md`: note the repo now has `pebble/` and `wear/` subprojects; Pebble commands run from `pebble/`; code-structure paths get the `pebble/` prefix.
- [ ] Update `README.md` to mention both platforms.
- [ ] Verify: `ls pebble/src/c/chronology.c` exists; `git status` shows renames.
- [ ] Commit: `refactor: move Pebble source into pebble/ subdirectory`

### Task 2: Scaffold the `wear/` Gradle project

**Files:**
- Create: `wear/settings.gradle.kts`, `wear/build.gradle.kts`, `wear/gradle.properties`, `wear/gradle/wrapper/*`, `wear/app/build.gradle.kts`, `wear/app/src/main/AndroidManifest.xml`, `wear/app/src/main/res/values/strings.xml`, `wear/app/src/main/res/xml/watch_face.xml`, `wear/app/src/main/res/drawable-nodpi/preview.png` (placeholder: copy of `store/screenshots/screenshot_chalk.png`), `wear/app/src/main/res/font/helvetica_digits.ttf` (copy of `pebble/resources/fonts/Helvetica-Digits.ttf`), stub `ChronologyWatchFaceService.kt` that renders a black screen.
- Modify: `.gitignore` (add `wear/.gradle`, `wear/build`, `wear/app/build`, `wear/local.properties`)

**Interfaces:**
- Produces: a compiling app module with service registered in the manifest as a watch face (`WallpaperService` intent filter, `WATCH_FACE` category, standalone=true, editor meta-data).

**Key manifest content:**

```xml
<manifest xmlns:android="http://schemas.android.com/apk/res/android">
  <uses-feature android:name="android.hardware.type.watch" />
  <uses-permission android:name="android.permission.WAKE_LOCK" />
  <application android:label="@string/app_name" android:icon="@mipmap/ic_launcher">
    <uses-library android:name="com.google.android.wearable" android:required="false" />
    <meta-data android:name="com.google.android.wearable.standalone" android:value="true" />
    <service
      android:name=".ChronologyWatchFaceService"
      android:directBootAware="true"
      android:exported="true"
      android:label="@string/app_name"
      android:permission="android.permission.BIND_WALLPAPER">
      <intent-filter>
        <action android:name="android.service.wallpaper.WallpaperService" />
        <category android:name="com.google.android.wearable.watchface.category.WATCH_FACE" />
      </intent-filter>
      <meta-data android:name="android.service.wallpaper" android:resource="@xml/watch_face" />
      <meta-data android:name="com.google.android.wearable.watchface.preview" android:resource="@drawable/preview" />
      <meta-data android:name="com.google.android.wearable.watchface.preview_circular" android:resource="@drawable/preview" />
      <meta-data android:name="com.google.android.wearable.watchface.wearableConfigurationAction"
        android:value="androidx.wear.watchface.editor.action.WATCH_FACE_EDITOR" />
    </service>
  </application>
</manifest>
```

**Steps:**

- [ ] Locate or download a Gradle distribution (check `~/.gradle/wrapper/dists` first); generate wrapper files in `wear/`.
- [ ] Write build files: AGP + Kotlin plugins, `compileSdk 34+`, `minSdk 30`, deps `androidx.wear.watchface:watchface:1.2.1`, `watchface-editor:1.2.1`, `androidx.activity:activity:1.9.x`, test dep `junit:junit:4.13.2`.
- [ ] Copy font and preview placeholder; generate launcher icon from `pebble/resources/images/app_icon.png`.
- [ ] Stub service: `createWatchFace` returns a `CanvasRenderer2` that fills black.
- [ ] Verify: `cd wear && ./gradlew :app:assembleDebug` succeeds.
- [ ] Commit: `feat(wear): scaffold Wear OS watch face project`

### Task 3: `DialMath.kt` pure geometry + unit tests (TDD)

**Files:**
- Create: `wear/app/src/main/java/com/artifact/chronology/DialMath.kt`
- Test: `wear/app/src/test/java/com/artifact/chronology/DialMathTest.kt`

**Interfaces (produces):**

```kotlin
object DialMath {
    // Clockwise degrees from 12 o'clock, e.g. 3:30 -> 105.0
    fun hourAngleDegrees(hour: Int, minute: Int): Float

    // Unit vector for a clock angle: x = sin, y = -cos (screen y grows down)
    fun unitX(angleDeg: Float): Float
    fun unitY(angleDeg: Float): Float

    // Dial center offset from screen center = -(screenSize/2 + orbitInset) * unit(angle)
    fun dialCenterX(cx: Float, angleDeg: Float, screenSize: Float, orbitInset: Float): Float
    fun dialCenterY(cy: Float, angleDeg: Float, screenSize: Float, orbitInset: Float): Float

    // Pebble 12h label: index 0 -> 12, else index
    fun label12(index: Int): Int

    // Pebble 24h label: absolute hour (1-24) nearest current time for tick i
    fun label24(index: Int, currentHour: Float): Int
}
```

**Test cases (write first, watch fail, then implement):**

```kotlin
class DialMathTest {
    @Test fun hourAngle_threeThirty() { assertEquals(105f, DialMath.hourAngleDegrees(3, 30), 1e-4f) }
    @Test fun hourAngle_wrapsPm() { assertEquals(105f, DialMath.hourAngleDegrees(15, 30), 1e-4f) }
    @Test fun label12_zeroIsTwelve() { assertEquals(12, DialMath.label12(0)); assertEquals(7, DialMath.label12(7)) }
    // At 15:00 the dial reads 13..24 on the visible arc
    @Test fun label24_afternoon() {
        assertEquals(24, DialMath.label24(0, 15.0f))
        assertEquals(13, DialMath.label24(1, 15.0f))
        assertEquals(15, DialMath.label24(3, 15.0f))
        assertEquals(21, DialMath.label24(9, 15.0f))
    }
    // Just before 1am the arc mixes ...23, 24, 1, 2...
    @Test fun label24_midnightWrap() {
        assertEquals(24, DialMath.label24(0, 0.5f))
        assertEquals(1, DialMath.label24(1, 0.5f))
        assertEquals(23, DialMath.label24(11, 0.5f))
    }
    @Test fun dialCenter_isOppositeHourDirection() {
        // At 12:00 angle=0, unit=(0,-1); dial center sits BELOW screen center
        val cy = DialMath.dialCenterY(100f, 0f, 200f, 180f)
        assertEquals(100f + 280f, cy, 1e-3f)
    }
}
```

**Implementation (ports of the C expressions):**

```kotlin
fun label24(index: Int, currentHour: Float): Int {
    val laps = (currentHour - index) / 12.0f
    val rounded = index + 12 * (laps + if (laps >= 0) 0.5f else -0.5f).toInt()
    val wrapped = ((rounded % 24) + 24) % 24
    return if (wrapped == 0) 24 else wrapped
}
```

**Steps:**

- [ ] Write `DialMathTest.kt`; run `./gradlew :app:testDebugUnitTest` → fails to compile (no DialMath).
- [ ] Implement `DialMath.kt`.
- [ ] Run tests → all pass.
- [ ] Commit: `feat(wear): dial geometry math with unit tests`

### Task 4: Full renderer

**Files:**
- Create: `wear/app/src/main/java/com/artifact/chronology/ChronologyRenderer.kt`, `WatchStyle.kt` (data class: bgColor, faceColor, handColor, faceClear, largeNumerals)
- Modify: `ChronologyWatchFaceService.kt` to use the renderer.

**Interfaces:**
- Consumes: `DialMath` functions from Task 3.
- Produces: `ChronologyRenderer(surfaceHolder, watchState, styleRepository, context)` extending `Renderer.CanvasRenderer2<SharedAssets>`; `WatchStyle.fromUserStyle(userStyle): WatchStyle`.

**Rendering constants (gabbro 260 px reference, multiply by `scale = minDim/260f`):**

| Element | Large numerals | Classic |
|---|---|---|
| Numeral font size | 95 | 42 |
| Hour inset (numeral/tick depth) | 28 | 14 |
| Hour tick stroke | 6 | 3 |
| 30-min tick stroke | 4 | 2 |
| Dot radius | 3 | 2 |
| Hand stroke | 9 | 9 |
| Orbit inset (round screens) | 188 | 188 |
| Dial radius | 1.5 × screen height | same |

**Render algorithm per frame (from `my_face_draw` + `my_hand_draw` + `update_frame_location`):**

1. `angle = DialMath.hourAngleDegrees(h, m)`; dial center `D = C - (S/2 + orbit) * unit(angle)`; dial radius `R = 1.5 * S`.
2. Fill canvas with bg color. If `!faceClear`, fill circle at D radius `R + 8*scale` with face color.
3. For each of 12 hour positions `i` (angle `i*30°`), in DIAL coordinates centered on D:
   - Label = `label24(i, curHour)` if system is 24h else `label12(i)`.
   - Hour tick: line from radius `R - hourInset` to `R`, face-text color.
   - Numeral: measure tight glyph bounds with `Paint.getTextBounds`; place the glyph box inward from the tick inner point along the radial by `gap + dEdge`, where `gap = hourInset/2` and `dEdge = min(halfW/|ux|, halfH/|uy|)` (distance from box center to the box edge along the radial unit vector `u`). Draw centered.
   - For j in 1..11 (2.5° steps): if `j % 3 == 0` draw a tick line (full `hourInset` length when `j == 6`, else half), minor color, else a dot at radius `R` (minor color). Minor color = dark gray on light face, light gray on dark face; face-text color = black on light face, white on dark.
4. Hand: line from D to `D + R*unit(angle)`, hand color, stroke 9×scale, round cap.
5. Ambient (`renderParameters.drawMode == DrawMode.AMBIENT`): force bg black, faceClear=true, hand white.

`interactiveDrawModeUpdateDelayMillis = 60_000`.

**Steps:**

- [ ] Implement `WatchStyle` with defaults (black/black/red/clear/large).
- [ ] Implement renderer per algorithm; wire into service.
- [ ] Verify: `./gradlew :app:assembleDebug` and unit tests pass.
- [ ] Commit: `feat(wear): full dial and hand rendering`

### Task 5: User style schema + on-watch editor

**Files:**
- Create: `wear/app/src/main/java/com/artifact/chronology/StyleSchema.kt`, `editor/EditorActivity.kt`, `res/layout/editor.xml` (simple LinearLayout of setting rows)
- Modify: `ChronologyWatchFaceService.kt` (`createUserStyleSchema`), `AndroidManifest.xml` (editor activity with `androidx.wear.watchface.editor.action.WATCH_FACE_EDITOR` intent filter).

**Schema (ids must be stable):**
- `dial_style`: List — `classic`, `large` (default `large`)
- `bg_color`: List — `black` (default), `white`, `blue`, `green`
- `face_clear`: Boolean, default true
- `face_color`: List — `black` (default), `white`, `gray`
- `hand_color`: List — `red` (default), `white`, `black`, `yellow`, `blue`

`WatchStyle.fromUserStyle` maps option ids → ARGB ints (red = `0xFFFF0000`).

**Editor:** `ComponentActivity` + `EditorSession.createOnWatchEditorSession`; each row is a Button that cycles its setting's options and applies via `session.userStyle`.

**Steps:**

- [ ] Implement schema; read it in the renderer via `currentUserStyleRepository.userStyle.value` each frame.
- [ ] Implement editor activity + manifest entry.
- [ ] Verify: build + unit tests pass.
- [ ] Commit: `feat(wear): user style schema and on-watch editor`

### Task 6: Emulator verification + docs

**Files:**
- Modify: `wear/app/src/main/res/drawable-nodpi/preview.png` (replace placeholder with real screenshot), `AGENTS.md`, `README.md`

**Steps:**

- [ ] Install Wear system image: `sdkmanager "system-images;android-36;android-wear;arm64-v8a"` (fall back to android-34 wear image if unavailable); create AVD with a small round Wear profile; boot.
- [ ] `adb install` the debug APK; activate: `adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation set-watchface --ecn component com.artifact.chronology/.ChronologyWatchFaceService`
- [ ] Screenshot via `adb exec-out screencap -p`; visually check: numerals upright, rim sweeps through screen at correct hour, hand from off-screen dial center through the visible area, colors correct.
- [ ] Exercise styles via the editor (or `adb` + screenshots at different times using `adb shell date` or debug angle); fix any visual defects found.
- [ ] Replace `preview.png` with a real screenshot; rebuild; commit.
- [ ] Update `AGENTS.md` (wear build/test/emulator commands) and `README.md`.
- [ ] Commit: `feat(wear): emulator-verified rendering, real preview, docs`
