# Ligne droite avec detection d'obstacle

Premiere etape du projet danse : le robot avance tout droit et s'arrete si un
obstacle est detecte a moins de `20 cm`.

Materiel utilise :

- moteurs Maqueen sur I2C `0x10` ;
- trigger ultrason sur `pin8` ;
- echo ultrason sur `pin12`.

Commandes :

```bash
make check PROJECT=danse_robot
make flash PROJECT=danse_robot
```

Reaction obstacle :

- stop ;
- arret pendant `100 ms` ;
- recul a vitesse maximale pendant `1 s` ;
- reprise immediate en avant a vitesse maximale.

Affichage :

- fleche haut : avance a vitesse maximale (`255`) ;
- croix : obstacle detecte pendant la reaction.
