#!/bin/sh
set -eu
cd "$(dirname "$0")"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
die() { echo "$*" >&2; exit 1; }

official=d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e
export BLACKBG_SIGNING_MODE=release
output=app/build
if [ "${1:-}" = --personal ]; then
    shift
    BLACKBG_SIGNING_MODE=personal
    output=app/build/personal
fi
[ "$#" -eq 0 ] || { [ "$#" -eq 1 ] && [ "$1" = :app:lintRelease ]; } ||
    die "Usage: $0 [--personal] [:app:lintRelease]"

owner=$(id -u)
os=$(uname -s)
require_private() {
    message="Signing requires private permissions on $1 (owner only)."
    private=$(find "$1" -prune ! -type l -user "$owner" \
        \( -perm 0400 -o -perm 0500 -o -perm 0600 -o -perm 0700 \) -print)
    [ "$private" = "$1" ] || die "$message"
    if [ "$os" = Darwin ]; then
        # macOS ACLs can grant access beyond the mode bits; each has an extra listing line.
        [ "$(LC_ALL=C ls -lde "$1" | wc -l)" -eq 1 ] || die "$message"
    fi
}

keys="$HOME/.android/blackbg-$BLACKBG_SIGNING_MODE"
if [ "$BLACKBG_SIGNING_MODE" = personal ] && [ ! -e "$keys" ]; then
    (
        umask 077
        mkdir -p "$HOME/.android"
        # Only the process that creates the directory may initialize it.
        mkdir "$keys"
        require_private "$keys"
        openssl rand -hex 32 > "$keys/password"
        "$JAVA_HOME/bin/keytool" -genkeypair -keystore "$keys/release.p12" \
            -storetype PKCS12 -storepass:file "$keys/password" -alias blackbg \
            -keyalg RSA -keysize 3072 -validity 10000 -dname "CN=BlackBG"
    )
fi
[ -f "$keys/password" ] && [ -s "$keys/password" ] &&
    [ -f "$keys/release.p12" ] && [ -s "$keys/release.p12" ] ||
    die "Missing signing credentials in $keys; restore release.p12 and password from backup."
for path in "$keys" "$keys/password" "$keys/release.p12"; do
    require_private "$path"
done

cert=$("$JAVA_HOME/bin/keytool" -exportcert -rfc -keystore "$keys/release.p12" \
    -storetype PKCS12 -storepass:file "$keys/password" -alias blackbg)
fingerprint=$(echo "$cert" | openssl x509 -noout -fingerprint -sha256)
expected=$(echo "${fingerprint#*=}" | tr -d ':' | tr A-F a-f)
if [ "$BLACKBG_SIGNING_MODE" = release ] && [ "$expected" != "$official" ]; then
    die "Signing certificate in $keys does not match the published BlackBG release."
fi
if [ "$BLACKBG_SIGNING_MODE" = personal ] && [ "$expected" = "$official" ]; then
    die "Cannot use the official certificate for a personal build."
fi

./gradlew :app:assembleRelease "$@"
apk="$output/outputs/apk/release/app-release.apk"
signers=$("$JAVA_HOME/bin/java" -jar "$ANDROID_HOME/build-tools/36.0.0/lib/apksigner.jar" \
    verify --print-certs "$apk") || die "APK verification failed: $apk"
actual=$(echo "$signers" | sed -n 's/^Signer #[0-9][0-9]* certificate SHA-256 digest: //p')
[ "$actual" = "$expected" ] || die "Unexpected APK signing certificate: $apk"
echo "Verified $apk (SHA-256 signer: $actual)"
