# BlackBG

Application Android en Kotlin, `minSdk = 36`, sans icône dans le lanceur.
Exposer un aperçu via `android.intent.action.SET_WALLPAPER`. À la confirmation,
appliquer un fond statique noir opaque aux écrans d’accueil et de verrouillage.
L’annulation ne doit rien modifier. Ne jamais lire ni sauvegarder les anciens
fonds, ni demander l’accès aux fichiers. Si Android refuse l’application du
fond, afficher l’erreur. Compiler la release signée avec `./build-local.sh`.
Livrer uniquement `arm64-v8a`, avec R8 et la réduction des ressources activés.
Conserver la clé de release hors du dépôt (`~/.android/blackbg-release/`).
