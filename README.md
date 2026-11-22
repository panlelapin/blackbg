# BlackBG

Un fond noir statique pour l’écran d’accueil et l’écran de verrouillage, sans
sauvegarde des anciens fonds ni accès aux fichiers. Pour Android 16 (API 36)
ou ultérieur, sur appareil ARM 64 bits (`arm64-v8a`).

## Installation

Télécharger l’APK signé depuis les [releases](https://github.com/panlelapin/blackbg/releases/latest)
et l’installer sur le téléphone. BlackBG n’a pas d’icône dans le lanceur.
Dans un sélecteur de fonds d’écran compatible, choisir **BlackBG**, puis
**Appliquer aux deux écrans**. Si le sélecteur du téléphone ne liste pas les
applications tierces, ouvrir l’aperçu via ADB :

```sh
adb shell am start -a android.intent.action.SET_WALLPAPER -p app.blackbg
```

## Compilation locale

Sur macOS avec Android Studio, installer la plateforme SDK 36.1, les Build Tools
36.0.0, le NDK 28.2.13676358 et CMake 3.22.1. Pour d’autres emplacements,
définir `JAVA_HOME` (JDK 21) et `ANDROID_HOME` (SDK Android).

```sh
./build-local.sh
```

Cette commande exige la clé officielle (`release.p12`, alias `blackbg`) et son
fichier `password` dans `~/.android/blackbg-release/`. Elle vérifie l’empreinte
SHA-256 du certificat publié
(`d7f02e4701a55950eba482d631b4df25d9fd8100c21f18f99e8897f1aab2ec5e`),
puis la signature de `app/build/outputs/apk/release/app-release.apk`.

Pour signer avec votre propre clé :

```sh
./build-local.sh --personal
```

Ce mode crée `~/.android/blackbg-personal/` avec des permissions privées au
premier lancement, puis réutilise sa clé. Sauvegardez le dossier en lieu sûr :
si un fichier manque, restaurez la paire `release.p12` et `password` à partir
de la même sauvegarde. L’APK personnel vérifié se trouve dans
`app/build/personal/outputs/apk/release/app-release.apk`.

Dans les deux modes, le dossier de signature et les deux fichiers doivent
vous appartenir et n’être accessibles qu’à vous (par exemple `700` pour le
dossier, `600` pour les fichiers, sans ACL supplémentaire sur macOS).
Le mode personnel refuse le certificat officiel. Pour exécuter aussi Lint,
ajoutez `:app:lintRelease` à la commande ; c’est le seul argument Gradle admis.

Si une ancienne version du script a créé **votre clé personnelle** dans
`~/.android/blackbg-release/`, migrez-la **avant** le premier `--personal` :
avec `umask 077`, créez `~/.android/blackbg-personal/` et copiez-y les deux
fichiers personnels, sans écraser de clé existante. Les deux modes conservent
l’identifiant `app.blackbg` : Android accepte une mise à jour avec la même clé,
mais exige de désinstaller l’application avant de passer à une autre signature.
