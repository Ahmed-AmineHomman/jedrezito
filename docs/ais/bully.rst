========
La Brute
========

**La Brute** (identifiant : ``bully``) est une intelligence artificielle opportuniste et agressive, guidée par la recherche systématique et immédiate du plus grand gain matériel possible.

Algorithme
^^^^^^^^^^

Lorsqu'arrive son tour de jeu, l'agent examine l'ensemble des coups légaux disponibles et applique les règles de décision suivantes :

1. **Priorité aux captures** :
   L'agent filtre l'ensemble des coups pour isoler ceux qui capturent une pièce adverse.

   - **Cible la plus précieuse** : parmi tous les coups de capture envisageables, l'agent privilégie en premier lieu ceux qui visent la pièce adverse possédant la valeur matérielle la plus forte (le Roi ayant une priorité absolue, suivi de la Reine, des Tours, des Fous et Cavaliers, puis des Pions).
   - **Attaquant de moindre valeur** : si plusieurs de ses propres pièces peuvent capturer la cible de valeur maximale, l'agent préfère effectuer la capture avec sa pièce la moins coûteuse (par exemple, capturer une pièce avec un pion plutôt qu'avec une dame).

2. **Coup de repli aléatoire** :
   Si la position ne propose aucun coup de capture légal, l'agent choisit alors uniformément au hasard parmi tous les déplacements légaux disponibles.

Comportement en partie
^^^^^^^^^^^^^^^^^^^^^^

- **Pression immédiate** : La Brute punit impitoyablement toute pièce adverse laissée sans défense à sa portée.
- **Myopie tactique** : focalisée exclusivement sur le coup immédiat, La Brute ne calcule pas les conséquences au coup suivant. Elle accepte volontiers de capturer une pièce adverse même si la case d'arrivée est gardée et que sa propre pièce sera immédiatement reprise, ce qui la rend vulnérable aux pièges et aux sacrifices positionnels.
