Le Joker
--------

Le **Joker** (identifiant : ``joker``) est un agent d'intelligence artificielle au comportement purement aléatoire.

.. list-table:: Profil de l'agent
   :widths: 30 70

   * - **Identifiant**
     - ``joker``
   * - **Style de jeu**
     - Imprévisible / Aléatoire
   * - **Règle de décision**
     - Tirage uniforme parmi tous les coups légaux
   * - **Évaluation matérielle**
     - Aucune

Algorithme
^^^^^^^^^^

Le fonctionnement du Joker repose sur un principe d'équiprobabilité élémentaire :

1. À son tour de jeu, l'agent recense l'ensemble exhaustif des coups légaux permis par la position courante du plateau.
2. Si au moins un coup légal existe, il en tire un au sort de façon uniforme, chaque coup ayant rigoureusement la même probabilité d'être sélectionné.

L'agent n'effectue aucune distinction entre un déplacement ordinaire, une capture de pièce adverse ou une promotion de pion.

Comportement en partie
^^^^^^^^^^^^^^^^^^^^^^

- **Imprévisibilité totale** : en l'absence de toute fonction d'évaluation de la position ou d'anticipation des réponses adverses, le jeu du Joker ne suit aucun plan ni logique tactique.
- **Référence expérimentale** : bien que faible face à des joueurs ou des agents plus élaborés, le Joker constitue un adversaire de référence (*baseline*) utile pour valider la correction du moteur de jeu et mesurer les progrès d'agents entraînés.
