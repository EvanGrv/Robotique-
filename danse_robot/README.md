# Danse autonome Maqueen

Ce projet combine :

- une choregraphie autonome ;
- la detection d'obstacles avec l'ultrason sur `pin8`/`pin12` ;
- une esquive prioritaire ;
- des icones correspondant aux mouvements ;
- des notes jouees pendant la danse ;
- une tentative courte et protegee de figure sur les roues arriere.

## Utilisation

```bash
make check PROJECT=danse_robot
make flash PROJECT=danse_robot
```

- `B` : arrete et met la danse en pause.
- `A` : reprend apres une pause.

## Securite

La figure sur les roues arriere est experimentale. Elle est limitee a `700 ms`
et s'arrete si un obstacle ou une inclinaison importante est detecte.

Un equilibre dynamique durable exige de calibrer l'axe de l'accelerometre, la
position cible et les gains d'une boucle de controle d'inclinaison sur le robot
reel. Le firmware actuel realise une impulsion protegee, pas un maintien
d'equilibre garanti.
