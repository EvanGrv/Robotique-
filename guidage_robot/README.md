# Guidage du robot Maqueen Plus

Ce projet contient :

- `firmware.py` : programme MicroPython execute sur la micro:bit.
- `telecommande.py` : telecommande executee sur le Mac.

Les commandes sont lancees depuis la racine du depot.

## Installation

Installez les outils Python si necessaire :

```sh
make setup
```

Flashez le firmware sur la micro:bit :

```sh
make flash
```

Si le volume `MICROBIT` n'est pas monte mais que le port serie fonctionne :

```sh
make install
```

## Telecommande

Lancez la telecommande :

```sh
make run
```

Touches : `Z`/`W` avancer, `S` reculer, `Q`/`A` gauche, `D` droite,
`Espace`/`X` arreter, `+`/`-` regler la vitesse et `I` afficher le statut.
Une direction reste active jusqu'a `Espace`/`X`. La telecommande renouvelle
l'ordre toutes les 200 ms, mais la voiture s'arrete automatiquement apres
700 ms si la liaison est coupee.

Commandes de securite :

```sh
make stop
make status
```
