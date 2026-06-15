# Controle simple de position

Le firmware applique directement cette boucle :

```text
while:
    update_position()
    move_to(1 m)
    sleep(10 ms)
```

## Calcul de la position

Chaque compteur de roue augmente positivement. Le registre de direction permet
de savoir si les ticks doivent etre ajoutes ou retires :

```text
delta = compteur_actuel - compteur_precedent
ticks_cumules += delta * direction

direction avant   = +1
direction arriere = -1
direction arret   = 0
```

Un saut impossible superieur a `100 ticks` entre deux boucles est ignore. Cela
evite qu'une difference negative interpretee sur 16 bits devienne `65535
ticks`, soit environ `110 m`.

La distance moyenne est :

```text
distance_m = ((ticks_gauche + ticks_droite) / 2) / ticks_par_metre
```

La valeur theorique utilisee est :

```text
ticks_par_metre = 80 / (2 * pi * 0.0215)
                 = environ 592.2
```

## Commande proportionnelle

```text
erreur_m = 1.0 - distance_m
commande = erreur_m * KP
```

- commande positive : direction `1`, avance ;
- commande negative : direction `2`, recule avec une vitesse `-commande` ;
- commande nulle : arret.

## Boutons

- `A` : aller vers la position `1 m`.
- `B` : arreter le robot.
- `A+B` : arreter et remettre a zero les compteurs materiels, les anciens
  compteurs et la position cumulee.

Le robot affiche son etat chaque seconde sur le port serie.
