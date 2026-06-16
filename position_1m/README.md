# Trajet automatique de 1 m

Des que la Maqueen est detectee, le firmware :

1. arrete les moteurs ;
2. remet les compteurs et la position a zero ;
3. calcule la cible theorique de `1 m` ;
4. active automatiquement le PID.

```python
TARGET_TICKS = 80 / (2 * pi * 0.0215)  # environ 592 ticks
KP, KI, KD = 0.8, 0, 0
MAX_SPEED = 200
```

La commande est strictement proportionnelle a la distance restante. Il n'y a
plus de zone de tolerance et plus de vitesse minimale forcee :

```python
error_ticks = TARGET_TICKS - position_ticks
commande = KP * error_ticks
```

La vitesse diminue donc naturellement en approchant de la cible.

## Boutons

- `A` : remettre la position a zero et recommencer un trajet de `1 m`.
- `B` : arreter le robot.

## Affichage

- croix : Maqueen non detectee ;
- fleche : trajet actif ;
- cible : position de `1 m` atteinte ;
- petit carre : arret manuel.
