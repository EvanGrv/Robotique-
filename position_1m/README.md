# Parcours mesure par odometrie des roues

Le robot utilise uniquement les encodeurs des roues. La conversion theorique
est :

```text
distance_par_tick = 2 * pi * rayon / ticks_par_tour
ticks_par_metre = ticks_par_tour / (2 * pi * rayon)
```

Avec `rayon = 0,0215 m` et `80 ticks/tour`, la valeur theorique est environ
`592,20 ticks/m`. Comme les ticks reels exposes par la Maqueen peuvent differer,
le firmware permet de mesurer puis sauvegarder la valeur reelle.

## Installation

```sh
make flash PROJECT=position_1m
```

Le robot fonctionne ensuite sans ordinateur.

## Calibration reelle des ticks par metre

1. Placez le robot au debut d'une distance mesuree de exactement `1 m`.
2. Appuyez sur `A+B`. Les encodeurs sont remis a zero et `C` s'affiche.
3. Faites rouler manuellement le robot jusqu'au repere de 1 m, sans le soulever.
4. Appuyez sur `B`.

La moyenne absolue des deux encodeurs devient un nouvel echantillon. Le
firmware sauvegarde la moyenne cumulative de toutes les mesures comme
`ticks_per_meter`.

Repetez cette procedure au moins cinq fois pour reduire l'erreur de placement
manuel. La valeur sauvegardee converge vers la moyenne des mesures.

## Parcourir une distance cible

Au repos :

- `B` ouvre le choix de distance.
- Dans le choix de distance, `A` ajoute `10 cm` et `B` sauvegarde.
- `A` definit la position actuelle comme origine `0`, calcule la cible et lance
  le parcours vers l'avant.

Exemple pour une cible de `1 m` :

```text
origine = 0 tick
cible = ticks_par_metre
erreur = cible - position_actuelle
```

Pendant un mouvement commande, le firmware lit a la fois :

```text
delta_ticks = (compteur_actuel - compteur_precedent) modulo 65536
position_signee += delta_ticks * signe(direction_moteur)
```

`direction=1` ajoute les ticks et `direction=2` les soustrait. Le PID peut donc
corriger un depassement en commandant un recul.

La commande moteur utilise toujours une vitesse positive :

```text
si commande > 0 : direction = 1, vitesse = commande
si commande < 0 : direction = 2, vitesse = abs(commande)
```

Donner directement une vitesse negative a la Maqueen serait incorrect.

Lorsque la cible est atteinte, les moteurs sont arretes et le parcours se
termine. Une limite de temps et une limite de depassement provoquent aussi un
arret de securite.

`B` ou `A+B` arrete le parcours.

## Point de reference

Les encodeurs mesurent une position relative a l'origine choisie avec `A`.
Pour partir depuis une position deja situee a `10 cm` du debut physique, il faut
que cette position soit connue dans les ticks. Si `A` est presse a cet endroit,
il devient volontairement la nouvelle origine `0`.

Le robot ne peut pas connaitre un deplacement effectue en le soulevant.

Les compteurs exposes par la Maqueen Plus V1 augmentent egalement lors d'un
recul manuel. Le registre de direction indique la direction commandee au
moteur, pas le sens physique detecte par l'encodeur. Si les roues tournent
manuellement pendant que les moteurs sont arretes (`direction=0`), le sens est
inconnu : le firmware declenche un arret de securite au lieu d'inventer une
position.

## PID

Le nombre de ticks par metre vient de la geometrie/calibration, pas du PID.

```text
commande = P * erreur
         + I * integrale(erreur)
         + D * derivee(erreur)
```

Les gains sauvegardes actuellement sont :

```text
P position = 0.3686
I position = 0.0
D position = 0.58
P direction = 0.75
D direction = 0.35
```

Ils peuvent etre ajustes apres observation, mais aucun entrainement n'est
necessaire pour calculer les distances.
