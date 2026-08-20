![image 1](https://github.com/user-attachments/assets/4c6ef1b3-d783-49d4-8f44-e8aae6ddfe75)

# Chronology
Watchface with a hyper-accurate hour hand that is
cropped to the current location on the clock's perimeter.

Two implementations:

- [`pebble/`](pebble/) — the original Pebble watchface (C, Clay config)
- [`wear/`](wear/) — Wear OS port, two flavors:
  - `wear/app/` — Kotlin (androidx.wear.watchface), for Wear OS 3/4 and upgraded-to-5 watches
  - `wear/wff/` — declarative Watch Face Format, for watches that ship with Wear OS 5+ and Play Store distribution

See [AGENTS.md](AGENTS.md) for build and emulator instructions for both.
