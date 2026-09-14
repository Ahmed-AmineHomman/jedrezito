================
Démarrage Rapide
================

Ce guide présente les étapes nécessaires pour installer l'environnement et lancer l'application ``jedrezito``.

Prérequis
---------

Assurez-vous de disposer d'une version de Python 3.10 ou supérieure installée sur votre système.

Installation
------------

1. Récupérez les sources du projet en clonant le dépôt ou en téléchargeant l'archive du code source :

   .. code-block:: bash

      git clone https://github.com/Ahmed-AmineHomman/jedrezito.git
      cd jedrezito

2. Installez les dépendances requises pour exécuter l'application :

   .. code-block:: bash

      pip install -r requirements.txt

Lancement de l'application
--------------------------

Pour démarrer l'interface graphique de ``jedrezito``, exécutez la commande suivante depuis la racine du dépôt :

.. code-block:: bash

   python app.py

L'application s'ouvre alors avec la configuration par défaut.

Pour découvrir les différentes options de lancement disponibles en ligne de commande (comme le choix de la variante ou de la langue), vous pouvez consulter l'aide intégrée :

.. code-block:: bash

   python app.py --help
