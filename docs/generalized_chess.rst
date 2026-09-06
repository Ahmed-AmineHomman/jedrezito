Jeu d'Echec Généraliste
=======================

Les Jeux d'Echec Généraliste (JEG) forment un ensemble infini de jeux de plateaux dont les échecs sont un cas particulier. Ce document présente les règles permettant à un jeu de pouvoir être défini comme un JEG.

Règles du jeu
-------------

Les éléménts constitutifs d'un JEG sont les suivants :

- Se joue sur un échiquier rectangulaire de taille `:math:N` par `:math:M` alternant cases sombres et cases claires. `:math:N` et `:math:M` doivent donc être des nombre pairs, pour assurer le même nombre de cases claires et de cases sombres.
- Se joue au tour par tour et oppose deux joueurs, qui jouent chacun leur tour.
- Chaque joueur dispose d'un ensemble de pièce, de couleurs claires ou sombres. Le joueur contrôlant les pièces claires démarre la partie. Chaque joueur démarre avec le même nombre de pièces.
- Les pièces de jeu sont composées de trois types :
    - *Le Roi*: pièce maîtresse ne pouvant être attrapée par l'adversaire, disposant de ses propres règles de mouvement et d'attaque.
    - *Les têtes* : une ou plusieurs pièces spéciales, pouvant être capturées sans entraîner la défaite.
    - *Les pions* : ensemble de pièces disposant des mêmes règles de mouvement et d'attaque, se transformant automatiquement en têtes lorsqu'elles atteignent la ligne opposée de l'échiquier. N'entraînent pas la défaite lorsque capturées.
- Un joueur, pendant son tour, ne peut agir qu'avec une seule pièce. Cette pièce peut soit se déplacer, soit attaquer. Les règles de déplacement et d'attaques sont propres à chaque pièce.
- Les pièces ne peuvent pas se "défendre" d'une attaque : lorsqu'une pièce attaque une autre, elle la capture sans possibilité d'esquive ou de défense, et ce quelques soient les pièces en jeu.

La partie se termine lorsque la pièce maîtresse d'un des adversaires ne peut plus éviter la capture (*mat*). Lorsqu'un joueur ne peut plus jouer sans entraîner la capture de son Roi, mais que ce dernier **n'est pas** menacé au début de son tour, alors la partie se termine en match nul (*pat*). Un joueur ne peut pas faire une action entraînant la menace de son Roi : de telles actions sont considérées invalides, et le joueur doit alors jouer autre chose. S'il ne peut pas, alors la partie se termine en *pat*.

Le nombre de pions ou de têtes n'est pas contraint par les règles. Il doit cependant y avoir un seul et unique Roi.

