# Donnees recuperees apres le test 1,30 m

## Configuration de la micro:bit

```text
ticks_per_meter=539.0
calibrated=True
calibration_samples=1
calibration_ticks_total=539.0
distance_cm=130
kp_position=0.3686
ki_position=0.0
kd_position=0.58
kp_heading=0.75
kd_heading=0.35
```

La cible calculee pour `1,30 m` est :

```text
int(539 * 1.30) = 700 ticks
```

La carte etait revenue au REPL MicroPython lors de la premiere lecture. Un
redemarrage logiciel a ensuite montre un firmware au repos avec une position
reinitialisee a zero. Aucune telemetrie du mouvement rate n'etait encore
disponible.

## Analyse du controleur

La version precedente utilisait :

```text
commande = P * erreur + I * integrale(erreur * dt) + D * delta_erreur / dt
```

Le terme derive etait donc explicitement dependant du temps. La nouvelle
version suit le modele discret demande :

```text
commande = P * erreur_ticks
```

`I` et `D` ne sont plus utilises dans la commande moteur.
