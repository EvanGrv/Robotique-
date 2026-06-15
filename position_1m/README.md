# Position 1 m - base minimale

Le firmware contient uniquement :

1. `coders()` et `directions()` pour lire la Maqueen.
2. `update_position()` pour cumuler les ticks signes.
3. `motor()` pour avancer ou reculer.
4. `move_to()` pour calculer le PID.

## Premier test

1. Appuyer sur `A+B` pour remettre les compteurs a zero.
2. Faire rouler manuellement le robot sur exactement `1 m`.
3. Appuyer sur `B`.

Le nombre moyen de ticks mesure devient `ticks_per_meter`.

## Utilisation

- `A` : aller a la position `1 m`.
- `B` : arreter et remettre la position a zero.
- `A+B` : refaire la mesure manuelle de `1 m`.

Le PID initialise l'integrale et l'erreur precedente a zero avant chaque
trajet. Les gains actuels sont :

```python
KP, KI, KD = 200, 0, 0
```

Un seul trajet manuel calibre les ticks par metre. Il ne permet pas de calculer
automatiquement des gains PID optimaux.
