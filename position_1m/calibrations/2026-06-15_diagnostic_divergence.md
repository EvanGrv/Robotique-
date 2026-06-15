# Diagnostic de divergence - 2026-06-15

## Configuration recuperee depuis la micro:bit

```text
ticks_per_meter=539.0
calibrated=True
calibration_samples=1
calibration_ticks_total=539.0
distance_cm=120
kp_position=0.3686
ki_position=0.0
kd_position=0.58
kp_heading=0.75
kd_heading=0.35
```

## Telemetrie observee

```text
cible = 646 ticks
gauche = 2002 ticks
droite = 2015 ticks
moyenne = 2008.5 ticks
distance estimee = 3.726345 m
erreur = -1362.5 ticks
```

## Cause

Les compteurs Maqueen augmentent pendant un recul. Le firmware precedent
supposait qu'ils devenaient negatifs ou diminuaient. Lorsqu'il commandait le
recul, la position mesuree augmentait encore, l'erreur devenait plus negative
et le robot reculait indefiniment.

Ce comportement ne vient pas des valeurs du PID. Le controleur utilisait un
modele de capteur incompatible avec les compteurs exposes par la Maqueen.

## Correction

Le firmware commande maintenant uniquement un parcours vers l'avant et
s'arrete definitivement a la cible. Il inclut egalement :

- un arret si le depassement depasse `30 ticks` ;
- un arret apres `20 secondes` ;
- aucune commande automatique de recul.
