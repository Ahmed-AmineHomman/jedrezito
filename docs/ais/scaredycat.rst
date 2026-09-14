================
Le Chat Échaudé
================

**Le Chat Échaudé** (identifiant : ``scaredycat``) est une intelligence artificielle prudente dont la ligne de conduite principale est la protection mutuelle systématique de ses pièces nobles (les têtes).

Algorithme
^^^^^^^^^^

À chaque tour de jeu, l'agent simule l'ensemble de ses coups légaux et évalue l'intégrité défensive de son armée à l'issue de chacun d'eux :

1. **Recherche de sécurité intégrale** :
   Un coup est qualifié de *sûr* si, une fois joué, chaque tête alliée (Reine, Tours, Fous, Cavaliers) restante sur le plateau est protégée par au moins une autre pièce alliée.

   - S'il existe un ou plusieurs coups sûrs, le Chat Échaudé applique parmi ceux-ci la stratégie de **La Brute** : il sélectionne en priorité la capture de la pièce adverse la plus valorisée avec sa pièce la plus modeste. S'il n'y a aucune prise sûre, il joue au hasard parmi les coups sûrs.

2. **Minimisation de l'exposition** :
   Si aucun coup légal ne permet de maintenir ou d'obtenir la protection de toutes ses têtes, l'agent opère un choix défensif de moindre mal. Il retient le coup qui minimise la valeur maximale parmi les têtes laissées sans couverture (en préservant en priorité sa Reine, puis ses Tours, Fous et Cavaliers).

3. **Fin de partie sans tête** :
   Dans l'éventualité où l'agent ne possède plus aucune tête sur l'échiquier, son comportement bascule vers une phase de contre-attaque : il pousse ses pions vers l'avant (en saisissant les occasions de capture sur leur chemin) dans le but d'obtenir une promotion et de faire renaître une nouvelle tête.

Comportement en partie
^^^^^^^^^^^^^^^^^^^^^^

- **Structure défensive dense** : Le Chat Échaudé maintient ses pièces regroupées en réseaux de défense mutuelle, évitant les incursions téméraires et les pièces isolées.
- **Résistance accrue** : comparé à des approches purement opportunistes, cet agent cède beaucoup plus difficilement son matériel lourd face aux attaques directes, mais peut parfois adopter une attitude trop passive lorsqu'il est contraint de replier ses pièces pour les défendre.
