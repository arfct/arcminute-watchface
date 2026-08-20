# Chronology

A watchface with an analog dial whose rim sweeps through the screen at the
current hour, configurable colors, and two dial styles (classic and large
numerals). Two implementations share this repo:

- `pebble/` — original Pebble version (C + Clay JS config)
- `wear/` — Wear OS version (Kotlin, androidx.wear.watchface)

## Pebble (`pebble/`)

Run all Pebble commands from the `pebble/` directory.

| Task | Command |
|------|---------|
| Build | `pebble build` |
| Run on gabbro emulator | `pebble build && pebble install --emulator gabbro && pebble logs` |
| Screenshot all emulators | `npm run screenshots` |
| Install on phone | `npm run install-phone` |

### Emulators

Target platforms: `aplite`, `basalt`, `chalk`, `diorite`, `emery`, `gabbro`

To run a specific emulator:
```
pebble install --emulator <platform>
pebble logs --emulator <platform>
pebble screenshot <output.png> --emulator <platform>
```

If an emulator gets stuck at boot, wipe its flash:
```
pkill -9 -f <platform>
rm ~/Library/Application\ Support/Pebble\ SDK/4.9.169/<platform>/qemu_spi_flash.bin
```

### Configuration

Settings are sent from the phone JS layer to the watch via `Pebble.sendAppMessage`. Persisted on the watch at these keys:

| Key | Message key | Persist key | Description |
|-----|-------------|-------------|-------------|
| `BG_HEX` | 10000 | 5 | Background color |
| `FACE_HEX` | 10001 | 6 | Face color |
| `HAND_HEX` | 10002 | 7 | Hand color |
| `FACE_CLEAR` | 10003 | 8 | Transparent face toggle |
| `DIAL_STYLE` | 10004 | 9 | 0 = classic, 1 = large numerals |

To send a setting to a running emulator:
```
pebble send-app-message --emulator <platform> --int <message_key>=<value>
```

Send each key as its own message. Passing multiple `--int` flags in a single
`send-app-message` call only delivers one of them (the others are silently
dropped). To change several settings, issue one command per key.

Example — enable large numerals on all emulators:
```
for platform in aplite basalt chalk diorite emery gabbro; do
  pebble send-app-message --emulator $platform --int 10004=1
done
```

To force a default setting for a build (e.g. screenshots), temporarily change the fallback value in `pebble/src/c/chronology.c` where persist keys are read on init, then revert after.

### Code structure

- `pebble/src/c/chronology.c` — main watchface logic (drawing, config handling)
- `pebble/src/pkjs/index.js` — phone-side JS, sends config messages to watch
- `pebble/src/pkjs/config.js` — Clay config schema for the settings UI
- `pebble/resources/fonts/` — custom digit fonts

## Wear OS (`wear/`)

Run all Gradle commands from the `wear/` directory.

| Task | Command |
|------|---------|
| Build debug APK | `./gradlew :app:assembleDebug` |
| Unit tests | `./gradlew :app:testDebugUnitTest` |
| Install on device/emulator | `adb install -r app/build/outputs/apk/debug/app-debug.apk` |

Activate the watchface on a connected Wear emulator/device:
```
adb shell am broadcast -a com.google.android.wearable.app.DEBUG_SURFACE --es operation set-watchface --ecn component com.artifact.chronology/.ChronologyWatchFaceService
```

Screenshot: `adb exec-out screencap -p > shot.png`

### Emulator

A Wear OS 4 (API 33) AVD named `chronology_wear` works for development:
```
~/Library/Android/sdk/emulator/emulator -avd chronology_wear -no-window -no-audio &
```
To open the on-watch editor: long-press the watchface (`adb shell input swipe 192 192 192 192 1500`), tap the pencil.

**Wear OS 5+ caveat:** devices that *launch* with Wear OS 5 (including the
API 34+ wear emulator images) reject androidx/legacy watch faces as
"Unsupported legacy watch face" — only the declarative Watch Face Format is
accepted for new installs there. Watches that *upgraded* to Wear OS 5 still
run this app, as do Wear OS 3/4 devices. A WFF rewrite would be needed for
new-device installs and Play Store distribution.

### Code structure

- `wear/app/src/main/java/com/artifact/chronology/DialMath.kt` — pure geometry (hour angle, orbit center, 24h labels); unit tested
- `wear/app/src/main/java/com/artifact/chronology/ChronologyRenderer.kt` — Canvas rendering (dial, numerals, ticks, hand, ambient)
- `wear/app/src/main/java/com/artifact/chronology/WatchStyle.kt` — style values resolved from the user style schema
- `wear/app/src/main/java/com/artifact/chronology/StyleSchema.kt` — UserStyleSchema (dial style, colors, transparent face)
- `wear/app/src/main/java/com/artifact/chronology/ChronologyWatchFaceService.kt` — WatchFaceService entry point
- `wear/app/src/main/java/com/artifact/chronology/editor/EditorActivity.kt` — minimal on-watch style editor

Rendering uses gabbro (260 px) as the reference coordinate space: all pixel
constants are gabbro values scaled by `screenMinDim / 260`. Keep the two
implementations visually in sync — `pebble/src/c/chronology.c` is the source
of truth for geometry.
