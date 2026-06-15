# Test BBC micro:bit

`microbit_test.py` utilise MicroPython et doit s'executer sur la micro:bit.
Il ne peut pas etre lance directement avec `python` ou `python3` sur le Mac.

## Envoyer le programme sur la carte

Branchez la micro:bit, puis lancez :

```sh
make flash
```

Cette commande envoie `microbit_test.py` par defaut. Pour choisir un autre
programme :

```sh
make flash fichier.py
```

La matrice LED doit alterner entre un coeur et un visage heureux.

Pour ouvrir la console serie :

```sh
make serial
```

Quittez la console serie avec `Ctrl-]`.

## Diagnostiquer la Maqueen Plus

Le diagnostic arrete d'abord les moteurs, puis lit la version et les capteurs
sans faire avancer la voiture :

```sh
make flash maqueen_diagnostic.py
make serial
```

## Telecommander la Maqueen par USB

Installez le controleur sur la micro:bit :

```sh
make flash maqueen_remote.py
```

Lancez ensuite la telecommande :

```sh
make remote
```

Touches : `Z`/`W` avancer, `S` reculer, `Q`/`A` gauche, `D` droite,
`Espace`/`X` arreter, `+`/`-` regler la vitesse et `I` afficher le statut.
Une direction reste active jusqu'a `Espace`/`X`. La telecommande renouvelle
l'ordre toutes les 200 ms, mais la voiture s'arrete automatiquement apres
700 ms si la liaison est coupee.
