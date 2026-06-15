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

Le nombre moyen de ticks mesure devient `ticks_per_meter`. La position courante
devient immediatement `1 m` et le PID commence a la maintenir.

## Utilisation

- `A` : reactiver le maintien de la position `1 m`.
- `B` pendant la calibration : enregistrer la position `1 m`.
- `A+B` : refaire la mesure manuelle de `1 m`.

Le zero est cree uniquement au debut de `A+B`. Il n'est jamais recrée lorsque
le robot atteint la cible, sinon le robot croirait a tort etre revenu a `0 m`
et repartirait vers l'avant.

Etats affiches :

- `R` : maintien en pause ;
- `C` : calibration obligatoire ou en cours ;
- fleche haute/basse : correction PID ;
- cible : position `1 m` maintenue.

Le PID initialise l'integrale et l'erreur precedente a zero avant chaque
trajet. Les gains actuels sont :

```python
KP, KI, KD = 200, 0, 0
```

Un seul trajet manuel calibre les ticks par metre. Il ne permet pas de calculer
automatiquement des gains PID optimaux.
