# Etat sauvegarde avant remplacement du programme

Derniere verification : 2026-06-15.

## GitHub

Depot :

```text
https://github.com/EvanGrv/Robotique-
```

Dernier commit sauvegarde :

```text
1092f52 fix: prevent odometry direction divergence
```

## Dernieres valeurs recuperees

```text
ticks_per_meter=539.0
calibration_samples=1
calibration_ticks_total=539.0
distance_cm=120

kp_position=0.3686
ki_position=0.0
kd_position=0.58
kp_heading=0.75
kd_heading=0.35
```

## Derniere telemetrie avant correctif

```text
target_ticks=646
left=2002
right=2015
average=2008.5
distance_m=3.726345
error=-1362.5
```

Cette telemetrie a permis de confirmer que les compteurs Maqueen augmentent
egalement lors d'un recul et ne fournissent pas un sens de rotation exploitable.

## Fichiers de reference

- `position_1m/firmware.py` : dernier firmware corrige.
- `position_1m/README.md` : procedure et limites.
- `position_1m/calibrations/2026-06-15_position_config_raw.txt` : premiere
  configuration brute recuperee.
- `position_1m/calibrations/2026-06-15_calibration_1m.md` : rapport initial.
- `position_1m/calibrations/2026-06-15_diagnostic_divergence.md` : analyse du
  mouvement infini et correctif.

## Etat de la micro:bit

Le dernier flash complet a nettoye le systeme de fichiers interne. Le fichier
`position_config.txt` n'est donc plus present sur la carte. Les valeurs utiles
sont toutefois archivees dans GitHub et integrees comme valeurs par defaut dans
le firmware.
