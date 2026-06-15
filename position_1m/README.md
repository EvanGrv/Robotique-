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

## PID complet en distance

Le terme proportionnel utilise directement l'erreur de distance :

```text
erreur_m = distance_cible_m - position_m
P = kp * erreur_m
```

L'integrale cumule l'erreur de distance. Elle corrige une erreur persistante,
par exemple si les moteurs manquent de force pres de la cible :

```text
integrale_m_s += erreur_m * dt
I = ki * integrale_m_s
```

L'integrale est limitee et suspendue lorsque la commande est saturee afin
d'eviter l'emballement.

Le derive utilise la vitesse mesuree par les codeurs. Il freine le robot quand
il approche de la cible :

```text
vitesse_m_s = (position_m - position_precedente_m) / dt
D = -kd * vitesse_m_s
```

La commande finale est :

```text
commande = P + I + D
```

Valeurs initiales du firmware :

```text
kp = 200
ki = 5
kd = 20
```

Le temps intervient seulement dans `I` et `D`, comme dans tout PID. La
position, l'erreur et la cible restent mesurees en metres par les codeurs.

Conversion de la commande vers la Maqueen :

```text
commande > 0 : direction=1, vitesse=commande
commande < 0 : direction=2, vitesse=-commande
commande = 0 : direction=0, vitesse=0
```

Une correction proportionnelle independante garde les deux roues alignees :

```text
erreur_direction_m = position_gauche_m - position_droite_m
correction = kp_heading * erreur_direction_m
```

## Essai et reglage

Le firmware affiche une ligne `STATUS` chaque seconde avec la position, la
vitesse, l'erreur et les contributions `p`, `i`, `d`.

1. Calibrez d'abord les ticks par metre avec plusieurs mesures exactes.
2. Posez le robot au point de depart et appuyez sur `A`.
3. Laissez-le atteindre la cible sans le toucher.
4. Repetez depuis le meme point, puis depuis une position differente.

Pour regler finement le PID, augmentez d'abord `kp`, ajoutez `kd` pour reduire
le depassement, puis ajoutez seulement un petit `ki` pour supprimer une erreur
finale persistante.

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
