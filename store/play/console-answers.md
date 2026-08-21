# Play Console answer sheet — Chronology

Everything the Console forms ask, decided once. Fill from here.

## App record

| Field | Value |
|---|---|
| App name | Chronology |
| Default language | English (United States) — en-US |
| App or game | App |
| Free or paid | Free |
| Category | Personalization |
| Tags | Watch faces |
| Contact email | nicholas@artifact.com |
| Privacy policy | https://arfct.github.io/chronology-watchface/privacy.html |

## Declarations

| Form | Answer |
|---|---|
| App access | All functionality available without special access (no login) |
| Ads | No, app does not contain ads |
| Content rating questionnaire | Category: Utility/Productivity/Communication/Other. No violence, sexuality, language, controlled substances, gambling, user interaction, location sharing, personal info sharing. Expected: Everyone. |
| Target audience | 18 and over (simplest; avoids child-directed review. The face is fine for all ages, but selecting under-13 audiences triggers Families policy requirements with no benefit.) |
| News app | No |
| COVID-19 tracing/status | No |
| Data safety | Does not collect or share any user data. No data collected, no data shared, no security section applies. |
| Government app | No |
| Financial features | None |
| Health apps | Not a health app |

## Form factor

- Release only to **Wear OS** track / opt into Wear OS form factor.
- Do NOT check phone/tablet/TV/auto as supported devices (manifest's
  `uses-feature android.hardware.type.watch` enforces this anyway).
- Wear OS screenshots: `wear-1-hero.png`, `wear-2-24h.png`,
  `wear-3-indigo.png`, `wear-4-classic.png` (1:1, 1080×1080).

## Release

| Field | Value |
|---|---|
| Track | Internal testing first; promote to Production after install check |
| AAB | wear/wff/build/outputs/bundle/release/wff-release.aab |
| versionCode / versionName | 1 / 1.0.0 |
| Play App Signing | Accept (Google holds signing key; our jks is the upload key) |
| Release name | 1.0.0 |

## Release notes (What's new, 431/500)

```
Chronology's first Wear OS release, ten years after the Pebble original.

A dial three times wider than your watch slides past the screen; you see the hour it is now, the minute marks around it, and a hand crossing from off-screen. In 24-hour mode the dial renumbers itself after noon.

Two dial styles, nineteen colors for the background and the hand, configured from the watch. No data collected, no permissions.
```
