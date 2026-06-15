# Position 1 m - base minimale

Le firmware contient uniquement :

1. `coders()` et `directions()` pour lire la Maqueen.
2. `update_position()` pour cumuler les ticks signes.
3. `motor()` pour avancer ou reculer.
4. `move_to()` pour calculer le PID.

## Premier test

Au demarrage, toutes les valeurs sont remises a zero :

```text
target_ticks = 0
ticks = 0
integrale = 0
erreur_precedente = 0
```

Aucune valeur theorique et aucune ancienne calibration ne sont utilisees.

1. Appuyer sur `A+B` pour lancer la mesure et remettre les compteurs a zero.
2. Faire rouler manuellement le robot sur exactement `1 m`.
3. Appuyer sur `B`.

Le nombre moyen de ticks mesure devient `target_ticks`. Cette reference est
capturee une seule fois. La position courante devient immediatement cette
reference et le PID commence a la maintenir.

## Utilisation

- `A` : reactiver le maintien de la position `1 m`.
- `B` pendant la calibration : enregistrer la position `1 m`.
- `A+B` : refaire la mesure manuelle de `1 m`.

Le zero est cree uniquement au debut de `A+B`. Il n'est jamais recrée lorsque
le robot atteint la cible, sinon le robot croirait a tort etre revenu a `0 m`
et repartirait vers l'avant.

Etats affiches :

- `R` : maintien en pause ;
- `C` : calibration obligatoire ou en cours ;
- fleche haute/basse : correction PID ;
- cible : position `1 m` maintenue.

Le PID travaille directement avec l'erreur en ticks et produit l'octet de
vitesse envoye a la Maqueen :

```python
erreur_ticks = ticks_cible - ticks_actuels
commande = KP * erreur_ticks

KP, KI, KD = 2, 0, 0
MAX_SPEED = 200
TOLERANCE_TICKS = 6
```

La commande reste nulle dans une zone de `6 ticks`. Hors de cette zone, elle
est strictement proportionnelle : `2` octets de vitesse par tick d'erreur,
jusqu'a la limite configuree de `200`.

Chaque lecture I2C suit explicitement :

```python
i2c.write(ADDR, bytes([registre]))  # place le curseur
data = i2c.read(ADDR, 4)            # lit le registre choisi
```

La commande moteur est ecrite uniquement lorsqu'elle change. Dans la zone
cible, l'arret est donc envoye une seule fois au lieu d'ecraser le registre de
direction `0x00` toutes les `10 ms`.
