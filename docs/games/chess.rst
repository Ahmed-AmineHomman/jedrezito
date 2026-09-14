Échecs
------

La variante des **Échecs** proposée dans ``jedrezito`` constitue l'adaptation du jeu d'échecs traditionnel aux règles fondamentales des Jeux d'Échecs Généralisés (JEG).

Plateau et armées
^^^^^^^^^^^^^^^^^

La partie se déroule sur un échiquier classique de **8×8** cases.

Chaque camp contrôle une armée de 16 pièces :

- **1 Roi** : la pièce maîtresse du jeu, dont la mise en échec et mat détermine l'issue de la partie ;
- **7 têtes** :
  - 1 Reine (valeur matérielle : 9) ;
  - 2 Tours (valeur matérielle : 5) ;
  - 2 Fous (valeur matérielle : 3) ;
  - 2 Cavaliers (valeur matérielle : 3) ;
- **8 Pions** (valeur matérielle : 1).

Disposition initiale
^^^^^^^^^^^^^^^^^^^^

Les pièces sont alignées sur les deux premières rangées de chaque joueur :

- **Première rangée** : Tour, Cavalier, Fou, Reine, Roi, Fou, Cavalier, Tour ;
- **Deuxième rangée** : 8 Pions.

Le camp adverse présente une disposition symétrique par rotation de 180°.

Déplacements et captures
^^^^^^^^^^^^^^^^^^^^^^^^

Chaque type de pièce suit ses mouvements géométriques caractéristiques :

- **Roi** : se déplace et capture d'une case dans toutes les directions (sauts d'amplitude 1 en ligne, colonne et diagonale).
- **Reine** : parcourt et capture sans limite de portée le long des lignes, des colonnes et des diagonales.
- **Tour** : parcourt et capture sans limite de portée le long des lignes et des colonnes.
- **Fou** : parcourt et capture sans limite de portée le long des diagonales.
- **Cavalier** : effectue des sauts en « L » (deux cases dans une direction puis une case perpendiculaire), en franchissant librement les cases intermédiaires.
- **Pion** : se déplace d'une case vers l'avant uniquement, et capture d'une case en diagonale vers l'avant uniquement. Lorsqu'un pion atteint la dernière rangée de l'échiquier, il est immédiatement promu en l'une des têtes autorisées : Reine, Tour, Fou ou Cavalier.

Spécificités au sein des JEG
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Afin de respecter la formulation formelle des JEG — reposant sur des déplacements exclusivement géométriques et un état de jeu instantané sans mémoire historique — cette variante présente quelques différences notables avec les règles internationales classiques :

- **Pas de roque** : aucun coup ne permet de déplacer deux pièces simultanément ;
- **Pas de prise en passant** : la capture d'un pion adverse s'effectue strictement sur la case d'arrivée de la pièce capturée ;
- **Pas de double pas initial du pion** : les pions avancent systématiquement d'une seule case à chaque coup.

L'objectif demeure classique : attaquer le Roi adverse jusqu'à le placer en échec sans coup légal de parade possible (**mat**).
