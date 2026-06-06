# Chronology

A Pebble watchface with analog clock display, configurable colors, and two dial styles (classic and large numerals). Built with the Pebble SDK in C, with a JavaScript config UI via Clay.

## Common Commands

| Task | Command |
|------|---------|
| Build | `pebble build` |
| Run on gabbro emulator | `pebble build && pebble install --emulator gabbro && pebble logs` |
| Screenshot all emulators | `npm run screenshots` |
| Install on phone | `npm run install-phone` |

## Emulators

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

## Configuration

Settings are sent from the phone JS layer to the watch via `Pebble.sendAppMessage`. Persisted on the watch at these keys:

| Key | Persist key | Description |
|-----|-------------|-------------|
| `BG_HEX` | 5 | Background color |
| `FACE_HEX` | 6 | Face color |
| `HAND_HEX` | 7 | Hand color |
| `FACE_CLEAR` | 8 | Transparent face toggle |
| `DIAL_STYLE` | 9 | 0 = classic, 1 = large numerals |

To force a default setting for a build (e.g. screenshots), temporarily change the fallback value in `src/c/chronology.c` where persist keys are read on init, then revert after.

## Code Structure

- `src/c/chronology.c` — main watchface logic (drawing, config handling)
- `src/pkjs/index.js` — phone-side JS, sends config messages to watch
- `src/pkjs/config.js` — Clay config schema for the settings UI
- `resources/fonts/` — custom digit fonts
