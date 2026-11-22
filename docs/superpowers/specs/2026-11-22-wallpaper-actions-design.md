# BlackBG : icônes et choix du fond d’écran

Dans le sélecteur de fonds d’écran Android, afficher un disque noir à fin contour blanc. Ne pas ajouter d’entrée dans le lanceur.

Conserver le fond noir de l’écran BlackBG. Remplacer les deux boutons par quatre lignes cliquables alignées à gauche, centrées verticalement en bloc. Chaque ligne commence par un pictogramme blanc sur un disque noir à fin contour blanc :

| Texte exact | Pictogramme | Action |
|---|---|---|
| Lockscreen | Cadenas | Écran de verrouillage uniquement |
| Homescreen | Maison | Écran d’accueil uniquement |
| Both | Petit cadenas à gauche, petite maison à droite | Les deux écrans |
| Cancel | Croix diagonale | Fermer sans rien modifier |

En cas de refus ou d’échec, afficher exactement « Couldn’t apply wallpaper. » et laisser l’utilisateur réessayer. Le fond reste noir opaque et statique. Ne jamais lire ni sauvegarder les anciens fonds et ne pas demander d’accès aux fichiers.

## Approche

Utiliser les vues Android existantes et des icônes vectorielles natives : elles restent nettes à toutes les densités, sans dépendance ni variantes bitmap. Conserver le traitement asynchrone et les marges système.

Conserver Kotlin, `minSdk = 36`, `arm64-v8a` uniquement, R8 et la réduction des ressources. Compiler la release signée avec `./build-local.sh`, avec la clé hors dépôt (`~/.android/blackbg-release/`).
