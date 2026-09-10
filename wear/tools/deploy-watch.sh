#!/usr/bin/env bash
# Build, install and activate Arcminute on a wirelessly-debugged Wear device,
# then hang up.
#
# Two things make a persistent connection a bad default:
#
#   1. adb's mDNS auto-connect re-attaches on its own whenever the watch
#      advertises _adb-tls-connect, so a plain `adb disconnect` does not
#      stick. ADB_MDNS_AUTO_CONNECT=0 is what actually stops it.
#   2. The watch drops the link the moment its screen sleeps, which truncates
#      screencaps and kills screenrecord mid-file. Reconnecting per operation
#      is more reliable than holding one open.
#
# The connect port is NOT stable: it changes whenever Wireless debugging is
# toggled on the watch (seen go 42765 -> 45989). Pairing survives, so no new
# code is needed, but the port must be rediscovered -- hence the mDNS lookup.
#
#   ./deploy-watch.sh              # build, deploy, disconnect
#   ./deploy-watch.sh --no-build   # deploy the existing APK
#   ./deploy-watch.sh --keep       # leave the connection up
set -uo pipefail

export ADB_MDNS_AUTO_CONNECT=0

PKG=com.artifact.arcminute.wff
WEAR_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
APK="$WEAR_DIR/wff/build/outputs/apk/release/wff-release.apk"
ADB="${ANDROID_HOME:-$HOME/Library/Android/sdk}/platform-tools/adb"
BUILD=1
KEEP=0
for a in "$@"; do
  case "$a" in
    --no-build) BUILD=0 ;;
    --keep) KEEP=1 ;;
    *) echo "unknown flag: $a" >&2; exit 2 ;;
  esac
done

find_endpoint() {
  # adb's own mDNS table first; it is already running a discovery daemon.
  local ep
  ep=$("$ADB" mdns services 2>/dev/null | awk '/_adb-tls-connect/ {print $3; exit}')
  [ -n "$ep" ] && { echo "$ep"; return; }
  # Fall back to Bonjour directly. dns-sd never exits, so cap it.
  local out; out=$(mktemp)
  dns-sd -B _adb-tls-connect._tcp local >"$out" 2>&1 & local pid=$!
  sleep 4; kill "$pid" 2>/dev/null
  local name; name=$(awk '/_adb-tls-connect/ {print $NF; exit}' "$out")
  [ -z "$name" ] && { rm -f "$out"; return 1; }
  dns-sd -L "$name" _adb-tls-connect._tcp local >"$out" 2>&1 & pid=$!
  sleep 4; kill "$pid" 2>/dev/null
  local host port
  host=$(grep -o 'at [A-Za-z0-9_.-]*\.local\.' "$out" | head -1 | sed 's/^at //')
  port=$(grep -o 'local\.:[0-9]*' "$out" | head -1 | cut -d: -f2)
  rm -f "$out"
  [ -n "$host" ] && [ -n "$port" ] && echo "${host%.}:$port"
}

[ "$BUILD" = 1 ] && { echo "==> building"; (cd "$WEAR_DIR" && ./gradlew :wff:assembleRelease -q) || exit 1; }
[ -f "$APK" ] || { echo "no APK at $APK" >&2; exit 1; }

echo "==> discovering watch"
EP="${WEAR_ADB_ENDPOINT:-$(find_endpoint)}"
[ -z "$EP" ] && {
  echo "No _adb-tls-connect advertisement found." >&2
  echo "Wake the watch, and check Developer options -> Wireless debugging is on." >&2
  echo "Or set WEAR_ADB_ENDPOINT=host:port to skip discovery." >&2
  exit 1
}
echo "    $EP"

ok=0
for i in $(seq 1 12); do
  "$ADB" disconnect "$EP" >/dev/null 2>&1
  "$ADB" connect "$EP" >/dev/null 2>&1
  sleep 2
  [ "$("$ADB" -s "$EP" get-state 2>/dev/null)" = "device" ] || { sleep 3; continue; }
  # A sleeping watch drops the link mid-install; waking it first is cheaper
  # than retrying a 40MB push.
  "$ADB" -s "$EP" shell input keyevent KEYCODE_WAKEUP >/dev/null 2>&1
  if "$ADB" -s "$EP" install -r "$APK" 2>&1 | tail -1 | grep -q Success; then ok=1; break; fi
  echo "    attempt $i failed, retrying"
  sleep 3
done
[ "$ok" = 1 ] || { echo "install failed" >&2; exit 1; }

"$ADB" -s "$EP" shell am broadcast \
  -a com.google.android.wearable.app.DEBUG_SURFACE \
  --es operation set-watchface --es watchFaceId "$PKG" >/dev/null 2>&1
"$ADB" -s "$EP" shell dumpsys package "$PKG" 2>/dev/null \
  | grep -E "versionCode=|versionName=" | head -2 | sed 's/^/    /'

if [ "$KEEP" = 0 ]; then
  "$ADB" disconnect "$EP" >/dev/null 2>&1
  echo "==> disconnected"
else
  echo "==> left connected at $EP"
fi
