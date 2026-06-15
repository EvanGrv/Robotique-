# Positionnement autonome avec calibration PID

Ce projet fonctionne sans ordinateur apres son installation. Les boutons de la
micro:bit commandent la calibration, les essais PID, la distance et le depart.

## Installation initiale

Depuis la racine du depot :

```sh
make install PROJECT=position_1m
```

Debranchez ensuite le cable USB. Le robot fonctionne avec les batteries de la
Maqueen.

## Commandes des boutons

### Au repos

- `A` : lancer le parcours avec la distance memorisee.
- `B` : choisir une distance entre 10 cm et 500 cm, par pas de 10 cm.
- `A+B` : ouvrir le menu calibration.

### Choix de distance

- `A` : ajouter 10 cm.
- `B` : sauvegarder et revenir au repos.

### Menu calibration

- `A` : commencer la mesure manuelle des ticks sur exactement 1 metre.
- `B` : ouvrir le mode de calibration PID.

### Mesure manuelle des ticks

1. Placez le robot au debut d'une distance mesuree de exactement 1 metre.
2. Au repos, appuyez sur `A+B`, puis sur `A`.
3. Faites rouler manuellement le robot jusqu'au repere de 1 metre, sans le
   soulever.
4. Appuyez sur `B` a l'arrivee.

Le robot sauvegarde la moyenne absolue des deux encodeurs comme
`ticks_per_meter`, puis ouvre automatiquement le mode de calibration PID.

### Calibration PID par essais

1. Replacez manuellement le robot au depart.
2. Appuyez sur `A` pour lancer un essai motorise.
3. Le robot parcourt la distance memorisee, s'arrete, calcule un score, conserve
   le meilleur PID connu puis prepare le candidat suivant.
4. Replacez-le au depart et appuyez de nouveau sur `A`.
5. Realisez idealement entre 20 et 30 essais afin de tester les gains dans les
   deux directions et de reduire progressivement les pas.
6. Appuyez sur `B` pour terminer : le meilleur PID mesure est restaure et
   sauvegarde.

Pendant tout mouvement, `A+B` provoque un arret d'urgence.

## Parametres memorises

Le fichier `position_config.txt` est sauvegarde dans la micro:bit :

```text
ticks_per_meter
calibrated
distance_cm
kp_position
ki_position
kd_position
kp_heading
kd_heading
pid_trials
```

Pour recuperer ces valeurs apres avoir reconnecte le cable USB :

```sh
make read-config PROJECT=position_1m
```

Le fichier est alors copie dans `position_1m/position_config.txt`.

## Entrainement PID utilise

Il n'existe pas de formule permettant de calculer exactement les gains PID a
partir d'un seul parcours manuel. Le parcours manuel calibre uniquement les
ticks par metre.

Chaque essai motorise mesure ensuite :

```text
depassement = position_finale - position_cible
erreur_direction = encodeur_gauche - encodeur_droit
score = abs(depassement) * 10
      + depassement_positif * 20
      + abs(erreur_direction) * 2
      + duree_en_secondes
```

Le depassement est davantage penalise qu'un arret legerement trop court. Le
robot teste successivement :

```text
P position
I position
D position
P direction
D direction
```

Pour chaque gain, il essaie une augmentation puis une diminution. Si le score
s'ameliore, le nouveau PID devient le meilleur. Sinon, le meilleur PID est
restaure, le pas de recherche diminue, puis le gain suivant est teste.

`I_position` commence a zero, mais il est maintenant reellement teste avec de
tres petits pas. Il restera nul si son ajout degrade le score.

## Limites physiques

Les encodeurs mesurent la rotation des roues, pas la position absolue sur le
sol. Un glissement, un deplacement du robot en le soulevant ou une roue bloquee
fausse la position.

Pour une garantie physique stricte du point d'arrivee, il faudra ajouter un
repere externe, par exemple une ligne au sol detectee par les capteurs de la
Maqueen.
