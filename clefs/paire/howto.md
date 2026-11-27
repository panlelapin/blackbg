# Repartir d’un clone de BlackBG

Il faut le dépôt **et la passphrase du coffre**. Cette passphrase est distincte
du mot de passe du keystore Android. Le dépôt étant public, choisir une phrase
longue et aléatoire (par exemple sept mots tirés au hasard) et la conserver
dans un gestionnaire de mots de passe. Sa perte rend la sauvegarde inutilisable.

| Fichier sous `clefs/` | Contenu | Protection |
|---|---|---|
| `paire/publique.txt` | Destinataire age de cette sauvegarde | Public |
| `paire/paire.tar.gz.age` | `publique.txt` et l’identité privée `privee.txt` | Ta passphrase |
| `release.tar.gz.age` | `release.p12` et son fichier `password` pour signer les APK BlackBG | Clé publique age |
| `discussions.tar.gz.age` | JSON natifs OpenCode du projet et manifeste SHA-256, parents avant enfants | Clé publique age |
| `catalogue.tar.gz.age` | Clé privée de l’index F-Droid (`repo-signing.p12`), `config.yml` avec les mots de passe, icônes et dossier `metadata/` | Même clé publique age |

La clé de signature de l’index du catalogue F-Droid est distincte de celle
des APK. Son archive ne contient pas les caches, journaux ni APK publics :
les fichiers publiés sont dans [`panlelapin/android`, dossier `fdroid/repo/`](https://github.com/panlelapin/android/tree/main/fdroid/repo).
L’archive des discussions est un instantané des sessions connues
du service OpenCode sur la machine de création, y compris les sous-agents et
les sessions archivées. Elle ne contient pas la base globale OpenCode.

## Première création, sur le Mac de signature

Prérequis : Python 3.9+, `age` (`brew install age`), JDK avec `keytool`,
OpenCode avec `opencode session export/import`. Depuis le dépôt :

```sh
python3 clefs/coffre.py creer
```

Saisir la passphrase **dans le terminal** quand `age` la demande, jamais en
argument, dans le chat ou dans Git. Le script vérifie le certificat Android,
exporte les sessions, crée la paire age, puis déchiffre les trois archives et
compare leur contenu avant de les installer. Il refuse d’écraser un coffre
existant. Les archives en clair et l’identité privée ne sont jamais écrites
dans le checkout.

Après le message « Coffre créé », versionner ces quatre fichiers :

```sh
git add -- clefs/paire/publique.txt clefs/paire/paire.tar.gz.age \
  clefs/release.tar.gz.age clefs/discussions.tar.gz.age
git commit -m "Sauvegarder la signature BlackBG et les sessions OpenCode chiffrées"
git push origin master
```

## Restaurer dans un nouveau clone

Installer les mêmes outils, cloner BlackBG et se placer à sa racine. Exécuter
uniquement la ou les opérations voulues :

```sh
python3 clefs/coffre.py restaurer-release
python3 clefs/coffre.py restaurer-discussions
```

Chaque commande demande **la même passphrase**. La première crée
`~/.android/blackbg-release/` en `700`, installe les deux fichiers en `600` et
vérifie l’empreinte du certificat. Elle refuse d’écraser un dossier existant.
Sur un Mac avec le SDK du projet, `./build-local.sh` peut ensuite signer la release.

La seconde vérifie les empreintes du manifeste puis importe chaque session
avec `opencode session import --directory <nouveau-clone>`, parent avant
enfant. Utiliser une installation sans ces identifiants de sessions : OpenCode
peut refuser les doublons. Vérifier ensuite avec `opencode session list`.
L’import recrée des conversations, pas les anciens worktrees ni un état de build.

### Restaurer le catalogue F-Droid

Depuis le clone, dans Bash ou Zsh, lancer le bloc suivant. `age` demande la
passphrase du coffre. La clé privée age passe par un tube, pas par un fichier.
La commande refuse de remplacer un répertoire de catalogue existant.

```sh
(
  set -euo pipefail
  umask 077
  parent="$HOME/.local/share"
  dest="$parent/blackbg-fdroid"
  mkdir -p "$parent"
  [[ ! -e "$dest" && ! -L "$dest" ]] || { echo "Destination existante : $dest" >&2; exit 1; }
  dest_tmp=$(mktemp -d "$parent/.blackbg-restauration.XXXXXXXX")
  trap 'rm -rf -- "$dest_tmp"' EXIT
  age -d clefs/paire/paire.tar.gz.age | tar -xzO -f - privee.txt |
    age -d -i - clefs/catalogue.tar.gz.age | tar -xz -f - -C "$dest_tmp"
  mkdir -m 700 "$dest"
  cp -Rp "$dest_tmp/." "$dest/"
)
```

Si le chemin utilisateur ou le SDK a changé, ajuster `keystore` et `sdk_path`
dans le `config.yml` restauré avant d’utiliser `fdroid update`. Réutiliser
`repo-signing.p12` : ne pas régénérer la clé avec `fdroid init`. Pour reprendre
une publication locale, récupérer aussi le `fdroid/repo/` actuel du catalogue
public comme `repo/` dans le répertoire restauré.
