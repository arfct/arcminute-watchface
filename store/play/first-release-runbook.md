# First release runbook — Arcminute

The rename to Arcminute needs a **new Play app record**: `applicationId` is
permanent once uploaded, so `com.artifact.chronology.wff` cannot be renamed and
cannot ever be reused. The old record is abandoned, not migrated.

The Play Developer API cannot create an app record, and Data Safety plus the
content rating questionnaire are Console-only. So release one is by hand;
release two onward is one `fastlane supply` command (see the end).

Every answer below comes from [console-answers.md](console-answers.md). The
build is `wear/wff/build/outputs/bundle/release/wff-release.aab`
(`com.artifact.arcminute.wff`, versionCode 2, versionName 1.1.0, zero dex).

## 1. Create the app record

Play Console → **All apps** → **Create app**.

| Field | Value |
|---|---|
| App name | Arcminute |
| Default language | English (United States) — en-US |
| App or game | App |
| Free or paid | Free |

Accept the declarations yourself. Do **not** reuse the old app record.

## 2. Abandon the old record

Old app → **Advanced settings** → unpublish. It reached production review, so it
cannot be deleted outright. Leaving it published would put two watch faces in
the store under different names.

## 3. Store listing

Main store listing → paste from
[listing.md](listing.md) (title 9/30, short 75/80, full 1113/4000).

Upload from `store/play/`:

| Slot | Files |
|---|---|
| App icon | `icon-512.png` |
| Feature graphic | `feature-graphic-1024x500.png` |
| Wear OS screenshots | `wear-1..4-*.png` |
| Phone screenshots | `phone-1..4-*.png` |
| 7-inch tablet | `tablet7-1..4-*.png` |
| 10-inch tablet | `tablet10-1..4-*.png` |

> **Trap, cost a week last time.** Listing edits sit in a **"Draft changes"**
> state until you click **Next → Save**. Draft assets do not count toward the
> Wear OS form-factor checklist, so "Upload Wear OS screenshots" stays unticked,
> which keeps "Opt in to Wear OS" locked, which makes public availability
> impossible. After uploading, confirm the header reads **"Changes ready to send
> for review"**, not "Draft changes".

## 4. Privacy policy — changed URL

App content → Privacy policy:

```
https://arfct.github.io/arcminute-watchface/privacy.html
```

The old `chronology-watchface` Pages URL now **404s**. GitHub redirects renamed
repository URLs but does *not* redirect Pages sites, so the previously
registered URL is dead and must be replaced, not relied on.

Requires `docs/privacy.html` to be pushed to `main` first.

## 5. Declarations

From [console-answers.md](console-answers.md): app access (no login), no ads,
content rating (Utility/Other, all "no" → Everyone), target audience 18+, not a
news app, no COVID features, Data Safety **no data collected or shared**, not a
government app, no financial features.

## 6. Form factors and track

Advanced settings → **Form factors** → complete the Wear OS checklist, then
**opt in to Wear OS**.

> **Trap.** Production has a form-factor selector next to its heading.
> **"Wear OS only" is a separate track** from the default "Phones, Tablets,
> Chrome OS, Android XR" track, which refuses a watch-only bundle. Upload to the
> Wear OS track.

## 7. Upload and release

Upload `wff-release.aab`. Enrol in Play App Signing when prompted.

> **Target API level.** Play requires Wear OS apps to target **Android 15
> (API 35) or higher**, enforced since 2026-08-31 — the rule is "within 1 year
> of the latest Wear OS release", so it moves. `targetSdk` was 34 and was
> bumped to 35 on 2026-09-06. The old Chronology record is still flagged
> non-compliant in Policy status.

> **Automatic protection must stay OFF.** It injects code, and a WFF package
> with minSdk ≥ 33 must contain zero dex files or bundletool rejects it.

Then submit from **Publishing overview** — uploading alone does not submit.

## 8. Every release after this one

The service account already exists:
`play-upload@artifact-play-store.iam.gserviceaccount.com`, key at
`~/.config/play/service-account.json`.

> **Two permission gotchas, both hit on 2026-09-06.** The account's access is
> scoped per-app through the "App management" permission group, so **every new
> app must be added to that group** or the API returns "The caller does not
> have permission" *at commit time*, after appearing to upload everything.
> Separately, a never-published app is a **draft app**, which needs the group's
> **"Edit and delete draft apps"** permission — distinct from the release
> permissions, and off by default.

Then:

```bash
python3 ~/.claude/skills/play-store-assets/scripts/supply_metadata.py \
  store/play --out wear/fastlane --version-code <N> --changelog "…"
```

Wear screenshots are not handled by that script; copy them in afterwards:

```bash
cp store/play/wear-*.png wear/fastlane/metadata/android/en-US/images/wearScreenshots/
```

```bash
cd wear && fastlane supply --aab wff/build/outputs/bundle/release/wff-release.aab --track production --metadata_path fastlane/metadata/android
```

Bump `versionCode` in `wear/wff/build.gradle.kts` for every upload.
