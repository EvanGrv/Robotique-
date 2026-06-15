# Controle de position en distance

Le firmware suit directement le modele :

```text
while True:
    update_position()
    move_to(target_distance)
    sleep(10)
```

## Position signee

La Maqueen fournit :

- un compteur positif par roue ;
- une direction moteur : `0=arret`, `1=avant`, `2=arriere`.

Le firmware cumule une distance signee :

```text
delta_ticks = compteur_actuel - compteur_precedent
signe = +1 si direction=1, -1 si direction=2
position_m += delta_ticks * signe / ticks_par_metre
```

La position du robot est :

```text
position_m = (position_gauche_m + position_droite_m) / 2
```

## Controle en distance

La commande ne depend pas du temps :

```text
erreur_m = distance_cible_m - position_m
commande = POSITION_KP * erreur_m
```

Avec :

```text
POSITION_KP = 200
```

Conversion de la commande vers la Maqueen :

```text
commande > 0 : direction=1, vitesse=commande
commande < 0 : direction=2, vitesse=-commande
commande = 0 : direction=0, vitesse=0
```

Une correction proportionnelle garde les deux roues alignees :

```text
erreur_direction_m = position_gauche_m - position_droite_m
correction = HEADING_KP * erreur_direction_m
```

## Calibration des ticks par metre

La valeur theorique issue de `2*pi*R` est uniquement informative. Une
calibration reelle est obligatoire.

1. Placez le robot au debut d'un metre mesure.
2. Appuyez sur `A+B`.
3. Faites rouler manuellement le robot sur exactement `1 m`.
4. Appuyez sur `B`.
5. Repetez plusieurs fois pour calculer une moyenne.

## Utilisation

- `A` : remet la position a zero et lance le mouvement vers la distance choisie.
- `B` : choisir la distance, par pas de `10 cm`.
- `B` pendant le mouvement : arret.
- `A+B` pendant le mouvement : arret d'urgence.

## Limite du mouvement manuel

Le registre direction indique la direction commandee au moteur. Lorsque le
robot est pousse manuellement avec les moteurs arretes, la direction vaut `0`.
Le sens du deplacement manuel est alors inconnu et le firmware s'arrete par
securite.
