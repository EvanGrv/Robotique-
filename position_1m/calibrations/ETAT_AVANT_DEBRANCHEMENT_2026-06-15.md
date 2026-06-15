# Etat avant debranchement - 2026-06-15

## Code sauvegarde

Le firmware actif est sauvegarde dans :

```text
position_1m/firmware.py
```

Installation future :

```sh
make flash PROJECT=position_1m
```

Dernier commit GitHub verifie avant cette modification :

```text
b0bdd44 fix: control position directly from signed tick error
```

## Etat de la calibration

Le fichier `position_config.txt` n'est pas present sur la micro:bit apres le
dernier flash complet.

La valeur historique `539 ticks/m` a ete declaree incorrecte par l'utilisateur.
Elle reste archivee dans les anciens rapports pour analyse, mais ne doit plus
etre utilisee pour piloter le robot.

Le firmware demarre donc maintenant avec :

```text
calibrated=False
calibration_samples=0
ticks_per_meter=592.204439...  # valeur theorique informative uniquement
```

Le robot refusera de lancer un parcours tant qu'une nouvelle calibration
manuelle n'aura pas ete sauvegardee avec `A+B`, deplacement manuel exact de
1 metre, puis `B`.
