#!/usr/bin/env bash
# Copy only the public repository into the local Pages checkout.
set -euo pipefail
die() { echo "$*" >&2; exit 1; }
[[ $# == 2 ]] || die "Usage : $0 <dossier-fdroid> <checkout-gh-pages>"
src=$(cd -- "$1/repo" && pwd -P)
pages=$(cd -- "$2" && pwd -P)
dest=$pages/fdroid/repo
[[ $(git -C "$pages" symbolic-ref --short HEAD) == gh-pages &&
   $(git -C "$pages" rev-parse --show-toplevel) == "$pages" ]] || die "Checkout gh-pages requis."
[[ ! -L $pages/fdroid && ! -L $dest ]] || die "Destination inattendue : $dest"
[[ $dest/ != "$src/"* && $src/ != "$dest/"* ]] || die "Source et destination doivent être séparées."
[[ -s $src/entry.jar && -s $src/index-v2.json ]] || die "Dépôt signé incomplet."

shopt -s nullglob
for published in "$dest"/*.apk; do
    cmp -s "$published" "$src/${published##*/}" ||
        die "APK publié absent ou différent : ${published##*/}. Restaurer le dépôt avant de continuer."
done
mkdir -p "$dest"
rsync -rtc --delete "$src/" "$dest/"
touch "$pages/.nojekyll"
