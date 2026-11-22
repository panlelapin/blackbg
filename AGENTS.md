# BlackBG

Application Android en Kotlin, `minSdk = 36`, sans icône dans le lanceur.
Exposer un aperçu via `android.intent.action.SET_WALLPAPER`, avec quatre choix
accessibles même en fenêtre basse : Lockscreen, Homescreen, Both et Cancel.
Avant le choix, Cancel et Retour ne doivent rien modifier. Après le choix,
appliquer une seule fois le fond noir opaque aux écrans demandés, même en cas
de rotation ou de Retour. Renvoyer `RESULT_OK` après succès ; en cas de refus,
afficher l’erreur et permettre un nouvel essai. Ne jamais lire ni sauvegarder
les anciens fonds, ni demander l’accès aux fichiers. Envoyer le PNG monochrome
4096 × 4096 en flux : pas de bitmap dimensionné selon l’écran dans l’application.
Android gère le recadrage et les écrans secondaires ; au-delà de 4096 pixels
sur un axe ou sur un écran non pris en charge, le rendu dépend du système.
Compiler la release signée avec `./build-local.sh`.
Livrer uniquement `arm64-v8a`, avec R8 et la réduction des ressources activés.
Conserver la clé de release hors du dépôt (`~/.android/blackbg-release/`).
