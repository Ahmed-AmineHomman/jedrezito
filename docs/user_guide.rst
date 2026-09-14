======================
Guide de l'Utilisateur
======================

Jeux Pris en Charge
===================

``jedrezito`` propose un moteur capable de faire tourner un ensemble de jeux "échiquéens" que l'on nomme les *Jeux d'Echecs Généralisés* (JEG). Chaque jeu spécifique appartenant à l'ensemble des JEGs nécessite simplement de définir certains attributs (du plateau, des pièces, etc...), et la combinaison avec le moteur de jeu générique en fait un jeu entièrement défini et jouable.

Jeux d'Echecs Généralisés (JEG)
===============================

Cette section, assez théorique et potentiellement indigeste, couvre la définition formelle de ce que sont les JEGs et leurs principes communs.

.. toctree::
   :maxdepth: 1

    Jeux d'Echecs Généralisés (JEG) <games/generalized_chess.rst>

Jeux Pris en Charge
===================

Cette section décrit tous les jeux proposés par ``jedrezito``.

.. toctree::
   :maxdepth: 1

    Echecs <games/chess.rst>
    Mini-échecs <games/mini_chess.rst>

IAs Généralistes
================

Les IAs Généralistes sont des IAs capables de jouer à n'importe quel JEG. Elles sont définies à l'aide d'algorithmes plus ou moins complexes et plus ou moins déterministes couvrant leur comportement dans tous les cas pouvant survenir au cours d'une partie de JEG.

.. toctree::
    :maxdepth: 1

    Le Joker ("joker") <ais/joker.rst>
    La Brute ("bully") <ais/bully.rst>
    Le Chat Echaudé ("scaredycat") <ais/scaredycat.rst>
