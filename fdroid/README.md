# Publier BlackBG sur GitHub Pages

La préparation ne déploie rien. Après la première publication, le client F-Droid
pourra installer et mettre à jour le même APK que celui des GitHub Releases.

### 1. Une fois, sur le Mac

Installer [fdroidserver](https://f-droid.org/docs/Installing_the_Server_and_Repo_Tools/)
(version 2.3 ou ultérieure), le SDK Android et le JDK du projet. Depuis la racine de BlackBG :

```sh
src="$PWD"
private="$HOME/.local/share/blackbg-fdroid"
export ANDROID_HOME="${ANDROID_HOME:-$HOME/Library/Android/sdk}"
export JAVA_HOME="${JAVA_HOME:-/Applications/Android Studio.app/Contents/jbr/Contents/Home}"
export PATH="$ANDROID_HOME/build-tools/36.0.0:$JAVA_HOME/bin:$PATH"
(umask 077 && mkdir -p "$(dirname "$private")" && mkdir "$private" &&
  cd "$private" && fdroid init)
```

Dans le `config.yml` généré, régler les champs suivants **en conservant les
paramètres de signature** :

```yaml
repo_url: https://panlelapin.github.io/blackbg/fdroid/repo
repo_name: BlackBG
repo_description: Versions officielles de BlackBG
archive_older: 0
make_current_version_link: false
```

Sauvegarder le dossier privé et le keystore indiqué dans `config.yml`.
Cette clé signe l’index, pas l’APK. Ne pas relancer `fdroid init` lors des mises
à jour, ni placer ce dossier sur GitHub.

### 2. À chaque release, générer l’index local

Télécharger **l’asset `.apk` du tag voulu**, pas celui d’une ancienne release.
Depuis BlackBG, avec les mêmes variables et le même `PATH` qu’à l’étape 1 :

```sh
mkdir -p "$private/metadata"
cp "$src/fdroid/app.blackbg.yml" "$private/metadata/"
./prepare-fdroid.sh "/chemin/vers/la-release.apk" "$private"
```

En cas d’erreur, ne pas publier. Après correction, on peut relancer avec les
mêmes octets. Pour un APK différent, augmenter le `versionCode` et utiliser
la même clé de release. Vérifier que `repo/entry.jar`, `repo/index-v2.json`
et `repo/app.blackbg_<versionCode>.apk` sont présents dans le dossier privé.

### 3. Publier uniquement les fichiers publics

Utiliser un checkout **séparé** de `gh-pages` (`pages="$HOME/blackbg-pages"`).
Si la branche existe, la cloner avec `git clone --branch gh-pages --single-branch
https://github.com/panlelapin/blackbg.git "$pages"` puis la garder à jour avec
`git -C "$pages" pull --ff-only`. Pour un **nouveau site** sans branche `gh-pages` :

```sh
pages="$HOME/blackbg-pages"
git init -b gh-pages "$pages"
git -C "$pages" remote add origin https://github.com/panlelapin/blackbg.git
```

Si Pages héberge déjà un site, conserver sa source et ajouter `fdroid/repo/` à
ce site plutôt que de le remplacer. Pour le site dédié :

```sh
mkdir -p "$pages/fdroid/repo"
touch "$pages/.nojekyll"
rsync -rt --delete "$private/repo/" "$pages/fdroid/repo/"
git -C "$pages" add -- .nojekyll fdroid/repo
git -C "$pages" diff --cached --stat
git -C "$pages" commit -m "Publier le dépôt F-Droid BlackBG"
git -C "$pages" push -u origin gh-pages
```

Dans GitHub → **Settings → Pages**, choisir **Deploy from a branch → gh-pages →
/(root)**. Le merge de la branche de préparation dans `master` ne déclenche
aucune publication.

### 4. Vérifier et partager le lien d’ajout

Une fois Pages déployé, comparer le fichier signé servi à celui du Mac, puis
faire de même pour le nouvel APK :

```sh
url=https://panlelapin.github.io/blackbg/fdroid/repo
apk=app.blackbg_12.apk  # remplacer 12 par le versionCode publié
(set -eo pipefail
 for file in entry.jar index-v2.json "$apk"; do
   curl -fsSL "$url/$file" | cmp "$private/repo/$file" -
 done
 echo "Fichiers identiques")
```

Lire l’empreinte **SHA256** du certificat de l’index avec
`keytool -printcert -jarfile "$private/repo/entry.jar"`. Enlever les `:`,
puis remplacer `EMPREINTE` par cette valeur dans
`https://panlelapin.github.io/blackbg/fdroid/repo/?fingerprint=EMPREINTE`.
Tester le lien dans F-Droid sur Android 16+ ARM64, vérifier que BlackBG apparaît
après actualisation, puis mettre le lien vérifié dans le README principal.
