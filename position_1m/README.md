# Position 1 m - base minimale

Le firmware contient uniquement :

1. `coders()` et `directions()` pour lire la Maqueen.
2. `update_position()` pour cumuler les ticks signes.
3. `motor()` pour avancer ou reculer.
4. `move_to()` pour calculer le PID.

## Premier test

Au demarrage, toutes les valeurs sont remises a zero :

```text
ticks_per_meter = 0
ticks = 0
integrale = 0
erreur_precedente = 0
```

Aucune valeur theorique et aucune ancienne calibration ne sont utilisees.

1. Appuyer sur `A+B` pour lancer la mesure et remettre les compteurs a zero.
2. Faire rouler manuellement le robot sur exactement `1 m`.
3. Appuyer sur `B`.

Le nombre moyen de ticks mesure devient `ticks_per_meter`.

Pendant la calibration et ensuite toutes les `500 ms`, le port serie affiche :

```text
READ compteur_gauche compteur_droit direction_gauche direction_droite ticks_signes position
```

Cela permet de verifier directement si l'adresse `0x00` renvoie `1` en poussant
le robot vers l'avant et `2` en le poussant vers l'arriere.

## Utilisation

- `A` : aller a la position `1 m`.
- `B` : arreter et remettre la position a zero.
- `A+B` : refaire la mesure manuelle de `1 m`.

Etats affiches :

- `R` : pret ;
- `C` : calibration obligatoire ou en cours ;
- fleche haute/basse : PID en mouvement ;
- cible : position atteinte.

Le PID initialise l'integrale et l'erreur precedente a zero avant chaque
trajet. Les gains actuels sont :

```python
KP, KI, KD = 200, 0, 0
```

Un seul trajet manuel calibre les ticks par metre. Il ne permet pas de calculer
automatiquement des gains PID optimaux.
