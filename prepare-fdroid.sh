#!/usr/bin/env bash
# Generate the local repository only. Publishing is a separate step.
set -euo pipefail
export LC_ALL=C
die() { echo "$*" >&2; exit 1; }
[[ $# == 2 ]] || die "Usage : $0 <apk-release> <dossier-fdroid-initialisé>"
[[ -f $1 ]] || die "APK introuvable : $1"
apk=$(cd -- "$(dirname -- "$1")" && pwd -P)/$(basename -- "$1")
cd -- "$2"
[[ -f config.yml && -d repo && ! -L repo ]] || die "Dépôt non initialisé : lancer fdroid init hors Git."
if git rev-parse --git-dir >/dev/null 2>&1; then die "Le dossier F-Droid privé doit être hors Git."; fi
for tool in apksigner aapt fdroid python3; do
    command -v "$tool" >/dev/null || die "Outil absent du PATH : $tool"
done

official=d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e
verify_apk() {
    local signature digests badging
    signature=$(apksigner verify --print-certs "$1")
    digests=$(sed -nE 's/^Signer #[0-9]+ certificate SHA-256 digest: (.*)$/\1/p' <<< "$signature")
    [[ $digests == "$official" ]] || die "Signataire inattendu : APK release officiel requis."
    badging=$(aapt dump badging "$1")
    version=$(sed -nE "s/^package: name='app[.]blackbg' versionCode='([0-9]+)' .*/\1/p" <<< "$badging")
    [[ $version =~ ^[0-9]+$ ]] || die "Paquet ou versionCode inattendu."
}

verify_apk "$apk"
staging=$(mktemp -d .prepare-fdroid.XXXXXXXX)
trap 'rm -rf -- "$staging"' EXIT
cp "$apk" "$staging/input.apk"
verify_apk "$staging/input.apk"

target="repo/app.blackbg_${version}.apk"
[[ ! -L $target && ! -d $target ]] || die "Destination inattendue : $target"
if [[ -f $target ]]; then
    cmp -s "$staging/input.apk" "$target" || die "Le versionCode $version correspond déjà à un autre APK."
else
    ln "$staging/input.apk" "$target"
fi
fdroid update --create-metadata
python3 - "$target" "$version" <<'PY'
import hashlib
import json
from pathlib import Path
import sys

apk = Path(sys.argv[1])
digest = hashlib.sha256(apk.read_bytes()).hexdigest()
index = json.loads(Path("repo/index-v2.json").read_bytes())
release = index.get("packages", {}).get("app.blackbg", {}).get("versions", {}).get(digest, {})
file = release.get("file", {})
if (release.get("manifest", {}).get("versionCode") != int(sys.argv[2]) or
        file.get("sha256") != digest or file.get("name") != "/" + apk.name):
    sys.exit("L’index F-Droid ne référence pas cet APK exact.")
PY
