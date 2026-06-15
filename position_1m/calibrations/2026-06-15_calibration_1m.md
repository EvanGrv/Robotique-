# Calibration 1 metre - 2026-06-15

Cet instantane a ete recupere depuis la memoire persistante de la micro:bit
avant qu'un autre programme soit injecte.

## Donnees brutes recuperees

```text
ticks_per_meter=539.0
calibrated=True
distance_cm=100
kp_position=0.3686
ki_position=0.0
kd_position=0.58
kp_heading=0.75
kd_heading=0.35
pid_trials=2
```

## Valeurs derivees

En prenant la mesure manuelle de 1 metre comme reference :

```text
ticks par metre = 539
distance par tick = 1 / 539 = 0.00185529 m
distance par tick = 1.85529 mm
```

La mesure reelle remplace l'estimation theorique de `592.2 ticks/m`.

## Cibles de distance

Les cibles sont arrondies vers le bas afin de limiter le risque de depassement.

| Distance | Cible |
|---:|---:|
| 0.10 m | 53 ticks |
| 0.20 m | 107 ticks |
| 0.50 m | 269 ticks |
| 1.00 m | 539 ticks |
| 1.50 m | 808 ticks |
| 2.00 m | 1078 ticks |
| 3.00 m | 1617 ticks |
| 4.00 m | 2156 ticks |
| 5.00 m | 2695 ticks |

## PID sauvegarde

```text
Kp position = 0.3686
Ki position = 0.0
Kd position = 0.58
Kp direction = 0.75
Kd direction = 0.35
Nombre d'essais PID = 2
```

Ces gains sont les derniers gains sauvegardes par le robot. Les donnees
intermediaires des deux essais n'etaient pas conservees par l'ancienne version
du firmware, donc il n'est pas possible de recalculer d'autres gains de facon
rigoureuse a partir de cette seule configuration finale.

## Diagnostic USB

Le volume MICROBIT contenait egalement :

```text
Assert
File: ../../../source/daplink/circ_buf.c
Line: 172
Source: Application
```

Cette assertion concerne l'interface USB DAPLink, pas directement les calculs
des encodeurs ou du PID.
