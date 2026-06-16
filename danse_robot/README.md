# Danse autonome Maqueen

Ce projet combine dans une boucle simple :

- la detection d'obstacles avec l'ultrason sur `pin8`/`pin12` ;
- une esquive prioritaire ;
- une danse avec affichage et musique ;
- des segments de danse pilotes par le PID de position du projet `position_1m` ;
- un test de roue arriere : arret, puis impulsion a vitesse `255`.

## Utilisation

```bash
make check PROJECT=danse_robot
make flash PROJECT=danse_robot
```

- `B` : arrete et met la danse en pause.
- `A` : reprend apres une pause.

## Securite

La detection d'obstacle est prioritaire pendant chaque segment de danse. Si un
obstacle est detecte a moins de `20 cm`, le robot stoppe, recule, tourne, puis
reprend la danse.

Le test de roue arriere est volontairement tres court (`180 ms`) car la vitesse
`255` est brutale. Ce n'est pas un maintien d'equilibre garanti.
