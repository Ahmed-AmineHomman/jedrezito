Échecs
------

La variante des **Échecs** proposée dans ``jedrezito`` constitue l'adaptation du jeu d'échecs traditionnel aux règles fondamentales des Jeux d'Échecs Généralisés (JEG).

Plateau et armée
^^^^^^^^^^^^^^^^

La partie se dispute sur un échiquier de **8×8** cases. Chaque camp dispose initialement d'une armée de 16 pièces :

.. list-table:: Composition de l'armée
   :widths: 15 15 12 12 46
   :header-rows: 1

   * - Pièce
     - Catégorie
     - Quantité
     - Valeur
     - Mouvements et captures
   * - **Roi**
     - Roi
     - 1
     - ∞
     - Déplacement et capture d'une case dans toutes les directions.
   * - **Reine**
     - Tête
     - 1
     - 9
     - Rayons orthogonaux et diagonaux sans limite de portée.
   * - **Tour**
     - Tête
     - 2
     - 5
     - Rayons orthogonaux (lignes et colonnes) sans limite de portée.
   * - **Fou**
     - Tête
     - 2
     - 3
     - Rayons diagonaux sans limite de portée.
   * - **Cavalier**
     - Tête
     - 2
     - 3
     - Sauts en « L » (1, 2) et (2, 1) avec franchissement des pièces intermédiaires.
   * - **Pion**
     - Pion
     - 8
     - 1
     - Déplacement d'une case vers l'avant ; capture d'une case en diagonale avant ; promotion en tête à la dernière rangée.

Disposition initiale
^^^^^^^^^^^^^^^^^^^^

Les pièces occupent les deux premières rangées de chaque joueur (la disposition du camp adverse étant symétrique par rotation de 180°) :

.. list-table:: Placement initial (camp blanc)
   :widths: 25 75
   :header-rows: 1

   * - Rangée
     - Pièces (de gauche à droite)
   * - **1** (arrière)
     - Tour, Cavalier, Fou, Reine, Roi, Fou, Cavalier, Tour
   * - **2** (pions)
     - 8 Pions

Spécificités
^^^^^^^^^^^^

Afin de respecter la formulation formelle des JEG — reposant sur des déplacements exclusivement géométriques et un état de jeu instantané sans mémoire historique — cette variante présente quelques différences notables avec les règles internationales classiques :

- **Pas de roque** : aucun coup ne permet de déplacer deux pièces simultanément ;
- **Pas de prise en passant** : la capture d'un pion s'effectue exclusivement sur la case de destination de la pièce ciblée ;
- **Pas de double pas initial du pion** : les pions avancent systématiquement d'une seule case à chaque coup.

L'objectif demeure classique : attaquer le Roi adverse jusqu'à le placer en échec sans coup légal de parade possible (**mat**).
