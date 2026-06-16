# Trajet automatique de 1 m

Des que la Maqueen est detectee, le firmware :

1. arrete les moteurs ;
2. remet les compteurs et la position a zero ;
3. calcule la cible theorique de `1 m` ;
4. active automatiquement le PID.

```python
TARGET_TICKS = 80 / (2 * pi * 0.0215)  # environ 592 ticks
KP, KI, KD = 1, 0, 0
MIN_SPEED = 40
MAX_SPEED = 200
TOLERANCE_TICKS = 4
```

La commande est proportionnelle a la distance restante avec une vitesse
minimale de correction hors tolerance :

```python
error_ticks = TARGET_TICKS - position_ticks
commande = KP * error_ticks
```

## Boutons

- `A` : remettre la position a zero et recommencer un trajet de `1 m`.
- `B` : arreter le robot.

## Affichage

- croix : Maqueen non detectee ;
- fleche : trajet actif ;
- cible : position de `1 m` atteinte ;
- petit carre : arret manuel.
