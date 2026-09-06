Jeux d'Échecs Généralisés
=========================

Les **Jeux d'Échecs Généralisés (JEG)** forment une famille de jeux de plateau abstraits partageant la structure fondamentale des échecs : deux armées symétriques s'affrontent sur un échiquier, chaque joueur déplaçant une unique pièce à son tour, avec pour objectif principal de mater le Roi adverse.

Les règles suivantes définissent le noyau commun que doit respecter un jeu pour être considéré comme un JEG.

1. Propriétés générales
---

Un JEG est un jeu :

* à **deux joueurs** ;
* **déterministe** : l'évolution de la partie ne fait intervenir aucun mécanisme aléatoire ;
* à **information parfaite** : l'état complet de la partie est connu des deux joueurs ;
* au **tour par tour**, les deux joueurs jouant alternativement.

Le joueur contrôlant les pièces claires joue le premier.

Dans les règles fondamentales d'un JEG, l'état d'une partie est entièrement et exclusivement constitué par :

* l'occupation des cases du plateau ;
* pour chaque pièce présente, son camp et son type ;
* le joueur dont c'est le tour.

Aucune autre information n'appartient à l'état du jeu.

En particulier, les règles fondamentales d'un JEG ne dépendent pas de l'historique de la partie, du nombre de coups déjà joués, d'un événement passé, d'une capacité temporaire ou de toute autre information qui ne serait pas représentée par l'état courant du plateau.

La variante d'épuisement des coups définie plus loin constitue une exception explicite à cette dernière propriété.

2. Échiquier
---

Un JEG se joue sur un échiquier rectangulaire de taille `N × M`, alternant cases claires et cases sombres.

`N` et `M` sont des nombres pairs.

La dimension séparant les deux joueurs comporte au moins quatre lignes, afin que les deux lignes de départ de chaque joueur soient distinctes.

Une case peut contenir au maximum une pièce.

3. Camps et armées
---

Chaque joueur contrôle une armée composée de pièces claires ou sombres.

Les deux joueurs disposent initialement d'armées strictement équivalentes :

* même nombre total de pièces ;
* même nombre de pièces de chaque type ;
* mêmes règles de déplacement et de capture pour les types correspondants ;
* mêmes valeurs matérielles pour les types correspondants.

La disposition initiale des deux camps est symétrique par rotation de 180° de l'échiquier, en échangeant les couleurs des pièces.

Les orientations « vers l'avant » et « vers l'arrière » sont inversées entre les deux camps.

Les cases non occupées au début de la partie restent libres : il n'est pas nécessaire de remplir entièrement les deux premières lignes de chaque camp.

4. Types de pièces
---

Chaque armée contient exactement trois catégories de pièces :

* un Roi ;
* un ensemble de têtes ;
* un ensemble de pions.

4.1. Le Roi
^^^^^^^^^^^^

Chaque joueur possède un et un seul **Roi**.

Le Roi est la pièce maîtresse du jeu. Sa capture n'est jamais effectivement jouée : la partie se termine dès que sa capture devient inévitable selon les règles du mat.

Le Roi possède des règles fixes de déplacement et de capture propres à son type.

Le Roi n'a pas de valeur matérielle finie. Il peut être considéré comme possédant une valeur infinie, mais il n'intervient jamais dans le calcul de la valeur matérielle d'une armée.

4.2. Les têtes
^^^^^^^^^^^^^^

Chaque joueur possède un nombre **impair et strictement positif** de têtes.

Les têtes constituent les pièces spécialisées de l'armée.

Il peut exister plusieurs types de têtes, chacun possédant :

* ses propres règles fixes de déplacement ;
* ses propres règles fixes de capture ;
* sa propre valeur matérielle.

Plusieurs pièces peuvent appartenir au même type de tête.

Toutes les têtes appartenant au même type possèdent nécessairement la même valeur matérielle, indépendamment :

* de leur camp ;
* de leur position initiale ;
* de la couleur de la case sur laquelle elles se trouvent ;
* de leur historique de déplacement.

La capture d'une tête n'entraîne pas directement la défaite.

4.3. Les pions
^^^^^^^^^^^^^^

Chaque joueur possède un nombre **pair et strictement positif** de pions.

Tous les pions d'un même JEG obéissent aux mêmes règles de déplacement, de capture et de promotion, avec une orientation inversée entre les deux camps.

Tous les pions possèdent la même valeur matérielle.

La capture d'un pion n'entraîne pas directement la défaite.

Lorsqu'un pion atteint la dernière ligne de l'échiquier du côté adverse, il est immédiatement promu en une tête.

Les types de têtes accessibles par promotion sont définis par les règles du JEG.

Si plusieurs promotions sont possibles, le joueur choisit parmi les types autorisés.

Un pion ne peut jamais être promu en Roi.

Une fois promu, il possède les règles de déplacement, les règles de capture et la valeur matérielle du type de tête obtenu.

5. Disposition initiale
---

Les pièces de chaque joueur sont placées exclusivement sur les deux lignes les plus proches de son bord de l'échiquier.

Tous les pions sont placés sur la deuxième ligne.

Le Roi et toutes les têtes sont placés sur la première ligne.

Le Roi ne possède aucune case initiale universellement imposée : chaque JEG définit librement sa position de départ sur la première ligne.

La disposition du joueur opposé est obtenue par symétrie de la disposition du premier joueur.

La position initiale doit être une position jouable :

* aucun des deux Rois ne doit être en échec ;
* le joueur contrôlant les pièces claires doit disposer d'au moins un coup légal.

La partie ne peut donc pas être terminée par mat ou par pat avant que le premier coup ait été joué.

6. Valeur matérielle des pièces
---

Tout type de pièce autre que le Roi possède obligatoirement une **valeur matérielle**, définie par un nombre entier strictement positif.

Cette valeur est attachée au type de pièce et non à une pièce individuelle.

Deux pièces appartenant au même type possèdent donc toujours la même valeur.

La valeur matérielle n'a aucune incidence sur :

* les règles de déplacement ;
* les règles de capture ;
* la légalité d'un coup ;
* les menaces ;
* l'échec ;
* le mat ;
* le pat ;
* les possibilités de promotion.

Elle constitue uniquement une mesure conventionnelle de la puissance matérielle d'une pièce.

La **valeur matérielle d'une armée** à un instant donné est définie comme la somme des valeurs matérielles de toutes les pièces de cette armée encore présentes sur le plateau, à l'exclusion du Roi.

Si l'on note `P` l'ensemble des pièces d'une armée autres que son Roi et `v(p)` la valeur de la pièce `p`, alors :

`V = Σ v(p)`

pour toutes les pièces `p` encore présentes sur le plateau.

7. Règles de déplacement et de capture
---

Chaque type de pièce possède :

* un ensemble fixe de **mouvements de déplacement** ;
* un ensemble fixe de **mouvements de capture**.

Les deux ensembles peuvent être identiques ou différents.

Les mouvements sont exclusivement géométriques et sont définis à partir de deux formes élémentaires :

* les **rayons** ;
* les **sauts**.

7.1. Repère relatif
^^^^^^^^^^^^^^^^^^^

Les mouvements d'une pièce sont décrits relativement à sa case courante.

On considère deux axes :

* l'axe des **lignes**, orienté vers l'avant du camp de la pièce ;
* l'axe des **colonnes**, perpendiculaire au précédent.

Un déplacement relatif `(a, b)` correspond donc à :

* `a` cases selon l'axe des lignes ;
* `b` cases selon l'axe des colonnes.

L'orientation vers l'avant est inversée entre les deux camps.

Les règles géométriques d'un même type sont ainsi identiques pour les deux joueurs.

7.2. Rayons
^^^^^^^^^^^

Un **rayon** permet à une pièce de parcourir plusieurs cases dans une direction rectiligne.

Il existe trois familles de rayons :

* les rayons de **ligne** ;
* les rayons de **colonne** ;
* les rayons **diagonaux**.

Chaque famille de rayons utilisée par une pièce possède une **portée**, qui est :

* soit un nombre entier strictement positif ;
* soit infinie.

Un rayon de ligne de portée `p` autorise les déplacements relatifs :

`(±k, 0)`

pour tout entier `k` tel que `1 ≤ k ≤ p`.

Un rayon de colonne de portée `p` autorise les déplacements relatifs :

`(0, ±k)`

pour tout entier `k` tel que `1 ≤ k ≤ p`.

Un rayon diagonal de portée `p` autorise les déplacements relatifs :

`(±k, ±k)`

pour tout entier `k` tel que `1 ≤ k ≤ p`.

Lorsque la portée est infinie, `k` n'est limité que par les dimensions de l'échiquier.

Une pièce se déplaçant selon un rayon ne peut franchir aucune pièce.

Toutes les cases situées strictement entre la case de départ et la case d'arrivée doivent donc être libres.

La première case occupée rencontrée bloque le rayon :

* si elle contient une pièce alliée, elle ne peut pas être atteinte ;
* si elle contient une pièce adverse et que le rayon considéré est autorisé pour la capture, cette pièce peut être capturée ;
* aucune case située au-delà ne peut être atteinte au cours de ce mouvement.

7.3. Sauts
^^^^^^^^^^

Un **saut** est défini par un couple d'entiers naturels `(a, b)`, avec `a` et `b` non simultanément nuls.

Un saut `(a, b)` autorise les déplacements relatifs obtenus par les combinaisons de signes :

`(±a, ±b)`

Les doublons éventuels sont ignorés.

Les coordonnées ne sont pas interchangeables automatiquement.

Ainsi, un saut `(1, 2)` n'implique pas le saut `(2, 1)`. Si les deux sont souhaités, ils doivent être définis séparément.

Un saut ne dépend pas de l'occupation des cases situées entre la case de départ et la case d'arrivée.

La pièce franchit donc librement toute pièce éventuellement présente sur ces cases.

Seule l'occupation de la case d'arrivée intervient.

7.4. Déplacement et capture
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Les mouvements autorisés pour le déplacement et ceux autorisés pour la capture sont définis séparément.

Un type de pièce peut donc, par exemple :

* se déplacer selon certains sauts et capturer selon d'autres ;
* se déplacer selon des rayons et capturer selon des sauts ;
* utiliser exactement les mêmes mouvements pour le déplacement et la capture.

Lors d'un déplacement, la case d'arrivée doit être vide.

Lors d'une capture, la case d'arrivée doit contenir une pièce adverse.

Les règles géométriques ne peuvent dépendre d'aucune autre caractéristique de la position que :

* la case de départ ;
* la case d'arrivée ;
* les limites de l'échiquier ;
* et, dans le cas d'un rayon, l'occupation des cases situées entre le départ et l'arrivée.

En particulier, l'occupation d'une case extérieure au trajet considéré ne peut jamais autoriser ou interdire un mouvement.

7.5. Mouvements vers l'avant
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Les mouvements du Roi et des têtes sont toujours symétriques autour de leur case de départ.

Cette symétrie résulte directement de la définition des rayons et des sauts.

Les pions peuvent faire exception à cette règle.

Pour leurs mouvements de déplacement et de capture, les règles d'un JEG peuvent imposer la restriction **vers l'avant uniquement**.

Lorsqu'elle s'applique, seuls les mouvements dont la composante selon l'axe des lignes est strictement positive sont conservés.

Ainsi :

* un saut `(1, 0)` restreint vers l'avant permet uniquement d'avancer d'une case ;
* un saut `(1, 1)` restreint vers l'avant permet uniquement les deux diagonales dirigées vers l'avant ;
* un rayon de ligne restreint vers l'avant ne s'étend que dans la direction du camp adverse ;
* un rayon diagonal restreint vers l'avant ne conserve que les deux directions diagonales orientées vers le camp adverse ;
* un rayon de colonne ne produit aucun mouvement lorsqu'il est soumis à cette restriction.

La restriction vers l'avant peut être définie indépendamment pour les mouvements de déplacement et de capture des pions.

7.6. Exemples classiques
^^^^^^^^^^^^^^^^^^^^^^^^

Les pièces des échecs classiques peuvent notamment être décrites de la manière suivante :

* **Pion** :

  * déplacement : saut `(1, 0)`, vers l'avant uniquement ;
  * capture : saut `(1, 1)`, vers l'avant uniquement.

* **Tour** :

  * rayons de ligne et de colonne de portée infinie.

* **Cavalier** :

  * sauts `(1, 2)` et `(2, 1)`.

* **Fou** :

  * rayons diagonaux de portée infinie.

* **Reine** :

  * rayons de ligne, de colonne et diagonaux de portée infinie.

* **Roi** :

  * sauts `(1, 0)`, `(0, 1)` et `(1, 1)`.

Ces exemples n'imposent aucune de ces règles particulières aux JEG : ils illustrent uniquement le système de définition des mouvements.

8. Définition d'un coup
---

À son tour, un joueur doit choisir exactement une de ses pièces et effectuer avec elle un coup légal.

Il n'est pas possible de passer volontairement son tour.

Un coup est défini par :

* une case de départ ;
* une case d'arrivée ;
* et, lorsqu'une promotion a lieu et que plusieurs promotions sont possibles, le type de tête choisi.

La case de départ doit contenir une pièce appartenant au joueur actif.

La case d'arrivée doit être :

* soit vide ;
* soit occupée par une unique pièce adverse.

Un coup est de l'un des deux types suivants :

* **déplacement** : la case d'arrivée est vide et le mouvement appartient aux mouvements de déplacement autorisés pour la pièce ;
* **capture** : la case d'arrivée contient une pièce adverse et le mouvement appartient aux mouvements de capture autorisés pour la pièce.

L'application d'un coup produit le nouvel état du jeu de la manière suivante :

1. la pièce jouée est retirée de sa case de départ ;
2. si le coup est une capture, la pièce adverse occupant la case d'arrivée est retirée du plateau ;
3. la pièce jouée est placée sur la case d'arrivée ;
4. si elle remplit les conditions de promotion, elle est remplacée par la tête correspondante ;
5. le tour est donné à l'autre joueur.

Aucune autre modification de l'état du jeu ne résulte d'un coup.

Il en découle notamment qu'un coup ne peut pas modifier plusieurs pièces alliées, capturer plusieurs pièces adverses ou produire un effet sur une case distincte de sa case d'arrivée.

9. Attaque et menace
---

Une pièce **menace** une case lorsqu'elle pourrait capturer une pièce adverse située sur cette case selon ses mouvements de capture, abstraction faite de la contrainte liée à la sécurité de son propre Roi.

Pour déterminer si une case est menacée :

* la géométrie du mouvement de capture doit être respectée ;
* dans le cas d'un rayon, aucune pièce ne doit bloquer le trajet jusqu'à cette case.

Une capture porte toujours sur l'unique pièce adverse occupant la case d'arrivée.

Lorsqu'une capture légale est jouée, cette pièce est retirée du plateau sans résolution supplémentaire.

Une capture ne dépend donc d'aucune valeur matérielle, probabilité, caractéristique défensive ou mécanisme de résistance.

10. Échec et légalité des coups
---

Un Roi est **en échec** lorsque sa case est menacée par au moins une pièce adverse.

Un coup est légal si :

* son déplacement géométrique est autorisé pour le type de pièce joué ;
* la case d'arrivée possède l'occupation requise pour un déplacement ou une capture ;
* dans le cas d'un rayon, aucune pièce ne bloque le trajet ;
* après application du coup, le Roi du joueur ayant joué n'est pas en échec.

Un joueur ne peut donc jamais effectuer un coup laissant son propre Roi menacé.

Lorsqu'un joueur commence son tour avec son Roi en échec, il doit jouer un coup légal supprimant cet échec.

11. Fin de partie
---

Dans les règles fondamentales d'un JEG, une partie se termine uniquement par **mat** ou par **pat**.

11.1. Mat
^^^^^^^^^

Un joueur est **mat** lorsque :

1. son Roi est en échec ;
2. il ne possède aucun coup légal permettant de supprimer cet échec.

La partie se termine immédiatement.

L'adversaire remporte la partie.

Le Roi n'est jamais effectivement capturé.

11.2. Pat
^^^^^^^^^

Un joueur est **pat** lorsque :

1. son Roi n'est pas en échec ;
2. il ne possède aucun coup légal.

La partie se termine immédiatement par un match nul.

Toute position qui n'est ni un mat ni un pat est non terminale dans les règles fondamentales du JEG.

12. Variante d'épuisement des coups
---

Un JEG peut proposer une variante facultative appelée **épuisement des coups**.

Cette variante n'appartient pas aux règles fondamentales obligatoires d'un JEG.

Lorsqu'elle est activée, un nombre entier strictement positif `T` est fixé avant le début de la partie.

Chaque joueur dispose alors d'au plus `T` tours de jeu.

Pour les besoins de cette variante uniquement, l'état de la partie est complété par le nombre de tours déjà joués par chacun des deux joueurs.

Le mat et le pat conservent leur priorité : si l'une de ces conditions survient avant l'épuisement des coups, la partie se termine immédiatement selon les règles habituelles.

Dans le cas contraire, la partie se termine dès que chacun des deux joueurs a joué exactement `T` coups.

On calcule alors la valeur matérielle de chaque armée restante.

Le joueur dont l'armée possède la plus grande valeur matérielle remporte la partie.

Si les deux armées possèdent la même valeur matérielle, la partie se termine par un match nul.

Le Roi n'intervient pas dans ce calcul.

13. Conséquences et exemples d'exclusion
---

Les règles précédentes définissent positivement les états possibles du jeu, les mouvements possibles et les transitions entre deux états.

Il en résulte notamment qu'un JEG ne peut pas comporter, dans son noyau fondamental :

* de mécanisme aléatoire ;
* d'information cachée ;
* de déplacement simultané de plusieurs pièces ;
* de capture de plusieurs pièces en un seul coup ;
* d'effet de zone ;
* de création spontanée de pièces ;
* de modification temporaire ou permanente des capacités d'une pièce ;
* de règles dépendant de l'historique de la partie ;
* de capture d'une pièce située sur une autre case que la case d'arrivée ;
* de mécanisme de combat supplémentaire après qu'une capture a été choisie ;
* de déplacement conditionné par l'occupation d'une case sans rapport avec le trajet géométrique de la pièce ;
* de mouvement autre qu'un rayon ou un saut tel que défini précédemment.

Ces éléments constituent des conséquences de la définition et non des règles supplémentaires indépendantes.

14. Rapport avec les échecs classiques
---

Les JEG sont conçus pour reproduire la structure essentielle des échecs, mais ils n'englobent pas intégralement les règles des échecs classiques.

Certaines règles particulières des échecs nécessitent en effet un état ou une transition que le noyau des JEG ne permet pas de représenter.

En particulier :

* le **roque** déplace deux pièces au cours d'un même coup et dépend du fait que le Roi et la Tour concernés n'aient jamais été déplacés ;
* la **prise en passant** dépend du coup immédiatement précédent et capture un pion qui ne se trouve pas sur la case d'arrivée ;
* la **répétition de position** dépend de l'historique des positions rencontrées ;
* la **règle des cinquante coups** dépend du nombre de coups écoulés depuis certains événements.

Les échecs classiques ne constituent donc pas, dans leur totalité, un JEG au sens strict de cette définition.

En revanche, leur structure fondamentale — échiquier, deux camps symétriques, Roi, pièces spécialisées, pions, déplacements géométriques par rayons et sauts, captures, promotion, échec, mat et pat — appartient bien au cadre des JEG.
